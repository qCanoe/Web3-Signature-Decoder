#!/usr/bin/env python3
"""
EIP712 动态解析演示

演示如何使用动态解析器解析任意 EIP712 签名结构
无需预先定义特定协议，自动推断字段含义和类型
"""

import json
import sys
import os

# 添加父目录到路径以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_dynamic, parse_and_format, analyze_eip712
from test_data import TEST_DATA_SET


def demo_seaport_order():
    """演示解析 Seaport NFT 订单"""
    print("演示 1: Seaport NFT 订单动态解析")
    print("-" * 50)
    
    # 使用动态解析器解析并格式化
    result_text = parse_and_format(TEST_DATA_SET["seaport_order"])
    print(result_text)


def demo_permit_message():
    """演示解析 Permit 授权消息"""
    print("\n\n2: ERC20 Permit 授权动态解析")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["permit"])
    print(result_text)


def demo_dao_voting():
    """演示解析 DAO 投票消息"""
    print("\n\n3: DAO 治理投票动态解析")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["dao_voting"])
    print(result_text)


def demo_custom_struct():
    """演示解析自定义复杂结构"""
    print("\n\n 演示 4: 自定义复杂结构动态解析")
    print("-" * 50)
    
    result_text = parse_and_format(TEST_DATA_SET["custom_struct"])
    print(result_text)


def demo_analysis_api():
    """演示分析 API"""
    print("\n\n 演示 5: 结构化分析 API")
    print("-" * 50)
    
    # 使用分析 API
    analysis = analyze_eip712(TEST_DATA_SET["simple_permit"])
    
    print(" 结构化分析结果:")
    print(f" 主要类型: {analysis['message']['primary_type']}")
    print(f" 消息描述: {analysis['message']['description']}")
    print(f" 字段数量: {len(analysis['message']['fields'])}")
    
    print(f"\n字段详情:")
    for field in analysis['message']['fields']:
        semantic_info = f" ({field['semantic']})" if field['semantic'] else ""
        print(f"   • {field['name']}: {field['type']}{semantic_info}")
        print(f"     值: {field['value']}")
        print(f"     描述: {field['description']}")


def main():
    """主函数"""
    # 运行所有演示
    demo_seaport_order()
    demo_permit_message()
    demo_dao_voting()
    demo_custom_struct()
    demo_analysis_api()


if __name__ == "__main__":
    main() 