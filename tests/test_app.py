import pytest
from app import CommentAnalyzer, app

def test_spam_detection():
    analyzer = CommentAnalyzer()
    assert analyzer.is_spam("Buy now! Click here") == True
    assert analyzer.is_spam("Great video!") == False

def test_question_detection():
    analyzer = CommentAnalyzer()
    assert analyzer.is_question("How does this work?") == True
    assert analyzer.is_question("What is that?") == True
    assert analyzer.is_question("Nice video") == False

def test_health_endpoint():
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'
