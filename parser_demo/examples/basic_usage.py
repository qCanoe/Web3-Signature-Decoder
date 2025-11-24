"""
Dynamic Parser Basic Usage Example
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser, parse_and_format, analyze_eip712
from test_data import ERC20_PERMIT, SEAPORT_ORDER


def main():
    """Basic usage example"""
    
    print("=" * 60)
    print("Dynamic EIP712 Parser - Basic Usage Example")
    print("=" * 60)
    
    # Create parser instance
    parser = DynamicEIP712Parser()
    
    # Example 1: Parse ERC20 Permit
    print("\nExample 1: ERC20 Permit Authorization")
    print("-" * 30)
    
    try:
        result = parser.parse_and_format(ERC20_PERMIT)
        print(result)
    except Exception as e:
        print(f"Parsing Failed: {e}")
    
    # Example 2: Parse Seaport Order
    print("\nExample 2: Seaport NFT Order")
    print("-" * 30)
    
    try:
        result = parser.parse_and_format(SEAPORT_ORDER)
        print(result)
    except Exception as e:
        print(f"Parsing Failed: {e}")
    
    # Example 3: Using convenience functions
    print("\nExample 3: Using Convenience Functions")
    print("-" * 30)
    
    try:
        # Direct formatted output
        result = parse_and_format(ERC20_PERMIT)
        print("Convenience Function Parsing Result:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        # Get structured analysis
        analysis = analyze_eip712(ERC20_PERMIT)
        print(f"\nStructured Analysis - Field Count: {analysis['field_count']}")
        print(f"Primary Type: {analysis['primary_type']}")
        
    except Exception as e:
        print(f"Convenience Function Usage Failed: {e}")


if __name__ == "__main__":
    main() 