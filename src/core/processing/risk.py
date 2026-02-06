from dataclasses import dataclass, field
from functools import lru_cache
import json
import re
from typing import Any, Dict, List, Optional, Set

from ..config import Config
from ..input.definitions import IntermediateRepresentation, SignatureType
from ..utils.logger import Logger
from .knowledge_base import KnowledgeBase
from .risk_policy import RiskPolicyLoader
from .risk_signals import RiskSignalExtractor
from .structure import SemanticStructure

_DATA_DIR = Config.DATA_DIR
logger = Logger.get_logger(__name__)


def _load_blacklist() -> Dict[str, Set[str]]:
    """Load address blacklist from JSON file."""
    filepath = _DATA_DIR / "address_blacklist.json"
    if not filepath.exists():
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        result: Dict[str, Set[str]] = {}
        for category, info in data.items():
            addresses = info.get("addresses", [])
            result[category] = {addr.lower() for addr in addresses}
        return result
    except Exception as error:
        logger.warning(f"Failed to load blacklist data: {error}")
        return {}


@dataclass
class RiskAssessment:
    level: str  # "low", "medium", "high", "critical"
    reasons: List[str]
    score: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class RiskEngine:
    """
    Multi-dimensional risk assessment with signal extraction and policy-driven scoring.
    """

    ADDRESS_BLACKLIST: Dict[str, Set[str]] = _load_blacklist()

    FALLBACK_DIMENSION_WEIGHTS = {
        "permission": 1.5,
        "financial": 1.3,
        "reputation": 1.2,
        "technical": 1.1,
        "behavioral": 1.0,
    }

    SIGNAL_REASON_FALLBACKS = {
        "infinite_allowance": "Infinite token allowance requested",
        "unknown_mainnet_contract": "Unknown contract on mainnet - verify before proceeding",
        "zero_consideration_nft_order": "NFT order with zero consideration - potential phishing",
        "blind_signing": "Dangerous: eth_sign blind signing",
        "multicall_complexity": "Complex multicall transaction",
        "long_lived_permission": "Long-lived permission without strict expiry",
        "high_value_native_transfer": "High value native transfer",
    }

    @staticmethod
    def assess(ir: IntermediateRepresentation, structure: SemanticStructure) -> RiskAssessment:
        policy = RiskPolicyLoader.load()
        dimension_weights = policy.weights or RiskEngine.FALLBACK_DIMENSION_WEIGHTS
        thresholds = policy.thresholds or {
            "critical": 85,
            "high": Config.RISK_THRESHOLDS["high"],
            "medium": Config.RISK_THRESHOLDS["medium"],
        }
        scores = Config.RISK_SCORES

        risk_breakdown: Dict[str, Dict[str, Any]] = {
            "permission": {"score": 0, "reasons": []},
            "financial": {"score": 0, "reasons": []},
            "reputation": {"score": 0, "reasons": []},
            "technical": {"score": 0, "reasons": []},
            "behavioral": {"score": 0, "reasons": []},
        }

        blacklist_result = RiskEngine._check_blacklist(ir, structure)
        if blacklist_result["is_blacklisted"]:
            return RiskAssessment(
                level="critical",
                reasons=blacklist_result["reasons"],
                score=100,
                details={
                    "blacklist_match": blacklist_result,
                    "risk_signals": [],
                    "risk_policy_version": policy.version,
                },
            )

        signals = RiskSignalExtractor.extract(ir, structure, policy.signal_overrides)
        triggered_signal_keys = {signal.key for signal in signals if signal.triggered}
        for signal in signals:
            if not signal.triggered:
                continue
            bucket = risk_breakdown.get(signal.dimension)
            if bucket is None:
                continue
            bucket["score"] += max(0, signal.weight)
            reason = (
                policy.reason_templates.get(signal.reason_tag)
                or RiskEngine.SIGNAL_REASON_FALLBACKS.get(signal.reason_tag)
                or signal.reason_tag.replace("_", " ").title()
            )
            bucket["reasons"].append(reason)

        RiskEngine._assess_permission_scope(ir, structure, risk_breakdown, scores)
        RiskEngine._assess_financial_risk(ir, structure, risk_breakdown, scores)
        RiskEngine._assess_reputation(ir, risk_breakdown, scores, triggered_signal_keys)
        RiskEngine._assess_technical_risk(ir, structure, risk_breakdown, scores)
        RiskEngine._assess_behavioral_patterns(ir, structure, risk_breakdown, scores)
        RiskEngine._assess_action_specific(ir, structure, risk_breakdown, policy)

        total_score = 0.0
        all_reasons: List[str] = []
        for dimension, bucket in risk_breakdown.items():
            total_score += bucket["score"] * float(dimension_weights.get(dimension, 1.0))
            all_reasons.extend(bucket["reasons"])

        total_score = min(100, int(total_score))
        if total_score >= int(thresholds.get("critical", 85)):
            level = "critical"
        elif total_score >= int(thresholds.get("high", Config.RISK_THRESHOLDS["high"])):
            level = "high"
        elif total_score >= int(thresholds.get("medium", Config.RISK_THRESHOLDS["medium"])):
            level = "medium"
        else:
            level = "low"

        unique_reasons = RiskEngine._dedupe_reasons(all_reasons)
        if not unique_reasons:
            unique_reasons = ["Standard operation - no significant risks detected"]

        return RiskAssessment(
            level=level,
            reasons=unique_reasons[:10],
            score=total_score,
            details={
                "breakdown": risk_breakdown,
                "weights": dimension_weights,
                "risk_signals": [signal.to_dict() for signal in signals],
                "risk_policy_version": policy.version,
            },
        )

    @staticmethod
    def _check_blacklist(ir: IntermediateRepresentation, structure: SemanticStructure) -> Dict[str, Any]:
        result = {"is_blacklisted": False, "reasons": [], "matches": []}

        addresses_to_check = set()
        if ir.contract:
            addresses_to_check.add(ir.contract.lower())
        if ir.sender:
            addresses_to_check.add(ir.sender.lower())

        for value in ir.params.values():
            if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
                addresses_to_check.add(value.lower())

        for ctx in structure.context:
            value = ctx.raw_value
            if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
                addresses_to_check.add(value.lower())

        for category, blacklist in RiskEngine.ADDRESS_BLACKLIST.items():
            for addr in addresses_to_check:
                if addr in blacklist:
                    result["is_blacklisted"] = True
                    result["matches"].append({"address": addr, "category": category})
                    category_labels = {
                        "phishing": "CRITICAL: Known phishing address detected",
                        "scam_contracts": "CRITICAL: Known scam contract detected",
                        "drainer": "CRITICAL: Known wallet drainer detected",
                        "honeypot": "CRITICAL: Known honeypot contract detected",
                        "reported": "WARNING: Community-reported malicious address",
                    }
                    result["reasons"].append(
                        category_labels.get(category, f"Blacklisted address: {category}")
                    )

        return result

    @staticmethod
    def _assess_permission_scope(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict[str, Dict[str, Any]],
        scores: Dict[str, int],
    ) -> None:
        bucket = breakdown["permission"]
        permission_scope = structure.permission_scope
        if permission_scope == "unlimited_permanent":
            bucket["score"] += scores.get("unlimited_permanent", 50)
            bucket["reasons"].append("Grants unlimited permanent permission - highest risk")
        elif permission_scope == "unlimited_time_limited":
            bucket["score"] += scores.get("unlimited_time_limited", 35)
            bucket["reasons"].append("Grants unlimited time-limited permission")
        elif permission_scope == "specific_amount_permanent":
            has_deadline = any(
                "deadline" in ctx.description.lower() or "expiry" in ctx.description.lower()
                for ctx in structure.context
            )
            if has_deadline:
                bucket["score"] += 10
                bucket["reasons"].append("Long-lived permission with distant expiry")
            else:
                bucket["score"] += scores.get("permanent", 25)
                bucket["reasons"].append("Permanent permission without expiry")

        action = structure.action.raw_value
        if action in {"approve", "authorization", "permit", "batch_approval"}:
            bucket["score"] += scores.get("approve", 15)
            bucket["reasons"].append("Grants spending permission to third party")

        for ctx in structure.context:
            if "Infinite" in ctx.description and KnowledgeBase.is_infinite_allowance(ctx.raw_value):
                bucket["score"] += 20
                bucket["reasons"].append("Infinite token allowance requested")
                break

    @staticmethod
    def _assess_financial_risk(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict[str, Dict[str, Any]],
        scores: Dict[str, int],
    ) -> None:
        bucket = breakdown["financial"]
        high_value_wei = int(Config.FINANCIAL_THRESHOLDS["high_value_eth"])
        high_value_usd = float(Config.FINANCIAL_THRESHOLDS["high_value_usd"])

        value_wei = RiskEngine._to_int(ir.value)
        if value_wei is not None and value_wei >= high_value_wei:
            bucket["score"] += scores.get("high_value_transfer", 30)
            bucket["reasons"].append(f"High value transfer: {value_wei / 1e18:.4f} ETH")

        for ctx in structure.context:
            label = ctx.description.lower()
            if "amount" not in label and "value" not in label:
                continue

            amount = RiskEngine._to_float(ctx.raw_value)
            if amount is None:
                continue

            # Avoid mixing integer raw base units with decimal business values.
            if amount > 1e12:
                continue

            if amount >= high_value_usd:
                bucket["score"] += 20
                bucket["reasons"].append("High value token operation")
                break

        if structure.action.raw_value in {"transfer_asset", "batch_transfer"}:
            bucket["score"] += scores.get("transfer", 25)
            bucket["reasons"].append("Irreversible asset transfer")

    @staticmethod
    def _assess_reputation(
        ir: IntermediateRepresentation,
        breakdown: Dict[str, Dict[str, Any]],
        scores: Dict[str, int],
        triggered_signals: Set[str],
    ) -> None:
        bucket = breakdown["reputation"]
        if not ir.contract:
            return

        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract)
        if contract_name:
            contract_lower = contract_name.lower()
            tier1_protocols = ["uniswap", "aave", "compound", "opensea", "seaport", "permit2"]
            tier2_protocols = ["1inch", "sushiswap", "curve", "balancer", "blur"]
            if any(name in contract_lower for name in tier1_protocols):
                bucket["score"] -= 15
                bucket["reasons"].append(f"Verified protocol: {contract_name}")
            elif any(name in contract_lower for name in tier2_protocols):
                bucket["score"] -= 10
                bucket["reasons"].append(f"Known protocol: {contract_name}")
            else:
                bucket["score"] += 5
                bucket["reasons"].append(f"Lesser-known contract: {contract_name}")
        else:
            if ir.chain_id == 1:
                if "unknown_mainnet_contract" not in triggered_signals:
                    bucket["score"] += scores.get("unknown_contract", 20)
                bucket["reasons"].append("Unknown contract on mainnet - verify before proceeding")
            else:
                bucket["score"] += 10
                bucket["reasons"].append("Unknown contract - verify contract address")

        bucket["score"] = max(0, bucket["score"])

    @staticmethod
    def _assess_technical_risk(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict[str, Dict[str, Any]],
        scores: Dict[str, int],
    ) -> None:
        bucket = breakdown["technical"]
        action = structure.action.raw_value or ""

        if ir.signature_type == SignatureType.ETH_SIGN:
            bucket["score"] += scores.get("blind_signing", 50)
            bucket["reasons"].append("Dangerous: eth_sign blind signing")

        if action in {"cross_contract_interaction", "batch_operation", "batch_swap", "batch_approval"}:
            bucket["score"] += scores.get("cross_contract", 20)
            bucket["reasons"].append("Complex multi-contract operation")

        if action in {"bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"}:
            bucket["score"] += scores.get("bridge", 30)
            bucket["reasons"].append("Cross-chain bridge - verify destination")

        summary = ir.metadata.get("multicall_summary", {})
        call_count = int(summary.get("total_calls", 0)) if isinstance(summary, dict) else 0
        if call_count > 5:
            bucket["score"] += 15
            bucket["reasons"].append(f"Complex batch with {call_count} operations")
        elif call_count > 2:
            bucket["score"] += 10
            bucket["reasons"].append(f"Batch operation with {call_count} calls")

    @staticmethod
    def _assess_behavioral_patterns(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict[str, Dict[str, Any]],
        scores: Dict[str, int],
    ) -> None:
        bucket = breakdown["behavioral"]

        text_content = " ".join(
            [
                str(ir.params.get("message", "")).lower(),
                str(ir.params.get("message_cleaned", "")).lower(),
                str(structure.action.description).lower(),
            ]
        )

        detected_patterns: List[tuple[str, str]] = []
        for category, keywords in Config.PHISHING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_content:
                    detected_patterns.append((category, keyword))

        for pattern_name, patterns in Config.SUSPICIOUS_PATTERNS.items():
            for pattern in patterns:
                if RiskEngine._matches_pattern(text_content, pattern):
                    detected_patterns.append((pattern_name, pattern))

        if detected_patterns:
            categories = {name for name, _ in detected_patterns}
            base_score = scores.get("phishing", 60)
            if len(categories) >= 3:
                bucket["score"] += base_score + 10
                bucket["reasons"].append("Multiple phishing indicators detected")
            elif len(categories) >= 2:
                bucket["score"] += base_score
                bucket["reasons"].append("Suspicious message patterns detected")
            else:
                bucket["score"] += max(0, base_score - 10)
                bucket["reasons"].append(
                    f"Warning: {detected_patterns[0][0].replace('_', ' ')} pattern detected"
                )

        if structure.action.raw_value == "governance_delegation":
            bucket["score"] += scores.get("delegation", 25)
            bucket["reasons"].append("Voting power delegation")

    @staticmethod
    def _assess_action_specific(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict[str, Dict[str, Any]],
        policy: Any,
    ) -> None:
        action = structure.action.raw_value or ""
        adjustment = policy.action_adjustments.get(action, {})
        reason_tag = adjustment.get("reason_tag")

        applied_reason = False
        for dimension, value in adjustment.items():
            if dimension == "reason_tag":
                continue
            if dimension not in breakdown:
                continue
            try:
                delta = int(value)
            except Exception:
                continue
            breakdown[dimension]["score"] = max(0, breakdown[dimension]["score"] + delta)
            applied_reason = True

        if reason_tag and applied_reason:
            reason = (
                policy.reason_templates.get(reason_tag)
                or RiskEngine.SIGNAL_REASON_FALLBACKS.get(reason_tag)
                or str(reason_tag).replace("_", " ").title()
            )
            breakdown["technical"]["reasons"].append(reason)

        if action == "phishing_nft_order":
            breakdown["behavioral"]["score"] += 30
            breakdown["behavioral"]["reasons"].append("Phishing-like NFT order behavior")

        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4 and RiskEngine._detect_zero_consideration_nft_order(ir):
            breakdown["behavioral"]["score"] += 25
            breakdown["behavioral"]["reasons"].append("NFT order with zero consideration - potential phishing")
            breakdown["technical"]["score"] += 15
            breakdown["technical"]["reasons"].append("Zero-value consideration detected in NFT order")

    @staticmethod
    @lru_cache(maxsize=100)
    def get_risk_explanation(level: str) -> Dict[str, str]:
        explanations = {
            "low": {
                "title": "Low Risk",
                "description": "This operation appears to be safe with minimal risk.",
                "recommendation": "You can proceed with normal caution.",
            },
            "medium": {
                "title": "Medium Risk",
                "description": "This operation has some risk factors that require attention.",
                "recommendation": "Review the details carefully before signing.",
            },
            "high": {
                "title": "High Risk",
                "description": "This operation has significant risk factors.",
                "recommendation": "Verify all details and the source before proceeding.",
            },
            "critical": {
                "title": "Critical Risk",
                "description": "This operation has critical security concerns.",
                "recommendation": "Do not proceed unless you are absolutely certain of the source.",
            },
        }
        return explanations.get(level, explanations["medium"])

    @staticmethod
    def reload_blacklist() -> None:
        RiskEngine.ADDRESS_BLACKLIST = _load_blacklist()

    @staticmethod
    def _detect_zero_consideration_nft_order(ir: IntermediateRepresentation) -> bool:
        return RiskSignalExtractor._detect_zero_consideration_nft_order(ir)

    @staticmethod
    def _extract_eip712_array_items(params: Dict[str, Any], prefix: str) -> List[Dict[str, Any]]:
        return RiskSignalExtractor._extract_eip712_array_items(params, prefix)

    @staticmethod
    def _matches_pattern(text: str, pattern: str) -> bool:
        if pattern.isalpha():
            return re.search(rf"\b{re.escape(pattern)}\b", text) is not None
        return pattern in text

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

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "").strip()
            if not cleaned:
                return None
            try:
                if cleaned.startswith("0x"):
                    return float(int(cleaned, 16))
                return float(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _dedupe_reasons(reasons: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for reason in reasons:
            if reason in seen:
                continue
            seen.add(reason)
            deduped.append(reason)
        return deduped
