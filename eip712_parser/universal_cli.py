#!/usr/bin/env python3
"""
EIP712 Universal Parser Command Line Tool
Supports automatic identification of different types of Ethereum signatures
"""

import sys
import json
import argparse
import os
from typing import Dict, Any
from . import parse_request, UniversalParser, SignatureDetector
from .security import SecurityChecker


def load_data(input_source: str) -> Any:
    """Load input data"""
    # If it's a file path
    if os.path.isfile(input_source):
        with open(input_source, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
    else:
        # Process as direct input data
        # First try to parse as JSON
        try:
            parsed = json.loads(input_source)
            return parsed
        except json.JSONDecodeError:
            # If not valid JSON, return original string
            return input_source


def format_eip712_result(parsed_message, security_result, format_type="text"):
    """Format EIP712 parsing result"""
    if format_type == "json":
        result = {
            "kind": parsed_message.kind if hasattr(parsed_message, 'kind') else None,
            "security": security_result
        }
        if hasattr(parsed_message, 'detail'):
            detail = parsed_message.detail
            result['detail'] = {
                'type': detail.type if hasattr(detail, 'type') else None,
                'order_type': detail.order_type if hasattr(detail, 'order_type') else None,
                'from': detail.from_address if hasattr(detail, 'from_address') else None
            }
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    # Text format
    lines = []
    lines.append("🔍 EIP712 Parsing Result")
    lines.append("=" * 40)
    
    if hasattr(parsed_message, 'kind'):
        lines.append(f"Message type: {parsed_message.kind}")
    
    if hasattr(parsed_message, 'detail'):
        detail = parsed_message.detail
        if hasattr(detail, 'type'):
            lines.append(f"Protocol type: {detail.type}")
        if hasattr(detail, 'order_type'):
            lines.append(f"Order type: {detail.order_type}")
        if hasattr(detail, 'from_address'):
            lines.append(f"Initiator: {detail.from_address}")
    
    # Security check result
    lines.append("\n🛡️  Security Check")
    lines.append("-" * 20)
    if security_result["is_safe"]:
        lines.append("✅ No security risks found")
    else:
        lines.append("⚠️  Potential risks found:")
        for warning in security_result.get("warnings", []):
            lines.append(f"  - {warning}")
    
    return '\n'.join(lines)


def format_universal_result(result: Dict[str, Any], format_type: str = "text") -> str:
    """Format universal parsing result"""
    if format_type == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    lines = []
    lines.append("🔍 Signature Recognition and Parsing Result")
    lines.append("=" * 40)
    
    # Signature information
    signature_info = result.get('signature_info', {})
    lines.append(f"Signature type: {signature_info.get('type', 'unknown')}")
    lines.append(f"Description: {signature_info.get('description', 'Unknown')}")
    lines.append(f"Data format: {signature_info.get('data_format', 'unknown')}")
    
    # Detailed analysis
    analysis = signature_info.get('analysis', {})
    if analysis:
        lines.append(f"\n📊 Detailed Analysis:")
        for key, value in analysis.items():
            if isinstance(value, list):
                lines.append(f"  {key}: {', '.join(map(str, value)) if value else 'None'}")
            else:
                lines.append(f"  {key}: {value}")
    
    # Parsing result
    lines.append(f"\n🔧 Parsing Result:")
    if result.get('success'):
        lines.append(f"✅ Parsing successful")
        
        parsed_data = result.get('parsed_data')
        if parsed_data:
            sig_type = signature_info.get('type')
            if sig_type == "eth_signTypedData_v4":
                if hasattr(parsed_data, 'kind'):
                    lines.append(f"Protocol type: {parsed_data.kind}")
                    if parsed_data.kind == "nft" and hasattr(parsed_data, 'detail'):
                        lines.append(f"NFT protocol: {parsed_data.detail.type}")
                        lines.append(f"Order type: {parsed_data.detail.order_type}")
            elif sig_type == "eth_sendTransaction":
                transaction_info = parsed_data.get('transaction', {})
                lines.append(f"From: {transaction_info.get('from', 'Unknown')}")
                lines.append(f"To: {transaction_info.get('to', 'Unknown')}")
                lines.append(f"Value: {transaction_info.get('value', '0')}")
            elif sig_type == "personal_sign":
                message_info = parsed_data.get('message_info', {})
                lines.append(f"Message length: {message_info.get('length', 0)}")
                lines.append(f"Language: {message_info.get('language', 'unknown')}")
            
            # Security warnings
            warnings = parsed_data.get('security_warnings', [])
            if warnings:
                lines.append(f"\n⚠️  Security Warnings:")
                for warning in warnings:
                    lines.append(f"  - {warning}")
    else:
        lines.append(f"❌ Parsing failed: {result.get('error', 'Unknown error')}")
    
    return '\n'.join(lines)


def format_detection_only(signature_info: Dict[str, Any], format_type: str = "text") -> str:
    """Format detection results only"""
    if format_type == "json":
        return json.dumps(signature_info, indent=2, ensure_ascii=False)
    
    lines = []
    lines.append("🔍 Signature Type Detection Result")
    lines.append("=" * 30)
    lines.append(f"Type: {signature_info['type']}")
    lines.append(f"Description: {signature_info['description']}")
    lines.append(f"Data Format: {signature_info['data_format']}")
    
    analysis = signature_info.get('analysis', {})
    if analysis:
        lines.append(f"\n📊 Detailed Analysis:")
        for key, value in analysis.items():
            if isinstance(value, list):
                lines.append(f"  {key}: {', '.join(map(str, value)) if value else 'None'}")
            else:
                lines.append(f"  {key}: {value}")
    
    return '\n'.join(lines)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="EIP712 Universal Signature Parser and Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Usage:
  # Use universal parser (automatically detect signature type)
  python -m eip712_parser.universal_cli data.json
  python -m eip712_parser.universal_cli "Hello, World!"
  
  # Detect signature type only
  python -m eip712_parser.universal_cli --detect-only "Hello, World!"
  
  # Read from standard input
  echo '{"message": "test"}' | python -m eip712_parser.universal_cli --stdin
  
  # Output JSON format
  python -m eip712_parser.universal_cli --format json data.json
  
  # Traditional EIP712 parsing mode
  python -m eip712_parser.universal_cli --eip712-only data.json
        """
    )
    
    parser.add_argument(
        'input',
        nargs='?',
        help='Input data file path or direct data input'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--detect-only',
        action='store_true',
        help='Detect signature type only, do not parse'
    )
    
    parser.add_argument(
        '--eip712-only',
        action='store_true',
        help='Use traditional EIP712 parser only'
    )
    
    parser.add_argument(
        '--stdin',
        action='store_true',
        help='Read data from standard input'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: standard output)'
    )
    
    parser.add_argument(
        '--price-threshold',
        type=float,
        default=0.1,
        help='Price safety threshold (ETH) (default: 0.1)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Read input data
        if args.stdin:
            data = sys.stdin.read().strip()
        elif args.input:
            data = load_data(args.input)
        else:
            print("Error: Please provide input data or use --stdin", file=sys.stderr)
            sys.exit(1)
        
        # Choose processing method
        if args.detect_only:
            # Detect signature type only
            detector = SignatureDetector()
            signature_info = detector.get_signature_info(data)
            output = format_detection_only(signature_info, args.format)
            
        elif args.eip712_only:
            # Traditional EIP712 parsing
            if not isinstance(data, dict):
                print("Error: EIP712 parser requires dictionary format data", file=sys.stderr)
                sys.exit(1)
            
            if args.verbose:
                print("Parsing EIP712 data...", file=sys.stderr)
            
            parsed_message = parse_request(data)
            if not parsed_message:
                print("❌ Unable to parse this EIP712 data format", file=sys.stderr)
                sys.exit(1)
            
            # Security check
            if args.verbose:
                print("Performing security check...", file=sys.stderr)
            
            security_checker = SecurityChecker(price_threshold=args.price_threshold)
            security_result = security_checker.check_message_security(parsed_message)
            
            output = format_eip712_result(parsed_message, security_result, args.format)
            
        else:
            # Use universal parser (default mode)
            if args.verbose:
                print("Performing signature identification and parsing...", file=sys.stderr)
            
            universal_parser = UniversalParser()
            result = universal_parser.parse(data)
            output = format_universal_result(result, args.format)
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            if args.verbose:
                print(f"Result saved to: {args.output}", file=sys.stderr)
        else:
            print(output)
    
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON format error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error occurred: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 