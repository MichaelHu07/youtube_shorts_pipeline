"""
ElevenLabs client for text-to-speech conversion
"""
import os
import requests
import sys
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import get_logger
from src.utils import ensure_directory, generate_timestamped_filename, handle_api_error

logger = get_logger('speech_synthesis')

class ElevenLabsClient:
    def __init__(self):
        """Initialize ElevenLabs client"""
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found in configuration")
        
        logger.info("ElevenLabs client initialized successfully")
    
    def text_to_speech(self, text: str, output_filename: Optional[str] = None) -> str:
        """
        Convert text to speech using ElevenLabs API with config settings
        
        Args:
            text: Text to convert to speech
            output_filename: Optional custom filename for output
        
        Returns:
            Path to generated audio file
        """
        try:
            logger.info(f"Converting text to speech: {text[:50]}...")
            
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_flash_v2_5",
                "voice_settings": {
                    "stability": PipelineConfig.VOICE_STABILITY,
                    "similarity_boost": PipelineConfig.VOICE_SIMILARITY_BOOST,
                    "style": PipelineConfig.VOICE_STYLE,
                    "use_speaker_boost": PipelineConfig.USE_SPEAKER_BOOST
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            audio_filepath = self._save_audio_file(response.content, output_filename)
            
            logger.info(f"Text-to-speech conversion completed: {audio_filepath}")
            return audio_filepath
            
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "ElevenLabs API request", 'speech_synthesis')
            raise
        except Exception as e:
            handle_api_error(e, "Text-to-speech conversion", 'speech_synthesis')
            raise
    
    def _save_audio_file(self, audio_content: bytes, output_filename: Optional[str] = None) -> str:
        """Save audio content to file using utility functions and config settings"""
        ensure_directory(Config.AUDIO_DIR)
        
        if not output_filename:
            if PipelineConfig.USE_TIMESTAMPED_FILENAMES:
                output_filename = generate_timestamped_filename('narration', 'mp3')
            else:
                output_filename = 'narration.mp3'
        
        # Ensure .mp3 extension
        if not output_filename.endswith('.mp3'):
            output_filename += '.mp3'
        
        filepath = os.path.join(Config.AUDIO_DIR, output_filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_content)
        
        logger.info(f"Audio file saved: {filepath}")
        return filepath
    
    def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            voices = response.json().get('voices', [])
            logger.info(f"Retrieved {len(voices)} available voices")
            
            return voices
            
        except Exception as e:
            handle_api_error(e, "Get available voices", 'speech_synthesis')
            return []
    
    def get_voice_info(self, voice_id: Optional[str] = None) -> dict:
        """Get information about a specific voice"""
        if not voice_id:
            voice_id = self.voice_id
        
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            voice_info = response.json()
            logger.info(f"Retrieved voice info for: {voice_info.get('name', 'Unknown')}")
            
            return voice_info
            
        except Exception as e:
            handle_api_error(e, "Get voice info", 'speech_synthesis')
            return {}
    
    def estimate_audio_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length using config settings
        
        Args:
            text: Text to estimate duration for
        
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        return PipelineConfig.get_duration_estimate(word_count) 