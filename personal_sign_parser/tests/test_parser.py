"""
PersonalSign Parser Tests
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser import PersonalSignParser, PersonalSignTemplateType
from personal_sign_parser.tests.test_data import get_test_data


def test_login_messages():
    """Test login message parsing"""
    parser = PersonalSignParser()
    test_data = get_test_data("login")
    
    print("🧪 Testing login message parsing...")
    
    for i, item in enumerate(test_data["login"]):
        message = item["message"]
        expected_template = item["expected_template"]
        expected_params = item["expected_params"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Message: {message[:50]}...")
        
        # Parse message
        result = parser.parse(message)
        
        # Check template type
        detected_template = result.template_info.template_type.value
        print(f"Expected template: {expected_template}")
        print(f"Detected template: {detected_template}")
        print(f"Confidence: {result.template_info.confidence:.1%}")
        
        # Check parameter extraction
        print("Extracted parameters:")
        for key, expected_value in expected_params.items():
            actual_value = getattr(result.extracted_parameters, key, None)
            print(f"  {key}: {actual_value} (expected: {expected_value})")
        
        # Security analysis
        print(f"Risk level: {result.risk_level}")
        if result.security_warnings:
            print(f"Security warnings: {result.security_warnings}")
        
        print("✅ Test passed" if detected_template == expected_template else "❌ Test failed")


def test_binding_messages():
    """Test binding message parsing"""
    parser = PersonalSignParser()
    test_data = get_test_data("binding")
    
    print("\n🧪 Testing binding message parsing...")
    
    for i, item in enumerate(test_data["binding"]):
        message = item["message"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Message: {message[:50]}...")
        
        result = parser.parse(message)
        detected_template = result.template_info.template_type.value
        
        print(f"Expected template: {expected_template}")
        print(f"Detected template: {detected_template}")
        print(f"Confidence: {result.template_info.confidence:.1%}")
        
        # Check binding-related parameters
        if result.extracted_parameters.binding_target:
            print(f"Binding target: {result.extracted_parameters.binding_target}")
        if result.extracted_parameters.binding_type:
            print(f"Binding type: {result.extracted_parameters.binding_type}")
        if result.extracted_parameters.verification_code:
            print(f"Verification code: {result.extracted_parameters.verification_code}")
        
        print("✅ Test passed" if detected_template == expected_template else "❌ Test failed")


def test_authorization_messages():
    """Test authorization message parsing"""
    parser = PersonalSignParser()
    test_data = get_test_data("authorization")
    
    print("\n🧪 Testing authorization message parsing...")
    
    for i, item in enumerate(test_data["authorization"]):
        message = item["message"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Message: {message[:50]}...")
        
        result = parser.parse(message)
        detected_template = result.template_info.template_type.value
        
        print(f"Expected template: {expected_template}")
        print(f"Detected template: {detected_template}")
        print(f"Confidence: {result.template_info.confidence:.1%}")
        print(f"Security level: {result.template_info.security_level}")
        
        # Check authorization-related parameters
        if result.extracted_parameters.permissions:
            print(f"Permissions: {result.extracted_parameters.permissions}")
        if result.extracted_parameters.resource:
            print(f"Resource: {result.extracted_parameters.resource}")
        if result.extracted_parameters.action:
            print(f"Action: {result.extracted_parameters.action}")
        
        print("✅ Test passed" if detected_template == expected_template else "❌ Test failed")


def test_high_risk_messages():
    """Test high-risk message detection"""
    parser = PersonalSignParser()
    test_data = get_test_data("high_risk")
    
    print("\n🧪 Testing high-risk message detection...")
    
    for i, item in enumerate(test_data["high_risk"]):
        message = item["message"]
        expected_risk = item["risk_level"]
        should_have_warnings = item["should_have_warnings"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Message: {message[:50]}...")
        
        result = parser.parse(message)
        
        print(f"Expected risk level: {expected_risk}")
        print(f"Detected risk level: {result.risk_level}")
        print(f"Security warnings: {result.security_warnings}")
        
        risk_correct = result.risk_level == expected_risk
        warnings_correct = bool(result.security_warnings) == should_have_warnings
        
        print("✅ Risk level correct" if risk_correct else "❌ Risk level incorrect")
        print("✅ Warning detection correct" if warnings_correct else "❌ Warning detection incorrect")


def test_hex_messages():
    """Test Hex-encoded message parsing"""
    parser = PersonalSignParser()
    test_data = get_test_data("hex_encoded")
    
    print("\n🧪 Testing Hex-encoded message parsing...")
    
    for i, item in enumerate(test_data["hex_encoded"]):
        message = item["message"]
        expected_decoded = item["expected_decoded"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Hex message: {message}")
        print(f"Expected decoded: {expected_decoded}")
        
        result = parser.parse(message)
        
        print(f"Detected as Hex: {result.is_hex}")
        print(f"Template type: {result.template_info.template_type.value}")
        print(f"Message length: {result.message_length}")
        
        print("✅ Test passed")


def test_multilingual_messages():
    """Test multilingual message parsing"""
    parser = PersonalSignParser()
    test_data = get_test_data("multilingual")
    
    print("\n🧪 Testing multilingual message parsing...")
    
    for i, item in enumerate(test_data["multilingual"]):
        message = item["message"]
        expected_language = item["language"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 Test case {i+1}:")
        print(f"Message: {message}")
        print(f"Expected language: {expected_language}")
        
        result = parser.parse(message)
        
        print(f"Detected language: {result.language}")
        print(f"Template type: {result.template_info.template_type.value}")
        
        language_correct = result.language == expected_language
        template_correct = result.template_info.template_type.value == expected_template
        
        print("✅ Language detection correct" if language_correct else "❌ Language detection incorrect")
        print("✅ Template detection correct" if template_correct else "❌ Template detection incorrect")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting PersonalSign parser tests...\n")
    
    try:
        test_login_messages()
        test_binding_messages()
        test_authorization_messages()
        test_high_risk_messages()
        test_hex_messages()
        test_multilingual_messages()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error occurred during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests() 