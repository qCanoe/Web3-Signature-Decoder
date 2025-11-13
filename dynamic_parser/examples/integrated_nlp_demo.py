"""
集成NLP功能演示
展示如何在核心EIP712解析器中使用NLP自然语言生成功能
"""

import sys
import os
import json

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import DynamicEIP712Parser


def demo_integrated_nlp():
    """演示集成的NLP功能"""
    print("🔗 集成NLP功能演示")
    print("=" * 60)
    
    # 创建带有NLP功能的解析器
    parser = DynamicEIP712Parser(enable_nlp=True)
    
    # 示例EIP712数据
    permit_data = {
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
            "name": "USDC",
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
    
    print("\n1️⃣ 仅使用自然语言生成:")
    try:
        nl_result = parser.generate_natural_language(permit_data)
        print(f"   📋 标题: {nl_result.title}")
        print(f"   📖 摘要: {nl_result.summary}")
        print(f"   ⚡ 操作: {nl_result.action_summary}")
        print(f"   🌍 环境: {nl_result.context}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("\n2️⃣ 完整分析（传统+自然语言）:")
    try:
        full_result = parser.analyze_with_natural_language(permit_data)
        
        print(f"   🔍 传统分析字段数: {full_result['traditional_analysis']['field_count']}")
        print(f"   🤖 自然语言可用: {full_result['has_natural_language']}")
        
        if full_result['natural_language']:
            nl = full_result['natural_language']
            print(f"   📝 自然语言标题: {nl['title']}")
            print(f"   📖 自然语言摘要: {nl['summary']}")
            
    except Exception as e:
        print(f"   ❌ 失败: {e}")


def demo_without_nlp():
    """演示未启用NLP功能时的行为"""
    print("\n🚫 未启用NLP功能演示")
    print("=" * 60)
    
    # 创建不带NLP功能的解析器
    parser = DynamicEIP712Parser(enable_nlp=False)
    
    permit_data = {
        "types": {"Permit": [{"name": "owner", "type": "address"}]},
        "primaryType": "Permit",
        "domain": {"name": "Test"},
        "message": {"owner": "0x123..."}
    }
    
    print("\n尝试生成自然语言描述:")
    try:
        nl_result = parser.generate_natural_language(permit_data)
        print(f"   ✅ 成功: {nl_result.title}")
    except ValueError as e:
        print(f"   ⚠️ 预期错误: {e}")
    except Exception as e:
        print(f"   ❌ 意外错误: {e}")


def demo_with_json_files():
    """从JSON文件演示"""
    print("\n📁 JSON文件演示")
    print("=" * 60)
    
    parser = DynamicEIP712Parser(enable_nlp=True)
    
    # 尝试加载JSON文件
    json_files = [
        "sample_data/erc20_permit.json",
        "sample_data/dao_vote.json"
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    for json_file in json_files:
        file_path = os.path.join(base_path, json_file)
        print(f"\n📄 处理文件: {json_file}")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result = parser.analyze_with_natural_language(data)
                
                if result['has_natural_language']:
                    nl = result['natural_language']
                    print(f"   📋 {nl['title']}")
                    print(f"   📖 {nl['summary']}")
                else:
                    print("   ⚠️ 自然语言生成不可用")
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
        else:
            print(f"   ⚠️ 文件不存在")


def compare_traditional_vs_nlp():
    """比较传统分析和NLP输出的差异"""
    print("\n⚖️ 传统分析 vs NLP输出对比")
    print("=" * 60)
    
    # 创建两个解析器进行对比
    traditional_parser = DynamicEIP712Parser(enable_nlp=False)
    nlp_parser = DynamicEIP712Parser(enable_nlp=True)
    
    sample_data = {
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}],
            "Order": [
                {"name": "maker", "type": "address"},
                {"name": "taker", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        "primaryType": "Order",
        "domain": {"name": "DEX"},
        "message": {
            "maker": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "taker": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "amount": "1000000000000000000"
        }
    }
    
    print("\n📊 传统分析结果:")
    try:
        traditional_result = traditional_parser.analyze_eip712(sample_data)
        print(f"   主类型: {traditional_result['primary_type']}")
        print(f"   字段数: {traditional_result['field_count']}")
        print(f"   描述: {traditional_result['message_description']}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print("\n🔤 NLP分析结果:")
    try:
        nlp_result = nlp_parser.generate_natural_language(sample_data)
        print(f"   标题: {nlp_result.title}")
        print(f"   摘要: {nlp_result.summary}")
        print(f"   操作: {nlp_result.action_summary}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")


def main():
    """主函数"""
    print("🚀 EIP712解析器集成NLP功能演示")
    print("这个演示展示如何在现有的EIP712解析器中集成NLP自然语言生成功能")
    print("=" * 80)
    
    # 运行各种演示
    demo_integrated_nlp()
    demo_without_nlp()
    demo_with_json_files()
    compare_traditional_vs_nlp()
    
    print("\n✅ 演示完成！")
    print("\n💡 集成使用说明:")
    print("   1. 创建解析器: parser = DynamicEIP712Parser(enable_nlp=True)")
    print("   2. 生成自然语言: nl_result = parser.generate_natural_language(data)")
    print("   3. 完整分析: full_result = parser.analyze_with_natural_language(data)")
    print("   4. 传统分析: traditional_result = parser.analyze_eip712(data)")


if __name__ == "__main__":
    main() 