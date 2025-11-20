"""
Permit-related parsers
"""

from .permit import Permit
from .permit2 import Permit2
from .permit_lens import PermitLens

from typing import Optional, List
from ..types import EIP712Like, ParsedMessage, PermitMessage, TransactionLike


# All available Permit parser adapters
ALL_ADAPTERS = [
    Permit,
    Permit2,
    PermitLens,
]


def parse_permit_from_request(request: EIP712Like) -> Optional[ParsedMessage]:
    """
    Parse Permit-related EIP712 requests
    
    Args:
        request: EIP712 format request data
        
    Returns:
        Parsed message, returns None if unable to parse
    """
    for adapter in ALL_ADAPTERS:
        try:
            parsed_detail = adapter.parse(request)
            return ParsedMessage(
                kind="permit",
                detail=parsed_detail
            )
        except Exception:
            # Skip parsing errors, try next adapter
            continue
    
    return None


def parse_permit_from_transaction(transaction: TransactionLike) -> Optional[List[PermitMessage]]:
    """
    Parse Permit messages from transaction data
    
    Args:
        transaction: Transaction data
        
    Returns:
        List of parsed Permit messages, returns None if unable to parse
    """
    for adapter in ALL_ADAPTERS:
        if not hasattr(adapter, 'parse_from_transaction'):
            continue
        
        try:
            parsed_detail = adapter.parse_from_transaction(transaction)
            if parsed_detail:
                return parsed_detail
        except Exception:
            # Skip parsing errors, try next adapter
            continue
    
    return None


__all__ = [
    "Permit",
    "Permit2",
    "PermitLens",
    "parse_permit_from_request",
    "parse_permit_from_transaction",
] 