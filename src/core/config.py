"""
Configuration management for Signature Semantic Decoder.
Supports environment variable overrides.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration settings for the signature decoder."""
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "core" / "processing" / "data"
    
    # Risk assessment thresholds
    RISK_THRESHOLDS = {
        "high": 70,
        "medium": 40,
        "low": 0
    }
    
    # Risk scoring weights
    RISK_SCORES = {
        "high_risk_param": 40,
        "medium_risk_param": 20,
        "approve": 15,
        "transfer": 25,
        "high_value_transfer": 30,
        "authentication": -10,
        "authorization": 20,
        "bridge": 30,
        "delegation": 25,
        "cross_contract": 20,
        "unlimited_permanent": 50,
        "unlimited_time_limited": 35,
        "permanent": 25,
        "phishing": 60,
        "blind_signing": 50,
        "unknown_contract": 20,
        "trusted_contract": -10  # Reduce risk for trusted contracts
    }

    # Financial thresholds
    FINANCIAL_THRESHOLDS = {
        "high_value_eth": int(os.getenv("HIGH_VALUE_ETH_THRESHOLD", "1000000000000000000")),  # 1 ETH
        "high_value_usd": float(os.getenv("HIGH_VALUE_USD_THRESHOLD", "1000.0"))  # $1000
    }
    
    # Phishing detection keywords
    PHISHING_KEYWORDS = {
        "urgent": ["urgent", "urgently", "immediately", "asap"],
        "time_pressure": ["expires", "deadline", "limited time", "act now"],
        "authority": ["verify", "confirm", "validate", "verification required"],
        "reward": ["claim", "reward", "bonus", "prize", "free"],
        "threat": ["suspend", "block", "disable", "freeze"]
    }
    
    # Additional suspicious patterns for phishing detection
    SUSPICIOUS_PATTERNS = {
        "similar_address": ["similar to", "looks like", "resembles"],
        "urgency": ["urgent", "immediately", "asap", "hurry", "quick", "fast"],
        "fake_reward": ["claim", "reward", "bonus", "prize", "free", "airdrop", "giveaway"],
        "authority_claim": ["official", "verified", "authentic", "legitimate"],
        "threat": ["suspend", "block", "disable", "freeze", "locked", "restricted"],
    }

    # EIP-712 validation settings
    EIP712_VALIDATION = {
        "strict_mode": os.getenv("EIP712_STRICT_MODE", "false").lower() == "true",
        "warn_only": os.getenv("EIP712_WARN_ONLY", "true").lower() == "true",
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
        "model": os.getenv("LLM_MODEL", "gpt-5.2"),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "100")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3"))
    }
    
    # Logging settings
    LOGGING = {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "file_enabled": os.getenv("LOG_FILE_ENABLED", "false").lower() == "true",
        "file_path": os.getenv("LOG_FILE_PATH", "logs/signature_decoder.log")
    }

    # Risk policy settings
    RISK_POLICY = {
        "version": os.getenv("RISK_POLICY_VERSION", "v1"),
        "filename": os.getenv("RISK_POLICY_FILENAME", "risk_policy.v1.json")
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
