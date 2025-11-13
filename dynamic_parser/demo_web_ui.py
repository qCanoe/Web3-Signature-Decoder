#!/usr/bin/env python3
"""
EIP712 签名解析器 Web UI 演示脚本
展示如何使用Web UI进行签名解析
"""

import json
import time
from pathlib import Path
from examples.test_data import ALL_TEST_DATA

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🚀 EIP712 签名解析器 Web UI 演示")
    print("=" * 60)
    print()

def show_test_data():
    """显示测试数据"""
    print("📋 可用的测试数据:")
    print("-" * 30)
    
    for i, (name, data) in enumerate(ALL_TEST_DATA.items(), 1):
        print(f"{i}. {name}")
        print(f"   类型: {data.get('primaryType', 'Unknown')}")
        print(f"   域名: {data.get('domain', {}).get('name', 'Unknown')}")
        print()

def demo_usage():
    """演示使用方法"""
    print("🎯 使用方法:")
    print("-" * 30)
    
    print("1. 启动Web UI:")
    print("   python run_ui.py")
    print()
    
    print("2. 访问浏览器:")
    print("   http://localhost:5000")
    print()
    
    print("3. 输入测试数据:")
    print("   点击'加载测试数据'按钮")
    print("   选择一个测试数据样本")
    print()
    
    print("4. 解析签名:")
    print("   点击'解析签名'按钮")
    print("   查看解析结果")
    print()

def show_sample_data():
    """显示示例数据"""
    print("📄 示例数据 (ERC20 Permit):")
    print("-" * 30)
    
    sample_data = ALL_TEST_DATA.get('ERC20_PERMIT', {})
    if sample_data:
        print(json.dumps(sample_data, indent=2, ensure_ascii=False))
    else:
        print("未找到示例数据")
    print()

def show_features():
    """显示功能特性"""
    print("✨ 功能特性:")
    print("-" * 30)
    
    features = [
        "直观的用户界面",
        "实时解析EIP712签名",
        "智能字段类型识别",
        "NLP自然语言生成",
        "多种测试数据样本",
        "详细的结构体展示",
        "格式化结果显示",
        "错误处理和调试信息",
        "响应式设计",
        "键盘快捷键支持"
    ]
    
    for feature in features:
        print(f"• {feature}")
    print()

def show_tips():
    """显示使用技巧"""
    print("💡 使用技巧:")
    print("-" * 30)
    
    tips = [
        "使用 Ctrl+Enter 快速解析签名",
        "使用 Ctrl+K 快速清空输入",
        "启用NLP功能获得自然语言描述",
        "查看'结构详情'标签页了解字段类型",
        "使用'导出结果'功能保存解析结果",
        "在移动设备上也能完美使用",
        "支持复制解析结果到剪贴板",
        "查看详细错误信息进行调试"
    ]
    
    for tip in tips:
        print(f"• {tip}")
    print()

def main():
    """主函数"""
    print_banner()
    
    # 显示功能特性
    show_features()
    
    # 显示使用方法
    demo_usage()
    
    # 显示测试数据
    show_test_data()
    
    # 显示使用技巧
    show_tips()
    
    # 显示示例数据
    show_sample_data()
    
    print("🎉 准备好了！现在运行 `python run_ui.py` 启动Web UI")
    print("=" * 60)

if __name__ == "__main__":
    main() 