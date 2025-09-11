# Short-Form Video Pipeline

A content creation pipeline that generates short-form vertical videos from Reddit posts using AI narration, Subtitle Generation, and background videos.

# Feature List: 

1. **Fetches engaging Reddit posts** from your target subreddit
2. **Generates AI narration** using ElevenLabs text-to-speech
3. **Combines with background video** from your uploaded collection
4. **Burns Auto-Generated subtitles onto background video** using OpenAI Whisper
5. **Generates vertical short-form format** (1080x1920) videos ready for upload

## Setup

### 1. Install Dependencies
- praw 7.7.1+
- elevenlabs 0.2.26+
- moviepy 1.0.3+
- openai-whisper 20231117+
- Pillow 10.1.0+
- requests 2.31.0+
- python-dotenv 1.0.0+
- opencv-python 4.8.1.78+
- numpy 1.24.3+
- ffmpeg-python 0.2.0+
- Python 3.8+ 

### 2. Configure API Keys

Add your API keys in `config.env`:

#### Required API Keys:
- Reddit API account
- ElevenLabs API account 

### 3. Add Background Videos
Drop background videos in `data/videos/` folder.

### 4. Run the Pipeline

run `main.py`

## Configuration

Adjust pipeline behavior by editing `config/pipeline_config.py`:

#### Content filtering
MIN_UPVOTES: Minimum post upvotes
MIN_POST_LENGTH: Minimum post length
TIME_FILTER: Reddit time filter

#### Video quality
OUTPUT_WIDTH: Video width
OUTPUT_HEIGHT: Video height (vertical format)
VIDEO_FPS: Frames per second 

#### Voice settings
VOICE_STABILITY: Range (0.0-1.0)
VOICE_SIMILARITY_BOOST: Range (0.0-1.0)

## Config Features

- **Smart Reddit filtering** (upvotes, length, duration)
- **Random post selection** from top posts for variety
- **Configurable voice settings** for optimal narration
- **Configuration validation** to prevent errors

---

# Field Testing:

<img width="3024" height="4032" alt="image" src="https://github.com/user-attachments/assets/2c972a12-1215-46de-84ac-e49bfc61f6f0" />

<img width="1320" height="2304" alt="image" src="https://github.com/user-attachments/assets/c05b25eb-0692-4661-bbcb-d6ae77f7e2c2" />


- Uploaded videos generated using youtube_shorts_pipeline
- No-Copyright Minecraft parkour footage as B-roll
- Average view count of 700 Across 30+ Videos

