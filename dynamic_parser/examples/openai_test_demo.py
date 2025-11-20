"""
OpenAI GPT-4.1-mini Test Tool

Usage:
python openai_test_demo.py <file_path>
Example: python openai_test_demo.py ../data/t2_unlimitedPermit.json
"""

import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai_nlp_generator import create_openai_generator, generate_english_with_openai

# Read from API key file
def load_api_key():
    """Load API key"""
    api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "api_key.txt")
    try:
        with open(api_key_path, 'r') as f:
            content = f.read().strip()
            # Extract OpenAI key
            for line in content.split('\n'):
                if line.startswith('OpenAI:'):
                    return line.split(':', 1)[1].strip()
    except Exception as e:
        print(f"❌ Unable to read API key: {e}")
        return None

def find_test_file(file_input):
    """Find test file"""
    # If it's an absolute or relative path, use it directly
    if os.path.exists(file_input):
        return file_input
    
    # 检查常见目录
    search_paths = [
        file_input,  # 当前目录
        os.path.join("sample_data", file_input),  # sample_data目录
        os.path.join("..", "data", file_input),  # 上级data目录
        os.path.join(os.path.dirname(__file__), "sample_data", file_input)  # 绝对sample_data路径
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    return None

def test_eip712_file(test_file):
    """测试EIP712文件"""
    try:
        with open(test_file, 'r') as f:
            eip712_data = json.load(f)
        
        api_key = load_api_key()
        if not api_key:
            print("Error: No API key found")
            return None
            
        # 生成英文描述
        result = generate_english_with_openai(eip712_data, api_key)
        
        print(f"Title: {result.title}")
        print(f"Summary: {result.summary}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Risk Explanation: {result.risk_explanation}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None







def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python openai_test_demo.py <file_path>")
        print("Example: python openai_test_demo.py ../data/t2_unlimitedPermit.json")
        return
    
    file_input = sys.argv[1]
    test_file = find_test_file(file_input)
    
    if not test_file:
        print(f"Error: File not found: {file_input}")
        return
    
    print(f"Testing: {test_file}")
    test_eip712_file(test_file)

if __name__ == "__main__":
    main() 