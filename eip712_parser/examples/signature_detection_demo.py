#!/usr/bin/env python3
"""
签名识别器演示
展示如何使用签名识别器和通用解析器
"""

import json
import sys
import os

# 添加父目录到路径以导入模块  
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eip712_parser import SignatureDetector, SignatureType, UniversalParser


def demo_signature_detection():
    """演示签名识别功能"""
    
    print("🔍 以太坊签名识别器演示")
    print("=" * 60)
    
    # 准备不同类型的测试数据
    test_cases = [
        # 1. EIP-712 结构化数据签名
        {
            "name": "EIP-712 Seaport 签名",
            "data": {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "OrderComponents": [
                        {"name": "offerer", "type": "address"},
                        {"name": "offer", "type": "OfferItem[]"}
                    ],
                    "OfferItem": [
                        {"name": "itemType", "type": "uint8"},
                        {"name": "token", "type": "address"}
                    ]
                },
                "primaryType": "OrderComponents",
                "domain": {
                    "name": "Seaport",
                    "version": "1.1",
                    "chainId": "1",
                    "verifyingContract": "0x00000000006c3852cbEf3e08E8dF289169EdE581"
                },
                "message": {
                    "offerer": "0xcA1a218397f00ef0549e2555031a24B906200207",
                    "offer": []
                }
            }
        },
        
        # 2. 交易数据
        {
            "name": "以太坊交易",
            "data": {
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x0987654321098765432109876543210987654321",
                "value": "0xde0b6b3a7640000",  # 1 ETH
                "data": "0xa9059cbb0000000000000000000000000987654321098765432109876543210987654321000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "gas": "0x5208",
                "gasPrice": "0x3b9aca00",
                "nonce": "0x1"
            }
        },
        
        # 3. 个人消息签名
        {
            "name": "个人消息签名",
            "data": "Hello, this is a message to be signed!"
        },
        
        # 4. 个人消息签名 (中文)
        {
            "name": "中文个人消息",
            "data": "你好，这是一条需要签名的消息。请确认你信任此网站。"
        },
        
        # 5. 十六进制个人消息
        {
            "name": "十六进制个人消息",
            "data": "0x48656c6c6f2c20576f726c6421"  # "Hello, World!" 的十六进制
        },
        
        # 6. 原始签名数据
        {
            "name": "原始签名数据",
            "data": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef01"
        },
        
        # 7. 哈希数据
        {
            "name": "哈希数据",
            "data": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        },
        
        # 8. JSON 格式的个人消息
        {
            "name": "JSON 格式个人消息",
            "data": {
                "message": "Please sign this message to prove ownership of your wallet.",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    ]
    
    detector = SignatureDetector()
    universal_parser = UniversalParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}: {test_case['name']}")
        print("-" * 40)
        
        # 检测签名类型
        signature_info = detector.get_signature_info(test_case['data'])
        
        print(f"🔍 检测结果:")
        print(f"   类型: {signature_info['type']}")
        print(f"   描述: {signature_info['description']}")
        print(f"   数据格式: {signature_info['data_format']}")
        
        # 显示分析结果
        analysis = signature_info.get('analysis', {})
        if analysis:
            print(f"📊 详细分析:")
            for key, value in analysis.items():
                if isinstance(value, list):
                    print(f"   {key}: {', '.join(map(str, value)) if value else '无'}")
                else:
                    print(f"   {key}: {value}")
        
        # 使用通用解析器
        print(f"🔧 通用解析结果:")
        parse_result = universal_parser.parse(test_case['data'])
        
        if parse_result['success']:
            print(f"   ✅ 解析成功")
            
            # 显示特定解析结果
            parsed_data = parse_result.get('parsed_data')
            if parsed_data:
                if signature_info['type'] == SignatureType.ETH_SIGN_TYPED_DATA_V4:
                    if hasattr(parsed_data, 'kind'):
                        print(f"   协议类型: {parsed_data.kind}")
                        if parsed_data.kind == "nft":
                            print(f"   NFT协议: {parsed_data.detail.type}")
                            print(f"   订单类型: {parsed_data.detail.order_type}")
                elif signature_info['type'] == SignatureType.ETH_SEND_TRANSACTION:
                    transaction_info = parsed_data.get('transaction', {})
                    print(f"   从: {transaction_info.get('from', 'Unknown')[:10]}...")
                    print(f"   到: {transaction_info.get('to', 'Unknown')[:10]}...")
                    print(f"   价值: {transaction_info.get('value', '0')}")
                elif signature_info['type'] == SignatureType.PERSONAL_SIGN:
                    message_info = parsed_data.get('message_info', {})
                    print(f"   消息长度: {message_info.get('length', 0)}")
                    print(f"   语言: {message_info.get('language', 'unknown')}")
        else:
            print(f"   ❌ 解析失败: {parse_result.get('error', '未知错误')}")
        
        # 安全警告
        if signature_info['type'] in [SignatureType.ETH_SEND_TRANSACTION, SignatureType.PERSONAL_SIGN]:
            parse_result = universal_parser.parse(test_case['data'])
            if parse_result['success'] and parse_result['parsed_data']:
                warnings = parse_result['parsed_data'].get('security_warnings', [])
                if warnings:
                    print(f"⚠️  安全警告:")
                    for warning in warnings:
                        print(f"   - {warning}")


def demo_batch_detection():
    """演示批量检测功能"""
    print(f"\n{'='*60}")
    print("📦 批量签名检测演示")
    print("="*60)
    
    # 模拟从文件或API获取的多个签名数据
    batch_data = [
        '"Hello World!"',  # 简单字符串
        '{"message": "Sign this"}',  # JSON个人消息
        '{"to": "0x123", "value": "1000"}',  # 简单交易
        '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',  # 哈希
    ]
    
    detector = SignatureDetector()
    
    print("检测结果汇总:")
    print("-" * 40)
    
    type_counts = {}
    
    for i, data_str in enumerate(batch_data, 1):
        try:
            # 尝试解析JSON，如果失败则作为字符串处理
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = data_str.strip('"')  # 移除可能的引号
            
            signature_type = detector.detect_signature_type(data)
            type_counts[signature_type] = type_counts.get(signature_type, 0) + 1
            
            print(f"  数据 {i}: {signature_type}")
            
        except Exception as e:
            print(f"  数据 {i}: 检测失败 - {e}")
    
    print(f"\n统计结果:")
    for sig_type, count in type_counts.items():
        print(f"  {sig_type}: {count} 个")


def main():
    """主函数"""
    try:
        demo_signature_detection()
        demo_batch_detection()
        
        print(f"\n{'='*60}")
        print("🎉 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 