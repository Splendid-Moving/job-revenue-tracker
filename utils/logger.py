import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
log_filename = os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger('job_form_automation')

def log_info(message):
    """Log info message"""
    logger.info(message)

def log_error(message, exc_info=None):
    """Log error message with optional exception info"""
    logger.error(message, exc_info=exc_info)

def log_warning(message):
    """Log warning message"""
    logger.warning(message)
