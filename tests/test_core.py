import unittest
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.processing.transaction_decoder import TransactionDecoder
from src.core.processing.risk import RiskEngine, RiskAssessment
from src.core.input.definitions import IntermediateRepresentation, SignatureType
from src.core.processing.structure import SemanticStructure, SemanticComponent
from src.core.processing.interpreter import Interpreter
from src.core.input.adapter import InputAdapter
from src.core.processing.knowledge_base import KnowledgeBase
from src.core.output.highlighter import TextHighlighter


class TestTransactionDecoder(unittest.TestCase):
    """Test cases for TransactionDecoder"""
    
    def test_erc20_transfer(self):
        """Test ERC20 transfer decoding"""
        # transfer(address,uint256) -> 0xa9059cbb
        calldata = "0xa9059cbb000000000000000000000000123456789012345678901234567890123456789000000000000000000000000000000000000000000000000000000000000003e8"
        decoded = TransactionDecoder.decode(calldata)
        
        self.assertEqual(decoded['function_name'], 'transfer')
        self.assertEqual(decoded['parameters']['to'], '0x1234567890123456789012345678901234567890')
        self.assertEqual(decoded['parameters']['amount'], 1000)
        self.assertEqual(decoded['category'], 'erc20_transfer')

    def test_erc20_approve_infinite(self):
        """Test ERC20 infinite approval decoding"""
        # approve(address,uint256) -> 0x095ea7b3
        calldata = "0x095ea7b30000000000000000000000001234567890123456789012345678901234567890ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        decoded = TransactionDecoder.decode(calldata)
        
        self.assertEqual(decoded['function_name'], 'approve')
        self.assertEqual(decoded['parameters']['amount'], 2**256 - 1)
        self.assertEqual(decoded['category'], 'erc20_approve')

    def test_unknown_selector(self):
        """Test unknown function selector handling"""
        calldata = "0x12345678" + "0" * 64
        decoded = TransactionDecoder.decode(calldata)
        
        self.assertEqual(decoded.get('function_selector'), '0x12345678')
        self.assertIsNone(decoded.get('function_name'))

    def test_empty_calldata(self):
        """Test empty calldata handling"""
        self.assertEqual(TransactionDecoder.decode(""), {})
        self.assertEqual(TransactionDecoder.decode(None), {})
        self.assertEqual(TransactionDecoder.decode("0x"), {})

    def test_short_calldata(self):
        """Test calldata too short for function selector"""
        self.assertEqual(TransactionDecoder.decode("0x1234"), {})

    def test_invalid_hex(self):
        """Test invalid hex handling"""
        result = TransactionDecoder.decode("0xGGGGGGGG")
        # Should return empty or handle gracefully
        self.assertIsInstance(result, dict)

    def test_multicall_detection(self):
        """Test multicall detection"""
        # multicall(bytes[]) selector
        self.assertTrue(TransactionDecoder.is_multicall("0xac9650d8" + "0" * 64))
        self.assertTrue(TransactionDecoder.is_multicall("0x5ae401dc" + "0" * 64))
        self.assertFalse(TransactionDecoder.is_multicall("0xa9059cbb" + "0" * 64))

    def test_type_extraction_simple(self):
        """Test simple type extraction from signature"""
        types = TransactionDecoder._extract_types_from_signature("transfer(address,uint256)")
        self.assertEqual(types, ["address", "uint256"])

    def test_type_extraction_with_tuple(self):
        """Test tuple type extraction from signature"""
        types = TransactionDecoder._extract_types_from_signature("func(uint256,(address,uint256))")
        self.assertEqual(types, ["uint256", "(address,uint256)"])

    def test_type_extraction_with_array(self):
        """Test array type extraction from signature"""
        types = TransactionDecoder._extract_types_from_signature("func(address[],uint256)")
        self.assertEqual(types, ["address[]", "uint256"])


class TestInputAdapter(unittest.TestCase):
    """Test cases for InputAdapter"""
    
    def test_eip712_dict_input(self):
        """Test EIP-712 dict input adaptation"""
        data_dict = {
            "types": {"EIP712Domain": []}, 
            "domain": {}, 
            "primaryType": "EIP712Domain", 
            "message": {}
        }
        ir = InputAdapter.adapt(data_dict)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SIGN_TYPED_DATA_V4)
    
    def test_eip712_string_input(self):
        """Test EIP-712 JSON string input adaptation"""
        data_str = '{"types": {"EIP712Domain": []}, "domain": {}, "primaryType": "EIP712Domain", "message": {}}'
        ir = InputAdapter.adapt(data_str)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SIGN_TYPED_DATA_V4)
    
    def test_personal_sign_text(self):
        """Test personal sign text message"""
        ir = InputAdapter.adapt("Hello World")
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)
    
    def test_personal_sign_hex(self):
        """Test personal sign hex message"""
        ir = InputAdapter.adapt("0x1234567890")
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)

    def test_transaction_detection(self):
        """Test transaction detection"""
        data = {
            "to": "0x1234567890123456789012345678901234567890",
            "value": "1000000000000000000",
            "data": "0x"
        }
        ir = InputAdapter.adapt(data)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SEND_TRANSACTION)

    def test_origin_preservation(self):
        """Test that origin is preserved"""
        data = {"message": "test"}
        ir = InputAdapter.adapt(data, origin="https://example.com")
        self.assertEqual(ir.dapp_url, "https://example.com")

    def test_chain_id_hex_parsing(self):
        """Test hex chain ID parsing"""
        data = {
            "types": {
                "EIP712Domain": [{"name": "chainId", "type": "uint256"}],
                "Test": [{"name": "value", "type": "uint256"}]
            },
            "domain": {"chainId": "0x1"},
            "primaryType": "Test",
            "message": {"value": 123}
        }
        ir = InputAdapter.adapt(data)
        # Chain ID should be parsed from hex
        self.assertEqual(ir.chain_id, 1)


class TestRiskEngine(unittest.TestCase):
    """Test cases for RiskEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SEND_TRANSACTION,
            raw_data={},
            chain_id=1
        )
        self.base_structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Test", "test"),
            target_object=SemanticComponent("Object", "Contract", "0xContract"),
            context=[]
        )
    
    def test_phishing_detection(self):
        """Test phishing keyword detection"""
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Urgent Action", "urgent_action"),
            target_object=SemanticComponent("Object", "Contract", "0xContract"),
            context=[]
        )
        self.base_ir.params = {"message": "Please sign urgently to verify your account"}
        
        risks = RiskEngine.assess(self.base_ir, structure)
        self.assertTrue(any("Phishing" in r or "phishing" in r.lower() for r in risks.reasons))

    def test_high_risk_param(self):
        """Test high risk parameter detection"""
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Approve", "approve"),
            target_object=SemanticComponent("Object", "Token", "0xToken"),
            context=[
                SemanticComponent("Context", "Infinite Allowance", "MAX", risk_factor="high")
            ],
            permission_scope="unlimited_permanent"  # Add high-risk permission scope
        )
        
        risks = RiskEngine.assess(self.base_ir, structure)
        # Should be high risk due to infinite allowance + unlimited permanent permission
        self.assertIn(risks.level, ["high", "critical"])

    def test_known_contract_reduces_risk(self):
        """Test that known contracts reduce risk"""
        # Uniswap V3 Router on Mainnet
        self.base_ir.contract = "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45"
        
        risks = RiskEngine.assess(self.base_ir, self.base_structure)
        self.assertTrue(any("Known protocol" in r or "Verified" in r for r in risks.reasons))

    def test_unknown_contract_mainnet_risk(self):
        """Test unknown contract on mainnet has higher risk"""
        self.base_ir.contract = "0x1111111111111111111111111111111111111111"
        self.base_ir.chain_id = 1
        
        risks = RiskEngine.assess(self.base_ir, self.base_structure)
        self.assertTrue(any("Unknown contract" in r or "unknown" in r.lower() for r in risks.reasons))

    def test_authentication_low_risk(self):
        """Test authentication actions are low risk"""
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Sign In", "authentication"),
            target_object=SemanticComponent("Object", "DApp", "Example"),
            context=[]
        )
        
        risks = RiskEngine.assess(self.base_ir, structure)
        self.assertEqual(risks.level, "low")

    def test_risk_score_capped(self):
        """Test that risk score is capped at 100"""
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Approve", "approve"),
            target_object=SemanticComponent("Object", "Token", "0xToken"),
            context=[
                SemanticComponent("Context", "Infinite Allowance", "MAX", risk_factor="high"),
                SemanticComponent("Context", "High Value", "1000000", risk_factor="high"),
            ],
            permission_scope="unlimited_permanent"
        )
        self.base_ir.params = {"message": "urgent claim reward verify"}
        
        risks = RiskEngine.assess(self.base_ir, structure)
        self.assertLessEqual(risks.score, 100)


class TestKnowledgeBase(unittest.TestCase):
    """Test cases for KnowledgeBase"""
    
    def test_function_name_lookup(self):
        """Test function name lookup"""
        name = KnowledgeBase.get_function_name("0xa9059cbb")
        self.assertEqual(name, "transfer")

    def test_function_definition_lookup(self):
        """Test function definition lookup"""
        definition = KnowledgeBase.get_function_definition("0x095ea7b3")
        self.assertIsNotNone(definition)
        self.assertEqual(definition["name"], "approve")
        self.assertEqual(definition["category"], "erc20_approve")

    def test_contract_name_lookup(self):
        """Test contract name lookup"""
        name = KnowledgeBase.get_contract_name(1, "0x000000000022d473030f116ddee9f6b43ac78ba3")
        self.assertEqual(name, "Permit2")

    def test_chain_name_lookup(self):
        """Test chain name lookup"""
        self.assertEqual(KnowledgeBase.get_chain_name(1), "Ethereum")
        self.assertEqual(KnowledgeBase.get_chain_name(137), "Polygon")
        self.assertEqual(KnowledgeBase.get_chain_name(99999), "Chain 99999")

    def test_infinite_allowance_int(self):
        """Test infinite allowance detection for int"""
        self.assertTrue(KnowledgeBase.is_infinite_allowance(2**256 - 1))
        self.assertTrue(KnowledgeBase.is_infinite_allowance(2**255 + 1))
        self.assertFalse(KnowledgeBase.is_infinite_allowance(1000))

    def test_infinite_allowance_hex(self):
        """Test infinite allowance detection for hex string"""
        max_uint = "0x" + "f" * 64
        self.assertTrue(KnowledgeBase.is_infinite_allowance(max_uint))

    def test_eip712_category_lookup(self):
        """Test EIP-712 type category lookup"""
        self.assertEqual(KnowledgeBase.get_eip712_category("Permit"), "authorization")
        self.assertEqual(KnowledgeBase.get_eip712_category("Vote"), "governance")
        self.assertEqual(KnowledgeBase.get_eip712_category("Unknown"), "unknown")


class TestPerformance(unittest.TestCase):
    """Performance benchmark tests"""
    
    def test_decode_performance(self):
        """Test decoding performance"""
        calldata = "0xa9059cbb000000000000000000000000123456789012345678901234567890123456789000000000000000000000000000000000000000000000000000000000000003e8"
        
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            TransactionDecoder.decode(calldata)
        
        elapsed = time.time() - start
        avg_time = elapsed / iterations * 1000  # ms
        
        print(f"\nDecode performance: {avg_time:.3f}ms per call ({iterations} iterations)")
        self.assertLess(avg_time, 10)  # Should be under 10ms per call

    def test_risk_assessment_performance(self):
        """Test risk assessment performance"""
        ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SEND_TRANSACTION,
            raw_data={},
            chain_id=1
        )
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Approve", "approve"),
            target_object=SemanticComponent("Object", "Token", "0xToken"),
            context=[]
        )
        
        iterations = 500
        start = time.time()
        
        for _ in range(iterations):
            RiskEngine.assess(ir, structure)
        
        elapsed = time.time() - start
        avg_time = elapsed / iterations * 1000  # ms
        
        print(f"\nRisk assessment performance: {avg_time:.3f}ms per call ({iterations} iterations)")
        self.assertLess(avg_time, 20)  # Should be under 20ms per call


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_empty_inputs(self):
        """Test handling of empty inputs"""
        self.assertEqual(TransactionDecoder.decode(""), {})
        self.assertEqual(TransactionDecoder.decode(None), {})
        
        ir = InputAdapter.adapt("")
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        ir = InputAdapter.adapt("{invalid json}")
        # Should treat as personal sign message
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)

    def test_very_long_calldata(self):
        """Test handling of very long calldata"""
        # Multicall with many nested calls
        calldata = "0xac9650d8" + "0" * 10000
        result = TransactionDecoder.decode(calldata)
        # Should not crash
        self.assertIsInstance(result, dict)

    def test_unicode_message(self):
        """Test handling of unicode messages"""
        ir = InputAdapter.adapt("Hello 世界 🌍")
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)
        self.assertIn("Hello", str(ir.params))

    def test_nested_eip712(self):
        """Test deeply nested EIP-712 structures"""
        data = {
            "types": {
                "EIP712Domain": [{"name": "name", "type": "string"}],
                "Outer": [{"name": "inner", "type": "Inner"}],
                "Inner": [{"name": "value", "type": "uint256"}]
            },
            "domain": {"name": "Test"},
            "primaryType": "Outer",
            "message": {"inner": {"value": 123}}
        }
        ir = InputAdapter.adapt(data)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SIGN_TYPED_DATA_V4)
        # Check flattened params
        self.assertIn("inner.value", ir.params)


class TestInterpreterPermissionScope(unittest.TestCase):
    """Test permission scope inference in Interpreter"""

    def setUp(self):
        self.interpreter = Interpreter()
        self.base_ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SIGN_TYPED_DATA_V4,
            raw_data={},
            chain_id=1
        )

    def _make_structure(self, action_type: str, context: list[SemanticComponent]) -> SemanticStructure:
        return SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Test", action_type),
            target_object=SemanticComponent("Object", "Contract", "0xContract"),
            context=context
        )

    def test_expired_deadline_is_not_permanent(self):
        """Expired deadlines should not be treated as permanent."""
        past_deadline = int(time.time()) - 60
        structure = self._make_structure(
            "authorization",
            [
                SemanticComponent("Context", "Amount", "1000"),
                SemanticComponent("Context", "Deadline", str(past_deadline)),
            ],
        )

        scope = self.interpreter._infer_permission_level(structure, self.base_ir)
        self.assertEqual(scope, "specific_amount_time_limited")

    def test_deadline_with_no_amount_is_time_limited(self):
        """Deadline without amount should be time-limited for authorization."""
        future_deadline = int(time.time()) + 600
        structure = self._make_structure(
            "authorization",
            [
                SemanticComponent("Context", "Deadline", str(future_deadline)),
            ],
        )

        scope = self.interpreter._infer_permission_level(structure, self.base_ir)
        self.assertEqual(scope, "time_limited")


class TestTextHighlighter(unittest.TestCase):
    """Test TextHighlighter escaping and highlighting"""

    def test_html_is_escaped(self):
        """Ensure raw HTML is escaped to prevent injection."""
        text = '<img src=x onerror=alert(1)> Please approve'
        highlighted = TextHighlighter.highlight_keywords(text)

        self.assertIn("&lt;img", highlighted)
        self.assertNotIn("<img", highlighted)

    def test_highlight_still_applies(self):
        """Ensure keyword highlighting still works after escaping."""
        text = "Approve transfer of 1 ETH"
        highlighted = TextHighlighter.highlight_keywords(text)

        self.assertIn('class="action-keyword"', highlighted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
