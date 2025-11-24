import json
import re
from typing import Any, Dict, Union, Optional
from .definitions import IntermediateRepresentation, SignatureType
from .validators import InputValidator
from ..processing.transaction_decoder import TransactionDecoder

class InputAdapter:
    """
    Adapts raw input data into a unified Intermediate Representation (IR).
    """
    
    # Regex patterns from legacy SignatureClassifier
    HEX_PATTERNS = {
        "address": re.compile(r'^0x[a-fA-F0-9]{40}$'),
        "hash": re.compile(r'^0x[a-fA-F0-9]{64}$'),
        "signature": re.compile(r'^0x[a-fA-F0-9]{130}$'),
        "hex_data": re.compile(r'^0x[a-fA-F0-9]+$')
    }

    @staticmethod
    def adapt(data: Union[str, Dict[str, Any]], origin: Optional[str] = None) -> IntermediateRepresentation:
        """
        Main entry point to convert raw data to IR.
        
        Args:
            data: Raw signature data (string or dict)
            origin: DApp origin URL (optional, from raw_request.origin)
        
        Returns:
            IntermediateRepresentation with normalized data
        """
        # 1. Normalize input to dict if possible
        normalized_data = InputAdapter._normalize_input(data)
        
        # 2. Detect type
        sig_type = InputAdapter._detect_type(normalized_data)
        
        # 3. Construct IR based on type
        if sig_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            ir = InputAdapter._adapt_eip712(normalized_data, origin)
        elif sig_type == SignatureType.ETH_SEND_TRANSACTION:
            ir = InputAdapter._adapt_transaction(normalized_data)
        elif sig_type == SignatureType.PERSONAL_SIGN:
            ir = InputAdapter._adapt_personal_sign(normalized_data)
        elif sig_type == SignatureType.ETH_SIGN:
            ir = InputAdapter._adapt_eth_sign(normalized_data)
        else:
            ir = IntermediateRepresentation(
                signature_type=SignatureType.UNKNOWN,
                raw_data=data,
                params={"error": "Unknown signature format"}
            )
        
        # 4. Set DApp origin if provided (for all types)
        if origin:
            ir.dapp_url = origin
        
        return ir

    @staticmethod
    def _normalize_input(data: Union[str, Dict[str, Any]]) -> Any:
        if isinstance(data, str):
            data = data.strip()
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data

    @staticmethod
    def _detect_type(data: Any) -> SignatureType:
        if isinstance(data, dict):
            if InputValidator.validate_eip712(data):
                return SignatureType.ETH_SIGN_TYPED_DATA_V4
            if InputValidator.validate_transaction(data):
                # Heuristic: if it looks like a tx
                if "to" in data and ("value" in data or "data" in data):
                    return SignatureType.ETH_SEND_TRANSACTION
                # Fallback for weaker matches
                tx_fields = ["gas", "gasPrice", "nonce", "chainId"]
                if any(f in data for f in tx_fields) and "to" in data:
                     return SignatureType.ETH_SEND_TRANSACTION
            
            if "message" in data:
                 return SignatureType.PERSONAL_SIGN

        if isinstance(data, str):
            if data.startswith("0x"):
                # Enhanced detection using regex
                if InputAdapter.HEX_PATTERNS["signature"].match(data):
                    return SignatureType.ETH_SIGN
                if InputAdapter.HEX_PATTERNS["hash"].match(data):
                    return SignatureType.ETH_SIGN
                if InputAdapter.HEX_PATTERNS["address"].match(data):
                    return SignatureType.PERSONAL_SIGN
                
                # Long hex string fallback
                if len(data) > 130: 
                     return SignatureType.PERSONAL_SIGN # Likely hex message
            return SignatureType.PERSONAL_SIGN # Default text

        return SignatureType.UNKNOWN

    @staticmethod
    def _adapt_eip712(data: Dict[str, Any], origin: Optional[str] = None) -> IntermediateRepresentation:
        domain = data.get("domain", {})
        
        # Extract chain_id safely
        chain_id = domain.get("chainId")
        if isinstance(chain_id, str) and chain_id.startswith("0x"):
            try:
                chain_id = int(chain_id, 16)
            except ValueError:
                pass
        elif isinstance(chain_id, str) and chain_id.isdigit():
             chain_id = int(chain_id)

        ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SIGN_TYPED_DATA_V4,
            raw_data=data,
            chain_id=chain_id,
            contract=domain.get("verifyingContract"),
            params=data.get("message", {}),
            metadata={
                "primaryType": data.get("primaryType"),
                "domain": domain,
                "types": data.get("types")
            }
        )
        
        # Try to extract origin from domain.name if not provided
        if not origin and domain.get("name"):
            # Domain name might contain protocol info, but not full URL
            # In real wallet, origin comes from browser context
            pass
        
        return ir

    @staticmethod
    def _adapt_transaction(data: Dict[str, Any]) -> IntermediateRepresentation:
        # Decode chain_id
        chain_id = data.get("chainId")
        if chain_id:
            if isinstance(chain_id, str) and chain_id.startswith("0x"):
                chain_id = int(chain_id, 16)
            elif isinstance(chain_id, str):
                chain_id = int(chain_id)

        # Base params
        params = {
            "calldata": data.get("data"),
            "gas": data.get("gas"),
            "nonce": data.get("nonce")
        }

        # ABI decoding
        decoded_call = TransactionDecoder.decode(data.get("data"))
        if decoded_call:
            params["decoded_parameters"] = decoded_call.get("parameters")

        assets = TransactionDecoder.infer_assets(decoded_call, data.get("to"), data.get("value"))

        return IntermediateRepresentation(
            signature_type=SignatureType.ETH_SEND_TRANSACTION,
            raw_data=data,
            chain_id=chain_id,
            sender=data.get("from"),
            contract=data.get("to"),
            value=InputAdapter._normalize_numeric_value(data.get("value", "0")),
            params=params,
            decoded_call=decoded_call or {},
            assets=assets
        )

    @staticmethod
    def _adapt_personal_sign(data: Any) -> IntermediateRepresentation:
        msg_content = data
        if isinstance(data, dict):
            msg_content = data.get("message")
        
        return IntermediateRepresentation(
            signature_type=SignatureType.PERSONAL_SIGN,
            raw_data=data,
            params={"message": msg_content}
        )

    @staticmethod
    def _adapt_eth_sign(data: Any) -> IntermediateRepresentation:
        return IntermediateRepresentation(
            signature_type=SignatureType.ETH_SIGN,
            raw_data=data,
            params={"raw": data}
        )

    @staticmethod
    def _normalize_numeric_value(value: Any) -> str:
        normalized = TransactionDecoder._normalize_int(value)
        if normalized is None:
            return str(value)
        return str(normalized)
