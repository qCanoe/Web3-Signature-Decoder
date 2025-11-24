"""
NLP Natural Language Generator Demo
Demonstrates how to directly use NLP models to convert structured EIP712 data to natural language output
"""

import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_natural_language_generator import create_nlp_generator, NaturalLanguageOutput


def print_natural_language_output(output: NaturalLanguageOutput):
    """Print natural language output results"""
    print("=" * 80)
    print(f"📋 Title: {output.title}")
    print("=" * 80)
    
    print(f"\n📖 Brief Summary:")
    print(f"   {output.summary}")
    
    print(f"\n🔍 Detailed Description:")
    print(f"   {output.detailed_description}")
    
    print(f"\n📝 Field Details:")
    for field_desc in output.field_descriptions:
        print(f"   {field_desc}")
    
    print(f"\n🌍 Execution Context:")
    print(f"   {output.context}")
    
    print(f"\n⚡ Action Summary:")
    print(f"   {output.action_summary}")
    
    print("\n" + "=" * 80)


def demo_erc20_permit():
    """Demonstrate natural language conversion for ERC20 authorization permit"""
    print("\n🚀 Demo 1: ERC20 Token Authorization Permit")
    
    # ERC20 Permit data
    erc20_permit_data = {
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
            "name": "USD Coin",
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
    
    # Create NLP generator
    generator = create_nlp_generator()
    
    # Convert to natural language
    result = generator.convert_to_natural_language(erc20_permit_data)
    
    # Output results
    print_natural_language_output(result)


def demo_seaport_order():
    """Demonstrate natural language conversion for Seaport NFT order"""
    print("\n🚀 Demo 2: Seaport NFT Marketplace Order")
    
    # Seaport Order data (simplified version)
    seaport_order_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "OrderComponents": [
                {"name": "offerer", "type": "address"},
                {"name": "zone", "type": "address"},
                {"name": "offer", "type": "OfferItem[]"},
                {"name": "consideration", "type": "ConsiderationItem[]"},
                {"name": "orderType", "type": "uint8"},
                {"name": "startTime", "type": "uint256"},
                {"name": "endTime", "type": "uint256"},
                {"name": "salt", "type": "uint256"}
            ]
        },
        "primaryType": "OrderComponents",
        "domain": {
            "name": "Seaport",
            "version": "1.4",
            "chainId": 1,
            "verifyingContract": "0x00000000006c3852cbEf3e08E8dF289169EdE581"
        },
        "message": {
            "offerer": "0x8ba1f109551bD432803012645Hac136c22C04e2D",
            "zone": "0x0000000000000000000000000000000000000000",
            "offer": [
                {
                    "itemType": 2,
                    "token": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                    "identifierOrCriteria": "8547",
                    "startAmount": "1",
                    "endAmount": "1"
                }
            ],
            "consideration": [
                {
                    "itemType": 0,
                    "token": "0x0000000000000000000000000000000000000000",
                    "identifierOrCriteria": "0",
                    "startAmount": "975000000000000000",
                    "endAmount": "975000000000000000",
                    "recipient": "0x8ba1f109551bD432803012645Hac136c22C04e2D"
                }
            ],
            "orderType": 0,
            "startTime": 1699143856,
            "endTime": 1700007856,
            "salt": 123456789
        }
    }
    
    # Create NLP generator
    generator = create_nlp_generator()
    
    # Convert to natural language
    result = generator.convert_to_natural_language(seaport_order_data)
    
    # Output results
    print_natural_language_output(result)


def demo_with_template_generation():
    """Demonstrate natural language generation using templates"""
    print("\n🚀 Demo 3: Natural Language Generation Using Templates")
    
    # Simple voting data
    vote_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "Vote": [
                {"name": "voter", "type": "address"},
                {"name": "proposal", "type": "uint256"},
                {"name": "support", "type": "uint8"}
            ]
        },
        "primaryType": "Vote",
        "domain": {
            "name": "GovernanceDAO",
            "version": "1",
            "chainId": 1
        },
        "message": {
            "voter": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "proposal": 15,
            "support": 1
        }
    }
    
    # Generate using NLP templates
    try:
        generator = create_nlp_generator()
        result = generator.convert_to_natural_language(vote_data)
        print_natural_language_output(result)
    except Exception as e:
        print(f"NLP Generation Failed: {e}")


def demo_from_json_file():
    """Demo loading data from JSON files"""
    print("\n🚀 Demo 4: Loading Data from JSON Files")
    
    # Try to load sample JSON files
    json_files = [
        "sample_data/erc20_permit.json",
        "sample_data/seaport_order.json",
        "sample_data/dao_vote.json"
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    generator = create_nlp_generator()
    
    for json_file in json_files:
        file_path = os.path.join(base_path, json_file)
        if os.path.exists(file_path):
            print(f"\n📁 Loading File: {json_file}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result = generator.convert_to_natural_language(data)
                print_natural_language_output(result)
                
            except Exception as e:
                print(f"   ❌ File Processing Failed: {e}")
        else:
            print(f"   ⚠️ File Not Found: {json_file}")


def compare_outputs():
    """Compare different output formats"""
    print("\n🚀 Demo 5: Output Format Comparison")
    
    # Use simple data for comparison
    simple_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "Transfer": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        "primaryType": "Transfer",
        "domain": {
            "name": "MyToken",
            "chainId": 1
        },
        "message": {
            "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "to": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "amount": "5000000000000000000"
        }
    }
    
    generator = create_nlp_generator()
    result = generator.convert_to_natural_language(simple_data)
    
    print("🎯 Natural Language Format Output:")
    print_natural_language_output(result)
    
    print("\n📊 Structured Format Comparison:")
    print("   Traditional Format: Field list + Technical description")
    print("   NLP Format: Fluent English + Contextual explanation")
    print("   Advantage: Easier to understand, suitable for general users")


def main():
    """Main function"""
    print("🔤 EIP712 Structured Data NLP Natural Language Generator Demo")
    print("=" * 80)
    print("This demo shows how to directly use NLP technology to convert complex EIP712 structured data")
    print("into fluent English natural language descriptions without relying on AI-enhanced analysis.")
    print("=" * 80)
    
    # Run various demos
    demo_erc20_permit()
    demo_seaport_order()
    demo_with_template_generation()
    demo_from_json_file()
    compare_outputs()
    
    print("\n✅ Demo Complete!")
    print("\n💡 Usage Instructions:")
    print("   1. Import nlp_natural_language_generator module")
    print("   2. Create generator: generator = create_nlp_generator()")
    print("   3. Convert data: result = generator.convert_to_natural_language(data)")
    print("   4. Get natural language output: result.summary, result.detailed_description, etc.")


if __name__ == "__main__":
    main() 