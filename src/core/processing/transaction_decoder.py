from __future__ import annotations

from typing import Dict, Any, List, Optional
import eth_abi
from eth_utils import to_hex, to_checksum_address

from .knowledge_base import KnowledgeBase


class TransactionDecoder:
    """
    Lightweight ABI decoder using eth-abi for robust decoding.
    """

    @staticmethod
    def decode(calldata: Optional[str]) -> Dict[str, Any]:
        if not calldata or len(calldata) < 10 or not calldata.startswith("0x"):
            return {}

        selector = calldata[:10].lower()
        definition = KnowledgeBase.get_function_definition(selector)
        if not definition:
            return {"function_selector": selector}

        try:
            # Get types from definition
            param_types = definition.get("params", [])
            
            # Handle "tuple" placeholder in JSON which eth-abi doesn't understand directly
            # We attempt to extract the real structure from the signature string
            if "tuple" in param_types:
                extracted_types = TransactionDecoder._extract_types_from_signature(definition["signature"])
                if extracted_types:
                    param_types = extracted_types

            # Decode using eth-abi
            # calldata[10:] is the data part
            data_bytes = bytes.fromhex(calldata[10:])
            decoded_values = eth_abi.decode(param_types, data_bytes)

            # Map values to parameter names
            parameters = {}
            param_names = definition.get("param_names", [])
            
            for i, value in enumerate(decoded_values):
                name = param_names[i] if i < len(param_names) else f"param_{i}"
                parameters[name] = TransactionDecoder._normalize_decoded_value(value, param_types[i] if i < len(param_types) else None)

            return {
                "function_selector": selector,
                "function_name": definition["name"],
                "signature": definition["signature"],
                "category": definition.get("category"),
                "parameters": parameters,
            }
        except Exception as e:
            # Log error and return minimal info
            # In a real app we might want to log this properly
            return {
                "function_selector": selector,
                "function_name": definition.get("name"),
                "error": f"Decoding failed: {str(e)}"
            }

    @staticmethod
    def infer_assets(decoded: Dict[str, Any], contract_address: Optional[str], native_value: Any) -> List[Dict[str, Any]]:
        assets: List[Dict[str, Any]] = []

        native_amount = TransactionDecoder._normalize_int(native_value)
        if native_amount and native_amount > 0:
            assets.append({
                "type": "native",
                "symbol": "ETH",
                "amount_wei": native_amount,
                "amount_formatted": TransactionDecoder._format_amount(native_amount, 18),
                "direction": "outgoing"
            })

        if not decoded or "parameters" not in decoded:
            return assets

        category = decoded.get("category")
        params = decoded.get("parameters", {})
        token_meta = KnowledgeBase.get_token_metadata(contract_address)
        decimals = token_meta.get("decimals", 18)
        symbol = token_meta.get("symbol") or "TOKEN"

        if category in {"erc20_transfer", "erc20_transfer_from"}:
            # Handle different parameter names for transfer vs transferFrom
            amount = None
            if "amount" in params:
                amount = TransactionDecoder._normalize_int(params["amount"])
            elif "value" in params: # Some variants
                amount = TransactionDecoder._normalize_int(params["value"])
            
            if amount:
                assets.append({
                    "type": "token",
                    "symbol": symbol,
                    "token_address": contract_address,
                    "amount_raw": amount,
                    "amount_formatted": TransactionDecoder._format_amount(amount, decimals),
                    "direction": "outgoing"
                })
        elif category == "erc20_approve":
            amount = TransactionDecoder._normalize_int(params.get("amount") or params.get("value"))
            if amount:
                assets.append({
                    "type": "approval",
                    "symbol": symbol,
                    "token_address": contract_address,
                    "amount_raw": amount,
                    "amount_formatted": TransactionDecoder._format_amount(amount, decimals),
                    "direction": "authorization"
                })

        return assets

    @staticmethod
    def _extract_types_from_signature(signature: str) -> List[str]:
        """
        Extract parameter types from a function signature string.
        Handles basic nested tuples.
        Example: "func(uint256,(address,uint256))" -> ["uint256", "(address,uint256)"]
        """
        start = signature.find('(')
        end = signature.rfind(')')
        if start == -1 or end == -1:
            return []
        
        content = signature[start+1:end]
        if not content:
            return []
            
        types = []
        current = []
        depth = 0
        for char in content:
            if char == ',' and depth == 0:
                types.append("".join(current).strip())
                current = []
            else:
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                current.append(char)
        
        if current:
            types.append("".join(current).strip())
            
        return types

    @staticmethod
    def _normalize_decoded_value(value: Any, type_str: Optional[str] = None) -> Any:
        """Normalize decoded values to JSON-serializable format."""
        if isinstance(value, bytes):
            return to_hex(value)
        
        if isinstance(value, (list, tuple)):
            return [TransactionDecoder._normalize_decoded_value(v) for v in value]
        
        if isinstance(value, str) and len(value) == 42 and value.startswith("0x"):
             try:
                 return to_checksum_address(value)
             except:
                 return value
                 
        # If the type was explicitly address, try to checksum it
        if type_str == 'address' and isinstance(value, str):
             try:
                 return to_checksum_address(value)
             except:
                 return value

        return value

    @staticmethod
    def _normalize_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                if value.startswith("0x"):
                    return int(value, 16)
                return int(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _format_amount(amount: int, decimals: int) -> str:
        try:
            scaled = amount / (10 ** decimals)
            if scaled >= 1:
                return f"{scaled:,.4f}"
            return f"{scaled:.6f}".rstrip("0").rstrip(".")
        except Exception:
            return str(amount)
