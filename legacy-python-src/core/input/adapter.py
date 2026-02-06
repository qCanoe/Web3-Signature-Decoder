import json
import re
from typing import Any, Dict, Union, Optional
from .definitions import IntermediateRepresentation, SignatureType
from .validators import InputValidator
from ..processing.transaction_decoder import TransactionDecoder
from ..config import Config
from ..utils.logger import Logger

logger = Logger.get_logger(__name__)

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
            except ValueError as error:
                logger.debug(f"Invalid hex chainId: {error}")
        elif isinstance(chain_id, str) and chain_id.isdigit():
             chain_id = int(chain_id)

        # Parse nested EIP-712 types recursively
        types = data.get("types", {})
        primary_type = data.get("primaryType", "")
        message = data.get("message", {})

        schema_validation = {"valid": True, "errors": []}
        if Config.EIP712_VALIDATION.get("validate_nested_types", True):
            is_valid, errors = InputValidator.validate_eip712_schema_integrity(data)
            schema_validation = {"valid": is_valid, "errors": errors}
            if not is_valid:
                if Config.EIP712_VALIDATION.get("strict_mode") and not Config.EIP712_VALIDATION.get("warn_only", True):
                    raise ValueError(f"EIP-712 schema validation failed: {errors}")
                logger.warning(f"EIP-712 schema integrity warning: {errors}")
        
        # Flatten nested structures while preserving hierarchy
        flattened_params = InputAdapter._flatten_eip712_message(message, primary_type, types)
        
        ir = IntermediateRepresentation(
            signature_type=SignatureType.ETH_SIGN_TYPED_DATA_V4,
            raw_data=data,
            chain_id=chain_id,
            contract=domain.get("verifyingContract"),
            params=flattened_params,
            metadata={
                "primaryType": primary_type,
                "domain": domain,
                "types": types,
                "original_message": message,  # Preserve original structure
                "schema_validation": schema_validation,
            }
        )
        
        # Try to extract origin from domain.name if not provided
        if not origin and domain.get("name"):
            # Domain name might contain protocol info, but not full URL
            # In real wallet, origin comes from browser context
            logger.debug("Origin not provided; keeping as None for EIP-712")
        
        return ir
    
    @staticmethod
    def _flatten_eip712_message(message: Dict[str, Any], type_name: str, types: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Recursively flatten nested EIP-712 message structures.
        
        Args:
            message: The message dictionary to flatten
            type_name: The type name of the current message
            types: The types dictionary containing type definitions
            prefix: Prefix for flattened keys (for nested structures)
            
        Returns:
            Flattened dictionary with all nested fields
        """
        flattened: Dict[str, Any] = {}
        
        if type_name not in types:
            # If type not found, just return the message as-is
            return {f"{prefix}{k}" if prefix else k: v for k, v in message.items()}
        
        type_def = types[type_name]
        if not isinstance(type_def, list):
            return flattened
        
        for field_def in type_def:
            if not isinstance(field_def, dict):
                continue
            
            field_name = field_def.get("name")
            field_type = field_def.get("type")
            
            if not field_name or field_name not in message:
                continue
            
            field_value = message[field_name]
            field_key = f"{prefix}{field_name}" if prefix else field_name
            
            # Handle array types (e.g. Type[], uint256[])
            is_array = False
            base_type = field_type
            if isinstance(field_type, str) and "[" in field_type:
                base_type = field_type.split("[", 1)[0]
                is_array = True

            if is_array and isinstance(field_value, list):
                # Flatten each array element
                for idx, item in enumerate(field_value):
                    item_key = f"{field_key}[{idx}]"
                    if base_type in types and isinstance(item, dict):
                        nested_flattened = InputAdapter._flatten_eip712_message(
                            item, base_type, types, prefix=f"{item_key}."
                        )
                        flattened.update(nested_flattened)
                    else:
                        flattened[item_key] = item
                continue

            # Check if field_type is a custom type (nested structure)
            if field_type in types and isinstance(field_value, dict):
                # Recursively flatten nested structure
                nested_flattened = InputAdapter._flatten_eip712_message(
                    field_value, field_type, types, prefix=f"{field_key}."
                )
                flattened.update(nested_flattened)
            else:
                # Primitive type or untyped structure, add directly
                flattened[field_key] = field_value
        
        return flattened

    @staticmethod
    def _adapt_transaction(data: Dict[str, Any]) -> IntermediateRepresentation:
        # Decode chain_id
        chain_id = data.get("chainId")
        if chain_id:
            if isinstance(chain_id, str) and chain_id.startswith("0x"):
                try:
                    chain_id = int(chain_id, 16)
                except ValueError:
                    chain_id = None
            elif isinstance(chain_id, str):
                try:
                    chain_id = int(chain_id)
                except ValueError:
                    chain_id = None

        # Base params
        params = {
            "calldata": data.get("data"),
            "gas": data.get("gas"),
            "nonce": data.get("nonce")
        }

        # ABI decoding with chain context for dynamic fallback
        calldata = data.get("data")
        contract_to = data.get("to")
        
        # Check if it's a multicall transaction
        if TransactionDecoder.is_multicall(calldata):
            decoded_call = TransactionDecoder.decode_multicall(
                calldata,
                chain_id=chain_id,
                contract_address=contract_to
            )
        else:
            decoded_call = TransactionDecoder.decode(
                calldata,
                chain_id=chain_id,
                contract_address=contract_to
            )
        
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
        
        # Parse EIP-191 prefix if present
        eip191_prefix = None
        actual_message = msg_content
        
        if isinstance(msg_content, str):
            # Check for EIP-191 standard prefix: \x19Ethereum Signed Message:\n{length}{message}
            if msg_content.startswith("\x19Ethereum Signed Message:\n"):
                eip191_prefix = "standard"
                # Extract the actual message (skip prefix + length)
                parts = msg_content.split("\n", 1)
                if len(parts) == 2:
                    try:
                        # First part after prefix is length
                        length_part = parts[0].replace("\x19Ethereum Signed Message:\n", "")
                        if length_part.isdigit():
                            actual_message = parts[1]
                    except Exception as error:
                        logger.debug(f"Failed to parse EIP-191 prefix length: {error}")
            elif "\x19" in msg_content:
                eip191_prefix = "custom"
        
        params = {
            "message": actual_message,
            "eip191_prefix": eip191_prefix
        }
        
        return IntermediateRepresentation(
            signature_type=SignatureType.PERSONAL_SIGN,
            raw_data=data,
            params=params
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
