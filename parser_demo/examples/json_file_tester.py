"""
JSON File Tester
Supports reading EIP712 data from external JSON files and parsing them
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_parser import DynamicEIP712Parser, parse_and_format, analyze_eip712


class JsonFileTester:
    """JSON file tester"""
    
    def __init__(self):
        self.parser = DynamicEIP712Parser()
    
    def read_json_file(self, file_path: str) -> dict:
        """
        Read JSON file
        
        Args:
            file_path: JSON file path
            
        Returns:
            Parsed dictionary data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"❌ File Not Found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON Format Error: {e}")
            return None
        except Exception as e:
            print(f"❌ File Read Failed: {e}")
            return None
    
    def validate_eip712_data(self, data: dict) -> bool:
        """
        Validate if data is valid EIP712 data
        
        Args:
            data: Data to validate
            
        Returns:
            Whether the data is valid EIP712 data
        """
        required_fields = ['types', 'domain', 'primaryType', 'message']
        
        if not isinstance(data, dict):
            print("❌ Data Format Error: Not a valid dictionary format")
            return False
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"❌ Missing Required Fields: {', '.join(missing_fields)}")
            return False
        
        if 'EIP712Domain' not in data['types']:
            print("❌ Missing EIP712Domain type definition")
            return False
        
        if data['primaryType'] not in data['types']:
            print(f"❌ Primary Type '{data['primaryType']}' not defined in types")
            return False
        
        return True
    
    def test_single_file(self, file_path: str, output_format: str = 'formatted') -> bool:
        """
        Test a single JSON file
        
        Args:
            file_path: JSON file path
            output_format: Output format ('formatted', 'structured', 'both')
            
        Returns:
            Whether test succeeded
        """
        print(f"\n📋 Testing File: {file_path}")
        print("=" * 60)
        
        # Read file
        data = self.read_json_file(file_path)
        if data is None:
            return False
        
        # Validate data format
        if not self.validate_eip712_data(data):
            return False
        
        try:
            # Parse data
            if output_format in ['formatted', 'both']:
                print("\n📝 Formatted Output:")
                result = parse_and_format(data)
                print(result)
            
            if output_format in ['structured', 'both']:
                print("\n📊 Structured Analysis:")
                analysis = analyze_eip712(data)
                self._print_structured_analysis(analysis)
            
            print("\n✅ Test Succeeded!")
            return True
            
        except Exception as e:
            print(f"❌ Parsing Failed: {e}")
            return False
    
    def test_directory(self, directory_path: str, output_format: str = 'formatted') -> dict:
        """
        Test all JSON files in a directory
        
        Args:
            directory_path: Directory path
            output_format: Output format
            
        Returns:
            Test result statistics
        """
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ Directory Not Found: {directory_path}")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        json_files = list(directory.glob('*.json'))
        if not json_files:
            print(f"❌ No JSON Files Found in Directory: {directory_path}")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        print(f"\n🚀 Batch Testing Directory: {directory_path}")
        print(f"📁 Found {len(json_files)} JSON files")
        print("=" * 80)
        
        success_count = 0
        failed_count = 0
        
        for json_file in json_files:
            success = self.test_single_file(str(json_file), output_format)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        # Output statistics
        total = len(json_files)
        print(f"\n📈 Test Statistics:")
        print(f"   • Total Files: {total}")
        print(f"   • Success: {success_count} ({success_count/total:.1%})")
        print(f"   • Failed: {failed_count} ({failed_count/total:.1%})")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': total
        }
    
    def _print_structured_analysis(self, analysis: dict):
        """Print structured analysis results"""
        print(f"   Primary Type: {analysis['primary_type']}")
        print(f"   Structure Description: {analysis['message_description']}")
        print(f"   Field Count: {analysis['field_count']}")
        
        print(f"\n   Field Details:")
        for field in analysis['fields']:
            confidence_str = f"{field['confidence']:.0%}" if field['confidence'] > 0 else "N/A"
            semantic_str = field['semantic'] or "Unrecognized"
            print(f"     • {field['name']}: {semantic_str} ({confidence_str})")
    
    def create_sample_files(self, output_dir: str = "sample_data"):
        """
        Create sample JSON files for testing
        
        Args:
            output_dir: Output directory
        """
        from test_data import ALL_TEST_DATA
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📁 Creating Sample JSON Files to Directory: {output_dir}")
        
        created_files = []
        for name, data in ALL_TEST_DATA.items():
            file_path = output_path / f"{name}.json"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                created_files.append(file_path)
                print(f"   ✅ Created: {file_path}")
            except Exception as e:
                print(f"   ❌ Creation Failed {file_path}: {e}")
        
        print(f"\n🎉 Successfully Created {len(created_files)} Sample Files!")
        return created_files


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='EIP712 JSON File Tester')
    parser.add_argument('path', nargs='?', help='JSON file or directory path')
    parser.add_argument('--format', '-f', choices=['formatted', 'structured', 'both'], 
                       default='formatted', help='Output format')
    parser.add_argument('--create-samples', '-c', action='store_true', 
                       help='Create sample JSON files')
    parser.add_argument('--sample-dir', '-d', default='sample_data', 
                       help='Sample file output directory')
    
    args = parser.parse_args()
    
    tester = JsonFileTester()
    
    # Create sample files
    if args.create_samples:
        tester.create_sample_files(args.sample_dir)
        if not args.path:
            args.path = args.sample_dir
    
    # If no path specified, show help
    if not args.path:
        parser.print_help()
        print(f"\n💡 Tips:")
        print(f"   • Test single file: python json_file_tester.py sample.json")
        print(f"   • Test entire directory: python json_file_tester.py ./sample_data/")
        print(f"   • Create sample files: python json_file_tester.py --create-samples")
        return
    
    # Determine if it's a file or directory
    path = Path(args.path)
    
    if path.is_file():
        # Test single file
        tester.test_single_file(str(path), args.format)
    elif path.is_dir():
        # Test directory
        tester.test_directory(str(path), args.format)
    else:
        print(f"❌ Path Not Found: {args.path}")


if __name__ == "__main__":
    main() 