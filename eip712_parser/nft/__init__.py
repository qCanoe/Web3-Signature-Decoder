"""
NFT-related parsers
"""

from .seaport import Seaport
from .blur import Blur
from .looksrare import LooksRare
from .seaport_v14 import SeaportV14
from .blend import Blend

from typing import Optional, List
from ..types import EIP712Like, ParsedMessage


# All available parser adapters
ALL_ADAPTERS = [
    Seaport,
    Blur,
    LooksRare,
    SeaportV14,
    Blend,
]


def parse_request(request: EIP712Like) -> Optional[ParsedMessage]:
    """
    Parse NFT-related EIP712 requests
    
    Args:
        request: EIP712 format request data
        
    Returns:
        Parsed message, returns None if unable to parse
    """
    for adapter in ALL_ADAPTERS:
        try:
            parsed_detail = adapter.parse(request)
            return ParsedMessage(
                kind="nft",
                detail=parsed_detail
            )
        except Exception:
            # Skip parsing errors, try next adapter
            continue
    
    return None


__all__ = [
    "Seaport",
    "Blur", 
    "LooksRare",
    "SeaportV14",
    "Blend",
    "parse_request",
] 