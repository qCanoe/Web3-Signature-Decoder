"""
Comprehensive security checker
"""

from typing import Dict, List, Optional
from ..types import NFTMessage, PermitMessage, ParsedMessage
from .price import check_price_security, analyze_balance_changes, detect_suspicious_patterns


class SecurityChecker:
    """Comprehensive security checker"""
    
    def __init__(self, price_threshold: float = 0.1):
        """
        Initialize security checker
        
        Args:
            price_threshold: Price threshold (in ETH)
        """
        self.price_threshold = price_threshold
    
    def check_message_security(self, message: ParsedMessage) -> Dict[str, any]:
        """
        Check message security
        
        Args:
            message: Parsed message
            
        Returns:
            Security check result
        """
        if message.kind == "nft":
            return self.check_nft_security(message.detail)
        elif message.kind == "permit":
            return self.check_permit_security(message.detail)
        else:
            return {"is_safe": False, "errors": ["Unknown message type"]}
    
    def check_nft_security(self, nft_message: NFTMessage) -> Dict[str, any]:
        """
        Check NFT message security
        
        Args:
            nft_message: NFT message
            
        Returns:
            Security check result
        """
        result = {
            "is_safe": True,
            "warnings": [],
            "errors": [],
            "checks": {}
        }
        
        # Price security check
        price_check = check_price_security(nft_message, self.price_threshold)
        result["checks"]["price"] = price_check
        if not price_check["is_safe"]:
            result["is_safe"] = False
            result["warnings"].extend(price_check["warnings"])
            result["errors"].extend(price_check["errors"])
        
        # Balance change analysis
        balance_analysis = analyze_balance_changes(nft_message.balance_change)
        result["checks"]["balance"] = balance_analysis
        
        # Suspicious pattern detection
        suspicious_patterns = detect_suspicious_patterns(nft_message)
        if suspicious_patterns:
            result["warnings"].extend(suspicious_patterns)
            result["is_safe"] = False
        
        result["checks"]["suspicious_patterns"] = suspicious_patterns
        
        return result
    
    def check_permit_security(self, permit_message: PermitMessage) -> Dict[str, any]:
        """
        Check Permit message security
        
        Args:
            permit_message: Permit message
            
        Returns:
            Security check result
        """
        result = {
            "is_safe": True,
            "warnings": [],
            "errors": [],
            "checks": {}
        }
        
        # Check authorization count
        permit_count = len(permit_message.permits)
        if permit_count > 5:
            result["warnings"].append(f"Batch authorization count is high: {permit_count} items")
            result["is_safe"] = False
        
        # Check authorization expiration time
        for i, permit in enumerate(permit_message.permits):
            try:
                expiration = int(permit.expiration)
                # Check if it's unlimited authorization (usually a very large number)
                if expiration > 2**64 - 1:
                    result["warnings"].append(f"Authorization {i+1} is set to never expire")
                    result["is_safe"] = False
            except (ValueError, TypeError):
                result["errors"].append(f"Authorization {i+1} expiration time format error")
                result["is_safe"] = False
        
        result["checks"]["permit_analysis"] = {
            "permit_count": permit_count,
            "permits": [
                {
                    "spender": permit.spender,
                    "amount": permit.amount,
                    "expiration": permit.expiration
                }
                for permit in permit_message.permits
            ]
        }
        
        return result 