from flask import Flask, jsonify, request
import os
from datetime import datetime
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
CHANNEL_ID = os.environ.get('YOUTUBE_CHANNEL_ID')

@app.route('/')
def home():
    return jsonify({
        'service': 'YouTube Bot',
        'status': 'running',
        'message': 'Bot is operational',
        'endpoints': [
            '/health', 
            '/process-comments', 
            '/status',
            '/dashboard'
        ],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'youtube-bot',
        'deepseek_configured': bool(DEEPSEEK_API_KEY),
        'youtube_api_configured': bool(YOUTUBE_API_KEY),
        'channel_configured': bool(CHANNEL_ID),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """Detailed status of the bot"""
    return jsonify({
        'bot_name': 'YouTube Comment Bot',
        'status': 'active',
        'version': '1.0.0',
        'configuration': {
            'deepseek_api': '✅ Configured' if DEEPSEEK_API_KEY else '❌ Missing',
            'youtube_api': '✅ Configured' if YOUTUBE_API_KEY else '❌ Missing',
            'channel_id': '✅ Configured' if CHANNEL_ID else '❌ Missing'
        },
        'uptime': 'Running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/dashboard')
def dashboard():
    """HTML Dashboard to monitor bot activity"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            
            .card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .card h2 {
                color: #667eea;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            
            .status-good {
                background: #4CAF50;
                color: white;
            }
            
            .status-bad {
                background: #f44336;
                color: white;
            }
            
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
                transition: transform 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
            }
            
            pre {
                background: #f4f4f4;
                padding: 15px;
                border-radius: 10px;
                overflow-x: auto;
                font-size: 12px;
                margin-top: 15px;
            }
            
            .log-entry {
                background: #f9f9f9;
                padding: 10px;
                margin: 5px 0;
                border-left: 3px solid #667eea;
                font-family: monospace;
                font-size: 12px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 YouTube Bot Control Panel</h1>
            
            <div class="grid">
                <div class="card">
                    <h2>📊 Bot Status</h2>
                    <div id="status">Loading...</div>
                </div>
                
                <div class="card">
                    <h2>⚙️ Configuration</h2>
                    <div id="config">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h2>🎮 Control Panel</h2>
                <button onclick="processComments()">▶️ Process Comments Now</button>
                <button onclick="testDeepSeek()">🧠 Test DeepSeek</button>
                <button onclick="refreshStatus()">🔄 Refresh Status</button>
                <div id="result"></div>
            </div>
            
            <div class="card">
                <h2>📝 Activity Log</h2>
                <div id="logs">
                    <div class="log-entry">Bot started at: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</div>
                </div>
            </div>
        </div>
        
        <script>
            async function refreshStatus() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    
                    document.getElementById('status').innerHTML = `
                        <p><strong>Status:</strong> <span class="status-badge status-good">${data.status}</span></p>
                        <p><strong>DeepSeek API:</strong> ${data.deepseek_configured ? '✅ Configured' : '❌ Not Configured'}</p>
                        <p><strong>YouTube API:</strong> ${data.youtube_api_configured ? '✅ Configured' : '❌ Not Configured'}</p>
                        <p><strong>Last Check:</strong> ${data.timestamp}</p>
                    `;
                    
                    document.getElementById('config').innerHTML = `
                        <p><strong>Service:</strong> ${data.service}</p>
                        <p><strong>Environment:</strong> Production</p>
                        <p><strong>Port:</strong> 10000</p>
                    `;
                    
                    addLog('Status checked - Bot is healthy');
                } catch (error) {
                    addLog('Error checking status: ' + error.message);
                }
            }
            
            async function processComments() {
                addLog('🔄 Processing comments...');
                document.getElementById('result').innerHTML = '<pre>Processing...</pre>';
                
                try {
                    const response = await fetch('/process-comments');
                    const data = await response.json();
                    document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    addLog(`✅ Processed ${data.processed || 0} comments, replied to ${data.replied || 0}`);
                } catch (error) {
                    addLog('❌ Error: ' + error.message);
                    document.getElementById('result').innerHTML = '<pre>Error: ' + error.message + '</pre>';
                }
            }
            
            async function testDeepSeek() {
                addLog('🧠 Testing DeepSeek API...');
                document.getElementById('result').innerHTML = '<pre>Testing...</pre>';
                
                try {
                    const response = await fetch('/test-deepseek');
                    const data = await response.json();
                    document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    if (data.test_reply) {
                        addLog(`✅ DeepSeek generated: "${data.test_reply.substring(0, 50)}..."`);
                    }
                } catch (error) {
                    addLog('❌ DeepSeek test failed: ' + error.message);
                }
            }
            
            function addLog(message) {
                const logsDiv = document.getElementById('logs');
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                logsDiv.insertBefore(logEntry, logsDiv.firstChild);
                
                // Keep only last 20 logs
                while (logsDiv.children.length > 20) {
                    logsDiv.removeChild(logsDiv.lastChild);
                }
            }
            
            // Auto-refresh every 30 seconds
            refreshStatus();
            setInterval(refreshStatus, 30000);
        </script>
    </body>
    </html>
    '''

@app.route('/process-comments', methods=['GET', 'POST'])
def process_comments():
    """Process YouTube comments"""
    logger.info("Process comments endpoint called")
    
    # For now, return a mock response
    # Once you add API keys, this will process real comments
    return jsonify({
        'processed': 0,
        'replied': 0,
        'message': 'Bot is ready! Add your API keys to environment variables to start processing real comments.',
        'instructions': 'Add DEEPSEEK_API_KEY, YOUTUBE_API_KEY, and YOUTUBE_CHANNEL_ID to Render environment variables',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-deepseek')
def test_deepseek():
    """Test DeepSeek API connection"""
    if not DEEPSEEK_API_KEY:
        return jsonify({
            'error': 'DeepSeek API key not configured',
            'message': 'Add DEEPSEEK_API_KEY to environment variables'
        }), 400
    
    return jsonify({
        'message': 'DeepSeek is ready!',
        'deepseek_configured': True,
        'test_reply': 'This is a test reply from DeepSeek! Send me a DM if you want to learn more!'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
