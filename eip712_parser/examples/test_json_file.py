#!/usr/bin/env python3
"""
Test JSON File Parsing
Tests the dynamic parser's ability to parse external JSON files
"""

import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_and_format, parse_dynamic, analyze_eip712


def test_json_file():
    
    # Read JSON file
    json_file_path = os.path.join(os.path.dirname(__file__), "test_data.json")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            eip712_data = json.load(f)
        
        print("JSON file read successfully")
        print(f"File path: {json_file_path}")
        print(f"Primary type: {eip712_data['primaryType']}")
        print(f"Domain name: {eip712_data['domain']['name']}")
        print()
        
        # Use dynamic parser to parse
        result_text = parse_and_format(eip712_data)
        print(result_text)
        
        # Use analysis API  
        print("\nStructured Analysis:")
        print("-" * 40)
        analysis = analyze_eip712(eip712_data)
        
        print(f"Primary type: {analysis['message']['primary_type']}")
        print(f"Message description: {analysis['message']['description']}")
        print(f"Field count: {len(analysis['message']['fields'])}")
        
        print(f"\nField Details:")
        for field in analysis['message']['fields']:
            semantic_info = f" ({field['semantic']})" if field['semantic'] else ""
            print(f"   • {field['name']}: {field['type']}{semantic_info}")
            print(f"     Value: {field['value']}")
            print(f"     Description: {field['description']}")
        
        # Check special field handling
        print("\nField Recognition Test:")
        print("-" * 40)
        
        result = parse_dynamic(eip712_data)
        for field in result.message.fields:
            if field.name == "minter":
                print(f"'minter' field correctly identified as: {field.semantic}")
            elif field.name == "tokenId":
                print(f"'tokenId' field correctly identified as: {field.semantic}")
            elif field.name == "price":
                print(f"'price' field correctly identified as: {field.semantic}")
        
    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        print("Please ensure test_data.json file exists in the examples directory")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    except Exception as e:
        print(f"Parsing error: {e}")


def main():
    """Main function"""
    test_json_file()


if __name__ == "__main__":
    main() 