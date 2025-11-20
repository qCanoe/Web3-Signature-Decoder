#!/usr/bin/env python3
"""
EIP712 Parser Advanced Analysis Example
Demonstrates detailed signature analysis and modular parameter breakdown
"""

import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_request
from eip712_parser.security import SecurityChecker
from eip712_parser.types import OrderType, NFTProtocolType


def analyze_eip712_signature(eip712_data, signature_name=""):
    """
    Detailed analysis of EIP712 signature
    
    Args:
        eip712_data: Data in EIP712 format
        signature_name: Signature name (for display)
    """
    print(f"\n{'='*60}")
    print(f"Analyzing {signature_name} EIP712 Signature")
    print(f"{'='*60}")
    
    # 1. Basic information analysis
    print(" Basic Information:")
    print(f"   Primary type: {eip712_data.get('primaryType', 'Unknown')}")
    print(f"   Domain name: {eip712_data.get('domain', {}).get('name', 'Unknown')}")
    print(f"   Version: {eip712_data.get('domain', {}).get('version', 'Unknown')}")
    print(f"   Chain ID: {eip712_data.get('domain', {}).get('chainId', 'Unknown')}")
    print(f"   Verifying contract: {eip712_data.get('domain', {}).get('verifyingContract', 'Unknown')}")
    
    # 2. Type structure analysis
    print("\n🏗️  Type Structure:")
    types = eip712_data.get('types', {})
    for type_name, type_fields in types.items():
        print(f"   {type_name}:")
        for field in type_fields:
            print(f"     - {field['name']}: {field['type']}")
    
    # 3. Message content analysis
    print("\n📦 Message Content:")
    message = eip712_data.get('message', {})
    for key, value in message.items():
        if isinstance(value, list):
            print(f"   {key}: [Array, length: {len(value)}]")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    print(f"     [{i}]:")
                    for k, v in item.items():
                        print(f"       {k}: {v}")
                else:
                    print(f"     [{i}]: {item}")
        elif isinstance(value, dict):
            print(f"   {key}: [Object]")
            for k, v in value.items():
                print(f"     {k}: {v}")
        else:
            print(f"   {key}: {value}")
    
    # 4. Parsing analysis
    print("\n Parsing Analysis:")
    try:
        parsed_message = parse_request(eip712_data)
        
        if parsed_message:
            print(f"   ✅ Parsing successful - Type: {parsed_message.kind}")
            
            if parsed_message.kind == "nft":
                analyze_nft_message(parsed_message.detail)
            elif parsed_message.kind == "permit":
                analyze_permit_message(parsed_message.detail)
                
            # 5. Security analysis
            print("\n  Security Analysis:")
            security_checker = SecurityChecker(price_threshold=0.1)
            security_result = security_checker.check_message_security(parsed_message)
            
            if security_result["is_safe"]:
                print("   ✅ No security risks found")
            else:
                print("   ⚠️  Potential risks found:")
                for warning in security_result.get("warnings", []):
                    print(f"     - {warning}")
                for error in security_result.get("errors", []):
                    print(f"     - Error: {error}")
            
            # Display detailed check results
            checks = security_result.get("checks", {})
            if "price" in checks:
                price_check = checks["price"]
                if "price_analysis" in price_check:
                    analysis = price_check["price_analysis"]
                    print(f"\n💰 Price Analysis:")
                    print(f"   NFT count: {analysis.get('nft_count', 0)}")
                    print(f"   Total price: {analysis.get('total_price_eth', 0):.6f} ETH")
                    print(f"   Total price (Wei): {analysis.get('total_price_wei', '0')}")
            
            if "balance" in checks:
                balance_check = checks["balance"]
                print(f"\n📊 Balance Change Analysis:")
                print(f"   Addresses involved: {balance_check.get('addresses', 0)}")
                print(f"   Total changes: {balance_check.get('total_changes', 0)}")
                
                for addr, details in balance_check.get("address_details", {}).items():
                    print(f"   Address {addr[:10]}...:")
                    print(f"     Change items: {details['change_count']}")
                    for key_id, amount in details["changes"].items():
                        print(f"     {key_id}: {amount}")
        else:
            print("   ❌ Unable to parse this signature format")
    
    except Exception as e:
        print(f"   ❌ Parsing error: {e}")


def analyze_nft_message(nft_message):
    """Analyze NFT message details"""
    print(f"   Protocol: {nft_message.type.value}")
    print(f"   Order type: {nft_message.order_type.value}")
    print(f"   Initiator: {nft_message.offerer}")
    print(f"   Start time: {nft_message.start_time}")
    print(f"   End time: {nft_message.end_time}")
    
    print(f"\n     Offer Items ({len(nft_message.offer)}):")
    for i, item in enumerate(nft_message.offer):
        if item.kind == "nft":
            detail = item.detail
            print(f"     [{i+1}] NFT: {detail.collection}")
            print(f"         Token ID: {detail.token_id}")
            print(f"         Amount: {detail.amount}")
            if detail.type:
                print(f"         Type: {detail.type}")
        elif item.kind == "token":
            detail = item.detail
            eth_amount = float(detail.amount) / (10**18) if detail.type == "native" else detail.amount
            print(f"     [{i+1}] Token: {detail.currency}")
            print(f"         Amount: {eth_amount if detail.type == 'native' else detail.amount}")
            if detail.type:
                print(f"         Type: {detail.type}")
    
    print(f"\n     Consideration Items ({len(nft_message.consideration)}):")
    for i, item in enumerate(nft_message.consideration):
        if item.kind == "nft":
            detail = item.detail
            print(f"     [{i+1}] NFT: {detail.collection}")
            print(f"         Token ID: {detail.token_id}")
            print(f"         Amount: {detail.amount}")
        elif item.kind == "token":
            detail = item.detail
            eth_amount = float(detail.amount) / (10**18) if detail.type == "native" else detail.amount
            print(f"     [{i+1}] Token: {detail.currency}")
            print(f"         Amount: {eth_amount if detail.type == 'native' else detail.amount}")


def analyze_permit_message(permit_message):
    """Analyze Permit message details"""
    print(f"   Authorization count: {len(permit_message.permits)}")
    
    for i, permit in enumerate(permit_message.permits):
        print(f"\n   📝 Authorization [{i+1}]:")
        print(f"     Authorized to: {permit.spender}")
        print(f"     Amount: {permit.amount}")
        print(f"     Nonce: {permit.nonce}")
        print(f"     Expiration: {permit.expiration}")
        if permit.owner:
            print(f"     Owner: {permit.owner}")
        if permit.token:
            print(f"     Token: {permit.token}")


def main():
    """Main function"""
    
    # Seaport listing example
    seaport_listing = {
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
                {"name": "zoneHash", "type": "bytes32"},
                {"name": "salt", "type": "uint256"},
                {"name": "conduitKey", "type": "bytes32"},
                {"name": "counter", "type": "uint256"}
            ],
            "OfferItem": [
                {"name": "itemType", "type": "uint8"},
                {"name": "token", "type": "address"},
                {"name": "identifierOrCriteria", "type": "uint256"},
                {"name": "startAmount", "type": "uint256"},
                {"name": "endAmount", "type": "uint256"}
            ],
            "ConsiderationItem": [
                {"name": "itemType", "type": "uint8"},
                {"name": "token", "type": "address"},
                {"name": "identifierOrCriteria", "type": "uint256"},
                {"name": "startAmount", "type": "uint256"},
                {"name": "endAmount", "type": "uint256"},
                {"name": "recipient", "type": "address"}
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
            "offer": [
                {
                    "itemType": "2",
                    "token": "0xB852c6b5892256C264Cc2C888eA462189154D8d7",
                    "identifierOrCriteria": "3377",
                    "startAmount": "1",
                    "endAmount": "1"
                }
            ],
            "consideration": [
                {
                    "itemType": "1",
                    "token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "identifierOrCriteria": "0",
                    "startAmount": "3700000000000000000",
                    "endAmount": "3700000000000000000",
                    "recipient": "0xcA1a218397f00ef0549e2555031a24B906200207"
                }
            ],
            "startTime": "1675151142",
            "endTime": "1676015142",
            "orderType": "2",
            "zone": "0x110b2B128A9eD1be5Ef3232D8e4E41640dF5c2Cd",
            "zoneHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "salt": "24446860302761739304752683030156737591518664810215442929818316022741225326226",
            "conduitKey": "0x0000007b02230091a7ed01230072f7006a004d60a8d4e71d599b8104250f0000",
            "counter": "0"
        }
    }
    
    # Permit example
    permit_example = {
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
            "chainId": "1",
            "verifyingContract": "0xA0b86a33E6441b8e4E0Af17E43Dd0b0D1B0E7a8E"
        },
        "message": {
            "owner": "0x1234567890123456789012345678901234567890",
            "spender": "0x0987654321098765432109876543210987654321",
            "value": "1000000000000000000000",
            "nonce": "0",
            "deadline": "1735689600"
        }
    }
    
    # Analyze examples
    analyze_eip712_signature(seaport_listing, "Seaport NFT Listing")
    analyze_eip712_signature(permit_example, "ERC20 Permit Authorization")
    
    print(f"\n{'='*60}")
    print("Analysis complete! 🎉")
    print(f"{'='*60}")


if __name__ == "__main__":
    main() 