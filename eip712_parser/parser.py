"""
EIP712 Main Parser - Supports protocol-specific parsing and universal dynamic parsing
"""

from typing import Optional, Union, Dict, Any
from .types import EIP712Like, ParsedMessage
from .dynamic_parser import DynamicEIP712Parser, EIP712ParseResult
from . import nft
from . import permit


def parse_request(request: EIP712Like) -> Optional[ParsedMessage]:
    """
    Parse EIP712 request - protocol-specific parsing
    
    Args:
        request: EIP712 format request data
        
    Returns:
        Parsed message, returns None if unable to parse
    """
    # Try to parse NFT-related requests
    nft_result = nft.parse_request(request)
    if nft_result:
        return nft_result
    
    # Try to parse Permit-related requests
    permit_result = permit.parse_permit_from_request(request)
    if permit_result:
        return permit_result
    
    return None


def parse_dynamic(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> EIP712ParseResult:
    """
    Dynamically parse arbitrary EIP712 signature structures
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Dynamic parsing result, containing complete structure tree and semantic annotations
    """
    parser = DynamicEIP712Parser()
    return parser.parse(eip712_data)


def parse_and_format(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> str:
    """
    Parse and format EIP712 data as readable text
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Formatted readable text
    """
    parser = DynamicEIP712Parser()
    result = parser.parse(eip712_data)
    return parser.format_result(result)


def analyze_eip712(eip712_data: Union[EIP712Like, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze EIP712 data and return structured analysis result
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Analysis result dictionary
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