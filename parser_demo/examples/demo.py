"""
Dynamic Parser Complete Demo
Demonstrates all features and capabilities
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser
from test_data import ALL_TEST_DATA


def demo_parser():
    """Complete demonstration of dynamic parser functionality"""
    
    
    parser = DynamicEIP712Parser()
    
    for name, data in ALL_TEST_DATA.items():
        print(f"\n📋 Test Data: {name.upper()}")
        print("=" * 80)
        
        try:
            # Parse data
            result = parser.parse(data)
            formatted_result = parser.format_result(result)
            
            print(formatted_result)
            
        except Exception as e:
            print(f"❌ Parsing Failed: {e}")
            continue



def main():
    """Main function"""
    demo_parser()


if __name__ == "__main__":
    main()