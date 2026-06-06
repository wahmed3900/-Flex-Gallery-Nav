from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flex Gallery Nav</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .gallery {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                width: 300px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }
            .card:hover {
                transform: translateY(-5px);
            }
            h1 {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
        </style>
    </head>
    <body>
        <h1>🎨 Flex Gallery Nav</h1>
        <div class="gallery">
            <div class="card"><h3>📸 Image 1</h3><p>Sample gallery item</p></div>
            <div class="card"><h3>🎨 Image 2</h3><p>Sample gallery item</p></div>
            <div class="card"><h3>🖼️ Image 3</h3><p>Sample gallery item</p></div>
            <div class="card"><h3>✨ Image 4</h3><p>Sample gallery item</p></div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))