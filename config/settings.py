"""
Configuration settings for Short-Form Video Pipeline
Environment variables, API keys, and system paths only
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Reddit Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'ShortFormVideoBot/1.0')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')
    
    # Default subreddit (can be overridden by pipeline_config.py or runtime parameters)
    TARGET_SUBREDDIT = os.getenv('TARGET_SUBREDDIT', 'AmItheAsshole')
    
    # Background video source configuration
    PARKOUR_CHANNEL_URL = os.getenv('PARKOUR_CHANNEL_URL', '@OrbitalNCG')
    MAX_VIDEOS_TO_DOWNLOAD = int(os.getenv('MAX_VIDEOS_TO_DOWNLOAD', 50))
    
    # System Paths (environment-specific, not user-configurable)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    
    # Data subdirectories
    REDDIT_POSTS_DIR = os.path.join(DATA_DIR, 'reddit_posts')
    AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
    VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
    SUBTITLES_DIR = os.path.join(DATA_DIR, 'subtitles')
    FINAL_VIDEOS_DIR = os.path.join(OUTPUT_DIR, 'final_videos')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET',
            'ELEVENLABS_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True 