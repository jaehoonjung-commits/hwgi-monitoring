"""HTML page for testing webhook payloads with curl commands."""

def render_test_page() -> str:
    """Render an interactive testing page for webhook payloads."""
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webhook 테스트 - Grafana Webhook Receiver</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 18px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            color: #555;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input[type="text"],
        input[type="email"],
        input[type="tel"],
        select,
        textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="email"]:focus,
        input[type="tel"]:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            resize: vertical;
            min-height: 150px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
            flex: 1;
            min-width: 150px;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #333;
            flex: 1;
            min-width: 150px;
        }
        
        .btn-secondary:hover {
            background: #e8e8e8;
        }
        
        .btn-copy {
            background: #48bb78;
            color: white;
            padding: 8px 12px;
            font-size: 13px;
        }
        
        .btn-copy:hover {
            background: #38a169;
        }
        
        .btn-execute {
            background: #ed8936;
            color: white;
            padding: 8px 12px;
            font-size: 13px;
            margin-left: 8px;
        }
        
        .btn-execute:hover {
            background: #dd6b20;
        }
        
        .btn-execute.loading {
            opacity: 0.7;
            cursor: not-allowed;
        }
        
        .response-container {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            display: none;
        }
        
        .response-container.active {
            display: block;
        }
        
        .response-status {
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .response-status.success {
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #48bb78;
        }
        
        .response-status.error {
            background: #fed7d7;
            color: #742a2a;
            border-left: 4px solid #f56565;
        }
        
        .response-body {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .curl-container {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            position: relative;
        }
        
        .curl-command {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
            margin: 10px 0;
        }
        
        .copy-button {
            position: absolute;
            top: 15px;
            right: 15px;
        }
        
        .success-message {
            color: #48bb78;
            margin-top: 10px;
            display: none;
            font-size: 14px;
        }
        
        .toggle-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        
        .tab-btn {
            background: none;
            border: none;
            padding: 12px 16px;
            cursor: pointer;
            color: #999;
            font-weight: 600;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }
            
            .two-column {
                grid-template-columns: 1fr;
            }
        }
        
        .info-box {
            background: #e6f2ff;
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <!-- Left Panel: Input Form -->
            <div class="panel">
                <div class="toggle-tabs">
                    <button class="tab-btn active" onclick="switchTab('grafana')">Grafana</button>
                    <button class="tab-btn" onclick="switchTab('ums')">UMS Kakao</button>
                </div>
                
                <!-- Grafana Tab -->
                <div id="grafana" class="tab-content active">
                    <div class="info-box">
                        ℹ️ Grafana 알림 웹훅 형식으로 메시지를 생성합니다
                    </div>
                    
                    <div class="form-group">
                        <label>Alert Name (알림 이름)</label>
                        <input type="text" id="grafana_alertname" placeholder="HighCPUUsage" value="HighCPUUsage">
                    </div>
                    
                    <div class="form-group">
                        <label>Severity (심각도)</label>
                        <select id="grafana_severity">
                            <option value="critical">Critical</option>
                            <option value="warning" selected>Warning</option>
                            <option value="info">Info</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Instance (인스턴스)</label>
                        <input type="text" id="grafana_instance" placeholder="instance-1" value="instance-1">
                    </div>
                    
                    <div class="form-group">
                        <label>Alert Group (알림 그룹)</label>
                        <input type="text" id="grafana_group" placeholder="dev-1" value="dev-1">
                    </div>
                    
                    <div class="form-group">
                        <label>Summary (요약)</label>
                        <textarea id="grafana_summary" placeholder="CPU usage is high">CPU usage is high</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Description (설명)</label>
                        <textarea id="grafana_description" placeholder="CPU usage is above 90% for 5 minutes">CPU usage is above 90% for 5 minutes</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Server URL</label>
                        <input type="text" id="grafana_url" placeholder="http://localhost:8000" value="http://localhost:8000">
                    </div>
                    
                    <div class="button-group">
                        <button class="btn-primary" onclick="generateGrafanaCurl()">Generate Curl</button>
                        <button class="btn-secondary" onclick="clearGrafanaForm()">Clear</button>
                    </div>
                </div>
                
                <!-- UMS Tab -->
                <div id="ums" class="tab-content">
                    <div class="info-box">
                        ℹ️ UMS Kakao 메시지 형식으로 생성합니다
                    </div>
                    
                    <div class="form-group">
                        <label>Alert Name (알림 이름)</label>
                        <input type="text" id="ums_alertname" placeholder="HighCPUUsage" value="자원사용량경고">
                    </div>
                    
                    <div class="form-group">
                        <label>Instance (인스턴스)</label>
                        <input type="text" id="ums_instance" placeholder="instance-1" value="DEVOPS 클러스터 1번 노드">
                    </div>
                    
                    <div class="form-group">
                        <label>Summary (요약)</label>
                        <textarea id="ums_summary" placeholder="Main message here">노드의 사용량이 90% 이상입니다</textarea>
                    </div>
                    
                    <div class="two-column">
                        <div class="form-group">
                            <label>Receiver Name (수신자 이름)</label>
                            <input type="text" id="ums_receiver_name" placeholder="정재훈" value="정재훈">
                        </div>
                        
                        <div class="form-group">
                            <label>Receiver Phone (수신자 전화)</label>
                            <input type="tel" id="ums_receiver_phone" placeholder="01020083890" value="01020083890">
                        </div>
                    </div>
                    
                    <div class="two-column">
                        <div class="form-group">
                            <label>Ecard No (카드번호)</label>
                            <input type="text" id="ums_ecard" placeholder="3402" value="3402">
                        </div>
                        
                        <div class="form-group">
                            <label>Channel</label>
                            <input type="text" id="ums_channel" placeholder="A" value="A">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Server URL</label>
                        <input type="text" id="ums_url" placeholder="http://localhost:8000" value="http://localhost:8000">
                    </div>
                    
                    <div class="button-group">
                        <button class="btn-primary" onclick="generateUmsCurl()">Generate Curl</button>
                        <button class="btn-secondary" onclick="clearUmsForm()">Clear</button>
                    </div>
                </div>
            </div>
            
            <!-- Right Panel: Output -->
            <div class="panel">
                <h2>Curl 명령어</h2>
                
                <div class="curl-container">
                    <div class="copy-button">
                        <button class="btn-copy" onclick="copyCurl()">📋 Copy</button>
                        <button class="btn-execute" id="execute-btn" onclick="executeCurl()">▶ Execute</button>
                    </div>
                    <div id="curl-output" class="curl-command">Ready to generate...</div>
                    <div id="success-message" class="success-message">✓ Copied to clipboard!</div>
                </div>
                
                <div id="response-container" class="response-container">
                    <h3 style="margin-bottom: 12px;">응답 결과</h3>
                    <div id="response-status" class="response-status"></div>
                    <div id="response-body" class="response-body"></div>
                </div>
                
                <div class="form-group" style="margin-top: 20px;">
                    <label>JSON Payload (포함된 내용)</label>
                    <textarea id="json-output" readonly style="min-height: 300px; background: #f8f9fa; color: #333;">JSON payload will appear here...</textarea>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function generateGrafanaCurl() {
            const alertname = document.getElementById('grafana_alertname').value || 'Alert';
            const severity = document.getElementById('grafana_severity').value || 'warning';
            const instance = document.getElementById('grafana_instance').value || 'instance-1';
            const group = document.getElementById('grafana_group').value || 'dev-1';
            const summary = document.getElementById('grafana_summary').value || 'Summary';
            const description = document.getElementById('grafana_description').value || 'Description';
            const url = document.getElementById('grafana_url').value || 'http://localhost:8000';
            
            const now = new Date().toISOString();
            const payload = {
                receiver: "webhook_receiver",
                status: "firing",
                alerts: [
                    {
                        status: "firing",
                        labels: {
                            alertname: alertname,
                            severity: severity,
                            alert_group: group,
                            instance: instance
                        },
                        annotations: {
                            summary: summary,
                            description: description
                        },
                        startsAt: now,
                        endsAt: "0001-01-01T00:00:00Z"
                    }
                ]
            };
            
            displayCurl(url, '/webhook/grafana', payload);
        }
        
        function generateUmsCurl() {
            const alertname = document.getElementById('ums_alertname').value || 'Alert';
            const instance = document.getElementById('ums_instance').value || 'Instance';
            const summary = document.getElementById('ums_summary').value || 'Summary';
            const receiverName = document.getElementById('ums_receiver_name').value || 'Name';
            const receiverPhone = document.getElementById('ums_receiver_phone').value || '01000000000';
            const ecard = document.getElementById('ums_ecard').value || '3402';
            const channel = document.getElementById('ums_channel').value || 'A';
            const url = document.getElementById('ums_url').value || 'http://localhost:8000';
            
            const now = new Date();
            const timeStr = String(now.getHours()).padStart(2, '0') + '|' +
                           String(now.getMinutes()).padStart(2, '0') + '|' +
                           String(now.getSeconds()).padStart(2, '0');
            
            const jonmun = "@s@|f|6|Grafana|" + alertname + "|" + instance + " - " + summary + "|" + timeStr;
            
            const payload = {
                header: {
                    ifGlobalNo: generateIfGlobalNo(),
                    chnlSysCd: "AAA",
                    ifOrgCd: "UMS",
                    applCd: "GRFN",
                    ifKindCd: "0100",
                    ifTxCd: "10000",
                    sftno: "8094310",
                    respCd: "",
                    respMsg: ""
                },
                payload: {
                    cnt: 1,
                    request: [
                        {
                            ecardNo: parseInt(ecard),
                            channel: channel,
                            tmplType: "J",
                            receivcerNm: receiverName,
                            receiver: receiverPhone,
                            senderNm: "한화손해보험",
                            reqUserId: "8094310",
                            jonmun: jonmun
                        }
                    ]
                }
            };
            
            displayCurl(url, '/hwgi/ums/UMSMEMMA020010000', payload);
        }
        
        function generateIfGlobalNo() {
            const now = new Date();
            const dateStr = String(now.getFullYear()) +
                           String(now.getMonth() + 1).padStart(2, '0') +
                           String(now.getDate()).padStart(2, '0') +
                           String(now.getHours()).padStart(2, '0') +
                           String(now.getMinutes()).padStart(2, '0') +
                           String(now.getSeconds()).padStart(2, '0');
            const ms = String(now.getMilliseconds()).padStart(3, '0');
            return dateStr + ms + 'AAAA' + '123457';
        }
        
        function displayCurl(baseUrl, endpoint, payload) {
            const jsonStr = JSON.stringify(payload, null, 2);
            
            // Escape quotes for curl
            const escapedJson = jsonStr
                .replace(/\\\\/g, '\\\\\\\\')
                .replace(/"/g, '\\\\"')
                .replace(/\\n/g, '\\n');
            
            const curlCommand = `curl -X POST "${baseUrl}${endpoint}" \\
  -H "Content-Type: application/json" \\
  -d '${jsonStr}'`;
            
            document.getElementById('curl-output').textContent = curlCommand;
            document.getElementById('json-output').textContent = jsonStr;
            
            // Store request info for execution
            storeRequestInfo(baseUrl, endpoint, payload);
            
            // Hide response container when new request is generated
            document.getElementById('response-container').classList.remove('active');
        }
        
        function copyCurl() {
            const curlText = document.getElementById('curl-output').textContent;
            navigator.clipboard.writeText(curlText).then(() => {
                const msg = document.getElementById('success-message');
                msg.style.display = 'block';
                setTimeout(() => {
                    msg.style.display = 'none';
                }, 2000);
            }).catch(err => {
                alert('Failed to copy: ' + err);
            });
        }
        
        function clearGrafanaForm() {
            document.getElementById('grafana_alertname').value = 'HighCPUUsage';
            document.getElementById('grafana_severity').value = 'warning';
            document.getElementById('grafana_instance').value = 'instance-1';
            document.getElementById('grafana_group').value = 'dev-1';
            document.getElementById('grafana_summary').value = 'CPU usage is high';
            document.getElementById('grafana_description').value = 'CPU usage is above 90% for 5 minutes';
            document.getElementById('curl-output').textContent = 'Ready to generate...';
            document.getElementById('json-output').textContent = 'JSON payload will appear here...';
        }
        
        function clearUmsForm() {
            document.getElementById('ums_alertname').value = '자원사용량경고';
            document.getElementById('ums_instance').value = 'DEVOPS 클러스터 1번 노드';
            document.getElementById('ums_summary').value = '노드의 사용량이 90% 이상입니다';
            document.getElementById('ums_receiver_name').value = '정재훈';
            document.getElementById('ums_receiver_phone').value = '01020083890';
            document.getElementById('ums_ecard').value = '3402';
            document.getElementById('ums_channel').value = 'A';
            document.getElementById('curl-output').textContent = 'Ready to generate...';
            document.getElementById('json-output').textContent = 'JSON payload will appear here...';
        }
        
        let lastPayload = null;
        let lastUrl = null;
        let lastEndpoint = null;
        
        function storeRequestInfo(url, endpoint, payload) {
            lastPayload = payload;
            lastUrl = url;
            lastEndpoint = endpoint;
        }
        
        async function executeCurl() {
            if (!lastUrl || !lastEndpoint || !lastPayload) {
                alert('Please generate a curl command first!');
                return;
            }
            
            const executeBtn = document.getElementById('execute-btn');
            const responseContainer = document.getElementById('response-container');
            const responseStatus = document.getElementById('response-status');
            const responseBody = document.getElementById('response-body');
            
            // Disable button and show loading state
            executeBtn.classList.add('loading');
            executeBtn.disabled = true;
            executeBtn.textContent = '⏳ Executing...';
            
            try {
                // Extract base URL (without trailing slash)
                const baseUrl = lastUrl.endsWith('/') ? lastUrl.slice(0, -1) : lastUrl;
                const fullUrl = baseUrl + lastEndpoint;
                
                const response = await fetch(fullUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(lastPayload)
                });
                
                const responseData = await response.json();
                
                // Show response container
                responseContainer.classList.add('active');
                
                // Display status
                const statusClass = response.ok ? 'success' : 'error';
                responseStatus.className = 'response-status ' + statusClass;
                responseStatus.textContent = `${response.status} ${response.statusText} - ${response.ok ? '✓ Success' : '✗ Error'}`;
                
                // Display response body
                responseBody.textContent = JSON.stringify(responseData, null, 2);
                
                // Scroll to response
                setTimeout(() => {
                    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
                
            } catch (error) {
                // Show error
                responseContainer.classList.add('active');
                responseStatus.className = 'response-status error';
                responseStatus.textContent = `❌ Request Error: ${error.message}`;
                responseBody.textContent = error.toString();
            } finally {
                // Re-enable button
                executeBtn.classList.remove('loading');
                executeBtn.disabled = false;
                executeBtn.textContent = '▶ Execute';
            }
        }
    </script>
</body>
</html>
"""
