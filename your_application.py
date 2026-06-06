from app import app

# This file is for Render compatibility
# It imports the Flask app from app.py

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)