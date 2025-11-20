#!/usr/bin/env python3
"""
EIP712 Dynamic Parsing Demo

Demonstrates how to use the dynamic parser to parse arbitrary EIP712 signature structures
No need to predefine specific protocols, automatically infers field meanings and types
"""

import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_dynamic, parse_and_format, analyze_eip712
from test_data import TEST_DATA_SET


def demo_seaport_order():
    """Demo parsing Seaport NFT order"""
    print("Demo 1: Seaport NFT Order Dynamic Parsing")
    print("-" * 50)
    
    # Use dynamic parser to parse and format
    result_text = parse_and_format(TEST_DATA_SET["seaport_order"])
    print(result_text)


def demo_permit_message():
    """Demo parsing Permit authorization message"""
    print("\n\nDemo 2: ERC20 Permit Authorization Dynamic Parsing")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["permit"])
    print(result_text)


def demo_dao_voting():
    """Demo parsing DAO voting message"""
    print("\n\nDemo 3: DAO Governance Voting Dynamic Parsing")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["dao_voting"])
    print(result_text)


def demo_custom_struct():
    """Demo parsing custom complex structure"""
    print("\n\nDemo 4: Custom Complex Structure Dynamic Parsing")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["custom_struct"])
    print(result_text)


def demo_analysis_api():
    """Demo analysis API"""
    print("\n\nDemo 5: Structured Analysis API")
    print("-" * 50)
    
    # Use analysis API
    analysis = analyze_eip712(TEST_DATA_SET["simple_permit"])
    
    print(" Structured Analysis Result:")
    print(f" Primary type: {analysis['message']['primary_type']}")
    print(f" Message description: {analysis['message']['description']}")
    print(f" Field count: {len(analysis['message']['fields'])}")
    
    print(f"\nField Details:")
    for field in analysis['message']['fields']:
        semantic_info = f" ({field['semantic']})" if field['semantic'] else ""
        print(f"   • {field['name']}: {field['type']}{semantic_info}")
        print(f"     Value: {field['value']}")
        print(f"     Description: {field['description']}")


def main():
    """Main function"""
    # Run all demos
    demo_seaport_order()
    demo_permit_message()
    demo_dao_voting()
    demo_custom_struct()
    demo_analysis_api()


if __name__ == "__main__":
    main() 