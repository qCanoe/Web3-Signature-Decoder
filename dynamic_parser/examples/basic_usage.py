"""
动态解析器基本使用示例
"""

import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser, parse_and_format, analyze_eip712
from test_data import ERC20_PERMIT, SEAPORT_ORDER


def main():
    """基本使用示例"""
    
    print("=" * 60)
    print("动态 EIP712 解析器 - 基本使用示例")
    print("=" * 60)
    
    # 创建解析器实例
    parser = DynamicEIP712Parser()
    
    # 示例 1: 解析 ERC20 Permit
    print("\n示例 1: ERC20 Permit 授权")
    print("-" * 30)
    
    try:
        result = parser.parse_and_format(ERC20_PERMIT)
        print(result)
    except Exception as e:
        print(f"解析失败: {e}")
    
    # 示例 2: 解析 Seaport 订单
    print("\n示例 2: Seaport NFT 订单")
    print("-" * 30)
    
    try:
        result = parser.parse_and_format(SEAPORT_ORDER)
        print(result)
    except Exception as e:
        print(f"解析失败: {e}")
    
    # 示例 3: 使用便捷函数
    print("\n示例 3: 使用便捷函数")
    print("-" * 30)
    
    try:
        # 直接格式化输出
        result = parse_and_format(ERC20_PERMIT)
        print("便捷函数解析结果:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        # 获取结构化分析
        analysis = analyze_eip712(ERC20_PERMIT)
        print(f"\n结构化分析 - 字段数量: {analysis['field_count']}")
        print(f"主要类型: {analysis['primary_type']}")
        
    except Exception as e:
        print(f"便捷函数使用失败: {e}")


if __name__ == "__main__":
    main() 