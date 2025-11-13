"""
PersonalSign 解析器测试
"""

import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser import PersonalSignParser, PersonalSignTemplateType
from personal_sign_parser.tests.test_data import get_test_data


def test_login_messages():
    """测试登录消息解析"""
    parser = PersonalSignParser()
    test_data = get_test_data("login")
    
    print("🧪 测试登录消息解析...")
    
    for i, item in enumerate(test_data["login"]):
        message = item["message"]
        expected_template = item["expected_template"]
        expected_params = item["expected_params"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"消息: {message[:50]}...")
        
        # 解析消息
        result = parser.parse(message)
        
        # 检查模板类型
        detected_template = result.template_info.template_type.value
        print(f"期望模板: {expected_template}")
        print(f"检测模板: {detected_template}")
        print(f"置信度: {result.template_info.confidence:.1%}")
        
        # 检查参数提取
        print("提取的参数:")
        for key, expected_value in expected_params.items():
            actual_value = getattr(result.extracted_parameters, key, None)
            print(f"  {key}: {actual_value} (期望: {expected_value})")
        
        # 安全分析
        print(f"风险级别: {result.risk_level}")
        if result.security_warnings:
            print(f"安全警告: {result.security_warnings}")
        
        print("✅ 测试通过" if detected_template == expected_template else "❌ 测试失败")


def test_binding_messages():
    """测试绑定消息解析"""
    parser = PersonalSignParser()
    test_data = get_test_data("binding")
    
    print("\n🧪 测试绑定消息解析...")
    
    for i, item in enumerate(test_data["binding"]):
        message = item["message"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"消息: {message[:50]}...")
        
        result = parser.parse(message)
        detected_template = result.template_info.template_type.value
        
        print(f"期望模板: {expected_template}")
        print(f"检测模板: {detected_template}")
        print(f"置信度: {result.template_info.confidence:.1%}")
        
        # 检查绑定相关参数
        if result.extracted_parameters.binding_target:
            print(f"绑定目标: {result.extracted_parameters.binding_target}")
        if result.extracted_parameters.binding_type:
            print(f"绑定类型: {result.extracted_parameters.binding_type}")
        if result.extracted_parameters.verification_code:
            print(f"验证码: {result.extracted_parameters.verification_code}")
        
        print("✅ 测试通过" if detected_template == expected_template else "❌ 测试失败")


def test_authorization_messages():
    """测试授权消息解析"""
    parser = PersonalSignParser()
    test_data = get_test_data("authorization")
    
    print("\n🧪 测试授权消息解析...")
    
    for i, item in enumerate(test_data["authorization"]):
        message = item["message"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"消息: {message[:50]}...")
        
        result = parser.parse(message)
        detected_template = result.template_info.template_type.value
        
        print(f"期望模板: {expected_template}")
        print(f"检测模板: {detected_template}")
        print(f"置信度: {result.template_info.confidence:.1%}")
        print(f"安全级别: {result.template_info.security_level}")
        
        # 检查授权相关参数
        if result.extracted_parameters.permissions:
            print(f"权限: {result.extracted_parameters.permissions}")
        if result.extracted_parameters.resource:
            print(f"资源: {result.extracted_parameters.resource}")
        if result.extracted_parameters.action:
            print(f"操作: {result.extracted_parameters.action}")
        
        print("✅ 测试通过" if detected_template == expected_template else "❌ 测试失败")


def test_high_risk_messages():
    """测试高风险消息检测"""
    parser = PersonalSignParser()
    test_data = get_test_data("high_risk")
    
    print("\n🧪 测试高风险消息检测...")
    
    for i, item in enumerate(test_data["high_risk"]):
        message = item["message"]
        expected_risk = item["risk_level"]
        should_have_warnings = item["should_have_warnings"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"消息: {message[:50]}...")
        
        result = parser.parse(message)
        
        print(f"期望风险级别: {expected_risk}")
        print(f"检测风险级别: {result.risk_level}")
        print(f"安全警告: {result.security_warnings}")
        
        risk_correct = result.risk_level == expected_risk
        warnings_correct = bool(result.security_warnings) == should_have_warnings
        
        print("✅ 风险级别正确" if risk_correct else "❌ 风险级别错误")
        print("✅ 警告检测正确" if warnings_correct else "❌ 警告检测错误")


def test_hex_messages():
    """测试 Hex 编码消息解析"""
    parser = PersonalSignParser()
    test_data = get_test_data("hex_encoded")
    
    print("\n🧪 测试 Hex 编码消息解析...")
    
    for i, item in enumerate(test_data["hex_encoded"]):
        message = item["message"]
        expected_decoded = item["expected_decoded"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"Hex 消息: {message}")
        print(f"期望解码: {expected_decoded}")
        
        result = parser.parse(message)
        
        print(f"检测为 Hex: {result.is_hex}")
        print(f"模板类型: {result.template_info.template_type.value}")
        print(f"消息长度: {result.message_length}")
        
        print("✅ 测试通过")


def test_multilingual_messages():
    """测试多语言消息解析"""
    parser = PersonalSignParser()
    test_data = get_test_data("multilingual")
    
    print("\n🧪 测试多语言消息解析...")
    
    for i, item in enumerate(test_data["multilingual"]):
        message = item["message"]
        expected_language = item["language"]
        expected_template = item["expected_template"]
        
        print(f"\n📝 测试用例 {i+1}:")
        print(f"消息: {message}")
        print(f"期望语言: {expected_language}")
        
        result = parser.parse(message)
        
        print(f"检测语言: {result.language}")
        print(f"模板类型: {result.template_info.template_type.value}")
        
        language_correct = result.language == expected_language
        template_correct = result.template_info.template_type.value == expected_template
        
        print("✅ 语言检测正确" if language_correct else "❌ 语言检测错误")
        print("✅ 模板检测正确" if template_correct else "❌ 模板检测错误")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 PersonalSign 解析器测试...\n")
    
    try:
        test_login_messages()
        test_binding_messages()
        test_authorization_messages()
        test_high_risk_messages()
        test_hex_messages()
        test_multilingual_messages()
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests() 