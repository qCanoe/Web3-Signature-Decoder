from __future__ import annotations

from typing import Dict, Any, List, Optional

from .knowledge_base import KnowledgeBase


class TransactionDecoder:
    """Lightweight ABI decoder for common Ethereum transaction patterns."""

    WORD_HEX_LENGTH = 64  # 32 bytes

    @staticmethod
    def decode(calldata: Optional[str]) -> Dict[str, Any]:
        if not calldata or len(calldata) < 10 or not calldata.startswith("0x"):
            return {}

        selector = calldata[:10].lower()
        definition = KnowledgeBase.get_function_definition(selector)
        if not definition:
            return {"function_selector": selector}

        raw_params = calldata[10:]
        parameters = TransactionDecoder._decode_parameters(
            raw_params,
            definition.get("params", []),
            definition.get("param_names", []),
        )

        return {
            "function_selector": selector,
            "function_name": definition["name"],
            "signature": definition["signature"],
            "category": definition.get("category"),
            "parameters": parameters,
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

        if not decoded:
            return assets

        category = decoded.get("category")
        params = decoded.get("parameters", {})
        token_meta = KnowledgeBase.get_token_metadata(contract_address)
        decimals = token_meta.get("decimals", 18)
        symbol = token_meta.get("symbol") or "TOKEN"

        if category in {"erc20_transfer", "erc20_transfer_from"}:
            amount = TransactionDecoder._normalize_int(params.get("amount") or params.get("param_1") or params.get("param_2"))
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
            amount = TransactionDecoder._normalize_int(params.get("amount") or params.get("param_1"))
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
    def _decode_parameters(raw_params: str, param_types: List[str], param_names: List[str]) -> Dict[str, Any]:
        decoded: Dict[str, Any] = {}

        for index, param_type in enumerate(param_types):
            start = index * TransactionDecoder.WORD_HEX_LENGTH
            end = start + TransactionDecoder.WORD_HEX_LENGTH
            word = raw_params[start:end]
            if len(word) < TransactionDecoder.WORD_HEX_LENGTH:
                break

            name = param_names[index] if index < len(param_names) else f"param_{index}"
            decoded[name] = TransactionDecoder._decode_word(word, param_type)

        return decoded

    @staticmethod
    def _decode_word(word: str, param_type: str) -> Any:
        if param_type == "address":
            return "0x" + word[-40:]
        if param_type.startswith("uint"):
            return int(word, 16)
        if param_type == "bool":
            return int(word, 16) > 0
        if param_type == "bytes":
            return "0x" + word
        # For unsupported or dynamic types, keep raw hex
        return "0x" + word

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

