import logging
import sys

def setup_logger():
    """Set up the logger for the TTRPG Assistant."""
    # Prevent duplicate handlers if this function is called multiple times
    logger = logging.getLogger("TTRPG_Assistant")
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Create handlers
    # Direct console logs to stderr to keep stdout clean for JSON-RPC
    stream_handler = logging.StreamHandler(sys.stderr)
    file_handler = logging.FileHandler("ttrpg_assistant.log")

    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()