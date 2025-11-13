#!/usr/bin/env python3
"""
测试 JSON 文件解析
测试动态解析器对外部 JSON 文件的解析能力
"""

import json
import sys
import os

# 添加父目录到路径以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import parse_and_format, parse_dynamic, analyze_eip712


def test_json_file():
    
    # 读取 JSON 文件
    json_file_path = os.path.join(os.path.dirname(__file__), "test_data.json")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            eip712_data = json.load(f)
        
        print("JSON 文件读取成功")
        print(f"文件路径: {json_file_path}")
        print(f"主要类型: {eip712_data['primaryType']}")
        print(f"域名称: {eip712_data['domain']['name']}")
        print()
        
        # 使用动态解析器解析
        result_text = parse_and_format(eip712_data)
        print(result_text)
        
        # 使用分析 API  
        print("\n结构化分析:")
        print("-" * 40)
        analysis = analyze_eip712(eip712_data)
        
        print(f"主要类型: {analysis['message']['primary_type']}")
        print(f"消息描述: {analysis['message']['description']}")
        print(f"字段数量: {len(analysis['message']['fields'])}")
        
        print(f"\n字段详情:")
        for field in analysis['message']['fields']:
            semantic_info = f" ({field['semantic']})" if field['semantic'] else ""
            print(f"   • {field['name']}: {field['type']}{semantic_info}")
            print(f"     值: {field['value']}")
            print(f"     描述: {field['description']}")
        
        # 检查特殊字段处理
        print("\n字段识别测试:")
        print("-" * 40)
        
        result = parse_dynamic(eip712_data)
        for field in result.message.fields:
            if field.name == "minter":
                print(f"'minter' 字段被正确识别为: {field.semantic}")
            elif field.name == "tokenId":
                print(f"'tokenId' 字段被正确识别为: {field.semantic}")
            elif field.name == "price":
                print(f"'price' 字段被正确识别为: {field.semantic}")
        
    except FileNotFoundError:
        print(f"文件未找到: {json_file_path}")
        print("请确保 test_data.json 文件存在于 examples 目录中")
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
    except Exception as e:
        print(f"解析错误: {e}")


def main():
    """主函数"""
    test_json_file()


if __name__ == "__main__":
    main() 