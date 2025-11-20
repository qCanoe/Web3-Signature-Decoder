"""
Price security check module
"""

from typing import Dict, List, Optional, Tuple
from ..types import NFTMessage, ParsedDetail, BalanceChange


def check_price_security(message: NFTMessage, price_threshold: float = 0.1) -> Dict[str, any]:
    """
    Check price security
    
    Args:
        message: NFT message
        price_threshold: Price threshold (in ETH)
        
    Returns:
        Security check result
    """
    result = {
        "is_safe": True,
        "warnings": [],
        "errors": [],
        "price_analysis": {}
    }
    
    # Analyze price
    nft_items = [item for item in message.offer if item.kind == "nft"]
    token_items = [item for item in message.consideration if item.kind == "token"]
    
    if nft_items and token_items:
        # Calculate NFT count and token amount
        nft_count = len(nft_items)
        total_token_amount = sum(float(item.detail.amount) for item in token_items)
        
        # Simple price check
        if total_token_amount < price_threshold * (10**18):  # Convert to wei
            result["warnings"].append(f"Price may be too low: {total_token_amount / (10**18):.4f} ETH")
            result["is_safe"] = False
        
        result["price_analysis"] = {
            "nft_count": nft_count,
            "total_price_wei": str(int(total_token_amount)),
            "total_price_eth": total_token_amount / (10**18)
        }
    
    return result


def analyze_balance_changes(balance_change: BalanceChange) -> Dict[str, any]:
    """
    Analyze balance changes
    
    Args:
        balance_change: Balance change data
        
    Returns:
        Analysis result
    """
    analysis = {
        "addresses": len(balance_change),
        "total_changes": 0,
        "address_details": {}
    }
    
    for address, changes in balance_change.items():
        analysis["address_details"][address] = {
            "change_count": len(changes),
            "changes": changes
        }
        analysis["total_changes"] += len(changes)
    
    return analysis


def detect_suspicious_patterns(message: NFTMessage) -> List[str]:
    """
    Detect suspicious patterns
    
    Args:
        message: NFT message
        
    Returns:
        List of suspicious patterns
    """
    warnings = []
    
    # Check if there are a large number of NFT transfers
    nft_count = sum(1 for item in message.offer if item.kind == "nft")
    if nft_count > 10:
        warnings.append(f"Involves large number of NFT transfers: {nft_count} items")
    
    # Check if there are zero-price transactions
    zero_price_tokens = [
        item for item in message.consideration 
        if item.kind == "token" and float(item.detail.amount) == 0
    ]
    if zero_price_tokens:
        warnings.append("Zero-price transaction detected")
    
    # Check time window
    if hasattr(message, 'start_time') and hasattr(message, 'end_time'):
        try:
            duration = int(message.end_time) - int(message.start_time)
            if duration > 86400 * 365:  # More than one year
                warnings.append(f"Order validity period too long: {duration // 86400} days")
        except (ValueError, TypeError):
            pass
    
    return warnings 