import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.pipeline import SemanticPipeline
from src.utils.mock_data import ALL_TEST_DATA
from src.core.input.definitions import SignatureType

class TestSemanticPipeline(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = SemanticPipeline()

    def test_process_erc20_permit(self):
        print("\nTesting Pipeline: ERC20 Permit")
        data = ALL_TEST_DATA["erc20_permit"]
        result = self.pipeline.process(data)
        
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SIGN_TYPED_DATA_V4)
        self.assertEqual(result['pipeline_result']['semantic']['action']['type'], 'authorization')
        self.assertIn("Authorization", result['pipeline_result']['ui']['title'])
        # Verify risk level logic (Permit usually has some risk due to off-chain nature)
        self.assertIn(result['pipeline_result']['ui']['risk_level'], ['low', 'medium', 'high'])

    def test_process_eth_transfer(self):
        print("\nTesting Pipeline: ETH Transfer")
        data = ALL_TEST_DATA["eth_transfer"]
        result = self.pipeline.process(data)
        
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SEND_TRANSACTION)
        self.assertEqual(result['pipeline_result']['semantic']['action']['type'], 'transfer_asset')
        self.assertIn("Transfer", result['pipeline_result']['ui']['title'])
        # High value ETH transfer should be high risk
        if float(data['value']) >= 1e18:
            self.assertEqual(result['pipeline_result']['ui']['risk_level'], 'high')

    def test_process_uniswap_swap(self):
        print("\nTesting Pipeline: Uniswap Swap")
        data = ALL_TEST_DATA["uniswap_swap"]
        result = self.pipeline.process(data)
        
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SEND_TRANSACTION)
        # Should be classified as swap/interaction
        self.assertTrue(result['pipeline_result']['semantic']['action']['type'] in ['defi_swap', 'contract_interaction', 'cross_contract_interaction'])
        
        # Verify decoded parameters exist
        self.assertTrue(result['pipeline_result']['technical']['decoded_parameters'])
        self.assertIn("amountOutMin", result['pipeline_result']['technical']['decoded_parameters'])

    def test_process_personal_sign_login(self):
        print("\nTesting Pipeline: Personal Sign Login")
        data = ALL_TEST_DATA["msg_login"]
        result = self.pipeline.process(data)
        
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.PERSONAL_SIGN)
        self.assertEqual(result['pipeline_result']['semantic']['action']['type'], 'authentication')
        self.assertEqual(result['pipeline_result']['ui']['risk_level'], 'low')

    def test_process_personal_sign_phishing(self):
        print("\nTesting Pipeline: Personal Sign Phishing")
        data = ALL_TEST_DATA["msg_phishing"]
        result = self.pipeline.process(data)
        
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.PERSONAL_SIGN)
        # Should detect phishing keywords
        self.assertEqual(result['pipeline_result']['ui']['risk_level'], 'high')
        self.assertTrue(any("Phishing" in r for r in result['pipeline_result']['ui']['risk_reasons']))

if __name__ == "__main__":
    unittest.main()

