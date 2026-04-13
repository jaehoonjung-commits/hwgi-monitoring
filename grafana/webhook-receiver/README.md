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

## 5) 수신자 설정 파일

`recipients.yaml` 파일에서 수신자와 라우팅 규칙을 관리합니다. 서버는 웹훅 요청마다 파일을 다시 읽기 때문에 파일 수정 후 재배포 없이 규칙을 바꿀 수 있습니다.

- 수신자 구조: recipients 리스트 (oncall-p1 같은 별도 키 없이 사용)
- 수신자 속성: id(10자리 숫자), phone_number, email, team_name, recipient_group_name, instance_name, alert_receive_level, notification_channels
- 규칙: instance_pattern(정규식), severity, recipient_group_name

라우팅이 없을 때는 `alert_receive_level`이 alert의 `severity`와 일치하고, 수신자의 `recipient_group_name`이 alert `labels.recipient_group_name`과 일치하는 경우에만 전송됩니다.

`notification_channels`에 `gmail`, `sms`, `kakao`를 지정할 수 있습니다. 채널별 환경변수가 없으면 해당 채널은 DRY-RUN(로그 출력) 모드로 동작합니다.
