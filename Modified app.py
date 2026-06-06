from chalice import Chalice, ScheduledEvent
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import os
import json
import random
import boto3
from datetime import datetime, timedelta

app = Chalice(app_name='youtube-bot')
lambda_client = boto3.client('lambda')

# Environment variables
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
CHANNEL_ID = os.environ.get('YOUTUBE_CHANNEL_ID')

def is_safe_to_reply(comment):
    """Skip negative/spam comments"""
    blocked_terms = ['scam', 'fake news', 'spam', 'bot', 'trash']
    comment_lower = comment.lower()
    return not any(term in comment_lower for term in blocked_terms)

def is_genuine_question(comment):
    """Only reply to real questions"""
    return '?' in comment or any(word in comment.lower() for word in 
                                  ['how', 'what', 'why', 'can you', 'help'])

def generate_friendly_reply(comment, author):
    """Generate a helpful reply"""
    replies = [
        f"Thanks for asking, {author}! Check our tutorial section for help! 😊",
        f"Great question! Here's a quick tip for '{comment[:50]}...' - watch our beginner's guide!",
        f"Thanks {author}! We've got a video covering exactly this topic.",
        f"Appreciate your engagement! The short answer is yes - check our pinned comment for details."
    ]
    return random.choice(replies)

def get_recent_comments(youtube, channel_id):
    """Fetch recent comments from your channel's videos"""
    channels_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()
    
    if not channels_response.get('items'):
        return []
    
    uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    videos_response = youtube.playlistItems().list(
        part='snippet',
        playlistId=uploads_playlist_id,
        maxResults=3
    ).execute()
    
    comments = []
    for video in videos_response['items']:
        video_id = video['snippet']['resourceId']['videoId']
        
        try:
            comment_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=5
            ).execute()
            
            for item in comment_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': comment['id'],
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'video_id': video_id,
                    'published_at': comment['publishedAt']
                })
        except HttpError as e:
            if e.resp.status == 403:
                print(f"Comments disabled for video {video_id}")
            continue
    
    return comments

def post_reply(youtube, comment_id, reply_text):
    """Post a reply to a comment"""
    try:
        youtube.comments().insert(
            part='snippet',
            body={
                'snippet': {
                    'parentId': comment_id,
                    'textOriginal': reply_text
                }
            }
        ).execute()
        print(f"✅ Replied to comment: {comment_id}")
        return True
    except HttpError as e:
        print(f"❌ Failed to reply: {e}")
        return False

def schedule_next_run():
    """Schedule the next Lambda invocation after random 20-45 minutes"""
    # Random delay between 20-45 minutes (in seconds)
    delay_minutes = random.randint(20, 45)
    delay_seconds = delay_minutes * 60
    
    # Calculate future time
    future_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
    
    # Schedule using CloudWatch Events (create a one-time rule)
    events_client = boto3.client('events')
    rule_name = f'youtube-bot-schedule-{future_time.strftime("%Y%m%d%H%M%S")}'
    
    # Create a one-time rule
    cron_expression = f"cron({future_time.minute} {future_time.hour} {future_time.day} {future_time.month} ? {future_time.year})"
    
    try:
        # Create rule
        events_client.put_rule(
            Name=rule_name,
            ScheduleExpression=cron_expression,
            State='ENABLED'
        )
        
        # Add Lambda target
        events_client.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': '1',
                'Arn': os.environ.get('LAMBDA_FUNCTION_ARN'),
                'Input': json.dumps({'source': 'self_scheduled'})
            }]
        )
        
        # Clean up old rules (keep last 10)
        cleanup_old_rules(events_client)
        
        print(f"📅 Scheduled next run in {delay_minutes} minutes at {future_time}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to schedule: {e}")
        return False

def cleanup_old_rules(events_client):
    """Remove old schedule rules to avoid clutter"""
    rules = events_client.list_rules(NamePrefix='youtube-bot-schedule-')
    
    # Sort by creation time (oldest first)
    rule_names = [rule['Name'] for rule in rules['Rules']]
    
    # Keep only last 10, delete rest
    for rule_name in rule_names[:-10]:
        try:
            # Remove targets first
            events_client.remove_targets(
                Rule=rule_name,
                Ids=['1']
            )
            # Delete rule
            events_client.delete_rule(Name=rule_name)
            print(f"🧹 Cleaned up old rule: {rule_name}")
        except Exception as e:
            print(f"⚠️ Failed to delete {rule_name}: {e}")

# Main Lambda handler
@app.lambda_function()
def process_comments(event, context):
    """Main function - runs on a random schedule"""
    print("🤖 Bot woke up at", datetime.utcnow())
    
    # Initialize YouTube API
    youtube = googleapiclient.discovery.build(
        'youtube', 'v3',
        developerKey=YOUTUBE_API_KEY
    )
    
    # Get recent comments (last 2 hours only)
    recent_comments = get_recent_comments(youtube, CHANNEL_ID)
    
    # Filter comments from last 2 hours
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    new_comments = []
    
    for comment in recent_comments:
        comment_time = datetime.fromisoformat(comment['published_at'].replace('Z', '+00:00'))
        if comment_time > two_hours_ago:
            new_comments.append(comment)
    
    # Reply to new comments
    replies_posted = 0
    for comment in new_comments[:10]:  # Max 10 replies per run
        if is_safe_to_reply(comment['text']) and is_genuine_question(comment['text']):
            reply = generate_friendly_reply(comment['text'], comment['author'])
            
            if post_reply(youtube, comment['id'], reply):
                replies_posted += 1
            
            # Be respectful of API rate limits
            time.sleep(2)
    
    print(f"✅ Processed {len(new_comments)} comments, replied to {replies_posted}")
    
    # Schedule the next run (20-45 minutes from now)
    schedule_next_run()
    
    return {
        'processed': len(new_comments),
        'replied': replies_posted,
        'next_run_scheduled': True
    }