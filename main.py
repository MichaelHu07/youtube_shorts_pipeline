"""
Main Short-Form Video Pipeline Orchestrator
"""
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Union

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import setup_logging, get_logger
from src.reddit_fetcher import RedditClient
from src.speech_synthesis import ElevenLabsClient
from src.video_downloader import VideoManager
from src.video_editor import VideoComposer
from src.subtitle_generator import WhisperSubtitles

class ShortFormVideoPipeline:
    def __init__(self):
        """Initialize the short-form video pipeline"""
        # Fix ImageMagick configuration for MoviePy
        try:
            import moviepy.config
            moviepy.config.IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
        except Exception as e:
            pass  # Continue even if ImageMagick config fails
        
        # Setup logging
        self.logger = setup_logging()
        
        # Validate configurations
        try:
            Config.validate_config()
            PipelineConfig.validate_config()
            self.logger.info("Configuration validated successfully")
        except ValueError as e:
            self.logger.error(f"Configuration error: {e}")
            raise
        
        # Check subtitle system if subtitles are enabled
        if PipelineConfig.GENERATE_SUBTITLES:
            from src.utils import check_subtitle_system
            self.subtitle_system_status = check_subtitle_system()
            
            # Update config based on system capabilities
            if not self.subtitle_system_status['textclip_working'] and PipelineConfig.RENDER_SUBTITLES:
                self.logger.warning("Subtitle rendering disabled due to system limitations")
                print("WARNING: Subtitle rendering automatically disabled - will generate subtitle files only")
        else:
            self.subtitle_system_status = None
        
        # Initialize components
        self.reddit_client = None
        self.tts_client = None
        self.video_manager = None
        self.video_composer = None
        self.subtitle_generator = None
        
        self.logger.info("Short-Form Video Pipeline initialized")
    
    def run_pipeline(self, 
                    subreddit: Optional[str] = None,
                    manual_url: Optional[str] = None,
                    show_config: bool = True) -> Dict:
        """
        Run the complete pipeline with progress tracking
        
        Args:
            subreddit: Target subreddit (default from config)
            manual_url: Manual Reddit post URL to use instead of random selection
            show_config: Whether to display configuration summary
        
        Returns:
            Dictionary with pipeline results
        """
        try:
            from src.utils import PipelineProgress
            progress = PipelineProgress()
            
            if show_config:
                PipelineConfig.print_config_summary()
            
            self.logger.info("Starting short-form video pipeline")
            results = {}
            
            # Step 1: Fetch Reddit post
            progress.show_step("Fetching")
            if manual_url:
                reddit_post = self._fetch_reddit_post_by_url(manual_url)
            else:
                reddit_post = self._fetch_reddit_post(subreddit)
            if not reddit_post:
                raise Exception("Failed to fetch Reddit post")
            results['reddit_post'] = reddit_post
            
            # Step 2: Generate narration script and audio
            progress.next_step()
            audio_path = self._generate_narration(reddit_post)
            if not audio_path:
                raise Exception("Failed to generate narration")
            results['audio_path'] = audio_path
            
            # Step 3: Get background video from uploaded files
            progress.next_step()
            background_video = self._get_background_video()
            if not background_video:
                raise Exception("Failed to get background video")
            results['background_video'] = background_video
            
            # Step 4: Generate subtitles (if enabled)
            subtitles = []
            if PipelineConfig.GENERATE_SUBTITLES:
                progress.next_step()
                subtitles = self._generate_subtitles(audio_path)
                results['subtitles'] = subtitles
            else:
                progress.next_step()  # Skip subtitle step
            
            # Step 5: Compose final video
            progress.next_step()
            final_video_path = self._compose_video(
                background_video, audio_path, subtitles
            )
            if not final_video_path:
                raise Exception("Failed to compose video")
            results['final_video_path'] = final_video_path
            
            # Auto cleanup if configured
            if PipelineConfig.AUTO_CLEANUP_ON_SUCCESS:
                self.cleanup_old_files()
            
            progress.complete()
            self.logger.info("Pipeline completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def _fetch_reddit_post(self, subreddit: Optional[str] = None) -> Optional[Dict]:
        """Fetch a suitable Reddit post"""
        try:
            if not self.reddit_client:
                self.reddit_client = RedditClient()
            
            # Pass None to use random subreddit selection if no specific subreddit provided
            post_data = self.reddit_client.fetch_top_post(subreddit)
            if not post_data:
                return None
            
            # Create narration script
            script = self.reddit_client.create_narration_script(post_data)
            post_data['narration_script'] = script
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Reddit post: {e}")
            return None
    
    def _generate_narration(self, reddit_post: Dict) -> Optional[str]:
        """Generate audio narration from Reddit post"""
        try:
            if not self.tts_client:
                self.tts_client = ElevenLabsClient()
            
            script = reddit_post.get('narration_script', '')
            if not script:
                self.logger.error("No narration script found")
                return None
            
            # Generate filename based on post ID if configured
            if PipelineConfig.INCLUDE_POST_ID_IN_FILENAMES:
                audio_filename = f"narration_{reddit_post['id']}.mp3"
            else:
                audio_filename = None  # Let the client generate it
            
            audio_path = self.tts_client.text_to_speech(script, audio_filename)
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate narration: {e}")
            return None
    
    def _get_background_video(self) -> Optional[str]:
        """Get background video from manually uploaded files in data/videos folder"""
        try:
            if not self.video_manager:
                self.video_manager = VideoManager()
            
            # Get random video from manually uploaded videos
            video_path = self.video_manager.get_random_video()
            
            if not video_path:
                self.logger.error("No background videos found in data/videos/ folder")
                self.logger.info(f"Please add video files ({', '.join(PipelineConfig.SUPPORTED_VIDEO_FORMATS)}) to the data/videos/ folder")
                return None
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Failed to get background video: {e}")
            return None
    
    def _fetch_reddit_post_by_url(self, url: str) -> Optional[Dict]:
        """Fetch a specific Reddit post by URL"""
        try:
            if not self.reddit_client:
                self.reddit_client = RedditClient()
            
            post_data = self.reddit_client.fetch_post_by_url(url)
            if not post_data:
                return None
            
            # Create narration script
            script = self.reddit_client.create_narration_script(post_data)
            post_data['narration_script'] = script
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Reddit post by URL: {e}")
            return None
    
    def _generate_subtitles(self, audio_path: str) -> List[Dict]:
        """Generate subtitles using Whisper"""
        try:
            if not self.subtitle_generator:
                self.subtitle_generator = WhisperSubtitles(
                    model_size=PipelineConfig.WHISPER_MODEL_SIZE
                )
            
            subtitles = self.subtitle_generator.generate_subtitles(
                audio_path, 
                max_words_per_segment=PipelineConfig.MAX_WORDS_PER_SUBTITLE
            )
            return subtitles
            
        except Exception as e:
            self.logger.error(f"Failed to generate subtitles: {e}")
            return []
    
    def _compose_video(self, 
                      background_video: str,
                      audio_path: str,
                      subtitles: Optional[List[Dict]] = None) -> Optional[Union[str, List[str]]]:
        """Compose final video"""
        try:
            if not self.video_composer:
                self.video_composer = VideoComposer()
            
            final_video_path = self.video_composer.compose_video(
                background_video_path=background_video,
                audio_path=audio_path,
                subtitles_data=subtitles
            )
            
            return final_video_path
            
        except Exception as e:
            self.logger.error(f"Failed to compose video: {e}")
            return None
    
    def cleanup_old_files(self):
        """Clean up old generated files using config settings"""
        try:
            self.logger.info("Cleaning up old files")
            
            # Clean up old background videos
            if self.video_manager:
                self.video_manager.clean_old_videos(keep_count=PipelineConfig.KEEP_VIDEO_FILES)
            
            # Clean up old audio files using utility function
            from src.utils import clean_old_files
            clean_old_files(Config.AUDIO_DIR, '.mp3', keep_count=PipelineConfig.KEEP_AUDIO_FILES, logger_name='pipeline')
            
            # Clean up old Reddit data files
            clean_old_files(Config.REDDIT_POSTS_DIR, '.json', keep_count=PipelineConfig.KEEP_REDDIT_DATA_FILES, logger_name='pipeline')
            clean_old_files(Config.REDDIT_POSTS_DIR, '.txt', keep_count=PipelineConfig.KEEP_REDDIT_DATA_FILES, logger_name='pipeline')
            
            # Clean up old subtitle files if they exist
            if PipelineConfig.GENERATE_SUBTITLES and PipelineConfig.SAVE_SUBTITLE_FILES:
                clean_old_files(Config.SUBTITLES_DIR, '.json', keep_count=PipelineConfig.KEEP_REDDIT_DATA_FILES, logger_name='pipeline')
                clean_old_files(Config.SUBTITLES_DIR, '.srt', keep_count=PipelineConfig.KEEP_REDDIT_DATA_FILES, logger_name='pipeline')
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

def main():
    """Main function"""
    try:
        # Simple input prompt for manual URL
        print("\n" + "="*50)
        print("SHORT-FORM VIDEO PIPELINE")
        print("="*50)
        manual_url = input("Enter Reddit post URL (or press Enter for random): ").strip()
        
        # Initialize pipeline
        pipeline = ShortFormVideoPipeline()
        
        # Run pipeline (manual upload only)
        results = pipeline.run_pipeline(
            subreddit=None,                                    # Uses TARGET_SUBREDDIT from .env file
            manual_url=manual_url if manual_url else None,     # Use manual URL if provided
            show_config=True                                   # Show configuration summary
        )
        
        print("\n" + "="*50)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Reddit Post: {results['reddit_post']['title'][:50]}...")
        print(f"Post Score: {results['reddit_post']['score']} upvotes")
        print(f"Estimated Duration: {results['reddit_post'].get('estimated_duration', 'Unknown')} seconds")
        print(f"Audio: {results['audio_path']}")
        print(f"Background Video: {results['background_video']}")
        # Handle both single video and split videos
        final_video = results['final_video_path']
        if isinstance(final_video, list):
            print(f"Final Videos: {len(final_video)} parts created (split for short-form content)")
            for i, video_path in enumerate(final_video, 1):
                print(f"  Part {i}: {video_path}")
        else:
            print(f"Final Video: {final_video}")
        
        if PipelineConfig.GENERATE_SUBTITLES and results.get('subtitles'):
            print(f"Subtitles: {len(results['subtitles'])} segments generated")
            if PipelineConfig.RENDER_SUBTITLES:
                print(f"Subtitles: Rendered directly onto video")
            else:
                print(f"Subtitles: Generated as separate file")
        
        if isinstance(final_video, list):
            print(f"\nYour {len(final_video)} video parts are ready for manual upload!")
        else:
            print("\nYour video is ready for manual upload!")
        print("="*50)
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 