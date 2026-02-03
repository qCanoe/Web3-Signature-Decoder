import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.processing.transaction_decoder import TransactionDecoder
from src.core.processing.risk import RiskEngine
from src.core.input.definitions import IntermediateRepresentation, SignatureType
from src.core.processing.structure import SemanticStructure, SemanticComponent, StructureParser
from src.core.input.adapter import InputAdapter
from src.core.processing.classifier import Classifier

class TestCoreProcessing(unittest.TestCase):
    
    def test_transaction_decoder(self):
        print("\nTesting TransactionDecoder...")
        
        # 1. ERC20 Transfer
        # transfer(address,uint256) -> 0xa9059cbb
        calldata = "0xa9059cbb000000000000000000000000123456789012345678901234567890123456789000000000000000000000000000000000000000000000000000000000000003e8"
        decoded = TransactionDecoder.decode(calldata)
        self.assertEqual(decoded['function_name'], 'transfer')
        self.assertEqual(decoded['parameters']['to'], '0x1234567890123456789012345678901234567890')
        self.assertEqual(decoded['parameters']['amount'], 1000)

        # 2. ERC20 Approve (Infinite)
        # approve(address,uint256) -> 0x095ea7b3
        calldata = "0x095ea7b30000000000000000000000001234567890123456789012345678901234567890ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        decoded = TransactionDecoder.decode(calldata)
        self.assertEqual(decoded['function_name'], 'approve')
        self.assertEqual(decoded['parameters']['amount'], 2**256 - 1)

        # 3. Unknown Selector
        calldata = "0x12345678" + "0" * 64
        decoded = TransactionDecoder.decode(calldata)
        self.assertEqual(decoded.get('function_selector'), '0x12345678')
        self.assertIsNone(decoded.get('function_name'))

    def test_input_adapter(self):
        print("\nTesting InputAdapter...")
        
        # 1. Dict Input (EIP-712)
        data_dict = {
            "types": {"EIP712Domain": []}, 
            "domain": {}, 
            "primaryType": "EIP712Domain", 
            "message": {}
        }
        ir = InputAdapter.adapt(data_dict)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SIGN_TYPED_DATA_V4)
        
        # 2. String Input (JSON)
        data_str = '{"types": {"EIP712Domain": []}, "domain": {}, "primaryType": "EIP712Domain", "message": {}}'
        ir = InputAdapter.adapt(data_str)
        self.assertEqual(ir.signature_type, SignatureType.ETH_SIGN_TYPED_DATA_V4)
        
        # 3. Personal Sign
        data_msg = "Hello World"
        ir = InputAdapter.adapt(data_msg)
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)
        
        # 4. Hex Message (should be Personal Sign if not strict structure)
        data_hex = "0x1234"
        ir = InputAdapter.adapt(data_hex)
        self.assertEqual(ir.signature_type, SignatureType.PERSONAL_SIGN)

        # 5. Invalid chain ID string should not crash
        data_invalid_chain = {
            "to": "0x1234567890123456789012345678901234567890",
            "value": "1000",
            "data": "0x",
            "chainId": "not-a-number"
        }
        ir = InputAdapter.adapt(data_invalid_chain)
        self.assertIsNone(ir.chain_id)

        # 6. EIP-712 array flatten should include indexed fields
        data_array = {
            "types": {
                "EIP712Domain": [{"name": "name", "type": "string"}],
                "OfferItem": [
                    {"name": "token", "type": "address"},
                    {"name": "startAmount", "type": "uint256"}
                ],
                "OrderComponents": [
                    {"name": "offer", "type": "OfferItem[]"}
                ]
            },
            "domain": {"name": "Test"},
            "primaryType": "OrderComponents",
            "message": {
                "offer": [
                    {"token": "0x0000000000000000000000000000000000000001", "startAmount": "1"}
                ]
            }
        }
        ir = InputAdapter.adapt(data_array)
        self.assertIn("offer[0].token", ir.params)
        self.assertIn("offer[0].startAmount", ir.params)

    def test_structure_parser_nested_context(self):
        print("\nTesting StructureParser nested context...")
        
        data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "PermitSingle": [
                    {"name": "details", "type": "PermitDetails"},
                    {"name": "spender", "type": "address"},
                    {"name": "sigDeadline", "type": "uint256"}
                ],
                "PermitDetails": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"}
                ]
            },
            "primaryType": "PermitSingle",
            "domain": {
                "name": "Permit2",
                "chainId": 1,
                "verifyingContract": "0x000000000022D473030F116dDEE9F6B43aC78BA3"
            },
            "message": {
                "details": {
                    "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "amount": "1000000000",
                    "expiration": 1705399200,
                    "nonce": 0
                },
                "spender": "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
                "sigDeadline": 1705315800
            }
        }
        
        ir = InputAdapter.adapt(data)
        ir = Classifier.classify(ir)
        structure = StructureParser.parse(ir)
        
        self.assertTrue(any(c.raw_value == data["message"]["spender"] for c in structure.context))
        self.assertTrue(any(str(c.raw_value) == "1000000000" for c in structure.context))

    def test_risk_engine(self):
        print("\nTesting RiskEngine...")
        
        # Mock IR
        ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SEND_TRANSACTION,
            raw_data={},
            chain_id=1
        )
        
        # 1. Phishing Detection
        structure = SemanticStructure(
            actor=SemanticComponent("Actor", "User", "0xUser"),
            action=SemanticComponent("Action", "Urgent Action", "urgent_action"),
            target_object=SemanticComponent("Object", "Contract", "0xContract"),
            context=[]
        )
        ir.params = {"message": "Please sign urgently to verify"}
        
        risks = RiskEngine.assess(ir, structure)
        self.assertTrue(any("Phishing" in r for r in risks.reasons))
        
        # 2. High Risk Param (Infinite Allowance)
        structure.context.append(SemanticComponent("Context", "Infinite Allowance", "MAX", risk_factor="high"))
        risks = RiskEngine.assess(ir, structure)
        self.assertEqual(risks.level, "high")
        
        # 3. Known Contract (Low Risk)
        # Uniswap V3 Router on Mainnet
        ir.contract = "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45" 
        risks = RiskEngine.assess(ir, structure)
        # Should have a reason about known protocol
        self.assertTrue(any("Known protocol" in r or "Uniswap" in r for r in risks.reasons))

if __name__ == "__main__":
    unittest.main()
