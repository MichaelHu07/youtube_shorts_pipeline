"""
Subtitle generation using OpenAI Whisper
"""
import os
import sys
import json
import whisper
from datetime import datetime
from typing import List, Dict, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import get_logger
from src.utils import ensure_directory, generate_timestamped_filename, handle_api_error

logger = get_logger('subtitle_generator')

class WhisperSubtitles:
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper subtitle generator
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        """
        try:
            logger.info(f"Loading Whisper model: {model_size}")
            self.model = whisper.load_model(model_size)
            self.model_size = model_size
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            handle_api_error(e, f"Load Whisper model {model_size}", 'subtitle_generator')
            self.model = None
    
    def generate_subtitles(self, audio_path: str, max_words_per_segment: int = 8) -> List[Dict]:
        """
        Generate subtitles from audio file using Whisper
        
        Args:
            audio_path: Path to audio file
            max_words_per_segment: Maximum words per subtitle segment
        
        Returns:
            List of subtitle segments with timing information
        """
        if self.model is None:
            logger.error("Whisper model not loaded")
            return []
            
        try:
            logger.info(f"Generating subtitles for: {audio_path}")
            
            # Transcribe audio with word-level timestamps
            result = self.model.transcribe(audio_path, word_timestamps=True)
            
            # Process into subtitle segments
            subtitle_segments = self._create_subtitle_segments(result, max_words_per_segment)
            
            # Save subtitles
            if PipelineConfig.SAVE_SUBTITLE_FILES:
                self._save_subtitles(subtitle_segments, audio_path)
            
            logger.info(f"Generated {len(subtitle_segments)} subtitle segments")
            return subtitle_segments
            
        except Exception as e:
            handle_api_error(e, "Generate subtitles", 'subtitle_generator')
            return []
    
    def _create_subtitle_segments(self, whisper_result: Dict, max_words_per_segment: int) -> List[Dict]:
        """
        Create subtitle segments from Whisper transcription result
        
        Args:
            whisper_result: Whisper transcription result
            max_words_per_segment: Maximum words per segment
        
        Returns:
            List of subtitle segments
        """
        try:
            subtitle_segments = []
            
            # Get segments from Whisper result
            segments = whisper_result.get('segments', [])
            
            for segment in segments:
                words = segment.get('words', [])
                if not words:
                    # Fallback to segment-level timing if word-level not available
                    text = segment.get('text', '').strip()
                    if text:
                        subtitle_segments.append({
                            'text': self._clean_subtitle_text(text),
                            'start': segment.get('start', 0),
                            'end': segment.get('end', 0),
                            'duration': segment.get('end', 0) - segment.get('start', 0)
                        })
                    continue
                
                # Process word-level timestamps
                current_segment = []
                current_start = None
                
                for word_info in words:
                    word = word_info.get('word', '').strip()
                    start_time = word_info.get('start', 0)
                    end_time = word_info.get('end', 0)
                    
                    if not word:
                        continue
                    
                    # Start new segment if needed
                    if current_start is None:
                        current_start = start_time
                    
                    current_segment.append(word)
                    
                    # Check if we should end current segment
                    should_end_segment = (
                        len(current_segment) >= max_words_per_segment or
                        self._is_sentence_end(word) or
                        (end_time - current_start) > PipelineConfig.MAX_SUBTITLE_DURATION
                    )
                    
                    if should_end_segment:
                        # Create subtitle segment
                        segment_text = ' '.join(current_segment)
                        segment_text = self._clean_subtitle_text(segment_text)
                        
                        subtitle_segments.append({
                            'text': segment_text,
                            'start': current_start,
                            'end': end_time,
                            'duration': end_time - current_start
                        })
                        
                        # Reset for next segment
                        current_segment = []
                        current_start = None
                
                # Handle remaining words in segment
                if current_segment and current_start is not None:
                    segment_text = ' '.join(current_segment)
                    segment_text = self._clean_subtitle_text(segment_text)
                    
                    # Use last word's end time
                    last_end = words[-1].get('end', current_start + 2.0)
                    
                    subtitle_segments.append({
                        'text': segment_text,
                        'start': current_start,
                        'end': last_end,
                        'duration': last_end - current_start
                    })
            
            return subtitle_segments
            
        except Exception as e:
            handle_api_error(e, "Create subtitle segments", 'subtitle_generator')
            return []
    
    def _is_sentence_end(self, word: str) -> bool:
        """Check if word ends a sentence"""
        return word.rstrip().endswith(('.', '!', '?'))
    
    def _clean_subtitle_text(self, text: str) -> str:
        """Clean subtitle text for better readability"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Fix punctuation spacing
        text = text.replace(' ,', ',')
        text = text.replace(' .', '.')
        text = text.replace(' !', '!')
        text = text.replace(' ?', '?')
        
        return text
    
    def _save_subtitles(self, subtitle_segments: List[Dict], audio_path: str) -> str:
        """Save subtitles to JSON file"""
        try:
            ensure_directory(Config.SUBTITLES_DIR)
            
            # Generate filename
            audio_filename = os.path.basename(audio_path)
            audio_name = os.path.splitext(audio_filename)[0]
            
            if PipelineConfig.INCLUDE_POST_ID_IN_FILENAMES:
                subtitle_filename = generate_timestamped_filename(
                    f"subtitles_{audio_name}", 'json'
                )
            else:
                subtitle_filename = generate_timestamped_filename('subtitles', 'json')
            
            subtitle_path = os.path.join(Config.SUBTITLES_DIR, subtitle_filename)
            
            # Save subtitles
            subtitle_data = {
                'audio_file': audio_path,
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model_size,
                'segments': subtitle_segments
            }
            
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                json.dump(subtitle_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Subtitles saved to: {subtitle_path}")
            return subtitle_path
            
        except Exception as e:
            handle_api_error(e, "Save subtitles", 'subtitle_generator')
            return ""
    
    def export_srt(self, subtitle_segments: List[Dict], output_path: Optional[str] = None) -> str:
        """Export subtitles in SRT format"""
        try:
            if not output_path:
                ensure_directory(Config.SUBTITLES_DIR)
                filename = generate_timestamped_filename('subtitles', 'srt')
                output_path = os.path.join(Config.SUBTITLES_DIR, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(subtitle_segments, 1):
                    start_time = self._seconds_to_srt_time(segment['start'])
                    end_time = self._seconds_to_srt_time(segment['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text']}\n\n")
            
            logger.info(f"SRT file exported to: {output_path}")
            return output_path
            
        except Exception as e:
            handle_api_error(e, "Export SRT", 'subtitle_generator')
            return ""
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}" 