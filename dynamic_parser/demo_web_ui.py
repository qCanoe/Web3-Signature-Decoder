#!/usr/bin/env python3
"""
EIP712 Signature Parser Web UI Demo Script
Demonstrates how to use the Web UI for signature parsing
"""

import json
import time
from pathlib import Path
from examples.test_data import ALL_TEST_DATA

def print_banner():
    """Print banner"""
    print("=" * 60)
    print("🚀 EIP712 Signature Parser Web UI Demo")
    print("=" * 60)
    print()

def show_test_data():
    """Show test data"""
    print("📋 Available test data:")
    print("-" * 30)
    
    for i, (name, data) in enumerate(ALL_TEST_DATA.items(), 1):
        print(f"{i}. {name}")
        print(f"   Type: {data.get('primaryType', 'Unknown')}")
        print(f"   Domain: {data.get('domain', {}).get('name', 'Unknown')}")
        print()

def demo_usage():
    """Demo usage"""
    print("🎯 Usage:")
    print("-" * 30)
    
    print("1. Start Web UI:")
    print("   python run_ui.py")
    print()
    
    print("2. Visit browser:")
    print("   http://localhost:5000")
    print()
    
    print("3. Input test data:")
    print("   Click 'Load Test Data' button")
    print("   Select a test data sample")
    print()
    
    print("4. Parse signature:")
    print("   Click 'Parse Signature' button")
    print("   View parsing results")
    print()

def show_sample_data():
    """Show sample data"""
    print("📄 Sample data (ERC20 Permit):")
    print("-" * 30)
    
    sample_data = ALL_TEST_DATA.get('ERC20_PERMIT', {})
    if sample_data:
        print(json.dumps(sample_data, indent=2, ensure_ascii=False))
    else:
        print("Sample data not found")
    print()

def show_features():
    """Show features"""
    print("✨ Features:")
    print("-" * 30)
    
    features = [
        "Intuitive user interface",
        "Real-time EIP712 signature parsing",
        "Smart field type recognition",
        "NLP natural language generation",
        "Multiple test data samples",
        "Detailed struct display",
        "Formatted result display",
        "Error handling and debug info",
        "Responsive design",
        "Keyboard shortcut support"
    ]
    
    for feature in features:
        print(f"• {feature}")
    print()

def show_tips():
    """Show tips"""
    print("💡 Tips:")
    print("-" * 30)
    
    tips = [
        "Use Ctrl+Enter to quickly parse signature",
        "Use Ctrl+K to quickly clear input",
        "Enable NLP feature for natural language description",
        "View 'Structure Details' tab to understand field types",
        "Use 'Export Results' feature to save parsing results",
        "Works perfectly on mobile devices",
        "Supports copying parsing results to clipboard",
        "View detailed error information for debugging"
    ]
    
    for tip in tips:
        print(f"• {tip}")
    print()

def main():
    """Main function"""
    print_banner()
    
    # Show features
    show_features()
    
    # Show usage
    demo_usage()
    
    # Show test data
    show_test_data()
    
    # Show tips
    show_tips()
    
    # Show sample data
    show_sample_data()
    
    print("🎉 Ready! Now run `python run_ui.py` to start Web UI")
    print("=" * 60)

if __name__ == "__main__":
    main() 