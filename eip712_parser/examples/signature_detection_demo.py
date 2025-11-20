#!/usr/bin/env python3
"""
Signature Detector Demo
Demonstrates how to use the signature detector and universal parser
"""

import json
import sys
import os

# Add parent directory to path to import modules  
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import SignatureDetector, SignatureType, UniversalParser


def demo_signature_detection():
    """Demo signature detection functionality"""
    
    print("🔍 Ethereum Signature Detector Demo")
    print("=" * 60)
    
    # Prepare test data of different types
    test_cases = [
        # 1. EIP-712 structured data signature
        {
            "name": "EIP-712 Seaport Signature",
            "data": {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "OrderComponents": [
                        {"name": "offerer", "type": "address"},
                        {"name": "offer", "type": "OfferItem[]"}
                    ],
                    "OfferItem": [
                        {"name": "itemType", "type": "uint8"},
                        {"name": "token", "type": "address"}
                    ]
                },
                "primaryType": "OrderComponents",
                "domain": {
                    "name": "Seaport",
                    "version": "1.1",
                    "chainId": "1",
                    "verifyingContract": "0x00000000006c3852cbEf3e08E8dF289169EdE581"
                },
                "message": {
                    "offerer": "0xcA1a218397f00ef0549e2555031a24B906200207",
                    "offer": []
                }
            }
        },
        
        # 2. Transaction data
        {
            "name": "Ethereum Transaction",
            "data": {
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x0987654321098765432109876543210987654321",
                "value": "0xde0b6b3a7640000",  # 1 ETH
                "data": "0xa9059cbb0000000000000000000000000987654321098765432109876543210987654321000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "gas": "0x5208",
                "gasPrice": "0x3b9aca00",
                "nonce": "0x1"
            }
        },
        
        # 3. Personal message signature
        {
            "name": "Personal Message Signature",
            "data": "Hello, this is a message to be signed!"
        },
        
        # 4. Personal message signature (Chinese)
        {
            "name": "Chinese Personal Message",
            "data": "你好，这是一条需要签名的消息。请确认你信任此网站。"
        },
        
        # 5. Hexadecimal personal message
        {
            "name": "Hexadecimal Personal Message",
            "data": "0x48656c6c6f2c20576f726c6421"  # Hexadecimal of "Hello, World!"
        },
        
        # 6. Raw signature data
        {
            "name": "Raw Signature Data",
            "data": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef01"
        },
        
        # 7. Hash data
        {
            "name": "Hash Data",
            "data": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        },
        
        # 8. JSON format personal message
        {
            "name": "JSON Format Personal Message",
            "data": {
                "message": "Please sign this message to prove ownership of your wallet.",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    ]
    
    detector = SignatureDetector()
    universal_parser = UniversalParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        # Detect signature type
        signature_info = detector.get_signature_info(test_case['data'])
        
        print(f"🔍 Detection Result:")
        print(f"   Type: {signature_info['type']}")
        print(f"   Description: {signature_info['description']}")
        print(f"   Data format: {signature_info['data_format']}")
        
        # Display analysis results
        analysis = signature_info.get('analysis', {})
        if analysis:
            print(f"📊 Detailed Analysis:")
            for key, value in analysis.items():
                if isinstance(value, list):
                    print(f"   {key}: {', '.join(map(str, value)) if value else 'None'}")
                else:
                    print(f"   {key}: {value}")
        
        # Use universal parser
        print(f"🔧 Universal Parsing Result:")
        parse_result = universal_parser.parse(test_case['data'])
        
        if parse_result['success']:
            print(f"   ✅ Parsing successful")
            
            # Display specific parsing results
            parsed_data = parse_result.get('parsed_data')
            if parsed_data:
                if signature_info['type'] == SignatureType.ETH_SIGN_TYPED_DATA_V4:
                    if hasattr(parsed_data, 'kind'):
                        print(f"   Protocol type: {parsed_data.kind}")
                        if parsed_data.kind == "nft":
                            print(f"   NFT protocol: {parsed_data.detail.type}")
                            print(f"   Order type: {parsed_data.detail.order_type}")
                elif signature_info['type'] == SignatureType.ETH_SEND_TRANSACTION:
                    transaction_info = parsed_data.get('transaction', {})
                    print(f"   From: {transaction_info.get('from', 'Unknown')[:10]}...")
                    print(f"   To: {transaction_info.get('to', 'Unknown')[:10]}...")
                    print(f"   Value: {transaction_info.get('value', '0')}")
                elif signature_info['type'] == SignatureType.PERSONAL_SIGN:
                    message_info = parsed_data.get('message_info', {})
                    print(f"   Message length: {message_info.get('length', 0)}")
                    print(f"   Language: {message_info.get('language', 'unknown')}")
        else:
            print(f"   ❌ Parsing failed: {parse_result.get('error', 'Unknown error')}")
        
        # Security warnings
        if signature_info['type'] in [SignatureType.ETH_SEND_TRANSACTION, SignatureType.PERSONAL_SIGN]:
            parse_result = universal_parser.parse(test_case['data'])
            if parse_result['success'] and parse_result['parsed_data']:
                warnings = parse_result['parsed_data'].get('security_warnings', [])
                if warnings:
                    print(f"⚠️  Security Warnings:")
                    for warning in warnings:
                        print(f"   - {warning}")


def demo_batch_detection():
    """Demo batch detection functionality"""
    print(f"\n{'='*60}")
    print("📦 Batch Signature Detection Demo")
    print("="*60)
    
    # Simulate multiple signature data from files or API
    batch_data = [
        '"Hello World!"',  # Simple string
        '{"message": "Sign this"}',  # JSON personal message
        '{"to": "0x123", "value": "1000"}',  # Simple transaction
        '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',  # Hash
    ]
    
    detector = SignatureDetector()
    
    print("Detection Results Summary:")
    print("-" * 40)
    
    type_counts = {}
    
    for i, data_str in enumerate(batch_data, 1):
        try:
            # Try to parse JSON, if fails treat as string
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = data_str.strip('"')  # Remove possible quotes
            
            signature_type = detector.detect_signature_type(data)
            type_counts[signature_type] = type_counts.get(signature_type, 0) + 1
            
            print(f"  Data {i}: {signature_type}")
            
        except Exception as e:
            print(f"  Data {i}: Detection failed - {e}")
    
    print(f"\nStatistics:")
    for sig_type, count in type_counts.items():
        print(f"  {sig_type}: {count}")


def main():
    """Main function"""
    try:
        demo_signature_detection()
        demo_batch_detection()
        
        print(f"\n{'='*60}")
        print("🎉 Demo complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error occurred during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 