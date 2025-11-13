"""
EIP712 主解析器 - 支持协议特定解析和通用动态解析
"""

from typing import Optional, Union, Dict, Any
from .types import EIP712Like, ParsedMessage
from .dynamic_parser import DynamicEIP712Parser, EIP712ParseResult
from . import nft
from . import permit


def parse_request(request: EIP712Like) -> Optional[ParsedMessage]:
    """
    解析 EIP712 请求 - 协议特定解析
    
    Args:
        request: EIP712 格式的请求数据
        
    Returns:
        解析后的消息，如果无法解析则返回 None
    """
    # 尝试解析 NFT 相关请求
    nft_result = nft.parse_request(request)
    if nft_result:
        return nft_result
    
    # 尝试解析 Permit 相关请求
    permit_result = permit.parse_permit_from_request(request)
    if permit_result:
        return permit_result
    
    return None


def parse_dynamic(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> EIP712ParseResult:
    """
    动态解析任意 EIP712 签名结构
    
    Args:
        eip712_data: EIP712 格式的数据
        
    Returns:
        动态解析结果，包含完整的结构树和语义标注
    """
    parser = DynamicEIP712Parser()
    return parser.parse(eip712_data)


def parse_and_format(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> str:
    """
    解析并格式化 EIP712 数据为可读文本
    
    Args:
        eip712_data: EIP712 格式的数据
        
    Returns:
        格式化的可读文本
    """
    parser = DynamicEIP712Parser()
    result = parser.parse(eip712_data)
    return parser.format_result(result)


def analyze_eip712(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析 EIP712 数据并返回结构化分析结果
    
    Args:
        eip712_data: EIP712 格式的数据
        
    Returns:
        分析结果字典
    """
    parser = DynamicEIP712Parser()
    result = parser.parse(eip712_data)
    
    return {
        "domain": {
            "name": result.domain.name,
            "description": result.domain.description,
            "fields": [
                {
                    "name": field.name,
                    "type": field.type_name,
                    "semantic": field.semantic.value if field.semantic else None,
                    "value": field.value,
                    "description": field.description
                }
                for field in result.domain.fields
            ]
        },
        "message": {
            "primary_type": result.primary_type,
            "description": result.message.description,
            "fields": [
                {
                    "name": field.name,
                    "type": field.type_name,
                    "semantic": field.semantic.value if field.semantic else None,
                    "value": field.value,
                    "description": field.description,
                    "is_array": field.is_array,
                    "children_count": len(field.children)
                }
                for field in result.message.fields
            ]
        }
    } 