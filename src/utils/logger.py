"""
Logging configuration
"""
import os
import logging
import sys

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party library log levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('git').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
