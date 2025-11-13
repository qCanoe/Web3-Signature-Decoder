"""
ETH Transaction Parser 测试套件
"""

import unittest
import json
from ..parser import EthTransactionParser
from ..models import TransactionType, RiskLevel
from .test_data import TEST_TRANSACTIONS, EXPECTED_RESULTS


class TestEthTransactionParser(unittest.TestCase):
    """ETH交易解析器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.parser = EthTransactionParser(enable_logging=True)
    
    def test_eth_transfer(self):
        """测试ETH转账"""
        tx = TEST_TRANSACTIONS["eth_transfer"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["eth_transfer"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertTrue(analysis.transaction.is_value_transfer)
        self.assertFalse(analysis.transaction.is_contract_call)
        self.assertAlmostEqual(analysis.transaction.value_eth, 0.1, places=6)
        
        # 检查描述内容
        for keyword in expected["description_contains"]:
            self.assertIn(keyword, analysis.description)
    
    def test_erc20_transfer(self):
        """测试ERC20代币转账"""
        tx = TEST_TRANSACTIONS["erc20_transfer"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["erc20_transfer"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertTrue(analysis.transaction.is_contract_call)
        self.assertIsNotNone(analysis.contract_call)
        self.assertEqual(analysis.contract_call.function_name, "transfer")
        
        # 检查代币信息
        if analysis.token_info:
            self.assertEqual(analysis.token_info.symbol, "USDT")
    
    def test_erc20_approve(self):
        """测试ERC20代币授权"""
        tx = TEST_TRANSACTIONS["erc20_approve"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["erc20_approve"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertIsNotNone(analysis.contract_call)
        self.assertEqual(analysis.contract_call.function_name, "approve")
        
        # 检查风险因素
        self.assertIn("疑似无限代币授权", analysis.risk_factors)
        self.assertTrue(len(analysis.security_warnings) > 0)
    
    def test_uniswap_swap(self):
        """测试Uniswap交换"""
        tx = TEST_TRANSACTIONS["uniswap_swap"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["uniswap_swap"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.contract_call.function_name, "swapExactETHForTokens")
    
    def test_nft_transfer(self):
        """测试NFT转移"""
        tx = TEST_TRANSACTIONS["nft_transfer"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["nft_transfer"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.contract_call.function_name, "transferFrom")
    
    def test_nft_approve_all(self):
        """测试NFT授权所有"""
        tx = TEST_TRANSACTIONS["nft_approve_all"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["nft_approve_all"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertIn("NFT全部授权", analysis.risk_factors)
    
    def test_contract_deploy(self):
        """测试合约部署"""
        tx = TEST_TRANSACTIONS["contract_deploy"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["contract_deploy"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertIsNone(analysis.transaction.to_address)
        self.assertTrue(analysis.transaction.is_contract_call)
    
    def test_high_value_eth(self):
        """测试大额ETH转账"""
        tx = TEST_TRANSACTIONS["high_value_eth"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["high_value_eth"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertIn("大额ETH转账", analysis.risk_factors)
        self.assertAlmostEqual(analysis.transaction.value_eth, 100.0, places=6)
    
    def test_unknown_contract(self):
        """测试未知合约调用"""
        tx = TEST_TRANSACTIONS["unknown_contract"]
        analysis = self.parser.parse(tx)
        expected = EXPECTED_RESULTS["unknown_contract"]
        
        self.assertEqual(analysis.transaction_type.value, expected["type"])
        self.assertEqual(analysis.risk_level.value, expected["risk_level"])
        self.assertIn("未知合约调用", analysis.risk_factors)
    
    def test_eip1559_transaction(self):
        """测试EIP-1559交易"""
        tx = TEST_TRANSACTIONS["eip1559"]
        analysis = self.parser.parse(tx)
        
        self.assertEqual(analysis.transaction_type, TransactionType.ETH_TRANSFER)
        self.assertIsNotNone(analysis.transaction.max_fee_per_gas)
        self.assertIsNotNone(analysis.transaction.max_priority_fee_per_gas)
        self.assertAlmostEqual(analysis.transaction.value_eth, 0.01, places=6)
    
    def test_batch_parsing(self):
        """测试批量解析"""
        transactions = [
            TEST_TRANSACTIONS["eth_transfer"],
            TEST_TRANSACTIONS["erc20_transfer"],
            TEST_TRANSACTIONS["nft_transfer"]
        ]
        
        results = self.parser.parse_batch(transactions)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].transaction_type, TransactionType.ETH_TRANSFER)
        self.assertEqual(results[1].transaction_type, TransactionType.TOKEN_TRANSFER)
        self.assertEqual(results[2].transaction_type, TransactionType.NFT_TRANSFER)
    
    def test_export_json(self):
        """测试JSON导出"""
        tx = TEST_TRANSACTIONS["eth_transfer"]
        analysis = self.parser.parse(tx)
        
        json_result = self.parser.export_analysis(analysis, "json")
        data = json.loads(json_result)
        
        self.assertEqual(data["transaction_type"], "eth_transfer")
        self.assertEqual(data["risk_level"], "low")
        self.assertIn("transaction", data)
    
    def test_export_text(self):
        """测试文本导出"""
        tx = TEST_TRANSACTIONS["erc20_approve"]
        analysis = self.parser.parse(tx)
        
        text_result = self.parser.export_analysis(analysis, "text")
        
        self.assertIn("ETH 交易分析报告", text_result)
        self.assertIn("token_approval", text_result)
        self.assertIn("high", text_result)
    
    def test_transaction_summary(self):
        """测试交易摘要"""
        tx = TEST_TRANSACTIONS["uniswap_swap"]
        analysis = self.parser.parse(tx)
        
        summary = self.parser.get_transaction_summary(analysis)
        
        self.assertIn("defi_swap", summary)
        self.assertIn("ETH数量:", summary)
        self.assertIn("swapExactETHForTokens", summary)
    
    def test_invalid_transaction(self):
        """测试无效交易"""
        invalid_tx = {"invalid": "data"}
        analysis = self.parser.parse(invalid_tx)
        
        self.assertEqual(analysis.transaction_type, TransactionType.UNKNOWN)
        self.assertEqual(analysis.risk_level, RiskLevel.HIGH)
        self.assertTrue(len(analysis.security_warnings) > 0)
    
    def test_json_string_input(self):
        """测试JSON字符串输入"""
        tx = TEST_TRANSACTIONS["eth_transfer"]
        tx_json = json.dumps(tx)
        
        analysis = self.parser.parse(tx_json)
        
        self.assertEqual(analysis.transaction_type, TransactionType.ETH_TRANSFER)
        self.assertEqual(analysis.risk_level, RiskLevel.LOW)


class TestTransactionAnalyzer(unittest.TestCase):
    """交易分析器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.parser = EthTransactionParser()
    
    def test_risk_analysis(self):
        """测试风险分析"""
        # 高风险：无限授权
        tx = TEST_TRANSACTIONS["erc20_approve"]
        analysis = self.parser.parse(tx)
        risks = self.parser.transaction_analyzer.get_transaction_risks(analysis)
        
        self.assertEqual(risks["risk_level"], "high")
        self.assertGreater(risks["risk_score"], 60)
        self.assertTrue(len(risks["recommendations"]) > 0)
        
        # 低风险：普通ETH转账
        tx = TEST_TRANSACTIONS["eth_transfer"]
        analysis = self.parser.parse(tx)
        risks = self.parser.transaction_analyzer.get_transaction_risks(analysis)
        
        self.assertEqual(risks["risk_level"], "low")
        self.assertLess(risks["risk_score"], 30)
    
    def test_transaction_descriptions(self):
        """测试交易描述生成"""
        test_cases = [
            ("eth_transfer", "转账"),
            ("erc20_transfer", "转账"),
            ("erc20_approve", "授权"),
            ("contract_deploy", "部署"),
            ("nft_transfer", "NFT"),
            ("uniswap_swap", "交换")
        ]
        
        for tx_name, expected_keyword in test_cases:
            tx = TEST_TRANSACTIONS[tx_name]
            analysis = self.parser.parse(tx)
            
            self.assertIn(expected_keyword, analysis.description)


class TestParameterExtractor(unittest.TestCase):
    """参数提取器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.parser = EthTransactionParser()
        self.extractor = self.parser.parameter_extractor
    
    def test_contract_call_extraction(self):
        """测试合约调用信息提取"""
        tx = TEST_TRANSACTIONS["erc20_transfer"]
        call_info = self.extractor.extract_contract_call_info(tx["data"])
        
        self.assertIsNotNone(call_info)
        self.assertEqual(call_info.function_selector, "0xa9059cbb")
        self.assertEqual(call_info.function_name, "transfer")
        self.assertIn("param_0", call_info.parameters)
        self.assertIn("param_1", call_info.parameters)
    
    def test_token_info_extraction(self):
        """测试代币信息提取"""
        tx = TEST_TRANSACTIONS["erc20_transfer"]
        call_info = self.extractor.extract_contract_call_info(tx["data"]) 
        token_info = self.extractor.extract_token_transfer_info(call_info, tx["to"])
        
        if token_info:
            self.assertEqual(token_info.symbol, "USDT")
            self.assertIsNotNone(token_info.amount)
    
    def test_gas_info_extraction(self):
        """测试Gas信息提取"""
        tx = TEST_TRANSACTIONS["eip1559"]
        gas_info = self.extractor.extract_gas_info(tx)
        
        self.assertIn("gas_limit", gas_info)
        self.assertIn("max_fee_per_gas", gas_info)
        self.assertIn("max_priority_fee_per_gas", gas_info)
        self.assertIn("max_fee_per_gas_gwei", gas_info)
    
    def test_address_validation(self):
        """测试地址验证"""
        valid_address = "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b"
        invalid_address = "0xinvalid"
        
        self.assertTrue(self.extractor.validate_address(valid_address))
        self.assertFalse(self.extractor.validate_address(invalid_address))
    
    def test_hex_data_validation(self):
        """测试十六进制数据验证"""
        valid_hex = "0x1234abcd"
        invalid_hex = "0xzzzz"
        
        self.assertTrue(self.extractor.validate_hex_data(valid_hex))
        self.assertFalse(self.extractor.validate_hex_data(invalid_hex))


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2) 