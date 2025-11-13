#!/usr/bin/env python3
"""
PersonalSign 解析器快速使用示例
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser import PersonalSignParser


def quick_example():
    """快速使用示例"""
    print("🚀 PersonalSign 解析器快速示例\n")
    
    # 创建解析器
    parser = PersonalSignParser()
    
    # 示例1: 登录消息
    print("📝 示例1: 登录消息")
    login_message = """Sign in to example.com
Nonce: abc123
Timestamp: 1640995200"""
    
    result = parser.parse(login_message)
    print(f"✅ 模板类型: {result.template_info.template_type.value}")
    print(f"✅ 置信度: {result.template_info.confidence:.1%}")
    print(f"✅ 域名: {result.extracted_parameters.domain}")
    print(f"✅ 随机数: {result.extracted_parameters.nonce}")
    print(f"✅ 风险级别: {result.risk_level}")
    
    # 示例2: JSON格式绑定消息
    print("\n📝 示例2: JSON格式绑定消息")
    binding_message = '{"type":"bind","email":"user@example.com","code":"123456"}'
    
    result = parser.parse(binding_message)
    print(f"✅ 模板类型: {result.template_info.template_type.value}")
    print(f"✅ 绑定目标: {result.extracted_parameters.binding_target}")
    print(f"✅ 验证码: {result.extracted_parameters.verification_code}")
    
    # 示例3: 高风险授权消息
    print("\n📝 示例3: 高风险授权消息")
    auth_message = """Authorize unlimited spending of your tokens
Amount: unlimited  
Spender: 0x1234567890123456789012345678901234567890"""
    
    result = parser.parse(auth_message)
    print(f"⚠️ 模板类型: {result.template_info.template_type.value}")
    print(f"⚠️ 风险级别: {result.risk_level}")
    print(f"⚠️ 安全警告: {result.security_warnings}")
    
    # 示例4: Hex编码消息
    print("\n📝 示例4: Hex编码消息")
    hex_message = "0x48656c6c6f20576f726c6421"  # "Hello World!"
    
    result = parser.parse(hex_message)
    print(f"✅ 是否为Hex: {result.is_hex}")
    print(f"✅ 模板类型: {result.template_info.template_type.value}")
    


if __name__ == "__main__":
    quick_example() 