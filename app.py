from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'service': 'YouTube Bot',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
