"""
Pipeline Configuration Settings
Adjust these values to customize the short-form video pipeline behavior
"""

class PipelineConfig:
    """Configuration settings for the short-form video pipeline"""
    
    # ============================================================================
    # REDDIT POST FILTERING SETTINGS
    # ============================================================================
    
    # Post content requirements
    MIN_POST_LENGTH = 2200         # Minimum characters in post content
    MAX_POST_LENGTH = None         # Maximum characters in post content (None = no limit)
    MIN_UPVOTES = 100             # Minimum upvotes required
    
    # Estimated video duration limits (in seconds)
    MIN_VIDEO_DURATION = 120        # Minimum video duration
    MAX_VIDEO_DURATION = 179        # 3 minutes maximum for short-form content
    WORDS_PER_MINUTE = 180         # Average speaking speed for duration estimation
    
    # Video splitting settings
    SPLIT_LONG_VIDEOS = True       # Split videos longer than duration limit
    
    # Post selection settings
    FETCH_POST_LIMIT = 25          # Number of posts to fetch from Reddit
    TOP_SAMPLE_SIZE = 10           # Random selection from top N highest-scoring posts
    TIME_FILTER = 'year'           # Reddit time filter: 'day', 'week', 'month', 'year', 'all'
    
    # Target subreddits (randomly selected from this list)
    TARGET_SUBREDDITS = [
        'AmItheAsshole',          # AITA posts
        'tifu',                   # Today I F'd Up
        'unpopularopinion',       # Unpopular opinions
        'maliciouscompliance',    # Malicious compliance stories
    ]
    
    # Content filters
    ALLOW_NSFW = True              # Allow NSFW content
    EXCLUDE_DELETED_AUTHORS = True # Skip posts from deleted accounts
    
    # ============================================================================
    # VIDEO PROCESSING SETTINGS
    # ============================================================================
    
    # Output video format
    OUTPUT_WIDTH = 1080            # Video width (vertical format: 1080)
    OUTPUT_HEIGHT = 1920           # Video height (vertical format: 1920) 
    VIDEO_FPS = 30                 # Frames per second
    
    # Video codec settings
    VIDEO_CODEC = 'libx264'        # Video codec
    AUDIO_CODEC = 'aac'            # Audio codec
    VIDEO_QUALITY = 'medium'       # 'low', 'medium', 'high'
    
    # Background video settings
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']
    LOOP_SHORT_VIDEOS = True       # Loop background videos if shorter than audio
    RANDOM_START_POSITION = True   # Start background videos at random positions
    
    # ============================================================================
    # AUDIO/SPEECH SETTINGS
    # ============================================================================
    
    # ElevenLabs voice settings
    VOICE_STABILITY = 0.5          # Voice stability (0.0-1.0)
    VOICE_SIMILARITY_BOOST = 0.75  # Similarity boost (0.0-1.0)
    VOICE_STYLE = 0.2              # Voice style (0.0-1.0)
    USE_SPEAKER_BOOST = True       # Enable speaker boost
    
    # Script generation
    INCLUDE_TITLE_IN_SCRIPT = True # Include post title in narration
    ADD_INTRO_PHRASE = True        # Add "Today's story:" intro
    ADD_OUTRO_PHRASE = True        # Add outro asking for engagement
    OUTRO_TEXT = "What do you think? Let me know in the comments below, and subscribe for more daily stories!"
    
    # Text cleaning
    CLEAN_REDDIT_FORMATTING = True # Remove Reddit-specific formatting
    EXPAND_ABBREVIATIONS = True    # Convert abbreviations to full words
    
    # ============================================================================
    # SUBTITLE SETTINGS
    # ============================================================================
    
    # Subtitle generation
    GENERATE_SUBTITLES = True      # Generate subtitles using Whisper
    RENDER_SUBTITLES = True        # Render subtitles onto video (requires ImageMagick)
    WHISPER_MODEL_SIZE = 'tiny'    # Whisper model: 'tiny', 'base', 'small', 'medium', 'large'
    MAX_WORDS_PER_SUBTITLE = 3     # Maximum words per subtitle segment
    MAX_SUBTITLE_DURATION = 1    # Maximum duration per subtitle (seconds)
    SAVE_SUBTITLE_FILES = True     # Save subtitle files to disk
    FALLBACK_WITHOUT_SUBTITLES = False  # Continue without subtitles if rendering fails
    
    # Subtitle styling
    SUBTITLE_FONT_SIZE = 70        # Font size for subtitles
    SUBTITLE_COLOR = 'white'       # Subtitle text color
    SUBTITLE_STROKE_COLOR = 'black' # Subtitle outline color
    SUBTITLE_STROKE_WIDTH = 4      # Subtitle outline width
    SUBTITLE_POSITION = 0.5        # Vertical position (0=top, 1=bottom)    
    # ============================================================================
    # FILE MANAGEMENT SETTINGS
    # ============================================================================
    
    # Cleanup settings
    KEEP_AUDIO_FILES = 20          # Number of audio files to keep
    KEEP_VIDEO_FILES = 10          # Number of background videos to keep
    KEEP_REDDIT_DATA_FILES = 50    # Number of Reddit post data files to keep
    AUTO_CLEANUP_ON_SUCCESS = True # Automatically clean old files after successful run
    
    # File naming
    USE_TIMESTAMPED_FILENAMES = True # Add timestamps to generated files
    INCLUDE_POST_ID_IN_FILENAMES = True # Include Reddit post ID in filenames
    
    # ============================================================================
    # LOGGING AND DEBUG SETTINGS  
    # ============================================================================
    
    # Logging levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    LOG_LEVEL = 'INFO'
    VERBOSE_LOGGING = False        # Enable detailed operation logging
    LOG_API_RESPONSES = False      # Log API response details (debug only)
    
    # Progress reporting
    SHOW_PROGRESS_BARS = True      # Show progress during video processing
    REPORT_SELECTION_STATS = True  # Log post selection statistics
    
    # ============================================================================
    # ERROR HANDLING SETTINGS
    # ============================================================================
    
    # Retry settings
    MAX_RETRIES_REDDIT = 3         # Max retries for Reddit API calls
    MAX_RETRIES_ELEVENLABS = 2     # Max retries for ElevenLabs API calls
    MAX_RETRIES_VIDEO_PROCESSING = 1 # Max retries for video processing
    
    # Fallback behavior
    SKIP_ON_FETCH_FAILURE = False  # Skip pipeline if Reddit fetch fails
    CONTINUE_WITHOUT_BACKGROUND = False # Continue if no background video found
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Validate duration settings
        if cls.MAX_VIDEO_DURATION is not None and cls.MIN_VIDEO_DURATION >= cls.MAX_VIDEO_DURATION:
            errors.append("MIN_VIDEO_DURATION must be less than MAX_VIDEO_DURATION")
        
        # Validate post length settings
        if cls.MAX_POST_LENGTH and cls.MIN_POST_LENGTH >= cls.MAX_POST_LENGTH:
            errors.append("MIN_POST_LENGTH must be less than MAX_POST_LENGTH")
            
        # Validate sample size
        if cls.TOP_SAMPLE_SIZE > cls.FETCH_POST_LIMIT:
            errors.append("TOP_SAMPLE_SIZE cannot be larger than FETCH_POST_LIMIT")
            
        # Validate video dimensions
        if cls.OUTPUT_WIDTH <= 0 or cls.OUTPUT_HEIGHT <= 0:
            errors.append("Video dimensions must be positive")
            
        # Validate voice settings
        if not (0 <= cls.VOICE_STABILITY <= 1):
            errors.append("VOICE_STABILITY must be between 0 and 1")
        if not (0 <= cls.VOICE_SIMILARITY_BOOST <= 1):
            errors.append("VOICE_SIMILARITY_BOOST must be between 0 and 1")
            
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    @classmethod
    def get_duration_estimate(cls, word_count: int) -> float:
        """Estimate video duration based on word count"""
        return (word_count / cls.WORDS_PER_MINUTE) * 60
    
    @classmethod
    def print_config_summary(cls):
        """Print a summary of current configuration"""
        print("\n" + "="*60)
        print("SHORT-FORM VIDEO PIPELINE CONFIGURATION")
        print("="*60)
        print(f"Reddit Filter: {cls.MIN_UPVOTES}+ upvotes, {cls.MIN_POST_LENGTH}-{cls.MAX_POST_LENGTH or '∞'} chars")
        print(f"Video Duration: {cls.MIN_VIDEO_DURATION}-{cls.MAX_VIDEO_DURATION}s")
        print(f"Selection: Random from top {cls.TOP_SAMPLE_SIZE} posts (last {cls.TIME_FILTER})")
        print(f"Output Format: {cls.OUTPUT_WIDTH}x{cls.OUTPUT_HEIGHT} @ {cls.VIDEO_FPS}fps")
        print(f"Voice Settings: Stability={cls.VOICE_STABILITY}, Boost={cls.VOICE_SIMILARITY_BOOST}")
        
        if cls.GENERATE_SUBTITLES:
            if cls.RENDER_SUBTITLES:
                print(f"Subtitles: Enabled with rendering (Whisper {cls.WHISPER_MODEL_SIZE} model)")
            else:
                print(f"Subtitles: Generated but not rendered (Whisper {cls.WHISPER_MODEL_SIZE} model)")
        else:
            print("Subtitles: Disabled")
            
        print("Videos ready for manual upload!")
        print("="*60 + "\n") 