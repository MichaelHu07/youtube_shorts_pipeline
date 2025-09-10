"""
Video composer for combining audio, video and subtitles into final short-form videos
"""
import os
import sys
import random
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.resize import resize
from typing import Optional, Dict, List, Union
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import get_logger
from src.utils import ensure_directory, generate_timestamped_filename, handle_api_error

logger = get_logger('video_editor')

class VideoComposer:
    def __init__(self):
        """Initialize video composer"""
        self.output_width = PipelineConfig.OUTPUT_WIDTH
        self.output_height = PipelineConfig.OUTPUT_HEIGHT
        self.fps = PipelineConfig.VIDEO_FPS
        
        logger.info("Video composer initialized successfully")
    
    def compose_video(self, 
                     background_video_path: str,
                     audio_path: str,
                     subtitles_data: Optional[List[Dict]] = None,
                     output_filename: Optional[str] = None) -> Union[str, List[str]]:
        """
        Compose final video with background, audio, and optional subtitles
        
        Args:
            background_video_path: Path to background video
            audio_path: Path to audio file
            subtitles_data: Optional list of subtitle segments
            output_filename: Optional custom output filename
        
        Returns:
            Path to final composed video
        """
        try:
            logger.info("Starting video composition")
            
            # Load video and audio
            video_clip = VideoFileClip(background_video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Get audio duration for video length
            target_duration = audio_clip.duration
            
            # Process background video
            processed_video = self._process_background_video(video_clip, target_duration)
            
            # Set audio
            final_video = processed_video.set_audio(audio_clip)
            
            # Add subtitles if provided and rendering is enabled
            if subtitles_data and PipelineConfig.GENERATE_SUBTITLES and PipelineConfig.RENDER_SUBTITLES:
                # Check if we can actually render subtitles
                try:
                    final_video = self._add_subtitles(final_video, subtitles_data)
                except Exception as subtitle_error:
                    logger.warning(f"Subtitle rendering failed, continuing without: {subtitle_error}")
                    # Continue with video without subtitles
            
            # Generate output path
            output_path = self._generate_output_path(output_filename)
            
            # Check if video needs to be split into parts
            if PipelineConfig.SPLIT_LONG_VIDEOS and target_duration > PipelineConfig.MAX_VIDEO_DURATION:
                logger.info(f"Video duration ({target_duration:.1f}s) exceeds duration limit ({PipelineConfig.MAX_VIDEO_DURATION}s), splitting into parts")
                output_paths = self._split_and_export_video(final_video, output_path)
                
                # Clean up
                video_clip.close()
                audio_clip.close()
                final_video.close()
                
                logger.info(f"Video splitting completed: {len(output_paths)} parts created")
                return output_paths  # Return list of video paths
            else:
                # Export single video
                logger.info(f"Exporting final video to: {output_path}")
                final_video.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                
                # Clean up
                video_clip.close()
                audio_clip.close()
                final_video.close()
                
                logger.info(f"Video composition completed: {output_path}")
                return output_path
            
        except Exception as e:
            handle_api_error(e, "Video composition", 'video_editor')
            raise
    
    def _add_subtitles(self, video_clip: VideoFileClip, subtitles_data: List[Dict]):
        """
        Add subtitles to video using simple text rendering
        
        Args:
            video_clip: Video clip to add subtitles to
            subtitles_data: List of subtitle segments
        
        Returns:
            Video with subtitles
        """
        try:
            logger.info(f"Adding {len(subtitles_data)} subtitle segments")
            
            subtitle_clips = []
            
            for subtitle in subtitles_data:
                text = subtitle['text']
                start_time = subtitle['start']
                end_time = subtitle['end']
                
                try:
                    # Create text clip with proper ImageMagick configuration
                    txt_clip = TextClip(
                        text,
                        fontsize=PipelineConfig.SUBTITLE_FONT_SIZE,
                        color=PipelineConfig.SUBTITLE_COLOR,
                        font='Arial-Bold',
                        stroke_color=PipelineConfig.SUBTITLE_STROKE_COLOR,
                        stroke_width=PipelineConfig.SUBTITLE_STROKE_WIDTH,
                        size=(int(self.output_width * 0.9), None),
                        method='caption'
                    ).set_start(start_time).set_end(end_time)
                    
                    # Position subtitle at bottom of screen
                    y_position = int(self.output_height * PipelineConfig.SUBTITLE_POSITION)
                    txt_clip = txt_clip.set_position(('center', y_position))
                    
                    subtitle_clips.append(txt_clip)
                    
                except Exception as text_error:
                    logger.warning(f"Failed to create subtitle for '{text}': {text_error}")
                    continue
            
            if subtitle_clips:
                # Composite video with subtitles
                final_video = CompositeVideoClip([video_clip] + subtitle_clips)
                logger.info(f"Successfully added {len(subtitle_clips)} subtitle segments")
                return final_video
            else:
                logger.warning("No subtitle clips created, returning original video")
                return video_clip
            
        except Exception as e:
            handle_api_error(e, "Add subtitles", 'video_editor')
            logger.warning("Subtitle rendering failed, continuing without subtitles")
            return video_clip  # Return original video if subtitle addition fails
    
    def _process_background_video(self, video_clip: VideoFileClip, target_duration: float) -> VideoFileClip:
        """Process background video for vertical short-form format"""
        try:
            # Get video dimensions
            video_width, video_height = video_clip.size
            
            # Calculate aspect ratios
            video_aspect = video_width / video_height
            target_aspect = self.output_width / self.output_height
            
            # Resize and crop to fit vertical format
            if video_aspect > target_aspect:
                # Video is wider, need to crop width
                new_height = self.output_height
                new_width = int(new_height * video_aspect)
                resized_clip = resize(video_clip, height=new_height)
                
                # Center crop
                x_center = new_width // 2
                crop_width = self.output_width
                x_start = x_center - crop_width // 2
                
                processed_clip = resized_clip.crop(x1=x_start, x2=x_start + crop_width)
            else:
                # Video is taller or same aspect, resize to fit width
                new_width = self.output_width
                new_height = int(new_width / video_aspect)
                processed_clip = resize(video_clip, width=new_width)
                
                # If still too tall, center crop
                if new_height > self.output_height:
                    y_center = new_height // 2
                    crop_height = self.output_height
                    y_start = y_center - crop_height // 2
                    processed_clip = processed_clip.crop(y1=y_start, y2=y_start + crop_height)
            
            # Adjust duration with random starting point
            if video_clip.duration < target_duration:
                # Loop video if too short
                loops_needed = int(target_duration / video_clip.duration) + 1
                processed_clip = processed_clip.loop(n=loops_needed)
                processed_clip = processed_clip.subclip(0, target_duration)
            else:
                # Pick random starting point for longer videos
                max_start_time = max(0, video_clip.duration - target_duration)
                random_start = random.uniform(0, max_start_time)
                processed_clip = processed_clip.subclip(random_start, random_start + target_duration)
                logger.info(f"Selected random snippet: {random_start:.1f}s - {random_start + target_duration:.1f}s")
            
            logger.info(f"Background video processed: {processed_clip.size} @ {target_duration}s")
            return processed_clip
            
        except Exception as e:
            handle_api_error(e, "Background video processing", 'video_editor')
            raise
    
    def _split_and_export_video(self, video_clip: Union[VideoFileClip, CompositeVideoClip], base_output_path: str) -> List[str]:
        """
        Split video into multiple parts for short-form duration limit
        
        Args:
            video_clip: The video clip to split
            base_output_path: Base output path for the video files
        
        Returns:
            List of paths to the split video files
        """
        try:
            total_duration = video_clip.duration
            max_duration = PipelineConfig.MAX_VIDEO_DURATION
            output_paths = []
            
            # Calculate number of parts needed
            num_parts = int(total_duration / max_duration) + (1 if total_duration % max_duration > 0 else 0)
            
            # Generate base filename without extension
            base_name = os.path.splitext(base_output_path)[0]
            
            for part_num in range(num_parts):
                start_time = part_num * max_duration
                end_time = min((part_num + 1) * max_duration, total_duration)
                
                # Create output path for this part
                part_filename = f"{base_name}_part{part_num + 1}.mp4"
                output_paths.append(part_filename)
                
                # Extract the segment
                video_segment = video_clip.subclip(start_time, end_time)
                
                logger.info(f"Exporting part {part_num + 1}/{num_parts}: {start_time:.1f}s - {end_time:.1f}s to {part_filename}")
                
                # Export the segment
                video_segment.write_videofile(
                    part_filename,
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=f'temp-audio-part{part_num + 1}.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                
                # Clean up segment
                video_segment.close()
            
            return output_paths
            
        except Exception as e:
            handle_api_error(e, "Video splitting", 'video_editor')
            raise

    def _generate_output_path(self, custom_filename: Optional[str] = None) -> str:
        """Generate output file path using utility functions"""
        ensure_directory(Config.FINAL_VIDEOS_DIR)
        
        if custom_filename:
            filename = custom_filename
        else:
            filename = generate_timestamped_filename('short_video', 'mp4')
        
        # Ensure .mp4 extension
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        return os.path.join(Config.FINAL_VIDEOS_DIR, filename)
    
    def create_preview_thumbnail(self, video_path: str, timestamp: float = 1.0) -> str:
        """Create a thumbnail from the video"""
        try:
            with VideoFileClip(video_path) as video:
                # Capture frame at specified timestamp
                frame = video.get_frame(timestamp)
                
                # Save thumbnail
                thumbnail_path = video_path.replace('.mp4', '_thumbnail.jpg')
                
                from PIL import Image
                img = Image.fromarray(frame)
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                logger.info(f"Thumbnail created: {thumbnail_path}")
                return thumbnail_path
                
        except Exception as e:
            handle_api_error(e, "Create thumbnail", 'video_editor')
            return ""
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get information about the composed video"""
        try:
            with VideoFileClip(video_path) as video:
                info = {
                    'duration': video.duration,
                    'fps': video.fps,
                    'size': video.size,
                    'filename': os.path.basename(video_path),
                    'file_size': os.path.getsize(video_path)
                }
                
                logger.info(f"Video info retrieved for: {video_path}")
                return info
                
        except Exception as e:
            handle_api_error(e, "Get video info", 'video_editor')
            return {} 