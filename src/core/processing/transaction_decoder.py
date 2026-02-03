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
    def decode(calldata: Optional[str], chain_id: Optional[int] = None, contract_address: Optional[str] = None) -> Dict[str, Any]:
        if not calldata or len(calldata) < 10 or not calldata.startswith("0x"):
            return {}

        selector = calldata[:10].lower()
        
        # Try static lookup first, then fallback to dynamic
        definition = KnowledgeBase.get_function_definition(selector)
        if not definition:
            # Try with fallback (dynamic ABI fetching)
            definition = KnowledgeBase.get_function_definition_with_fallback(
                selector, chain_id, contract_address
            )
        
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

    # Pre-defined tuple structures for common DeFi functions
    KNOWN_TUPLE_STRUCTURES: Dict[str, List[str]] = {
        # Uniswap V3 SwapRouter
        "exactInputSingle": ["address", "address", "uint24", "address", "uint256", "uint256", "uint256", "uint160"],
        "exactInput": ["bytes", "address", "uint256", "uint256", "uint256"],
        "exactOutputSingle": ["address", "address", "uint24", "address", "uint256", "uint256", "uint256", "uint160"],
        "exactOutput": ["bytes", "address", "uint256", "uint256", "uint256"],
        # Uniswap V3 SwapRouter02 (no deadline in tuple)
        "exactInputSingle_v2": ["address", "address", "uint24", "address", "uint256", "uint256", "uint160"],
        "exactInput_v2": ["bytes", "address", "uint256", "uint256"],
        "exactOutputSingle_v2": ["address", "address", "uint24", "address", "uint256", "uint256", "uint160"],
        "exactOutput_v2": ["bytes", "address", "uint256", "uint256"],
        # Uniswap V3 Position Manager
        "mint": ["address", "address", "uint24", "int24", "int24", "uint256", "uint256", "uint256", "uint256", "address", "uint256"],
        "increaseLiquidity": ["uint256", "uint256", "uint256", "uint256", "uint256", "uint256"],
        "decreaseLiquidity": ["uint256", "uint128", "uint256", "uint256", "uint256"],
        "collect": ["uint256", "address", "uint128", "uint128"],
        # Permit2
        "PermitSingle": ["address", "uint160", "uint48", "uint48"],
        "PermitBatch": ["(address,uint160,uint48,uint48)[]", "address", "uint256"],
        "SignatureTransferDetails": ["address", "uint256"],
        "TokenPermissions": ["address", "uint256"],
    }
    
    @staticmethod
    def _extract_types_from_signature(signature: str) -> List[str]:
        """
        Extract parameter types from a function signature string.
        Handles complex nested tuples including arrays.
        Example: "func(uint256,(address,uint256)[])" -> ["uint256", "(address,uint256)[]"]
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
        bracket_depth = 0
        
        for char in content:
            if char == ',' and depth == 0 and bracket_depth == 0:
                type_str = "".join(current).strip()
                if type_str:
                    types.append(type_str)
                current = []
            else:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                elif char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
                current.append(char)
        
        if current:
            type_str = "".join(current).strip()
            if type_str:
                types.append(type_str)
            
        return types
    
    @staticmethod
    def _parse_tuple_type(type_str: str) -> Dict[str, Any]:
        """
        Parse a tuple type string into components.
        
        Args:
            type_str: Tuple type like "(address,uint256)" or "(address,uint256)[]"
            
        Returns:
            Dict with 'components' list and 'is_array' flag
        """
        is_array = type_str.endswith("[]")
        if is_array:
            type_str = type_str[:-2]
        
        # Check if it's a tuple
        if not type_str.startswith("(") or not type_str.endswith(")"):
            return {"type": type_str, "is_array": is_array}
        
        # Extract inner types
        inner = type_str[1:-1]
        components = TransactionDecoder._extract_types_from_signature(f"dummy({inner})")
        
        # Recursively parse nested tuples
        parsed_components = []
        for comp in components:
            if comp.startswith("("):
                parsed_components.append(TransactionDecoder._parse_tuple_type(comp))
            else:
                parsed_components.append({"type": comp})
        
        return {
            "type": "tuple",
            "components": parsed_components,
            "is_array": is_array
        }
    
    @staticmethod
    def _decode_tuple_value(
        value: Any,
        type_info: Dict[str, Any],
        param_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Decode a tuple value into a structured dictionary.
        
        Args:
            value: The decoded tuple value
            type_info: Parsed type information
            param_names: Optional parameter names for the tuple fields
            
        Returns:
            Structured dictionary with named fields
        """
        if type_info.get("is_array") and isinstance(value, (list, tuple)):
            return [
                TransactionDecoder._decode_tuple_value(v, {**type_info, "is_array": False}, param_names)
                for v in value
            ]
        
        if type_info.get("type") != "tuple":
            return TransactionDecoder._normalize_decoded_value(value, type_info.get("type"))
        
        components = type_info.get("components", [])
        if not isinstance(value, (list, tuple)):
            return value
        
        result = {}
        for i, (v, comp) in enumerate(zip(value, components)):
            name = param_names[i] if param_names and i < len(param_names) else f"field_{i}"
            
            if comp.get("type") == "tuple":
                result[name] = TransactionDecoder._decode_tuple_value(v, comp)
            else:
                result[name] = TransactionDecoder._normalize_decoded_value(v, comp.get("type"))
        
        return result
    
    @staticmethod
    def decode_with_tuple_expansion(
        calldata: str,
        chain_id: Optional[int] = None,
        contract_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decode calldata with full tuple expansion for complex structures.
        
        Args:
            calldata: Transaction calldata
            chain_id: Chain ID for context
            contract_address: Contract address for context
            
        Returns:
            Decoded transaction with expanded tuple fields
        """
        basic_decode = TransactionDecoder.decode(calldata, chain_id, contract_address)
        
        if not basic_decode or "error" in basic_decode:
            return basic_decode
        
        func_name = basic_decode.get("function_name", "")
        signature = basic_decode.get("signature", "")
        
        # Check if we have known tuple structure
        if func_name in TransactionDecoder.KNOWN_TUPLE_STRUCTURES:
            tuple_types = TransactionDecoder.KNOWN_TUPLE_STRUCTURES[func_name]
            
            # Get the definition with tuple info
            definition = KnowledgeBase.get_function_definition(basic_decode.get("function_selector"))
            if definition and definition.get("tuple_definition"):
                tuple_param_names = definition["tuple_definition"].get("params", [])
                
                # Re-decode with tuple expansion
                params = basic_decode.get("parameters", {})
                for param_key, param_value in params.items():
                    if isinstance(param_value, (list, tuple)) and len(param_value) == len(tuple_types):
                        # This looks like a tuple, expand it
                        expanded = {}
                        for i, (val, type_str) in enumerate(zip(param_value, tuple_types)):
                            field_name = tuple_param_names[i] if i < len(tuple_param_names) else f"field_{i}"
                            expanded[field_name] = TransactionDecoder._normalize_decoded_value(val, type_str)
                        params[param_key] = expanded
                
                basic_decode["parameters"] = params
                basic_decode["tuple_expanded"] = True
        
        return basic_decode

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
    
    # Known multicall selectors
    MULTICALL_SELECTORS = {
        "0xac9650d8",  # multicall(bytes[])
        "0x5ae401dc",  # multicall(uint256,bytes[])
        "0x1f0464d1",  # multicall(bytes32,bytes[])
        "0x8d80ff0a",  # multiSend(bytes) - Safe/Gnosis
    }
    
    # Universal Router command types
    UNIVERSAL_ROUTER_COMMANDS = {
        0x00: "V3_SWAP_EXACT_IN",
        0x01: "V3_SWAP_EXACT_OUT",
        0x02: "PERMIT2_TRANSFER_FROM",
        0x03: "PERMIT2_PERMIT_BATCH",
        0x04: "SWEEP",
        0x05: "TRANSFER",
        0x06: "PAY_PORTION",
        0x07: "COMMAND_PLACEHOLDER_07",
        0x08: "V2_SWAP_EXACT_IN",
        0x09: "V2_SWAP_EXACT_OUT",
        0x0a: "PERMIT2_PERMIT",
        0x0b: "WRAP_ETH",
        0x0c: "UNWRAP_WETH",
        0x0d: "PERMIT2_TRANSFER_FROM_BATCH",
        0x0e: "BALANCE_CHECK_ERC20",
        0x0f: "COMMAND_PLACEHOLDER_0F",
        0x10: "SEAPORT_V1_5",
        0x11: "LOOKS_RARE_V2",
        0x12: "NFTX",
        0x13: "CRYPTOPUNKS",
        0x14: "OWNER_CHECK_721",
        0x15: "OWNER_CHECK_1155",
        0x16: "SWEEP_ERC721",
        0x17: "X2Y2_721",
        0x18: "SUDOSWAP",
        0x19: "NFT20",
        0x1a: "X2Y2_1155",
        0x1b: "FOUNDATION",
        0x1c: "SWEEP_ERC1155",
        0x1d: "ELEMENT_MARKET",
        0x1e: "SEAPORT_V1_4",
        0x1f: "EXECUTE_SUB_PLAN",
    }
    
    @staticmethod
    def is_multicall(calldata: Optional[str]) -> bool:
        """Check if calldata is a multicall transaction."""
        if not calldata or len(calldata) < 10:
            return False
        selector = calldata[:10].lower()
        return selector in TransactionDecoder.MULTICALL_SELECTORS
    
    @staticmethod
    def decode_multicall(
        calldata: str,
        chain_id: Optional[int] = None,
        contract_address: Optional[str] = None,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Decode multicall transaction data recursively.
        
        Args:
            calldata: The transaction calldata
            chain_id: Chain ID for context
            contract_address: Contract address for context
            max_depth: Maximum recursion depth
            
        Returns:
            Decoded multicall structure with nested calls
        """
        if max_depth <= 0:
            return {"error": "Max recursion depth reached"}
        
        if not calldata or len(calldata) < 10:
            return {}
        
        selector = calldata[:10].lower()
        
        # Check if it's a Universal Router execute
        if selector in ["0x3593564c", "0x24856bc3"]:
            return TransactionDecoder._decode_universal_router(
                calldata, chain_id, contract_address, max_depth
            )
        
        # Standard multicall decoding
        if selector not in TransactionDecoder.MULTICALL_SELECTORS:
            # Not a multicall, decode normally
            return TransactionDecoder.decode(calldata, chain_id, contract_address)
        
        try:
            data_bytes = bytes.fromhex(calldata[10:])
            
            # Decode based on selector
            if selector == "0xac9650d8":  # multicall(bytes[])
                decoded = eth_abi.decode(["bytes[]"], data_bytes)
                calls_data = decoded[0]
            elif selector == "0x5ae401dc":  # multicall(uint256,bytes[])
                decoded = eth_abi.decode(["uint256", "bytes[]"], data_bytes)
                deadline = decoded[0]
                calls_data = decoded[1]
            elif selector == "0x1f0464d1":  # multicall(bytes32,bytes[])
                decoded = eth_abi.decode(["bytes32", "bytes[]"], data_bytes)
                calls_data = decoded[1]
            elif selector == "0x8d80ff0a":  # Safe multiSend(bytes)
                return TransactionDecoder._decode_safe_multisend(
                    data_bytes, chain_id, max_depth
                )
            else:
                return {"function_selector": selector, "error": "Unknown multicall format"}
            
            # Decode each nested call
            nested_calls = []
            for i, call_data in enumerate(calls_data):
                if isinstance(call_data, bytes):
                    call_hex = "0x" + call_data.hex()
                else:
                    call_hex = call_data
                
                # Recursively decode if it's also a multicall
                if TransactionDecoder.is_multicall(call_hex):
                    nested_decoded = TransactionDecoder.decode_multicall(
                        call_hex, chain_id, contract_address, max_depth - 1
                    )
                else:
                    nested_decoded = TransactionDecoder.decode(
                        call_hex, chain_id, contract_address
                    )
                
                nested_calls.append({
                    "index": i,
                    "calldata": call_hex[:66] + "..." if len(call_hex) > 66 else call_hex,
                    "decoded": nested_decoded
                })
            
            result = {
                "function_selector": selector,
                "function_name": "multicall",
                "category": "multicall",
                "is_multicall": True,
                "call_count": len(nested_calls),
                "nested_calls": nested_calls,
            }
            
            if selector == "0x5ae401dc":
                result["deadline"] = deadline
            
            return result
            
        except Exception as e:
            return {
                "function_selector": selector,
                "function_name": "multicall",
                "error": f"Failed to decode multicall: {str(e)}"
            }
    
    @staticmethod
    def _decode_universal_router(
        calldata: str,
        chain_id: Optional[int],
        contract_address: Optional[str],
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Decode Uniswap Universal Router execute command.
        """
        selector = calldata[:10].lower()
        
        try:
            data_bytes = bytes.fromhex(calldata[10:])
            
            if selector == "0x3593564c":  # execute(bytes,bytes[],uint256)
                decoded = eth_abi.decode(["bytes", "bytes[]", "uint256"], data_bytes)
                commands = decoded[0]
                inputs = decoded[1]
                deadline = decoded[2]
            else:  # execute(bytes,bytes[])
                decoded = eth_abi.decode(["bytes", "bytes[]"], data_bytes)
                commands = decoded[0]
                inputs = decoded[1]
                deadline = None
            
            # Parse commands
            parsed_commands = []
            for i, cmd_byte in enumerate(commands):
                if i >= len(inputs):
                    break
                
                cmd_type = cmd_byte & 0x3f  # Lower 6 bits
                allow_revert = bool(cmd_byte & 0x80)  # Highest bit
                
                cmd_name = TransactionDecoder.UNIVERSAL_ROUTER_COMMANDS.get(
                    cmd_type, f"UNKNOWN_0x{cmd_type:02x}"
                )
                
                input_data = inputs[i]
                input_hex = "0x" + input_data.hex() if isinstance(input_data, bytes) else input_data
                
                parsed_commands.append({
                    "index": i,
                    "command": cmd_name,
                    "command_byte": f"0x{cmd_byte:02x}",
                    "allow_revert": allow_revert,
                    "input_preview": input_hex[:66] + "..." if len(input_hex) > 66 else input_hex,
                })
            
            result = {
                "function_selector": selector,
                "function_name": "execute",
                "category": "universal_router",
                "is_multicall": True,
                "command_count": len(parsed_commands),
                "commands": parsed_commands,
            }
            
            if deadline is not None:
                result["deadline"] = deadline
            
            return result
            
        except Exception as e:
            return {
                "function_selector": selector,
                "function_name": "execute",
                "error": f"Failed to decode Universal Router: {str(e)}"
            }
    
    @staticmethod
    def _decode_safe_multisend(
        data_bytes: bytes,
        chain_id: Optional[int],
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Decode Safe/Gnosis multiSend transaction.
        Format: {operation}{to}{value}{dataLength}{data}...
        """
        try:
            # Decode the bytes parameter
            decoded = eth_abi.decode(["bytes"], data_bytes)
            packed_txs = decoded[0]
            
            transactions = []
            offset = 0
            
            while offset < len(packed_txs):
                if offset + 85 > len(packed_txs):  # Minimum: 1+20+32+32 = 85 bytes header
                    break
                
                # Parse transaction header
                operation = packed_txs[offset]
                offset += 1
                
                to_address = "0x" + packed_txs[offset:offset+20].hex()
                offset += 20
                
                value = int.from_bytes(packed_txs[offset:offset+32], "big")
                offset += 32
                
                data_length = int.from_bytes(packed_txs[offset:offset+32], "big")
                offset += 32
                
                if offset + data_length > len(packed_txs):
                    break
                
                tx_data = "0x" + packed_txs[offset:offset+data_length].hex()
                offset += data_length
                
                # Decode the inner call
                if data_length > 0:
                    if TransactionDecoder.is_multicall(tx_data) and max_depth > 1:
                        inner_decoded = TransactionDecoder.decode_multicall(
                            tx_data, chain_id, to_address, max_depth - 1
                        )
                    else:
                        inner_decoded = TransactionDecoder.decode(
                            tx_data, chain_id, to_address
                        )
                else:
                    inner_decoded = {"type": "native_transfer"}
                
                transactions.append({
                    "index": len(transactions),
                    "operation": "call" if operation == 0 else "delegatecall",
                    "to": to_address,
                    "value": value,
                    "value_eth": TransactionDecoder._format_amount(value, 18),
                    "decoded": inner_decoded
                })
            
            return {
                "function_selector": "0x8d80ff0a",
                "function_name": "multiSend",
                "category": "multisig",
                "is_multicall": True,
                "transaction_count": len(transactions),
                "transactions": transactions,
            }
            
        except Exception as e:
            return {
                "function_selector": "0x8d80ff0a",
                "function_name": "multiSend",
                "error": f"Failed to decode multiSend: {str(e)}"
            }
    
    @staticmethod
    def get_multicall_summary(decoded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of a multicall transaction.
        
        Args:
            decoded: Decoded multicall data
            
        Returns:
            Summary with action types and counts
        """
        if not decoded.get("is_multicall"):
            return {}
        
        summary = {
            "total_calls": 0,
            "action_types": {},
            "has_swaps": False,
            "has_transfers": False,
            "has_approvals": False,
            "has_permits": False,
        }
        
        def count_actions(calls_list: List[Dict], key: str = "decoded"):
            for call in calls_list:
                decoded_call = call.get(key, {})
                if not decoded_call:
                    continue
                
                summary["total_calls"] += 1
                
                category = decoded_call.get("category", "unknown")
                summary["action_types"][category] = summary["action_types"].get(category, 0) + 1
                
                if "swap" in category.lower():
                    summary["has_swaps"] = True
                if "transfer" in category.lower():
                    summary["has_transfers"] = True
                if "approve" in category.lower():
                    summary["has_approvals"] = True
                if "permit" in category.lower():
                    summary["has_permits"] = True
                
                # Recurse into nested multicalls
                if decoded_call.get("is_multicall"):
                    nested = decoded_call.get("nested_calls") or decoded_call.get("transactions") or []
                    count_actions(nested)
        
        # Start counting
        calls = decoded.get("nested_calls") or decoded.get("transactions") or decoded.get("commands") or []
        count_actions(calls)
        
        return summary
