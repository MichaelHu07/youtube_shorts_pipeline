# Short-Form Video Pipeline

A streamlined content creation pipeline that generates short-form vertical videos from Reddit posts using AI narration and background videos.

## What It Does

1. **Fetches engaging Reddit posts** from your target subreddit
2. **Generates AI narration** using ElevenLabs text-to-speech
3. **Combines with background video** from your uploaded collection
4. **Creates vertical short-form format** (1080x1920) videos ready for upload

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `config.env.example` to `.env` and add your API keys:
```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
```

### 3. Add Background Videos
Place your background videos (MP4, MOV, AVI, MKV) in the `data/videos/` folder.

### 4. Run the Pipeline
```bash
python main.py
```

## Configuration

Adjust pipeline behavior by editing `config/pipeline_config.py`:

```python
# Content filtering
MIN_UPVOTES = 100              # Minimum post upvotes
MIN_POST_LENGTH = 300          # Minimum post length
TIME_FILTER = 'year'           # Reddit time filter

# Video quality
OUTPUT_WIDTH = 1080            # Video width
OUTPUT_HEIGHT = 1920           # Video height (vertical format)
VIDEO_FPS = 30                 # Frames per second

# Voice settings
VOICE_STABILITY = 0.5          # Voice stability (0.0-1.0)
VOICE_SIMILARITY_BOOST = 0.75  # Voice similarity (0.0-1.0)
```

## Project Structure

```
youtube_shorts_pipeline/
├── config/
│   ├── pipeline_config.py     # Main configuration file
│   └── settings.py           # Environment settings
├── data/
│   ├── videos/              # Add your background videos here
│   ├── audio/              # Generated narration files
│   └── reddit_posts/       # Fetched post data
├── output/
│   └── final_videos/       # Generated short-form videos
├── src/
│   ├── reddit_fetcher/     # Reddit API integration
│   ├── speech_synthesis/   # ElevenLabs TTS
│   ├── video_downloader/   # Video file management
│   └── video_editor/       # Video composition
└── main.py                 # Pipeline entry point
```

## Features

- **Smart Reddit filtering** (upvotes, length, duration)
- **Random post selection** from top posts for variety
- **Configurable voice settings** for optimal narration
- **Automatic file cleanup** to manage storage
- **Comprehensive logging** for debugging
- **Configuration validation** to prevent errors

## Requirements

- Python 3.8+
- Reddit API account
- ElevenLabs API account  
- Background videos in `data/videos/` folder

---

**Note**: This pipeline generates videos ready for manual upload to any platform. 