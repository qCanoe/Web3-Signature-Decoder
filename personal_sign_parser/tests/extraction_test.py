#!/usr/bin/env python3
"""
参数提取方法测试
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser.parameter_extractor import ParameterExtractor


def test_extraction_methods():
    """测试不同的参数提取方法"""
    extractor = ParameterExtractor()
    
    # 测试消息
    messages = [
        "Sign in to example.com\nNonce: abc123",
        '{"domain":"app.com","nonce":"xyz789"}', 
        "domain=site.com&nonce=token123",
        "Visit https://myapp.com and use nonce abc123"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"📝 测试 {i}: {message[:40]}...")
        
        # 详细提取过程
        cleaned = extractor._clean_message(message)
        print(f"  清理后: {cleaned}")
        
        # JSON 解析
        json_data = extractor._try_parse_json(cleaned)
        if json_data:
            print(f"  JSON解析: {json_data}")
        
        # 查询字符串解析
        query_data = extractor._try_parse_query_string(cleaned)
        if query_data:
            print(f"  查询字符串: {query_data}")
        
        # 最终提取结果
        params = extractor.extract(message)
        print(f"  最终结果:")
        print(f"    域名: {params.domain}")
        print(f"    随机数: {params.nonce}")
        print(f"    自定义字段: {params.custom_fields}")
        print()


if __name__ == "__main__":
    test_extraction_methods() 