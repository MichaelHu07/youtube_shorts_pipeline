"""
Utility functions for the Short-Form Video Pipeline
"""
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

def ensure_directory(directory_path: str) -> None:
    """Ensure a directory exists, create it if it doesn't"""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except Exception as e:
        raise Exception(f"Failed to create directory {directory_path}: {e}")

def generate_timestamped_filename(prefix: str, extension: str, post_id: str = None) -> str:
    """Generate a filename with timestamp and optional post ID"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if post_id:
        return f"{prefix}_{post_id}_{timestamp}.{extension}"
    else:
        return f"{prefix}_{timestamp}.{extension}"

def save_json_file(data: Dict[Any, Any], filepath: str) -> None:
    """Save data to a JSON file"""
    try:
        ensure_directory(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Failed to save JSON file {filepath}: {e}")

def handle_api_error(error: Exception, operation: str, module: str) -> None:
    """Handle API errors with consistent logging"""
    logger = logging.getLogger(f'short_form_video_pipeline.{module}')
    logger.error(f"API error during {operation}: {error}")

def check_subtitle_system() -> Dict[str, bool]:
    """Check if subtitle system is working properly"""
    try:
        from moviepy.editor import TextClip
        # Try to create a simple text clip
        test_clip = TextClip("test", fontsize=50, color='white', font='Arial')
        test_clip.close()
        return {
            'textclip_working': True,
            'whisper_available': True
        }
    except Exception as e:
        return {
            'textclip_working': False,
            'whisper_available': True,
            'error': str(e)
        }

class PipelineProgress:
    """Simple progress tracker for pipeline steps"""
    
    def __init__(self):
        self.steps = [
            "Fetching Reddit post",
            "Generating narration",
            "Getting background video", 
            "Generating subtitles",
            "Composing final video"
        ]
        self.current_step = 0
    
    def show_step(self, step_name: str = None):
        """Show current step"""
        if step_name:
            print(f"Step {self.current_step + 1}: {step_name}")
        else:
            print(f"Step {self.current_step + 1}: {self.steps[self.current_step]}")
    
    def next_step(self):
        """Move to next step"""
        self.current_step += 1
    
    def complete(self):
        """Mark pipeline as complete"""
        print("Pipeline completed successfully!")

def clean_old_files(directory: str, extension: str, keep_count: int = 10, logger_name: str = 'pipeline') -> None:
    """Clean up old files, keeping only the most recent ones"""
    try:
        logger = logging.getLogger(f'short_form_video_pipeline.{logger_name}')
        
        if not os.path.exists(directory):
            return
        
        # Get all files with the specified extension
        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        
        if len(files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        file_paths = [os.path.join(directory, f) for f in files]
        file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Remove old files
        files_to_remove = file_paths[keep_count:]
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                logger.info(f"Removed old file: {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Failed to remove {file_path}: {e}")
        
        logger.info(f"Cleaned up {len(files_to_remove)} old {extension} files from {directory}")
        
    except Exception as e:
        logger = logging.getLogger(f'short_form_video_pipeline.{logger_name}')
        logger.error(f"Failed to clean old files in {directory}: {e}")
