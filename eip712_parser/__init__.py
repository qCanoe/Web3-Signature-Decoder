"""
EIP712 Parser Module

Provides parsing functionality for Ethereum EIP712 signatures, including:
1. Protocol-specific parsers (NFT, Permit, etc.)
2. Universal dynamic parser (arbitrary EIP712 structures)
"""

# Protocol-specific parsing
from .parser import parse_request

# Dynamic parsing functionality  
from .parser import parse_dynamic, parse_and_format, analyze_eip712
from .dynamic_parser import (
    DynamicEIP712Parser, 
    EIP712ParseResult,
    FieldInfo,
    StructInfo,
    FieldType,
    FieldSemantic
)

# Type definitions
from .types import (
    EIP712Like,
    ParsedMessage,
    NFTMessage,
    PermitMessage,
    OrderType,
    NFTProtocolType
)

# Universal parser and signature detection
from .universal_parser import UniversalParser
from .signature_detector import SignatureDetector, SignatureType

__all__ = [
    # Main parsing functions
    "parse_request",           # Protocol-specific parsing
    "parse_dynamic",           # Dynamic parsing of arbitrary structures  
    "parse_and_format",        # Parse and format as text
    "analyze_eip712",          # Analyze and return structured result
    
    # Dynamic parser classes
    "DynamicEIP712Parser",
    "EIP712ParseResult", 
    "FieldInfo",
    "StructInfo",
    "FieldType",
    "FieldSemantic",
    
    # Type definitions
    "EIP712Like",
    "ParsedMessage", 
    "NFTMessage",
    "PermitMessage",
    "OrderType",
    "NFTProtocolType",
    
    # Utility classes
    "UniversalParser",
    "SignatureDetector",
    "SignatureType"
]

# Version information
__version__ = "1.1.0" 