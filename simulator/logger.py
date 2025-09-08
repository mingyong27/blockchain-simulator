# simulator/logger.py

import logging
import json
import os

LOG_FILE = "simulation_log.jsonl"

def setup_logger():
    """Sets up a global logger to output structured JSON data to a file."""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    handler = logging.FileHandler(LOG_FILE)
    logger = logging.getLogger('simulator')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

def log_event(logger, event_data):
    """Logs a dictionary as a JSON string line."""
    if logger:
        logger.info(json.dumps(event_data))