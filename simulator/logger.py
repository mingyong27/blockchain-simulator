# simulator/logger.py

import logging
import json
import os

LOG_FILE = "simulation_log.jsonl"

def setup_logger():
    """Sets up a global logger to output structured JSON data to a file."""
    # Ensure the log file is empty before a new run
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    handler = logging.FileHandler(LOG_FILE)
    # Get the root logger
    logger = logging.getLogger('simulator')
    logger.setLevel(logging.INFO)
    
    # This prevents adding handlers multiple times if the function is called again
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

def log_event(logger, event_data):
    """Logs a dictionary as a JSON string line."""
    if logger:
        logger.info(json.dumps(event_data))