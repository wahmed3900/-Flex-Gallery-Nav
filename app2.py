
"""
YouTube AI Comment Bot with DeepSeek Integration
Author: Waqas Ahmed
Tech Stack: Flask, YouTube API, DeepSeek API, Render.com
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Spam keywords to filter
SPAM_PATTERNS = [
    r'buy now', r'click here', r'free money', r'bitcoin',
    r'crypto', r'lottery', r'winner', r'casino', r'赌博'
]

# Question indicators
QUESTION_WORDS = ['what', 'how', 'why', 'when', 'where', 'who', 
                  'which', 'can you', 'could you', 'is it', 'does anyone']


class YouTubeCommentBot:
    """Handles YouTube API interactions and comment processing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = None
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_comments(self, video_id: str, max_results: int = 50) -> List[Dict]:
        """Fetch comments from a YouTube video"""
        if not self.youtube:
            logger.error("YouTube API not initialized")
            return []
        
        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                textFormat='plainText'
            )
            response = request.execute()
            
            comments = []
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': item['id'],
                    'author': snippet.get('authorDisplayName', 'Unknown'),
                    'text': snippet.get('textDisplay', ''),
                    'published_at': snippet.get('publishedAt', '')
                })
            
            logger.info(f"Fetched {len(comments)} comments from video {video_id}")
            return comments
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
    
    def post_reply(self, comment_id: str, reply_text: str) -> bool:
        """Post a reply to a comment"""
        if not self.youtube:
            return False
        
        try:
            request = self.youtube.comments().insert(
                part='snippet',
                body={
                    'snippet': {
                        'parentId': comment_id,
                        'textOriginal': reply_text[:1000]  # YouTube limit
                    }
                }
            )
            request.execute()
            logger.info(f"Posted reply to comment {comment_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to post reply: {e}")
            return False


class DeepSeekAIClient:
    """Handles DeepSeek AI API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_reply(self, comment_text: str, context: str = "") -> Optional[str]:
        """Generate an AI reply to a comment"""
        if not self.api_key:
            logger.error("DeepSeek API key not configured")
            return None
        
        prompt = f"""You are a helpful YouTube creator assistant. 
Generate a natural, engaging reply to this viewer comment:
Comment: "{comment_text}"
Context: {context if context else 'General YouTube video'}

Keep it:
- Under 150 characters
- Friendly and authentic
- End with "DM me for more details" if appropriate
Reply:"""
        
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers=self.headers,
                json={
                    'model': 'deepseek-chat',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.7,
                    'max_tokens': 150
                },
                timeout=10
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"Generated reply for comment: {comment_text[:50]}...")
                return reply
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek request failed: {e}")
            return None


class CommentAnalyzer:
    """Analyzes comments for quality and question detection"""
    
    @staticmethod
    def is_spam(text: str) -> bool:
        """Check if comment contains spam patterns"""
        text_lower = text.lower()
        for pattern in SPAM_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False
    
    @staticmethod
    def is_question(text: str) -> bool:
        """Check if comment is a genuine question"""
        text_lower = text.lower().strip()
        
        # Check for question mark
        if '?' in text:
            return True
        
        # Check for question words
        words = text_lower.split()
        for word in QUESTION_WORDS:
            if word in words or text_lower.startswith(word):
                return True
        
        return False
    
    @staticmethod
    def calculate_quality_score(comment: Dict) -> int:
        """Calculate comment quality score (0-100)"""
        score = 50  # Base score
        text = comment.get('text', '')
        
        # Longer comments are often better
        if len(text) > 50:
            score += 15
        elif len(text) > 20:
            score += 5
        
        # No excessive caps
        if text.isupper():
            score -= 20
        
        # Genuine question
        if CommentAnalyzer.is_question(text):
            score += 20
        
        return max(0, min(100, score))


# Initialize components
youtube_bot = YouTubeCommentBot(YOUTUBE_API_KEY)
ai_client = DeepSeekAIClient(DEEPSEEK_API_KEY)
analyzer = CommentAnalyzer()


# ========== ROUTES ==========

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'youtube': bool(YOUTUBE_API_KEY),
            'deepseek': bool(DEEPSEEK_API_KEY)
        }
    }), 200


@app.route('/api/analyze', methods=['POST'])
def analyze_comments():
    """Analyze comments from a YouTube video"""
    data = request.get_json()
    video_id = data.get('video_id')
    
    if not video_id:
        return jsonify({'error': 'video_id required'}), 400
    
    # Fetch comments
    comments = youtube_bot.get_comments(video_id)
    
    # Analyze each comment
    analyzed = []
    for comment in comments:
        analyzed.append({
            **comment,
            'is_spam': analyzer.is_spam(comment['text']),
            'is_question': analyzer.is_question(comment['text']),
            'quality_score': analyzer.calculate_quality_score(comment)
        })
    
    # Filter and sort
    genuine_comments = [c for c in analyzed if not c['is_spam']]
    genuine_comments.sort(key=lambda x: x['quality_score'], reverse=True)
    
    return jsonify({
        'total': len(analyzed),
        'spam_count': sum(1 for c in analyzed if c['is_spam']),
        'question_count': sum(1 for c in analyzed if c['is_question']),
        'genuine_comments': genuine_comments[:20]
    }), 200


@app.route('/api/reply', methods=['POST'])
def generate_and_reply():
    """Generate AI reply for a specific comment"""
    data = request.get_json()
    comment_text = data.get('comment_text')
    comment_id = data.get('comment_id')
    auto_post = data.get('auto_post', False)
    
    if not comment_text:
        return jsonify({'error': 'comment_text required'}), 400
    
    # Generate AI reply
    reply = ai_client.generate_reply(comment_text)
    
    if not reply:
        return jsonify({'error': 'Failed to generate reply'}), 500
    
    result = {
        'original_comment': comment_text,
        'generated_reply': reply,
        'posted': False
    }
    
    # Auto-post if requested
    if auto_post and comment_id:
        posted = youtube_bot.post_reply(comment_id, reply)
        result['posted'] = posted
    
    return jsonify(result), 200


@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get bot usage statistics (mock for now)"""
    return jsonify({
        'total_comments_analyzed': 1250,
        'spam_blocked': 340,
        'replies_generated': 156,
        'api_calls_remaining': 'N/A',
        'cost_saved_usd': 12.50  # vs OpenAI
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
