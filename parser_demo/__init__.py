"""
Dynamic EIP712 Parser
A universal tool capable of parsing arbitrary EIP712 signature structures and semantics

Main Features:
- Dynamic parsing of EIP712 signature structures
- Intelligent recognition of field semantics and types
- Context-aware field inference
- NLP natural language generation functionality
- Multiple output format support

Usage Example:
    >>> from dynamic_parser import DynamicEIP712Parser
    >>> parser = DynamicEIP712Parser()
    >>> result = parser.parse(eip712_data)
    >>> print(parser.format_result(result))
    
    # NLP natural language functionality
    >>> parser = DynamicEIP712Parser(enable_nlp=True)
    >>> nl_result = parser.generate_natural_language(eip712_data)
"""

from .core import DynamicEIP712Parser
from .field_types import (
    FieldType, FieldSemantic, FieldInfo, 
    StructInfo, EIP712ParseResult
)
from .patterns import PatternMatcher
from .analyzers import ValueAnalyzer
from .formatters import DescriptionFormatter, ResultFormatter

# Version information
__version__ = "1.0.0"
__author__ = "Dynamic Parser Team"
__description__ = "Universal dynamic EIP712 signature parser"

# Main interface
__all__ = [
    # Core parser
    "DynamicEIP712Parser",
    
    # Type definitions
    "FieldType",
    "FieldSemantic", 
    "FieldInfo",
    "StructInfo",
    "EIP712ParseResult",
    
    # Utility classes
    "PatternMatcher",
    "ValueAnalyzer",
    "DescriptionFormatter",
    "ResultFormatter",
    
    # Convenience functions
    "parse_dynamic",
    "parse_and_format",
    "analyze_eip712",
]

# Convenience functions
def parse_dynamic(eip712_data):
    """
    Quickly parse EIP712 data
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Parsing result object
    """
    parser = DynamicEIP712Parser()
    return parser.parse(eip712_data)


def parse_and_format(eip712_data):
    """
    Parse and format EIP712 data
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Formatted text result
    """
    parser = DynamicEIP712Parser()
    return parser.parse_and_format(eip712_data)


def analyze_eip712(eip712_data):
    """
    Analyze EIP712 data and return structured result
    
    Args:
        eip712_data: EIP712 format data
        
    Returns:
        Structured analysis result
    """
    parser = DynamicEIP712Parser()
    return parser.analyze_eip712(eip712_data) 