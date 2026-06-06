from flask import Flask, jsonify, request
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'service': 'YouTube Bot',
        'status': 'running',
        'message': 'Bot is operational',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/health',
            '/process-comments',
            '/webhook/youtube'
        ]
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'youtube-bot',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/process-comments', methods=['GET', 'POST'])
def process_comments():
    """Process YouTube comments"""
    try:
        if request.method == 'POST':
            data = request.json
            print(f"Received data: {data}")
        
        result = {
            'processed': 5,
            'replied': 2,
            'next_run_scheduled': True,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/youtube', methods=['POST'])
def youtube_webhook():
    """YouTube webhook receiver"""
    try:
        data = request.json
        print(f"Webhook received: {data}")
        
        return jsonify({
            'received': True,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
