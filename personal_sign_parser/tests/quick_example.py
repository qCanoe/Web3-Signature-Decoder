#!/usr/bin/env python3
"""
PersonalSign Parser Quick Usage Example
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser import PersonalSignParser


def quick_example():
    """Quick usage example"""
    print("🚀 PersonalSign Parser Quick Example\n")
    
    # Create parser
    parser = PersonalSignParser()
    
    # Example 1: Login message
    print("📝 Example 1: Login Message")
    login_message = """Sign in to example.com
Nonce: abc123
Timestamp: 1640995200"""
    
    result = parser.parse(login_message)
    print(f"✅ Template type: {result.template_info.template_type.value}")
    print(f"✅ Confidence: {result.template_info.confidence:.1%}")
    print(f"✅ Domain: {result.extracted_parameters.domain}")
    print(f"✅ Nonce: {result.extracted_parameters.nonce}")
    print(f"✅ Risk level: {result.risk_level}")
    
    # Example 2: JSON format binding message
    print("\n📝 Example 2: JSON Format Binding Message")
    binding_message = '{"type":"bind","email":"user@example.com","code":"123456"}'
    
    result = parser.parse(binding_message)
    print(f"✅ Template type: {result.template_info.template_type.value}")
    print(f"✅ Binding target: {result.extracted_parameters.binding_target}")
    print(f"✅ Verification code: {result.extracted_parameters.verification_code}")
    
    # Example 3: High-risk authorization message
    print("\n📝 Example 3: High-Risk Authorization Message")
    auth_message = """Authorize unlimited spending of your tokens
Amount: unlimited  
Spender: 0x1234567890123456789012345678901234567890"""
    
    result = parser.parse(auth_message)
    print(f"⚠️ Template type: {result.template_info.template_type.value}")
    print(f"⚠️ Risk level: {result.risk_level}")
    print(f"⚠️ Security warnings: {result.security_warnings}")
    
    # Example 4: Hex-encoded message
    print("\n📝 Example 4: Hex-Encoded Message")
    hex_message = "0x48656c6c6f20576f726c6421"  # "Hello World!"
    
    result = parser.parse(hex_message)
    print(f"✅ Is Hex: {result.is_hex}")
    print(f"✅ Template type: {result.template_info.template_type.value}")
    


if __name__ == "__main__":
    quick_example() 