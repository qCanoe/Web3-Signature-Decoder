"""
Integrated NLP Feature Demo
Demonstrates how to use NLP natural language generation in the core EIP712 parser
"""

import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import DynamicEIP712Parser


def demo_integrated_nlp():
    """Demonstrate integrated NLP features"""
    print("🔗 Integrated NLP Feature Demo")
    print("=" * 60)
    
    # Create parser with NLP features enabled
    parser = DynamicEIP712Parser(enable_nlp=True)
    
    # Sample EIP712 data
    permit_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"}
            ]
        },
        "primaryType": "Permit",
        "domain": {
            "name": "USDC",
            "version": "2",
            "chainId": 1,
            "verifyingContract": "0xA0b86a33E6411B3036c2F0F1AB5C6F3f22dd20f5"
        },
        "message": {
            "owner": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "spender": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "value": "1000000000000000000000",
            "nonce": 42,
            "deadline": 1699987456
        }
    }
    
    print("\n1️⃣ Natural Language Generation Only:")
    try:
        nl_result = parser.generate_natural_language(permit_data)
        print(f"   📋 Title: {nl_result.title}")
        print(f"   📖 Summary: {nl_result.summary}")
        print(f"   ⚡ Action: {nl_result.action_summary}")
        print(f"   🌍 Context: {nl_result.context}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n2️⃣ Full Analysis (Traditional + Natural Language):")
    try:
        full_result = parser.analyze_with_natural_language(permit_data)
        
        print(f"   🔍 Traditional Analysis Field Count: {full_result['traditional_analysis']['field_count']}")
        print(f"   🤖 Natural Language Available: {full_result['has_natural_language']}")
        
        if full_result['natural_language']:
            nl = full_result['natural_language']
            print(f"   📝 Natural Language Title: {nl['title']}")
            print(f"   📖 Natural Language Summary: {nl['summary']}")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")


def demo_without_nlp():
    """Demonstrate behavior when NLP features are disabled"""
    print("\n🚫 NLP Features Disabled Demo")
    print("=" * 60)
    
    # Create parser without NLP features
    parser = DynamicEIP712Parser(enable_nlp=False)
    
    permit_data = {
        "types": {"Permit": [{"name": "owner", "type": "address"}]},
        "primaryType": "Permit",
        "domain": {"name": "Test"},
        "message": {"owner": "0x123..."}
    }
    
    print("\nAttempting to generate natural language description:")
    try:
        nl_result = parser.generate_natural_language(permit_data)
        print(f"   ✅ Success: {nl_result.title}")
    except ValueError as e:
        print(f"   ⚠️ Expected Error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected Error: {e}")


def demo_with_json_files():
    """Demo with JSON files"""
    print("\n📁 JSON File Demo")
    print("=" * 60)
    
    parser = DynamicEIP712Parser(enable_nlp=True)
    
    # Try to load JSON files
    json_files = [
        "sample_data/erc20_permit.json",
        "sample_data/dao_vote.json"
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    for json_file in json_files:
        file_path = os.path.join(base_path, json_file)
        print(f"\n📄 Processing File: {json_file}")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result = parser.analyze_with_natural_language(data)
                
                if result['has_natural_language']:
                    nl = result['natural_language']
                    print(f"   📋 {nl['title']}")
                    print(f"   📖 {nl['summary']}")
                else:
                    print("   ⚠️ Natural Language Generation Unavailable")
                    
            except Exception as e:
                print(f"   ❌ Processing Failed: {e}")
        else:
            print(f"   ⚠️ File Not Found")


def compare_traditional_vs_nlp():
    """Compare differences between traditional analysis and NLP output"""
    print("\n⚖️ Traditional Analysis vs NLP Output Comparison")
    print("=" * 60)
    
    # Create two parsers for comparison
    traditional_parser = DynamicEIP712Parser(enable_nlp=False)
    nlp_parser = DynamicEIP712Parser(enable_nlp=True)
    
    sample_data = {
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}],
            "Order": [
                {"name": "maker", "type": "address"},
                {"name": "taker", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        "primaryType": "Order",
        "domain": {"name": "DEX"},
        "message": {
            "maker": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "taker": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "amount": "1000000000000000000"
        }
    }
    
    print("\n📊 Traditional Analysis Results:")
    try:
        traditional_result = traditional_parser.analyze_eip712(sample_data)
        print(f"   Primary Type: {traditional_result['primary_type']}")
        print(f"   Field Count: {traditional_result['field_count']}")
        print(f"   Description: {traditional_result['message_description']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n🔤 NLP Analysis Results:")
    try:
        nlp_result = nlp_parser.generate_natural_language(sample_data)
        print(f"   Title: {nlp_result.title}")
        print(f"   Summary: {nlp_result.summary}")
        print(f"   Action: {nlp_result.action_summary}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")


def main():
    """Main function"""
    print("🚀 EIP712 Parser Integrated NLP Feature Demo")
    print("This demo shows how to integrate NLP natural language generation in the existing EIP712 parser")
    print("=" * 80)
    
    # Run various demos
    demo_integrated_nlp()
    demo_without_nlp()
    demo_with_json_files()
    compare_traditional_vs_nlp()
    
    print("\n✅ Demo Complete!")
    print("\n💡 Integration Usage Instructions:")
    print("   1. Create parser: parser = DynamicEIP712Parser(enable_nlp=True)")
    print("   2. Generate natural language: nl_result = parser.generate_natural_language(data)")
    print("   3. Full analysis: full_result = parser.analyze_with_natural_language(data)")
    print("   4. Traditional analysis: traditional_result = parser.analyze_eip712(data)")


if __name__ == "__main__":
    main() 