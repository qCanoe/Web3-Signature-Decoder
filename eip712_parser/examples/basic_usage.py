#!/usr/bin/env python3
"""
EIP712 Parser Basic Usage Example
"""

import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_request
from eip712_parser.security import SecurityChecker

# Seaport listing example data
seaport_listing_example = {
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


def main():
    """Main function"""
    print("=== EIP712 Parser Example ===\n")
    
    # Parse EIP712 message
    print("1. Parsing Seaport listing message...")
    try:
        parsed_message = parse_request(seaport_listing_example)
        
        if parsed_message:
            print(f"✅ Parsing successful!")
            print(f"   Message type: {parsed_message.kind}")
            
            if parsed_message.kind == "nft":
                nft_detail = parsed_message.detail
                print(f"   Protocol type: {nft_detail.type}")
                print(f"   Order type: {nft_detail.order_type}")
                print(f"   Initiator: {nft_detail.offerer}")
                print(f"   Offer items count: {len(nft_detail.offer)}")
                print(f"   Consideration items count: {len(nft_detail.consideration)}")
                
                # Display offered NFTs
                for i, item in enumerate(nft_detail.offer):
                    if item.kind == "nft":
                        print(f"   NFT {i+1}: {item.detail.collection} #{item.detail.token_id}")
                
                # Display expected tokens
                for i, item in enumerate(nft_detail.consideration):
                    if item.kind == "token":
                        eth_amount = float(item.detail.amount) / (10**18)
                        print(f"   Token {i+1}: {eth_amount:.4f} ETH")
            
            print()
            
            # Security check
            print("2. Performing security check...")
            security_checker = SecurityChecker(price_threshold=1.0)  # 1 ETH threshold
            security_result = security_checker.check_message_security(parsed_message)
            
            if security_result["is_safe"]:
                print("✅ Security check passed")
            else:
                print("⚠️  Security risks found:")
                for warning in security_result["warnings"]:
                    print(f"   - {warning}")
                for error in security_result["errors"]:
                    print(f"   - Error: {error}")
            
            # Display price analysis
            if "price" in security_result["checks"]:
                price_analysis = security_result["checks"]["price"].get("price_analysis", {})
                if price_analysis:
                    print(f"\n3. Price Analysis:")
                    print(f"   NFT count: {price_analysis.get('nft_count', 0)}")
                    print(f"   Total price: {price_analysis.get('total_price_eth', 0):.4f} ETH")
            
        else:
            print("❌ Unable to parse this message")
            
    except Exception as e:
        print(f"❌ Error occurred during parsing: {e}")


if __name__ == "__main__":
    main() 