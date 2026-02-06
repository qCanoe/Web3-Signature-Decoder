"""
Unified logging module for the Signature Semantic Decoder.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class Logger:
    """Unified logger for the signature decoder."""
    
    _logger: Optional[logging.Logger] = None
    
    @staticmethod
    def get_logger(name: str = "signature_decoder", level: int = logging.INFO) -> logging.Logger:
        """
        Get or create a logger instance.
        
        Args:
            name: Logger name
            level: Logging level
            
        Returns:
            Logger instance
        """
        if Logger._logger is None:
            Logger._logger = logging.getLogger(name)
            Logger._logger.setLevel(level)
            
            # Avoid duplicate handlers
            if not Logger._logger.handlers:
                # Console handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                
                # Formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(formatter)
                
                Logger._logger.addHandler(console_handler)
        
        return Logger._logger
    
    @staticmethod
    def set_level(level: int) -> None:
        """Set logging level."""
        logger = Logger.get_logger()
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
    
    @staticmethod
    def add_file_handler(file_path: Optional[Path] = None) -> None:
        """
        Add file handler to logger.
        
        Args:
            file_path: Path to log file. If None, uses default location.
        """
        if file_path is None:
            file_path = Path("logs") / "signature_decoder.log"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger = Logger.get_logger()
        logger.addHandler(file_handler)

