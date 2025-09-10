"""
Logging configuration for Short-Form Video Pipeline
"""
import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(logs_dir, f'short_form_video_pipeline_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    # Create logger
    logger = logging.getLogger('short_form_video_pipeline')
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(f'short_form_video_pipeline.{name}') 