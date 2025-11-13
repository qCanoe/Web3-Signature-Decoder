"""
JSON文件测试器
支持读取外部JSON文件中的EIP712数据并进行解析
"""

import sys
import os
import json
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser, parse_and_format, analyze_eip712


class JsonFileTester:
    """JSON文件测试器"""
    
    def __init__(self):
        self.parser = DynamicEIP712Parser()
    
    def read_json_file(self, file_path: str) -> dict:
        """
        读取JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的字典数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"❌ 文件未找到: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {e}")
            return None
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None
    
    def validate_eip712_data(self, data: dict) -> bool:
        """
        验证是否为有效的EIP712数据
        
        Args:
            data: 待验证的数据
            
        Returns:
            是否为有效的EIP712数据
        """
        required_fields = ['types', 'domain', 'primaryType', 'message']
        
        if not isinstance(data, dict):
            print("❌ 数据格式错误: 不是有效的字典格式")
            return False
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"❌ 缺少必要字段: {', '.join(missing_fields)}")
            return False
        
        if 'EIP712Domain' not in data['types']:
            print("❌ 缺少EIP712Domain类型定义")
            return False
        
        if data['primaryType'] not in data['types']:
            print(f"❌ 主要类型 '{data['primaryType']}' 未在types中定义")
            return False
        
        return True
    
    def test_single_file(self, file_path: str, output_format: str = 'formatted') -> bool:
        """
        测试单个JSON文件
        
        Args:
            file_path: JSON文件路径
            output_format: 输出格式 ('formatted', 'structured', 'both')
            
        Returns:
            是否测试成功
        """
        print(f"\n📋 测试文件: {file_path}")
        print("=" * 60)
        
        # 读取文件
        data = self.read_json_file(file_path)
        if data is None:
            return False
        
        # 验证数据格式
        if not self.validate_eip712_data(data):
            return False
        
        try:
            # 解析数据
            if output_format in ['formatted', 'both']:
                print("\n📝 格式化输出:")
                result = parse_and_format(data)
                print(result)
            
            if output_format in ['structured', 'both']:
                print("\n📊 结构化分析:")
                analysis = analyze_eip712(data)
                self._print_structured_analysis(analysis)
            
            print("\n✅ 测试成功!")
            return True
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return False
    
    def test_directory(self, directory_path: str, output_format: str = 'formatted') -> dict:
        """
        测试目录下的所有JSON文件
        
        Args:
            directory_path: 目录路径
            output_format: 输出格式
            
        Returns:
            测试结果统计
        """
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ 目录不存在: {directory_path}")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        json_files = list(directory.glob('*.json'))
        if not json_files:
            print(f"❌ 目录中没有找到JSON文件: {directory_path}")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        print(f"\n🚀 批量测试目录: {directory_path}")
        print(f"📁 找到 {len(json_files)} 个JSON文件")
        print("=" * 80)
        
        success_count = 0
        failed_count = 0
        
        for json_file in json_files:
            success = self.test_single_file(str(json_file), output_format)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        # 输出统计结果
        total = len(json_files)
        print(f"\n📈 测试统计:")
        print(f"   • 总文件数: {total}")
        print(f"   • 成功: {success_count} ({success_count/total:.1%})")
        print(f"   • 失败: {failed_count} ({failed_count/total:.1%})")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': total
        }
    
    def _print_structured_analysis(self, analysis: dict):
        """打印结构化分析结果"""
        print(f"   主要类型: {analysis['primary_type']}")
        print(f"   结构描述: {analysis['message_description']}")
        print(f"   字段数量: {analysis['field_count']}")
        
        print(f"\n   字段详情:")
        for field in analysis['fields']:
            confidence_str = f"{field['confidence']:.0%}" if field['confidence'] > 0 else "N/A"
            semantic_str = field['semantic'] or "未识别"
            print(f"     • {field['name']}: {semantic_str} ({confidence_str})")
    
    def create_sample_files(self, output_dir: str = "sample_data"):
        """
        创建示例JSON文件用于测试
        
        Args:
            output_dir: 输出目录
        """
        from test_data import ALL_TEST_DATA
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📁 创建示例JSON文件到目录: {output_dir}")
        
        created_files = []
        for name, data in ALL_TEST_DATA.items():
            file_path = output_path / f"{name}.json"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                created_files.append(file_path)
                print(f"   ✅ 创建: {file_path}")
            except Exception as e:
                print(f"   ❌ 创建失败 {file_path}: {e}")
        
        print(f"\n🎉 成功创建 {len(created_files)} 个示例文件!")
        return created_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='EIP712 JSON文件测试器')
    parser.add_argument('path', nargs='?', help='JSON文件或目录路径')
    parser.add_argument('--format', '-f', choices=['formatted', 'structured', 'both'], 
                       default='formatted', help='输出格式')
    parser.add_argument('--create-samples', '-c', action='store_true', 
                       help='创建示例JSON文件')
    parser.add_argument('--sample-dir', '-d', default='sample_data', 
                       help='示例文件输出目录')
    
    args = parser.parse_args()
    
    tester = JsonFileTester()
    
    # 创建示例文件
    if args.create_samples:
        tester.create_sample_files(args.sample_dir)
        if not args.path:
            args.path = args.sample_dir
    
    # 如果没有指定路径，显示帮助
    if not args.path:
        parser.print_help()
        print(f"\n💡 提示:")
        print(f"   • 测试单个文件: python json_file_tester.py sample.json")
        print(f"   • 测试整个目录: python json_file_tester.py ./sample_data/")
        print(f"   • 创建示例文件: python json_file_tester.py --create-samples")
        return
    
    # 判断是文件还是目录
    path = Path(args.path)
    
    if path.is_file():
        # 测试单个文件
        tester.test_single_file(str(path), args.format)
    elif path.is_dir():
        # 测试目录
        tester.test_directory(str(path), args.format)
    else:
        print(f"❌ 路径不存在: {args.path}")


if __name__ == "__main__":
    main() 