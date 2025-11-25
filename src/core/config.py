"""
Configuration management for Signature Semantic Decoder.
Supports environment variable overrides.
"""

import os
from typing import Dict, Any, Optional


class Config:
    """Configuration settings for the signature decoder."""
    
    # Risk assessment thresholds
    RISK_THRESHOLDS = {
        "high": 70,
        "medium": 40,
        "low": 0
    }
    
    # Financial thresholds
    FINANCIAL_THRESHOLDS = {
        "high_value_eth": int(os.getenv("HIGH_VALUE_ETH_THRESHOLD", "1000000000000000000")),  # 1 ETH
        "high_value_usd": float(os.getenv("HIGH_VALUE_USD_THRESHOLD", "1000.0"))  # $1000
    }
    
    # EIP-712 validation settings
    EIP712_VALIDATION = {
        "strict_mode": os.getenv("EIP712_STRICT_MODE", "false").lower() == "true",
        "check_circular_deps": True,
        "validate_nested_types": True
    }
    
    # Performance settings
    PERFORMANCE = {
        "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
        "cache_size": int(os.getenv("CACHE_SIZE", "1000")),
        "cache_ttl": int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    }
    
    # LLM settings
    LLM = {
        "enabled": os.getenv("LLM_ENABLED", "false").lower() == "true",
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "100")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3"))
    }
    
    # Logging settings
    LOGGING = {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "file_enabled": os.getenv("LOG_FILE_ENABLED", "false").lower() == "true",
        "file_path": os.getenv("LOG_FILE_PATH", "logs/signature_decoder.log")
    }
    
    @staticmethod
    def get(key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., "RISK_THRESHOLDS.high")
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split(".")
        value = Config.__dict__
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    @staticmethod
    def update(section: str, updates: Dict[str, Any]) -> None:
        """
        Update configuration section.
        
        Args:
            section: Configuration section name
            updates: Dictionary of updates
        """
        if hasattr(Config, section):
            section_dict = getattr(Config, section)
            if isinstance(section_dict, dict):
                section_dict.update(updates)

