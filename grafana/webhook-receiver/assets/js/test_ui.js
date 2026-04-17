        const SERVER_UMS_API_URL = window.SERVER_UMS_API_URL || "";

        function safeParseJson(text) {
            try {
                return JSON.parse(text);
            } catch {
                return null;
            }
        }

        function setSelectOptions(selectId, options, fallbackValue) {
            const select = document.getElementById(selectId);
            if (!select) {
                return;
            }

            const normalizedOptions = Array.from(
                new Set((Array.isArray(options) ? options : []).map(value => String(value).trim()).filter(Boolean))
            );
            const selectedValue = normalizedOptions.includes(fallbackValue)
                ? fallbackValue
                : (normalizedOptions[0] || fallbackValue);

            if (!normalizedOptions.includes(selectedValue)) {
                normalizedOptions.unshift(selectedValue);
            }

            select.innerHTML = normalizedOptions
                .map(value => `<option value="${value}">${value}</option>`)
                .join('');
            select.value = selectedValue;
        }

        async function initializeGrafanaFilterOptions() {
            try {
                const response = await fetch('/api/grafana-filter-options');
                const responseText = await response.text();
                const data = safeParseJson(responseText) || {};

                setSelectOptions('grafana_severity', data.severities, 'warning');
                setSelectOptions('grafana_group', data.groups, 'dev-1');
            } catch {
                setSelectOptions('grafana_severity', ['warning'], 'warning');
                setSelectOptions('grafana_group', ['dev-1'], 'dev-1');
            }
        }

        function buildFallbackIfGlobalNo(linkCode) {
            const now = new Date();
            const dateStr = String(now.getFullYear()) +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            return dateStr + String(now.getMilliseconds()).padStart(3, '0') + linkCode + '000001';
        }

        function getUmsApiUrlInput() {
            const input = document.getElementById('ums_api_url');
            const value = input ? input.value.trim() : '';
            return value || SERVER_UMS_API_URL || 'http://ums-service.example.com:8080/api/ums';
        }

        function initializeUmsApiUrlInput() {
            const input = document.getElementById('ums_api_url');
            if (!input) {
                return;
            }
            input.value = SERVER_UMS_API_URL || 'http://ums-service.example.com:8080/api/ums';
        }

        function resolveUmsExecuteUrl(rawInput) {
            const trimmed = String(rawInput || '').trim();
            if (!trimmed) {
                return '';
            }
            if (/^https?:\/\//i.test(trimmed)) {
                return trimmed;
            }
            const normalizedPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
            return `${window.location.origin}${normalizedPath}`;
        }

        function getGrafanaApiUrlInput() {
            const input = document.getElementById('grafana_api_url');
            const value = input ? input.value.trim() : '';
            return value || 'http://ums-service.example.com:8080/api/ums';
        }

        function resolveGrafanaExecuteUrl(rawInput) {
            const trimmed = String(rawInput || '').trim();
            if (!trimmed) {
                return 'http://localhost:8000/grafana/webhook';
            }
            if (/^https?:\/\//i.test(trimmed)) {
                return trimmed;
            }
            const normalizedPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
            return `${window.location.origin}${normalizedPath}`;
        }

        function setValues(values) {
            Object.entries(values).forEach(([id, value]) => {
                document.getElementById(id).value = value;
            });
            document.getElementById('curl-output').textContent = 'Ready to generate...';
        }

        function hideResponse() {
            document.getElementById('response-container').classList.remove('active');
        }

        function showCopySuccess() {
            const msg = document.getElementById('success-message');
            msg.style.display = 'block';
            setTimeout(() => {
                msg.style.display = 'none';
            }, 2000);
        }

        function resetGeneratedOutput() {
            document.getElementById('curl-output').textContent = 'Ready to generate...';
            hideResponse();
            lastPayload = null;
            lastRequestUrl = null;

            const executeBtn = document.getElementById('execute-btn');
            if (executeBtn) {
                executeBtn.classList.remove('loading');
                executeBtn.disabled = false;
                executeBtn.textContent = '▶ Execute';
            }
        }

        function switchTab(event, tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            resetGeneratedOutput();
        }

        function buildGrafanaRequestData() {
            const alertname = document.getElementById('grafana_alertname').value || 'Alert';
            const severity = document.getElementById('grafana_severity').value || 'warning';
            const instance = document.getElementById('grafana_instance').value || 'instance-1';
            const group = document.getElementById('grafana_group').value || 'dev-1';
            const summary = document.getElementById('grafana_summary').value || 'Summary';
            const description = document.getElementById('grafana_description').value || 'Description';
            const now = new Date().toISOString();
            return {
                title: 'Grafana Webhook Curl',
                url: 'http://localhost:8000/grafana/webhook',
                payload: {
                    receiver: 'webhook_receiver',
                    status: 'firing',
                    alerts: [{
                        status: 'firing',
                        labels: {
                            alertname: alertname,
                            severity: severity,
                            alert_group: group,
                            instance: instance,
                        },
                        annotations: {
                            summary: summary,
                            description: description,
                        },
                        startsAt: now,
                        endsAt: '0001-01-01T00:00:00Z',
                    }],
                },
            };
        }

        async function buildUmsRequestData(grafanaRequest) {
            const previewResp = await fetch('/api/preview-kakao-requests', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(grafanaRequest.payload),
            });

            const previewData = safeParseJson(await previewResp.text());
            const kakaoRequests = Array.isArray(previewData?.kakao_requests) ? previewData.kakao_requests : [];
            const resolvedRecipients = Array.isArray(previewData?.resolved_recipients) ? previewData.resolved_recipients : [];
            const firstRequest = kakaoRequests[0] || {};
            const umsApiUrl = getGrafanaApiUrlInput() || getUmsApiUrlInput() || previewData?.ums_api_url || '';

            return {
                title: kakaoRequests.length > 0
                    ? `recipients.yaml match: ${kakaoRequests.length})`
                    : `매칭된 kakao 수신자 없음, resolved: ${resolvedRecipients.length})`,
                hasKakaoRecipient: kakaoRequests.length > 0,
                payload: firstRequest.request_payload || { header: {}, payload: { cnt: 0, request: [] } },
                umsApiUrl,
            };
        }

        async function buildUmsRequestDataFromForm() {
            const alertname = document.getElementById('ums_alertname').value || 'Alert';
            const instance = document.getElementById('ums_instance').value || 'Instance';
            const summary = document.getElementById('ums_summary').value || 'Summary';
            const receiverName = document.getElementById('ums_receiver_name').value || 'Name';
            const receiverPhone = document.getElementById('ums_receiver_phone').value || '01000000000';
            const ecare = document.getElementById('ums_ecare').value || '3402';
            const channel = document.getElementById('ums_channel').value || 'A';
            const umsApiUrl = getUmsApiUrlInput();
            const now = new Date();
            const timeStr = String(now.getHours()).padStart(2, '0') + '|' +
                String(now.getMinutes()).padStart(2, '0') + '|' +
                String(now.getSeconds()).padStart(2, '0');

            return {
                title: 'Kakao Webhook Curl (UMS form override)',
                umsApiUrl,
                payload: {
                    header: {
                        ifGlobalNo: await generateIfGlobalNo(),
                        chnlSysCd: 'AAA',
                        ifOrgCd: 'UMS',
                        applCd: 'MUMS',
                        ifKindCd: '0100',
                        ifTxCd: '10000',
                        stfno: '8094310',
                        respCd: '',
                        respMsg: '',
                    },
                    payload: {
                        cnt: 1,
                        request: [{
                            ecareNo: parseInt(ecare),
                            channel: channel,
                            tmplType: 'J',
                            receiverNm: receiverName,
                            receiver: receiverPhone,
                            sender: '1566-8000',
                            senderNm: '한화손해보험',
                            reqUserId: '8094310',
                            jonmun: '@s@|f|6|Grafana|' + alertname + '|' + instance + ' - ' + summary + '|' + timeStr,
                        }],
                    },
                },
            };
        }

        async function generateGrafanaCurl() {
            const grafanaRequest = buildGrafanaRequestData();
            const umsRequest = await buildUmsRequestData(grafanaRequest);
            displayBothCurls(grafanaRequest, umsRequest);
            storeRequestInfo(grafanaRequest.url, grafanaRequest.payload);
            hideResponse();
        }

        async function generateUmsCurl() {
            const umsRequest = await buildUmsRequestDataFromForm();
            displayUmsCurlOnly(umsRequest);
            storeRequestInfo(resolveUmsExecuteUrl(umsRequest.umsApiUrl), umsRequest.payload);
            hideResponse();
        }

        async function generateIfGlobalNo() {
            try {
                const response = await fetch('/api/generate-if-global-no');
                if (!response.ok) {
                    return buildFallbackIfGlobalNo('MUMS');
                }
                const data = await response.json();
                return data.ifGlobalNo;
            } catch {
                return buildFallbackIfGlobalNo('GRFN');
            }
        }

        function buildCurlCommand(baseUrl, endpoint, payload) {
            return `curl -X POST "${baseUrl}${endpoint}" \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(payload, null, 2)}'`;
        }

        function displayBothCurls(grafanaRequest, umsRequest) {
            const umsSection = umsRequest.baseUrl
                ? [`POST ${umsRequest.umsApiUrl || '(설정 없음)'}`, JSON.stringify(umsRequest.payload, null, 2)].join('\n')
                : `### ${umsRequest.title}\n# recipients.yaml 매칭된 kakao 수신자가 없습니다.`;

            document.getElementById('curl-output').textContent = [
                `### ${grafanaRequest.title}`,
                buildCurlCommand(grafanaRequest.baseUrl, grafanaRequest.endpoint, grafanaRequest.payload),
                umsSection,
            ].join('\n\n');
        }

        function copyCurl() {
            const curlText = document.getElementById('curl-output').textContent;
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(curlText)
                    .then(() => showCopySuccess())
                    .catch(() => fallbackCopyText(curlText));
                return;
            }
            fallbackCopyText(curlText);
        }

        function fallbackCopyText(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            textarea.style.top = '0';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            try {
                if (document.execCommand('copy')) {
                    showCopySuccess();
                } else {
                    alert('Failed to copy. Please select and copy manually.');
                }
            } catch (err) {
                alert('Failed to copy: ' + err);
            } finally {
                document.body.removeChild(textarea);
            }
        }

        function clearGrafanaFilters() {
            const severitySelect = document.getElementById('grafana_severity');
            const groupSelect = document.getElementById('grafana_group');
            if (severitySelect && severitySelect.options.length > 0) {
                severitySelect.selectedIndex = 0;
            }
            if (groupSelect && groupSelect.options.length > 0) {
                groupSelect.selectedIndex = 0;
            }
        }

        function clearGrafanaForm() {
            setValues({
                grafana_api_url: 'http://ums-service.example.com:8080/api/ums',
                grafana_alertname: 'HighCPUUsage',
                grafana_instance: 'instance-1',
                grafana_summary: 'CPU usage is high',
                grafana_description: 'CPU usage is above 90% for 5 minutes',
            });
            clearGrafanaFilters();
        }

        function clearUmsForm() {
            setValues({
                ums_api_url: SERVER_UMS_API_URL || '',
                ums_alertname: '자원사용량경고',
                ums_instance: 'DEVOPS 클러스터 1번 노드',
                ums_summary: '노드의 사용량이 90% 이상입니다',
                ums_receiver_name: '정재훈',
                ums_receiver_phone: '01020083890',
                ums_ecare: '3402',
                ums_channel: 'A',
            });
        }

        let lastPayload = null;
        let lastRequestUrl = null;

        function storeRequestInfo(url, payload) {
            lastPayload = payload;
            lastRequestUrl = url;
        }

        async function executeCurl() {
            if (!lastRequestUrl || !lastPayload) {
                alert('Please generate a curl command first!');
                return;
            }

            const executeBtn = document.getElementById('execute-btn');
            const responseContainer = document.getElementById('response-container');
            const responseStatus = document.getElementById('response-status');
            const responseBody = document.getElementById('response-body');
            const requestMethod = 'POST';
            const requestHeaders = { 'Content-Type': 'application/json' };
            const fullUrl = lastRequestUrl;

            executeBtn.classList.add('loading');
            executeBtn.disabled = true;
            executeBtn.textContent = '⏳ Executing...';

            try {
                const payloadToSend = JSON.parse(JSON.stringify(lastPayload));
                if (payloadToSend.header && payloadToSend.header.ifGlobalNo) {
                    payloadToSend.header.ifGlobalNo = await generateIfGlobalNo();
                }

                const proxyResponse = await fetch('/api/execute-curl-test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        method: requestMethod,
                        url: fullUrl,
                        headers: requestHeaders,
                        payload: payloadToSend,
                    })
                });

                const proxyResponseText = await proxyResponse.text();
                const proxyData = safeParseJson(proxyResponseText);
                if (!proxyData || (proxyData.ok !== true && proxyData.ok !== false)) {
                    throw new Error(proxyResponseText || 'Invalid proxy response');
                }

                const upstreamRequest = proxyData.request || {
                    method: requestMethod,
                    url: fullUrl,
                    headers: requestHeaders,
                };

                responseContainer.classList.add('active');

                if (!proxyData.ok) {
                    const upstreamError = proxyData.error || {};
                    responseStatus.className = 'response-status error';
                    responseStatus.textContent = `❌ Upstream Request Failed: ${upstreamError.type || 'RequestError'}`;
                    responseBody.textContent = [
                        'Request (executed by server):',
                        `method: ${upstreamRequest.method || requestMethod}`,
                        `url: ${upstreamRequest.url || fullUrl}`,
                        'headers:',
                        JSON.stringify(upstreamRequest.headers || requestHeaders, null, 2),
                        '',
                        'Error:',
                        upstreamError.message || proxyData.message || 'Upstream request failed',
                    ].join('\n');
                    return;
                }

                const upstreamResponse = proxyData.response || {};
                const upstreamStatus = Number(upstreamResponse.status || 0);
                const upstreamRawBody = upstreamResponse.body || '';
                const parsedBody = safeParseJson(upstreamRawBody);
                responseStatus.className = 'response-status ' + (upstreamStatus >= 200 && upstreamStatus < 400 ? 'success' : 'error');
                responseStatus.textContent = `${upstreamStatus} ${upstreamResponse.status_text || ''} - ${upstreamStatus >= 200 && upstreamStatus < 400 ? '✓ Success' : '✗ Error'}`;
                responseBody.textContent = [
                    'Request (executed by server):',
                    `method: ${upstreamRequest.method || requestMethod}`,
                    `url: ${upstreamRequest.url || fullUrl}`,
                    'headers:',
                    JSON.stringify(upstreamRequest.headers || requestHeaders, null, 2),
                    '',
                    'Response:',
                    parsedBody ? JSON.stringify(parsedBody, null, 2) : (upstreamRawBody || '(Empty response body)'),
                ].join('\n');

                setTimeout(() => {
                    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            } catch (error) {
                const errorMessage = error?.message || String(error);
                const isFailedToFetch = error instanceof TypeError && errorMessage.toLowerCase().includes('failed to fetch');

                responseContainer.classList.add('active');
                responseStatus.className = 'response-status error';

                if (isFailedToFetch) {
                    responseStatus.textContent = '❌ Network Error (DNS 또는 연결 실패)';
                    responseBody.textContent = [
                        '브라우저가 이 애플리케이션 서버(/api/execute-curl-test)에 연결하지 못했습니다.',
                        '(target URL 호출은 백엔드 서버에서 수행됩니다)',
                        '',
                        `method : ${requestMethod}`,
                        'url    : /api/execute-curl-test',
                        `online : ${navigator.onLine ? 'online' : 'offline (네트워크 끊김)'}`,
                    ].join('\n');
                } else {
                    responseStatus.textContent = `❌ Request Error: ${error?.name || 'Error'}`;
                    responseBody.textContent = [
                        `method : ${requestMethod}`,
                        `url    : ${fullUrl}`,
                        `error  : ${errorMessage}`,
                    ].join('\n');
                }
            } finally {
                executeBtn.classList.remove('loading');
                executeBtn.disabled = false;
                executeBtn.textContent = '▶ Execute';
            }
        }

        // Keep the latest function definitions so endpoint inputs are reflected in output.
        function buildCurlCommand(url, payload) {
            return `curl -X POST "${url}" \\\n+  -H "Content-Type: application/json" \\\n+  -d '${JSON.stringify(payload, null, 2)}'`;
        }

        function displayBothCurls(grafanaRequest, umsRequest) {
            const umsSection = umsRequest.hasKakaoRecipient
                ? [`POST ${umsRequest.umsApiUrl || '(설정 없음)'}`, JSON.stringify(umsRequest.payload, null, 2)].join('\n')
                : `### ${umsRequest.title}\n# recipients.yaml 매칭된 kakao 수신자가 없습니다.`;

            document.getElementById('curl-output').textContent = [
                `### ${grafanaRequest.title}`,
                buildCurlCommand(grafanaRequest.url, grafanaRequest.payload),
                umsSection,
            ].join('\n\n');
        }

        function displayUmsCurlOnly(umsRequest) {
            const umsUrl = umsRequest.umsApiUrl || '(UMS 엔드포인트 미설정)';
            document.getElementById('curl-output').textContent = [
                `### ${umsRequest.title}`,
                buildCurlCommand(umsUrl, umsRequest.payload),
            ].join('\n\n');
        }

        storeRequestInfo(resolveGrafanaExecuteUrl(getGrafanaApiUrlInput()), buildGrafanaRequestData().payload);
        initializeUmsApiUrlInput();
        initializeGrafanaFilterOptions();
