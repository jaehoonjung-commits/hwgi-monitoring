# FastAPI Grafana Webhook Receiver Sample

Grafana Alerting Webhook을 FastAPI로 받아서 alert 주요 내용을 콘솔에 출력하는 샘플입니다.

## 1) 실행

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

로그 레벨, 수신자 설정 파일 경로, Gmail 발송 계정을 환경변수로 변경할 수 있습니다.

```bash
LOG_LEVEL=DEBUG \
RECIPIENT_CONFIG_PATH=recipients.yaml \
FILE_OUTPUT_PATH=notification_results.log \
GMAIL_USER=sender@gmail.com \
GMAIL_APP_PASSWORD=abcdefghijklmnop \
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Docker 실행

이미지 빌드:

```bash
docker build -t grafana-webhook-receiver .
```

컨테이너 실행:

```bash
docker run --rm -p 8000:8000 \
  -e FILE_OUTPUT_PATH=/tmp/notification_results.log \
  -e GMAIL_USER=jaehoon.jung@kubeworks.net \
  -e GMAIL_APP_PASSWORD="owai wpqi oecn wvnm" \
  grafana-webhook-receiver
```

Gmail은 일반 계정 비밀번호가 아니라 앱 비밀번호를 사용해야 합니다.

## 3) 테스트 요청 예시

```bash
curl -X POST http://localhost:8000/webhook/grafana \\
  -H "Content-Type: application/json" \\
  -d '{
    "receiver": "webhook_receiver",
    "status": "firing",
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighCPUUsage",
          "severity": "critical",
          "instance": "server-01"
        },
        "annotations": {
          "summary": "CPU usage is high",
          "description": "CPU usage is above 90% for 5 minutes"
        },
        "startsAt": "2026-04-07T10:00:00Z",
        "endsAt": "0001-01-01T00:00:00Z"
      }
    ]
  }'
```

## 4) 확인 포인트

요청을 보내면 서버 콘솔에 다음 항목들이 출력됩니다.

- receiver
- status
- alerts_count
- 각 alert의 status, alertname, severity, instance
- summary, description, startsAt, endsAt

## 5) 브라우저에서 수신자 설정 확인 API

수신자 설정을 웹 브라우저에서 읽기 전용 표 형태로 확인할 수 있습니다.

- URL: `GET /recipients`
- 예시: `http://localhost:8000/recipients`

이 API는 현재 `RECIPIENT_CONFIG_PATH`에 설정된 YAML 파일을 읽어 다음 항목을 표시합니다.

- id
- team_name
- recipient_group_name
- instance_name
- email
- phone_number
- alert_receive_level
- notification_channels

## 6) 수신자 설정 파일

`recipients.yaml` 파일에서 수신자를 관리합니다. 서버는 웹훅 요청마다 파일을 다시 읽기 때문에 파일 수정 후 재배포 없이 규칙을 바꿀 수 있습니다.

- 수신자 구조: recipients 리스트 (oncall-p1 같은 별도 키 없이 사용)
- 수신자 속성: id(10자리 숫자), phone_number, email, team_name, recipient_group_name, instance_name, alert_receive_level, notification_channels

알림은 수신자의 `alert_receive_level`이 alert `severity`와 일치하고, 수신자의 `recipient_group_name`이 alert `labels.recipient_group_name`과 일치하는 경우에만 전송됩니다.

`notification_channels`에 `gmail`, `sms`, `kakao`, `file`을 지정할 수 있습니다. `file` 채널은 `FILE_OUTPUT_PATH`에 JSON Lines 형식으로 결과를 append 합니다. 채널별 환경변수가 없으면 외부 연동 채널은 DRY-RUN(로그 출력) 모드로 동작합니다.

`kakao` 채널은 UMS 엔드포인트로 전문을 생성해 전송합니다.

- 필수: `UMS_API_URL`
- 선택: `UMS_API_KEY`, `UMS_CHNL_SYS_CD`, `UMS_IF_ORG_CD`, `UMS_APPL_CD`, `UMS_IF_KIND_CD`, `UMS_IF_TX_CD`, `UMS_SFTNO`, `UMS_ECARD_NO`, `UMS_CHANNEL`, `UMS_TMPL_TYPE`, `UMS_SENDER_NAME`, `UMS_TIMEOUT_SEC`

현재 예시 Kubernetes 매니페스트는 `ConfigMap`을 `/config/recipients.yaml`에 읽기 전용으로 마운트하며, `/recipients` API는 해당 설정을 조회만 합니다.
