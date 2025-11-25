from typing import Optional
import re
from ..input.definitions import IntermediateRepresentation, SignatureType
from .knowledge_base import KnowledgeBase
from .extractors import ParameterExtractor

class Classifier:
    """
    Classifies the intent of the signature request.
    Determines 'what kind of operation' this is (e.g. Swap, Approve, Login).
    """

    @staticmethod
    def classify(ir: IntermediateRepresentation) -> IntermediateRepresentation:
        """
        Enriches the IR with specific action_type classification.
        """
        
        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            Classifier._classify_eip712(ir)
        elif ir.signature_type == SignatureType.ETH_SEND_TRANSACTION:
            Classifier._classify_transaction(ir)
        elif ir.signature_type == SignatureType.PERSONAL_SIGN:
            Classifier._classify_personal_sign(ir)
        elif ir.signature_type == SignatureType.ETH_SIGN:
            Classifier._classify_eth_sign(ir)
        elif ir.signature_type == SignatureType.UNKNOWN:
            Classifier._classify_unknown(ir)
        
        # Ensure action_type is always set
        if not ir.action_type:
            ir.action_type = "unknown_operation"
        
        return ir

    @staticmethod
    def _classify_eip712(ir: IntermediateRepresentation):
        primary_type = ir.metadata.get("primaryType", "")
        
        # 1. Check Knowledge Base
        category = KnowledgeBase.get_eip712_category(primary_type)
        if category != "unknown":
            ir.action_type = category
            # Additional checks for specific categories
            if category in ["bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"]:
                Classifier._classify_bridge(ir)
            elif category in ["governance_delegation", "delegation"]:
                Classifier._classify_delegation(ir)
            return

        # 2. Heuristics based on fields
        params = ir.params
        keys = [k.lower() for k in params.keys()]
        
        # Check for bridge patterns
        if Classifier._classify_bridge(ir):
            return
        
        # Check for delegation patterns
        if Classifier._classify_delegation(ir):
            return
        
        # Check for cross-contract patterns
        if Classifier._classify_cross_contract(ir):
            return
        
        if "spender" in keys and ("value" in keys or "amount" in keys):
            ir.action_type = "approve"
        elif "offer" in keys and "consideration" in keys:
            ir.action_type = "marketplace_listing"
        elif "proposalid" in keys or "vote" in keys:
            ir.action_type = "governance"
        elif "nonce" in keys and "deadline" in keys and len(keys) < 5:
            # Simple nonce/deadline structure often implies auth or permit
            ir.action_type = "authorization"
        else:
            ir.action_type = "structured_data_sign"
    
    @staticmethod
    def _classify_bridge(ir: IntermediateRepresentation) -> bool:
        """
        Classify bridge/cross-chain operations.
        
        Returns:
            True if classified as bridge operation
        """
        params = ir.params
        keys = [k.lower() for k in params.keys()]
        
        # Bridge indicators
        bridge_keywords = [
            "destinationchain", "targetchain", "sourcechain", "chainid",
            "lock", "unlock", "redeem", "mint", "burn", "bridge",
            "relayer", "wormhole", "multichain", "layerzero"
        ]
        
        # Check contract name
        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract or "")
        if contract_name:
            contract_lower = contract_name.lower()
            if any(kw in contract_lower for kw in ["bridge", "wormhole", "multichain", "layerzero", "across"]):
                ir.action_type = "bridge"
                return True
        
        # Check domain name
        domain = ir.metadata.get("domain", {})
        domain_name = domain.get("name", "").lower()
        if any(kw in domain_name for kw in ["bridge", "cross-chain", "multichain"]):
            ir.action_type = "bridge"
            return True
        
        # Check field names
        if any(kw in keys for kw in bridge_keywords):
            if "lock" in keys or "deposit" in keys:
                ir.action_type = "bridge_lock"
            elif "unlock" in keys or "withdraw" in keys:
                ir.action_type = "bridge_unlock"
            elif "redeem" in keys or "mint" in keys:
                ir.action_type = "bridge_redeem"
            else:
                ir.action_type = "bridge"
            return True
        
        return False
    
    @staticmethod
    def _classify_delegation(ir: IntermediateRepresentation) -> bool:
        """
        Classify delegation operations (voting power delegation).
        
        Returns:
            True if classified as delegation operation
        """
        params = ir.params
        keys = [k.lower() for k in params.keys()]
        primary_type = ir.metadata.get("primaryType", "").lower()
        
        # Delegation keywords
        delegation_keywords = ["delegate", "delegation", "delegatee", "delegator"]
        
        # Check primary type
        if any(kw in primary_type for kw in delegation_keywords):
            ir.action_type = "governance_delegation"
            return True
        
        # Check field names
        if any(kw in keys for kw in delegation_keywords):
            ir.action_type = "governance_delegation"
            return True
        
        # Check function name in decoded call
        decoded_call = ir.decoded_call or {}
        func_name = decoded_call.get("function_name", "").lower()
        if "delegate" in func_name:
            ir.action_type = "governance_delegation"
            return True
        
        return False
    
    @staticmethod
    def _classify_cross_contract(ir: IntermediateRepresentation) -> bool:
        """
        Classify cross-contract operations (operations that involve multiple contracts).
        
        Returns:
            True if classified as cross-contract operation
        """
        # Check if transaction involves router or aggregator patterns
        decoded_call = ir.decoded_call or {}
        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract or "")
        
        if contract_name:
            contract_lower = contract_name.lower()
            # Router contracts often perform cross-contract operations
            if "router" in contract_lower or "aggregator" in contract_lower:
                # Check if it's a swap or complex operation
                func_name = decoded_call.get("function_name", "").lower()
                if "swap" in func_name or "multicall" in func_name or "batch" in func_name:
                    ir.action_type = "cross_contract_interaction"
                    return True
        
        # Check for multicall patterns in data
        calldata = ir.params.get("calldata", "")
        if calldata and len(calldata) > 10:
            # Multicall selector: 0xac9650d8
            if calldata.startswith("0xac9650d8"):
                ir.action_type = "cross_contract_interaction"
                return True
        
        return False

    @staticmethod
    def _classify_transaction(ir: IntermediateRepresentation):
        decoded_call = ir.decoded_call or ir.metadata.get("decoded_call", {})
        category_hint = decoded_call.get("category")
        category_to_action = {
            "erc20_transfer": "transfer_asset",
            "erc20_transfer_from": "transfer_asset",
            "erc20_approve": "approve",
            "erc20_permit": "authorization",
            "permit2": "authorization",
            "erc721_transfer": "nft_transfer",
            "defi_swap": "defi_swap",
            "contract_withdraw": "withdraw",
        }

        if category_hint and category_hint in category_to_action:
            ir.action_type = category_to_action[category_hint]
            return

        calldata = ir.params.get("calldata")
        if not calldata or calldata == "0x":
            # Simple ETH transfer
            if ir.value and ir.value != "0":
                ir.action_type = "transfer_asset"
            else:
                ir.action_type = "contract_interaction"
            return

        # Check selector
        if len(calldata) >= 10:
            selector = calldata[:10]
            func_name = KnowledgeBase.get_function_name(selector)
            if func_name:
                if "approve" in func_name:
                    ir.action_type = "approve"
                elif "transfer" in func_name:
                    ir.action_type = "transfer_asset"
                else:
                    ir.action_type = "contract_call"
                return

        ir.action_type = "contract_interaction"

    @staticmethod
    def _classify_personal_sign(ir: IntermediateRepresentation):
        # Extract raw message
        raw_msg = ir.params.get("message", "")
        if not isinstance(raw_msg, str):
            raw_msg = str(raw_msg)
            
        # Clean it (decode hex if needed)
        msg = ParameterExtractor._clean_message(raw_msg)
        msg_lower = msg.lower()
        
        # Update IR param with cleaned message for downstream usage
        ir.params["message_cleaned"] = msg

        # Match against patterns in KnowledgeBase
        best_match = "sign_message" # Default
        max_score = 0

        for category, rules in KnowledgeBase.PERSONAL_SIGN_PATTERNS.items():
            score = 0
            # Keyword match
            for keyword in rules["keywords"]:
                if keyword in msg_lower:
                    score += 1
            
            # Regex pattern match
            for pattern in rules["patterns"]:
                if re.search(pattern, msg, re.IGNORECASE):
                    score += 2 # Patterns are stronger indicators
            
            if score > max_score:
                max_score = score
                best_match = category
        
        # Threshold
        if max_score > 0:
            ir.action_type = best_match
        else:
            # Fallback heuristics
            if "nonce" in msg_lower:
                ir.action_type = "authentication"
            else:
                ir.action_type = "sign_message"
    
    @staticmethod
    def _classify_eth_sign(ir: IntermediateRepresentation):
        """
        Classify ETH_SIGN type signatures (legacy hash signing).
        """
        # ETH_SIGN is typically used for signing raw message hashes
        # This is less common and often indicates lower-level operations
        raw_data = ir.params.get("raw", "")
        if isinstance(raw_data, str) and raw_data.startswith("0x"):
            # Check if it looks like a hash
            if len(raw_data) == 66:  # 32 bytes = 64 hex chars + 0x
                ir.action_type = "sign_hash"
            else:
                ir.action_type = "sign_raw_data"
        else:
            ir.action_type = "sign_hash"
    
    @staticmethod
    def _classify_unknown(ir: IntermediateRepresentation):
        """
        Classify unknown signature types.
        Attempts to infer type from raw data structure.
        """
        raw_data = ir.raw_data
        
        # Try to detect format from raw_data
        if isinstance(raw_data, dict):
            # Check if it might be EIP712-like
            if "domain" in raw_data and "message" in raw_data:
                # Try EIP712 classification
                ir.metadata["primaryType"] = raw_data.get("primaryType", "")
                Classifier._classify_eip712(ir)
                return
            # Check if it might be transaction-like
            if "to" in raw_data and ("value" in raw_data or "data" in raw_data):
                Classifier._classify_transaction(ir)
                return
        
        # Default fallback
        ir.action_type = "unknown_operation"
