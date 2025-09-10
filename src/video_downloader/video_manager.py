"""
Video Manager for handling background videos
"""
import os
import random
from typing import Optional, List
from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import get_logger
from src.utils import ensure_directory

logger = get_logger('video_manager')

class VideoManager:
    """Manages background videos for the pipeline"""
    
    def __init__(self):
        """Initialize video manager"""
        self.videos_dir = Config.VIDEOS_DIR
        ensure_directory(self.videos_dir)
        logger.info(f"Video manager initialized with directory: {self.videos_dir}")
    
    def get_random_video(self) -> Optional[str]:
        """Get a random video from the videos directory"""
        try:
            # Get all video files
            video_files = self._get_video_files()
            
            if not video_files:
                logger.warning("No video files found in videos directory")
                return None
            
            # Select random video
            selected_video = random.choice(video_files)
            logger.info(f"Selected video: {os.path.basename(selected_video)}")
            
            return selected_video
            
        except Exception as e:
            logger.error(f"Failed to get random video: {e}")
            return None
    
    def _get_video_files(self) -> List[str]:
        """Get list of video files from the videos directory"""
        video_files = []
        
        if not os.path.exists(self.videos_dir):
            return video_files
        
        for filename in os.listdir(self.videos_dir):
            if any(filename.lower().endswith(ext) for ext in PipelineConfig.SUPPORTED_VIDEO_FORMATS):
                video_path = os.path.join(self.videos_dir, filename)
                if os.path.isfile(video_path):
                    video_files.append(video_path)
        
        return video_files
    
    def clean_old_videos(self, keep_count: int = 10) -> None:
        """Clean up old video files, keeping only the most recent ones"""
        try:
            video_files = self._get_video_files()
            
            if len(video_files) <= keep_count:
                return
            
            # Sort by modification time (newest first)
            video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remove old files
            files_to_remove = video_files[keep_count:]
            for video_path in files_to_remove:
                try:
                    os.remove(video_path)
                    logger.info(f"Removed old video: {os.path.basename(video_path)}")
                except Exception as e:
                    logger.warning(f"Failed to remove {video_path}: {e}")
            
            logger.info(f"Cleaned up {len(files_to_remove)} old video files")
            
        except Exception as e:
            logger.error(f"Failed to clean old videos: {e}")
    
    def get_video_count(self) -> int:
        """Get the number of available video files"""
        return len(self._get_video_files())
