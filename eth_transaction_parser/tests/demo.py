#!/usr/bin/env python3
"""
ETH Transaction Parser 演示程序
"""

import json
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eth_transaction_parser import EthTransactionParser
from eth_transaction_parser.tests.test_data import TEST_TRANSACTIONS


def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("-" * 60)


def demo_basic_parsing():
    """演示基本解析功能"""
    
    parser = EthTransactionParser(enable_logging=False)
    
    # 演示不同类型的交易
    demo_cases = [
        ("ETH转账", "eth_transfer"),
        ("ERC20代币转账", "erc20_transfer"),
        ("ERC20代币授权", "erc20_approve"),
        ("Uniswap交换", "uniswap_swap"),
        ("NFT转移", "nft_transfer"),
        ("合约部署", "contract_deploy")
    ]
    
    for title, tx_key in demo_cases:
        print(f"\n📝 {title}:")
        tx = TEST_TRANSACTIONS[tx_key]
        analysis = parser.parse(tx)
        
        print(f"  类型: {analysis.transaction_type.value}")
        print(f"  风险级别: {analysis.risk_level.value}")
        print(f"  置信度: {analysis.confidence:.2f}")
        print(f"  描述: {analysis.description}")
        print(f"  摘要: {analysis.summary}")
        
        if analysis.risk_factors:
            print(f"  风险因素: {', '.join(analysis.risk_factors)}")
        
        if analysis.security_warnings:
            print(f"  安全警告: {', '.join(analysis.security_warnings)}")


def demo_risk_analysis():
    
    parser = EthTransactionParser()
    
    risk_cases = [
        ("低风险 - 普通ETH转账", "eth_transfer"),
        ("中等风险 - NFT授权所有", "nft_approve_all"), 
        ("高风险 - 无限代币授权", "erc20_approve"),
        ("中等风险 - 大额ETH转账", "high_value_eth"),
        ("中等风险 - 未知合约调用", "unknown_contract")
    ]
    
    for title, tx_key in risk_cases:
        print(f"\n⚠️  {title}:")
        tx = TEST_TRANSACTIONS[tx_key]
        analysis = parser.parse(tx)
        
        risks = parser.transaction_analyzer.get_transaction_risks(analysis)
        
        print(f"  风险级别: {risks['risk_level']}")
        print(f"  风险分数: {risks['risk_score']}/100")
        
        if risks['risk_factors']:
            print(f"  风险因素:")
            for factor in risks['risk_factors']:
                print(f"    - {factor}")
        
        if risks['security_warnings']:
            print(f"  安全警告:")
            for warning in risks['security_warnings']:
                print(f"    - {warning}")
        
        if risks['recommendations']:
            print(f"  安全建议:")
            for rec in risks['recommendations']:
                print(f"    - {rec}")


def demo_parameter_extraction():
    """演示参数提取功能"""
    
    parser = EthTransactionParser()
    
    print("\n ERC20代币转账参数解析:")
    tx = TEST_TRANSACTIONS["erc20_transfer"]
    analysis = parser.parse(tx)
    
    if analysis.contract_call:
        print(f"  函数选择器: {analysis.contract_call.function_selector}")
        print(f"  函数名称: {analysis.contract_call.function_name}")
        print(f"  函数签名: {analysis.contract_call.function_signature}")
        print(f"  参数:")
        for key, value in analysis.contract_call.parameters.items():
            print(f"    {key}: {value}")
    
    if analysis.token_info:
        print(f"  代币信息:")
        print(f"    合约地址: {analysis.token_info.address}")
        print(f"    代币符号: {analysis.token_info.symbol}")
        print(f"    转账数量: {analysis.token_info.amount_formatted}")
    
    print("\n Gas费用信息:")
    gas_info = parser.parameter_extractor.extract_gas_info(tx)
    for key, value in gas_info.items():
        if 'gwei' in key:
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")



def demo_batch_processing():
    """演示批量处理功能"""
    
    parser = EthTransactionParser()
    
    # 批量处理多个交易
    batch_txs = [
        TEST_TRANSACTIONS["eth_transfer"],
        TEST_TRANSACTIONS["erc20_transfer"],
        TEST_TRANSACTIONS["nft_transfer"],
        TEST_TRANSACTIONS["uniswap_swap"]
    ]
    
    print(f"\n📦 批量处理 {len(batch_txs)} 个交易:")
    
    results = parser.parse_batch(batch_txs)
    
    for i, analysis in enumerate(results):
        if analysis:
            print(f"  交易 {i+1}: {parser.get_transaction_summary(analysis)}")
        else:
            print(f"  交易 {i+1}: 解析失败")
    
    # 统计信息
    risk_levels = {}
    tx_types = {}
    
    for analysis in results:
        if analysis:
            risk_level = analysis.risk_level.value
            tx_type = analysis.transaction_type.value
            
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
    
    print(f"  风险级别分布: {dict(risk_levels)}")
    print(f"  交易类型分布: {dict(tx_types)}")


def main():
    """主函数"""
    
    try:
        # 执行各种演示
        demo_basic_parsing()
        demo_risk_analysis()
        demo_batch_processing()
        
        
    except KeyboardInterrupt:
        print("\n\n👋 演示已终止")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    main() 