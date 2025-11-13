"""
NFT 相关解析器
"""

from .seaport import Seaport
from .blur import Blur
from .looksrare import LooksRare
from .seaport_v14 import SeaportV14
from .blend import Blend

from typing import Optional, List
from ..types import EIP712Like, ParsedMessage


# 所有可用的解析器适配器
ALL_ADAPTERS = [
    Seaport,
    Blur,
    LooksRare,
    SeaportV14,
    Blend,
]


def parse_request(request: EIP712Like) -> Optional[ParsedMessage]:
    """
    解析 NFT 相关的 EIP712 请求
    
    Args:
        request: EIP712 格式的请求数据
        
    Returns:
        解析后的消息，如果无法解析则返回 None
    """
    for adapter in ALL_ADAPTERS:
        try:
            parsed_detail = adapter.parse(request)
            return ParsedMessage(
                kind="nft",
                detail=parsed_detail
            )
        except Exception:
            # 跳过解析错误，尝试下一个适配器
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