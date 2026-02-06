from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..config import Config
from ..input.definitions import IntermediateRepresentation, SignatureType
from .knowledge_base import KnowledgeBase
from .structure import SemanticStructure


@dataclass
class RiskSignal:
    key: str
    triggered: bool
    weight: int
    reason_tag: str
    dimension: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "triggered": self.triggered,
            "weight": self.weight,
            "reason_tag": self.reason_tag,
            "dimension": self.dimension,
        }


class RiskSignalExtractor:
    ORDERED_KEYS = [
        "infinite_allowance",
        "unknown_mainnet_contract",
        "zero_consideration_nft_order",
        "blind_signing",
        "multicall_complexity",
        "long_lived_permission",
        "high_value_native_transfer",
    ]

    @staticmethod
    def extract(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        signal_overrides: Dict[str, Dict[str, Any]],
    ) -> List[RiskSignal]:
        signals: List[RiskSignal] = []

        for key in RiskSignalExtractor.ORDERED_KEYS:
            override = signal_overrides.get(key, {})
            dimension = str(override.get("dimension") or "behavioral")
            weight = int(override.get("weight") or 0)
            reason_tag = str(override.get("reason_tag") or key)
            triggered = RiskSignalExtractor._is_triggered(key, ir, structure)
            signals.append(
                RiskSignal(
                    key=key,
                    triggered=triggered,
                    weight=weight,
                    reason_tag=reason_tag,
                    dimension=dimension,
                )
            )

        return signals

    @staticmethod
    def _is_triggered(key: str, ir: IntermediateRepresentation, structure: SemanticStructure) -> bool:
        if key == "infinite_allowance":
            return RiskSignalExtractor._has_infinite_allowance(ir, structure)
        if key == "unknown_mainnet_contract":
            return (
                ir.chain_id == 1
                and bool(ir.contract)
                and not KnowledgeBase.get_contract_name(ir.chain_id, ir.contract)
            )
        if key == "zero_consideration_nft_order":
            return RiskSignalExtractor._detect_zero_consideration_nft_order(ir)
        if key == "blind_signing":
            return ir.signature_type == SignatureType.ETH_SIGN
        if key == "multicall_complexity":
            summary = ir.metadata.get("multicall_summary", {})
            total_calls = int(summary.get("total_calls", 0)) if isinstance(summary, dict) else 0
            return bool((ir.decoded_call or {}).get("is_multicall")) and total_calls >= 3
        if key == "long_lived_permission":
            return RiskSignalExtractor._has_long_lived_permission(ir, structure)
        if key == "high_value_native_transfer":
            value_wei = RiskSignalExtractor._to_int(ir.value)
            return bool(
                value_wei is not None
                and value_wei >= int(Config.FINANCIAL_THRESHOLDS["high_value_eth"])
            )
        return False

    @staticmethod
    def _has_infinite_allowance(ir: IntermediateRepresentation, structure: SemanticStructure) -> bool:
        for ctx in structure.context:
            if "Infinite" in ctx.description and KnowledgeBase.is_infinite_allowance(ctx.raw_value):
                return True

        for key, value in (ir.params or {}).items():
            if any(k in key.lower() for k in ["value", "amount", "allowance"]):
                if KnowledgeBase.is_infinite_allowance(value):
                    return True
        return False

    @staticmethod
    def _has_long_lived_permission(ir: IntermediateRepresentation, structure: SemanticStructure) -> bool:
        if structure.permission_scope in {"unlimited_permanent", "specific_amount_permanent"}:
            return True

        now = int(time.time())
        one_year = 365 * 24 * 60 * 60
        for ctx in structure.context:
            if "deadline" not in ctx.description.lower() and "expiry" not in ctx.description.lower():
                continue
            deadline = RiskSignalExtractor._to_int(ctx.raw_value)
            if deadline is not None and deadline > (now + one_year):
                return True
        return False

    @staticmethod
    def _detect_zero_consideration_nft_order(ir: IntermediateRepresentation) -> bool:
        if ir.signature_type != SignatureType.ETH_SIGN_TYPED_DATA_V4:
            return False

        params = ir.params or {}
        offer_items = RiskSignalExtractor._extract_eip712_array_items(params, "offer")
        consideration_items = RiskSignalExtractor._extract_eip712_array_items(params, "consideration")
        if not offer_items or not consideration_items:
            return False

        def _is_nft(item: Dict[str, Any]) -> bool:
            item_type = RiskSignalExtractor._to_int(item.get("itemtype"))
            return item_type in {2, 3, 4, 5}

        def _is_zero_consideration(item: Dict[str, Any]) -> bool:
            amount = RiskSignalExtractor._to_int(
                item.get("startamount") or item.get("endamount") or item.get("amount")
            )
            if amount is None or amount != 0:
                return False
            token = item.get("token")
            token_zero = isinstance(token, str) and token.lower() == ("0x" + "0" * 40)
            item_type = RiskSignalExtractor._to_int(item.get("itemtype"))
            return token_zero or item_type in {0, 1}

        return any(_is_nft(item) for item in offer_items) and any(
            _is_zero_consideration(item) for item in consideration_items
        )

    @staticmethod
    def _extract_eip712_array_items(params: Dict[str, Any], prefix: str) -> List[Dict[str, Any]]:
        items: Dict[int, Dict[str, Any]] = {}
        prefix_lower = prefix.lower()
        for key, value in params.items():
            if not isinstance(key, str):
                continue
            key_lower = key.lower()
            if not key_lower.startswith(prefix_lower + "["):
                continue
            match = re.match(rf"^{re.escape(prefix_lower)}\[(\d+)\]\.(.+)$", key_lower)
            if not match:
                continue
            idx = int(match.group(1))
            field_name = match.group(2)
            items.setdefault(idx, {})[field_name] = value
        return [items[i] for i in sorted(items.keys())]

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
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
