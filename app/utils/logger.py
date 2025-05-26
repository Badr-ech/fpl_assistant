import logging
import sys
from typing import Optional


def setup_logger(name: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with appropriate formatting
    
    Args:
        name: Optional logger name
        log_level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if they already exist
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler to the logger
    logger.addHandler(handler)
    
    return logger
