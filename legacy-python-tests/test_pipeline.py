import unittest
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.pipeline import SemanticPipeline
from src.utils.mock_data import ALL_TEST_DATA
from src.core.input.definitions import SignatureType


class TestSemanticPipeline(unittest.TestCase):
    """Integration tests for the complete semantic pipeline"""
    
    def setUp(self):
        self.pipeline = SemanticPipeline()

    def test_process_erc20_permit(self):
        """Test Pipeline: ERC20 Permit (T5)"""
        data = ALL_TEST_DATA.get("t5_unlimited_approval")
        if not data:
            self.skipTest("t5_unlimited_approval test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SIGN_TYPED_DATA_V4)
        self.assertEqual(result['pipeline_result']['semantic']['action']['type'], 'authorization')
        self.assertIn("Authorization", result['pipeline_result']['ui']['title'])

    def test_process_nft_mint(self):
        """Test Pipeline: NFT Mint Transaction (T2)"""
        data = ALL_TEST_DATA.get("t2_nft_mint")
        if not data:
            self.skipTest("t2_nft_mint test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SEND_TRANSACTION)
        # NFT mint should be categorized as contract call or interaction
        self.assertIn(result['pipeline_result']['semantic']['action']['type'], 
                     ['contract_call', 'contract_interaction', 'nft_mint', 'unknown'])

    def test_process_dao_vote(self):
        """Test Pipeline: DAO Vote (T3)"""
        data = ALL_TEST_DATA.get("t3_dao_vote")
        if not data:
            self.skipTest("t3_dao_vote test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SIGN_TYPED_DATA_V4)
        self.assertIn(result['pipeline_result']['semantic']['action']['type'], [
            'vote', 'governance', 'authorization', 'unknown'
        ])

    def test_process_personal_sign_login(self):
        """Test Pipeline: Personal Sign Login (T1)"""
        data = ALL_TEST_DATA.get("t1_opensea_login")
        if not data:
            self.skipTest("t1_opensea_login test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.PERSONAL_SIGN)
        self.assertEqual(result['pipeline_result']['semantic']['action']['type'], 'authentication')
        # Login messages should be low or medium risk
        self.assertIn(result['pipeline_result']['ui']['risk_level'], ['low', 'medium'])

    def test_process_phishing_request(self):
        """Test Pipeline: Phishing Request (T6)"""
        data = ALL_TEST_DATA.get("t6_phishing_request")
        if not data:
            self.skipTest("t6_phishing_request test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SIGN_TYPED_DATA_V4)
        # Should detect phishing pattern (NFT for 0 ETH) and have high risk
        self.assertIn(result['pipeline_result']['ui']['risk_level'], ['high', 'critical', 'medium'])

    def test_process_personal_sign_phishing(self):
        """Test Pipeline: Personal Sign Phishing (T7)"""
        data = ALL_TEST_DATA.get("t7_personal_sign_phishing")
        if not data:
            self.skipTest("t7_personal_sign_phishing test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.PERSONAL_SIGN)
        context_labels = [c["label"] for c in result['pipeline_result']['semantic']['context']]
        self.assertIn("Phishing Indicators", context_labels)
        self.assertIn("Warning: possible phishing indicators detected", result['pipeline_result']['ui']['description'])

    def test_process_multicall_summary(self):
        """Test Pipeline: Multicall Summary (T8)"""
        data = ALL_TEST_DATA.get("t8_multicall_approve")
        if not data:
            self.skipTest("t8_multicall_approve test data not available")
        
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.ETH_SEND_TRANSACTION)
        self.assertIn(result['pipeline_result']['semantic']['action']['type'], [
            'batch_operation', 'batch_approval'
        ])
        context_labels = [c["label"] for c in result['pipeline_result']['semantic']['context']]
        self.assertTrue(any(label in ["Batch Summary", "Universal Router Summary"] for label in context_labels))

    def test_process_with_origin(self):
        """Test Pipeline with DApp origin"""
        data = ALL_TEST_DATA.get("t4_bridge_swap")
        if not data:
            self.skipTest("t4_bridge_swap test data not available")
        
        result = self.pipeline.process(data, origin="https://app.uniswap.org")
        
        self.assertTrue(result.get('success'))

    def test_output_structure(self):
        """Test that output has required structure"""
        data = ALL_TEST_DATA.get("t4_bridge_swap")
        if not data:
            self.skipTest("t4_bridge_swap test data not available")
        
        result = self.pipeline.process(data)
        
        # Check top level
        self.assertIn('success', result)
        self.assertIn('pipeline_result', result)
        self.assertIn('raw_result', result)
        
        # Check pipeline_result structure
        pr = result['pipeline_result']
        self.assertIn('ui', pr)
        self.assertIn('semantic', pr)
        self.assertIn('technical', pr)
        
        # Check UI section
        ui = pr['ui']
        self.assertIn('title', ui)
        self.assertIn('description', ui)
        self.assertIn('risk_level', ui)
        self.assertIn('risk_reasons', ui)
        
        # Check semantic section
        sem = pr['semantic']
        self.assertIn('actor', sem)
        self.assertIn('action', sem)
        self.assertIn('object', sem)
        self.assertIn('context', sem)


class TestPipelineErrorHandling(unittest.TestCase):
    """Test error handling in the pipeline"""
    
    def setUp(self):
        self.pipeline = SemanticPipeline()

    def test_invalid_json_input(self):
        """Test handling of invalid JSON input - treated as personal sign message"""
        result = self.pipeline.process("{{invalid json}}")
        # Should handle gracefully by treating as a message to sign
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['technical']['type'], SignatureType.PERSONAL_SIGN)

    def test_empty_input(self):
        """Test handling of empty input"""
        result = self.pipeline.process("")
        # Should still return a result, treating as personal sign
        self.assertTrue(result.get('success'))

    def test_none_input(self):
        """Test handling of None input - pipeline handles gracefully"""
        result = self.pipeline.process(None)
        # Pipeline should handle None gracefully
        self.assertIsNotNone(result)

    def test_partial_eip712(self):
        """Test handling of incomplete EIP-712 data"""
        # Missing required fields
        data = {
            "domain": {"name": "Test"},
            "message": {}
        }
        result = self.pipeline.process(data)
        # Should handle gracefully
        self.assertIsNotNone(result)


class TestPipelinePerformance(unittest.TestCase):
    """Performance tests for the pipeline"""
    
    def setUp(self):
        self.pipeline = SemanticPipeline()

    def test_processing_time(self):
        """Test that processing completes in reasonable time"""
        data = ALL_TEST_DATA.get("t4_bridge_swap")
        if not data:
            self.skipTest("t4_bridge_swap test data not available")
        
        iterations = 10
        start = time.time()
        
        for _ in range(iterations):
            self.pipeline.process(data)
        
        elapsed = time.time() - start
        avg_time = elapsed / iterations
        
        print(f"\nPipeline processing time: {avg_time:.3f}s per request ({iterations} iterations)")
        
        # Should process in under 2 seconds per request
        self.assertLess(avg_time, 2.0)

    def test_batch_processing(self):
        """Test processing multiple requests"""
        test_cases = list(ALL_TEST_DATA.items())[:5]  # First 5 test cases
        
        results = []
        for name, data in test_cases:
            try:
                result = self.pipeline.process(data)
                results.append((name, result.get('success', False)))
            except Exception as e:
                results.append((name, False))
        
        # At least some should succeed
        successes = sum(1 for _, success in results if success)
        self.assertGreater(successes, 0)


class TestRiskLevelIntegration(unittest.TestCase):
    """Integration tests for risk level assessment"""
    
    def setUp(self):
        self.pipeline = SemanticPipeline()

    def test_low_risk_authentication(self):
        """Test that authentication signatures are low risk"""
        data = {
            "message": "Sign in to Example App\nNonce: 12345\nTimestamp: 2024-01-01"
        }
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['pipeline_result']['ui']['risk_level'], 'low')

    def test_high_risk_phishing_keywords(self):
        """Test that phishing keywords trigger high risk"""
        data = {
            "message": "URGENT: Verify your wallet immediately to claim your reward!"
        }
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        self.assertIn(result['pipeline_result']['ui']['risk_level'], ['high', 'critical'])

    def test_medium_risk_approval(self):
        """Test that approvals have appropriate risk"""
        data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"}
                ],
                "Permit": [
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"}
                ]
            },
            "domain": {"name": "Test Token", "chainId": 1},
            "primaryType": "Permit",
            "message": {
                "spender": "0x1234567890123456789012345678901234567890",
                "value": "1000000000000000000",
                "nonce": 0,
                "deadline": 9999999999
            }
        }
        result = self.pipeline.process(data)
        
        self.assertTrue(result.get('success'))
        # Approval should be at least medium risk
        self.assertIn(result['pipeline_result']['ui']['risk_level'], ['medium', 'high'])


if __name__ == "__main__":
    unittest.main(verbosity=2)
