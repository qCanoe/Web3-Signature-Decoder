#!/usr/bin/env python3
"""
ETH Transaction Parser Demo Program
"""

import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eth_transaction_parser import EthTransactionParser
from eth_transaction_parser.tests.test_data import TEST_TRANSACTIONS


def print_separator(title: str = ""):
    """Print separator line"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("-" * 60)


def demo_basic_parsing():
    """Demo basic parsing functionality"""
    
    parser = EthTransactionParser(enable_logging=False)
    
    # Demo different types of transactions
    demo_cases = [
        ("ETH Transfer", "eth_transfer"),
        ("ERC20 Token Transfer", "erc20_transfer"),
        ("ERC20 Token Approval", "erc20_approve"),
        ("Uniswap Swap", "uniswap_swap"),
        ("NFT Transfer", "nft_transfer"),
        ("Contract Deployment", "contract_deploy")
    ]
    
    for title, tx_key in demo_cases:
        print(f"\n📝 {title}:")
        tx = TEST_TRANSACTIONS[tx_key]
        analysis = parser.parse(tx)
        
        print(f"  Type: {analysis.transaction_type.value}")
        print(f"  Risk level: {analysis.risk_level.value}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Description: {analysis.description}")
        print(f"  Summary: {analysis.summary}")
        
        if analysis.risk_factors:
            print(f"  Risk factors: {', '.join(analysis.risk_factors)}")
        
        if analysis.security_warnings:
            print(f"  Security warnings: {', '.join(analysis.security_warnings)}")


def demo_risk_analysis():
    
    parser = EthTransactionParser()
    
    risk_cases = [
        ("Low Risk - Normal ETH Transfer", "eth_transfer"),
        ("Medium Risk - NFT Approve All", "nft_approve_all"), 
        ("High Risk - Unlimited Token Approval", "erc20_approve"),
        ("Medium Risk - High-Value ETH Transfer", "high_value_eth"),
        ("Medium Risk - Unknown Contract Call", "unknown_contract")
    ]
    
    for title, tx_key in risk_cases:
        print(f"\n⚠️  {title}:")
        tx = TEST_TRANSACTIONS[tx_key]
        analysis = parser.parse(tx)
        
        risks = parser.transaction_analyzer.get_transaction_risks(analysis)
        
        print(f"  Risk level: {risks['risk_level']}")
        print(f"  Risk score: {risks['risk_score']}/100")
        
        if risks['risk_factors']:
            print(f"  Risk factors:")
            for factor in risks['risk_factors']:
                print(f"    - {factor}")
        
        if risks['security_warnings']:
            print(f"  Security warnings:")
            for warning in risks['security_warnings']:
                print(f"    - {warning}")
        
        if risks['recommendations']:
            print(f"  Security recommendations:")
            for rec in risks['recommendations']:
                print(f"    - {rec}")


def demo_parameter_extraction():
    """Demo parameter extraction functionality"""
    
    parser = EthTransactionParser()
    
    print("\n ERC20 Token Transfer Parameter Parsing:")
    tx = TEST_TRANSACTIONS["erc20_transfer"]
    analysis = parser.parse(tx)
    
    if analysis.contract_call:
        print(f"  Function selector: {analysis.contract_call.function_selector}")
        print(f"  Function name: {analysis.contract_call.function_name}")
        print(f"  Function signature: {analysis.contract_call.function_signature}")
        print(f"  Parameters:")
        for key, value in analysis.contract_call.parameters.items():
            print(f"    {key}: {value}")
    
    if analysis.token_info:
        print(f"  Token information:")
        print(f"    Contract address: {analysis.token_info.address}")
        print(f"    Token symbol: {analysis.token_info.symbol}")
        print(f"    Transfer amount: {analysis.token_info.amount_formatted}")
    
    print("\n Gas Fee Information:")
    gas_info = parser.parameter_extractor.extract_gas_info(tx)
    for key, value in gas_info.items():
        if 'gwei' in key:
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")



def demo_batch_processing():
    """Demo batch processing functionality"""
    
    parser = EthTransactionParser()
    
    # Batch process multiple transactions
    batch_txs = [
        TEST_TRANSACTIONS["eth_transfer"],
        TEST_TRANSACTIONS["erc20_transfer"],
        TEST_TRANSACTIONS["nft_transfer"],
        TEST_TRANSACTIONS["uniswap_swap"]
    ]
    
    print(f"\n📦 Batch processing {len(batch_txs)} transactions:")
    
    results = parser.parse_batch(batch_txs)
    
    for i, analysis in enumerate(results):
        if analysis:
            print(f"  Transaction {i+1}: {parser.get_transaction_summary(analysis)}")
        else:
            print(f"  Transaction {i+1}: Parsing failed")
    
    # Statistics
    risk_levels = {}
    tx_types = {}
    
    for analysis in results:
        if analysis:
            risk_level = analysis.risk_level.value
            tx_type = analysis.transaction_type.value
            
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
    
    print(f"  Risk level distribution: {dict(risk_levels)}")
    print(f"  Transaction type distribution: {dict(tx_types)}")


def main():
    """Main function"""
    
    try:
        # Execute various demos
        demo_basic_parsing()
        demo_risk_analysis()
        demo_batch_processing()
        
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo terminated")
    except Exception as e:
        print(f"\n❌ Error occurred during demo: {e}")


if __name__ == "__main__":
    main() 