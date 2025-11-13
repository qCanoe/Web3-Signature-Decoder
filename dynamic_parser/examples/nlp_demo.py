"""
NLP自然语言生成器演示
展示如何直接使用NLP模型将结构化EIP712数据转换为自然语言输出
"""

import sys
import os
import json

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_natural_language_generator import create_nlp_generator, NaturalLanguageOutput


def print_natural_language_output(output: NaturalLanguageOutput):
    """打印自然语言输出结果"""
    print("=" * 80)
    print(f"📋 标题: {output.title}")
    print("=" * 80)
    
    print(f"\n📖 简要总结:")
    print(f"   {output.summary}")
    
    print(f"\n🔍 详细描述:")
    print(f"   {output.detailed_description}")
    
    print(f"\n📝 字段详情:")
    for field_desc in output.field_descriptions:
        print(f"   {field_desc}")
    
    print(f"\n🌍 执行环境:")
    print(f"   {output.context}")
    
    print(f"\n⚡ 操作总结:")
    print(f"   {output.action_summary}")
    
    print("\n" + "=" * 80)


def demo_erc20_permit():
    """演示ERC20授权许可的自然语言转换"""
    print("\n🚀 演示1: ERC20代币授权许可")
    
    # ERC20 Permit数据
    erc20_permit_data = {
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
    
    # 创建NLP生成器
    generator = create_nlp_generator()
    
    # 转换为自然语言
    result = generator.convert_to_natural_language(erc20_permit_data)
    
    # 输出结果
    print_natural_language_output(result)


def demo_seaport_order():
    """演示Seaport NFT订单的自然语言转换"""
    print("\n🚀 演示2: Seaport NFT市场订单")
    
    # Seaport Order数据（简化版）
    seaport_order_data = {
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
                {"name": "salt", "type": "uint256"}
            ]
        },
        "primaryType": "OrderComponents",
        "domain": {
            "name": "Seaport",
            "version": "1.4",
            "chainId": 1,
            "verifyingContract": "0x00000000006c3852cbEf3e08E8dF289169EdE581"
        },
        "message": {
            "offerer": "0x8ba1f109551bD432803012645Hac136c22C04e2D",
            "zone": "0x0000000000000000000000000000000000000000",
            "offer": [
                {
                    "itemType": 2,
                    "token": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                    "identifierOrCriteria": "8547",
                    "startAmount": "1",
                    "endAmount": "1"
                }
            ],
            "consideration": [
                {
                    "itemType": 0,
                    "token": "0x0000000000000000000000000000000000000000",
                    "identifierOrCriteria": "0",
                    "startAmount": "975000000000000000",
                    "endAmount": "975000000000000000",
                    "recipient": "0x8ba1f109551bD432803012645Hac136c22C04e2D"
                }
            ],
            "orderType": 0,
            "startTime": 1699143856,
            "endTime": 1700007856,
            "salt": 123456789
        }
    }
    
    # 创建NLP生成器
    generator = create_nlp_generator()
    
    # 转换为自然语言
    result = generator.convert_to_natural_language(seaport_order_data)
    
    # 输出结果
    print_natural_language_output(result)


def demo_with_template_generation():
    """演示使用模板的自然语言生成"""
    print("\n🚀 演示3: 使用模板进行自然语言生成")
    
    # 简单的投票数据
    vote_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "Vote": [
                {"name": "voter", "type": "address"},
                {"name": "proposal", "type": "uint256"},
                {"name": "support", "type": "uint8"}
            ]
        },
        "primaryType": "Vote",
        "domain": {
            "name": "GovernanceDAO",
            "version": "1",
            "chainId": 1
        },
        "message": {
            "voter": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "proposal": 15,
            "support": 1
        }
    }
    
    # 使用NLP模板生成
    try:
        generator = create_nlp_generator()
        result = generator.convert_to_natural_language(vote_data)
        print_natural_language_output(result)
    except Exception as e:
        print(f"NLP生成失败: {e}")


def demo_from_json_file():
    """从JSON文件加载数据进行演示"""
    print("\n🚀 演示4: 从JSON文件加载数据")
    
    # 尝试加载示例JSON文件
    json_files = [
        "sample_data/erc20_permit.json",
        "sample_data/seaport_order.json",
        "sample_data/dao_vote.json"
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    generator = create_nlp_generator()
    
    for json_file in json_files:
        file_path = os.path.join(base_path, json_file)
        if os.path.exists(file_path):
            print(f"\n📁 加载文件: {json_file}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result = generator.convert_to_natural_language(data)
                print_natural_language_output(result)
                
            except Exception as e:
                print(f"   ❌ 处理文件失败: {e}")
        else:
            print(f"   ⚠️ 文件不存在: {json_file}")


def compare_outputs():
    """比较不同输出格式"""
    print("\n🚀 演示5: 输出格式比较")
    
    # 使用简单的数据进行比较
    simple_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "Transfer": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        "primaryType": "Transfer",
        "domain": {
            "name": "MyToken",
            "chainId": 1
        },
        "message": {
            "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "to": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "amount": "5000000000000000000"
        }
    }
    
    generator = create_nlp_generator()
    result = generator.convert_to_natural_language(simple_data)
    
    print("🎯 自然语言格式输出:")
    print_natural_language_output(result)
    
    print("\n📊 结构化格式对比:")
    print("   传统格式：字段列表 + 技术描述")
    print("   NLP格式：流畅中文 + 上下文解释")
    print("   优势：更容易理解，适合普通用户")


def main():
    """主函数"""
    print("🔤 EIP712结构化数据NLP自然语言生成器演示")
    print("=" * 80)
    print("本演示展示如何直接使用NLP技术将复杂的EIP712结构化数据")
    print("转换为流畅的中文自然语言描述，无需依赖AI增强分析。")
    print("=" * 80)
    
    # 运行各种演示
    demo_erc20_permit()
    demo_seaport_order()
    demo_with_template_generation()
    demo_from_json_file()
    compare_outputs()
    
    print("\n✅ 演示完成！")
    print("\n💡 使用说明:")
    print("   1. 导入 nlp_natural_language_generator 模块")
    print("   2. 创建生成器: generator = create_nlp_generator()")
    print("   3. 转换数据: result = generator.convert_to_natural_language(data)")
    print("   4. 获取自然语言输出: result.summary, result.detailed_description等")


if __name__ == "__main__":
    main() 