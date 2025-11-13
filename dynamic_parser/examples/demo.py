"""
动态解析器完整演示
展示所有功能和特性
"""

import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser
from test_data import ALL_TEST_DATA


def demo_parser():
    """完整演示动态解析器的功能"""
    
    
    parser = DynamicEIP712Parser()
    
    for name, data in ALL_TEST_DATA.items():
        print(f"\n📋 测试数据: {name.upper()}")
        print("=" * 80)
        
        try:
            # 解析数据
            result = parser.parse(data)
            formatted_result = parser.format_result(result)
            
            print(formatted_result)
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            continue



def main():
    """主函数"""
    demo_parser()


if __name__ == "__main__":
    main()