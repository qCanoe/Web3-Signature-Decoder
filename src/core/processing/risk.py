from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Set
import json
import re
from pathlib import Path
from functools import lru_cache
from ..input.definitions import IntermediateRepresentation, SignatureType
from .structure import SemanticStructure
from ..config import Config
from .knowledge_base import KnowledgeBase
from ..utils.logger import Logger

# Load blacklist data
_DATA_DIR = Config.DATA_DIR
logger = Logger.get_logger(__name__)

def _load_blacklist() -> Dict[str, Set[str]]:
    """Load address blacklist from JSON file."""
    filepath = _DATA_DIR / "address_blacklist.json"
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = {}
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
    Advanced risk assessment engine with multi-dimensional scoring.
    Supports blacklist checking, context-aware scoring, and detailed risk breakdown.
    """
    
    # Load blacklist
    ADDRESS_BLACKLIST: Dict[str, Set[str]] = _load_blacklist()
    
    # Risk score weights for different dimensions
    DIMENSION_WEIGHTS = {
        "permission": 1.5,      # Permission-related risks
        "financial": 1.3,       # Financial value risks
        "reputation": 1.2,      # Contract/address reputation
        "technical": 1.1,       # Technical risks
        "behavioral": 1.0,      # Behavioral patterns
    }
    
    
    @staticmethod
    def assess(ir: IntermediateRepresentation, structure: SemanticStructure) -> RiskAssessment:
        """
        Comprehensive multi-dimensional risk assessment.
        Returns a detailed risk assessment with score breakdown.
        """
        risk_breakdown = {
            "permission": {"score": 0, "reasons": []},
            "financial": {"score": 0, "reasons": []},
            "reputation": {"score": 0, "reasons": []},
            "technical": {"score": 0, "reasons": []},
            "behavioral": {"score": 0, "reasons": []},
        }
        
        scores = Config.RISK_SCORES
        
        # 1. Blacklist Check (Critical - immediate high risk)
        blacklist_result = RiskEngine._check_blacklist(ir, structure)
        if blacklist_result["is_blacklisted"]:
            return RiskAssessment(
                level="critical",
                reasons=blacklist_result["reasons"],
                score=100,
                details={"blacklist_match": blacklist_result}
            )
        
        # 2. Permission Scope Assessment
        RiskEngine._assess_permission_scope(ir, structure, risk_breakdown, scores)
        
        # 3. Financial Risk Assessment
        RiskEngine._assess_financial_risk(ir, structure, risk_breakdown, scores)
        
        # 4. Contract/Address Reputation
        RiskEngine._assess_reputation(ir, structure, risk_breakdown, scores)
        
        # 5. Technical Risk Assessment
        RiskEngine._assess_technical_risk(ir, structure, risk_breakdown, scores)
        
        # 6. Behavioral Pattern Analysis
        RiskEngine._assess_behavioral_patterns(ir, structure, risk_breakdown, scores)
        
        # 7. Action-specific Assessment
        RiskEngine._assess_action_specific(ir, structure, risk_breakdown, scores)
        
        # Calculate weighted total score
        total_score = 0
        all_reasons = []
        
        for dimension, data in risk_breakdown.items():
            weight = RiskEngine.DIMENSION_WEIGHTS.get(dimension, 1.0)
            weighted_score = data["score"] * weight
            total_score += weighted_score
            all_reasons.extend(data["reasons"])
        
        # Normalize to 0-100
        total_score = min(100, int(total_score))
        
        # Determine risk level
        thresholds = Config.RISK_THRESHOLDS
        if total_score >= 85:
            level = "critical"
        elif total_score >= thresholds["high"]:
            level = "high"
        elif total_score >= thresholds["medium"]:
            level = "medium"
        else:
            level = "low"
        
        # Deduplicate and limit reasons
        seen = set()
        unique_reasons = []
        for reason in all_reasons:
            if reason not in seen:
                seen.add(reason)
                unique_reasons.append(reason)
        
        if not unique_reasons:
            unique_reasons.append("Standard operation - no significant risks detected")
        
        return RiskAssessment(
            level=level,
            reasons=unique_reasons[:10],  # Limit to top 10 reasons
            score=total_score,
            details={
                "breakdown": risk_breakdown,
                "weights": RiskEngine.DIMENSION_WEIGHTS,
            }
        )
    
    @staticmethod
    def _check_blacklist(ir: IntermediateRepresentation, structure: SemanticStructure) -> Dict[str, Any]:
        """
        Check addresses against known blacklists.
        """
        result = {"is_blacklisted": False, "reasons": [], "matches": []}
        
        # Collect all addresses to check
        addresses_to_check = set()
        
        if ir.contract:
            addresses_to_check.add(ir.contract.lower())
        if ir.sender:
            addresses_to_check.add(ir.sender.lower())
        
        # Check params for addresses
        for key, value in ir.params.items():
            if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
                addresses_to_check.add(value.lower())
        
        # Check context for addresses
        for ctx in structure.context:
            value = ctx.raw_value
            if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
                addresses_to_check.add(value.lower())
        
        # Check against blacklists
        for category, blacklist in RiskEngine.ADDRESS_BLACKLIST.items():
            for addr in addresses_to_check:
                if addr in blacklist:
                    result["is_blacklisted"] = True
                    result["matches"].append({
                        "address": addr,
                        "category": category
                    })
                    
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
        breakdown: Dict,
        scores: Dict
    ):
        """Assess permission-related risks."""
        dimension = breakdown["permission"]
        
        # Check permission scope from structure
        permission_scope = structure.permission_scope
        
        if permission_scope == "unlimited_permanent":
            dimension["score"] += scores.get("unlimited_permanent", 50)
            dimension["reasons"].append("Grants unlimited permanent permission - highest risk")
        elif permission_scope == "unlimited_time_limited":
            dimension["score"] += scores.get("unlimited_time_limited", 35)
            dimension["reasons"].append("Grants unlimited time-limited permission")
        elif permission_scope == "specific_amount_permanent":
            dimension["score"] += scores.get("permanent", 25)
            dimension["reasons"].append("Permanent permission without expiry")
        
        # Check for infinite allowance in context
        for ctx in structure.context:
            if "Infinite" in ctx.description or ctx.risk_factor == "high":
                if KnowledgeBase.is_infinite_allowance(ctx.raw_value):
                    dimension["score"] += 25
                    dimension["reasons"].append("Infinite token allowance requested")
                    break
        
        # Check for approval actions
        action = structure.action.raw_value
        if action in ["approve", "authorization", "permit"]:
            dimension["score"] += scores.get("approve", 15)
            dimension["reasons"].append("Grants spending permission to third party")
    
    @staticmethod
    def _assess_financial_risk(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict,
        scores: Dict
    ):
        """Assess financial value-related risks."""
        dimension = breakdown["financial"]
        
        # Check native value
        if ir.value and ir.value != "0":
            try:
                value_wei = int(ir.value)
                if value_wei > Config.FINANCIAL_THRESHOLDS["high_value_eth"]:
                    dimension["score"] += scores.get("high_value_transfer", 30)
                    eth_value = value_wei / 1e18
                    dimension["reasons"].append(f"High value transfer: {eth_value:.4f} ETH")
            except (ValueError, TypeError) as error:
                logger.debug(f"Failed to parse native value: {error}")
        
        # Check token amounts in context
        for ctx in structure.context:
            if "Amount" in ctx.description or "value" in ctx.description.lower():
                try:
                    amount = float(ctx.raw_value) if ctx.raw_value else 0
                    if amount > Config.FINANCIAL_THRESHOLDS["high_value_eth"]:
                        dimension["score"] += 20
                        dimension["reasons"].append("High value token operation")
                        break
                except (ValueError, TypeError) as error:
                    logger.debug(f"Failed to parse token amount: {error}")
        
        # Transfer action specific
        if structure.action.raw_value == "transfer_asset":
            dimension["score"] += scores.get("transfer", 25)
            dimension["reasons"].append("Irreversible asset transfer")
    
    @staticmethod
    def _assess_reputation(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict,
        scores: Dict
    ):
        """Assess contract and address reputation."""
        dimension = breakdown["reputation"]
        
        if not ir.contract:
            return
        
        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract)
        
        if contract_name:
            contract_lower = contract_name.lower()
            
            # Highly reputable protocols
            tier1_protocols = ["uniswap", "aave", "compound", "opensea", "seaport", "permit2"]
            tier2_protocols = ["1inch", "sushiswap", "curve", "balancer", "blur"]
            
            if any(p in contract_lower for p in tier1_protocols):
                dimension["score"] -= 15  # Reduce risk
                dimension["reasons"].append(f"Verified protocol: {contract_name}")
            elif any(p in contract_lower for p in tier2_protocols):
                dimension["score"] -= 10
                dimension["reasons"].append(f"Known protocol: {contract_name}")
            else:
                dimension["score"] += 5
                dimension["reasons"].append(f"Lesser-known contract: {contract_name}")
        else:
            # Unknown contract
            if ir.chain_id == 1:  # Mainnet
                dimension["score"] += scores.get("unknown_contract", 20)
                dimension["reasons"].append("Unknown contract on mainnet - verify before proceeding")
            else:
                dimension["score"] += 10
                dimension["reasons"].append("Unknown contract - verify contract address")
        
        # Ensure non-negative
        dimension["score"] = max(0, dimension["score"])
    
    @staticmethod
    def _assess_technical_risk(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict,
        scores: Dict
    ):
        """Assess technical and signature type risks."""
        dimension = breakdown["technical"]
        
        # Blind signing risk
        if ir.signature_type == SignatureType.ETH_SIGN:
            dimension["score"] += scores.get("blind_signing", 50)
            dimension["reasons"].append("Dangerous: eth_sign blind signing")
        
        # Cross-contract operations
        if structure.action.raw_value in ["cross_contract_interaction", "batch_operation"]:
            dimension["score"] += scores.get("cross_contract", 20)
            dimension["reasons"].append("Complex multi-contract operation")
        
        # Bridge operations
        if structure.action.raw_value in ["bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"]:
            dimension["score"] += scores.get("bridge", 30)
            dimension["reasons"].append("Cross-chain bridge - verify destination")
        
        # Check for multicall complexity
        multicall_summary = ir.metadata.get("multicall_summary", {})
        if multicall_summary:
            call_count = multicall_summary.get("total_calls", 0)
            if call_count > 5:
                dimension["score"] += 15
                dimension["reasons"].append(f"Complex batch with {call_count} operations")
            elif call_count > 2:
                dimension["score"] += 10
                dimension["reasons"].append(f"Batch operation with {call_count} calls")
    
    @staticmethod
    def _assess_behavioral_patterns(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict,
        scores: Dict
    ):
        """Assess suspicious behavioral patterns."""
        dimension = breakdown["behavioral"]
        
        # Gather text content
        text_content = ""
        text_content += str(ir.params.get("message", "")).lower()
        text_content += " " + str(ir.params.get("message_cleaned", "")).lower()
        text_content += " " + structure.action.description.lower()
        
        # Check for phishing keywords
        phishing_keywords = Config.PHISHING_KEYWORDS
        detected_patterns = []
        
        for category, keywords in phishing_keywords.items():
            for keyword in keywords:
                if keyword in text_content:
                    detected_patterns.append((category, keyword))
        
        # Additional pattern checks (use word boundaries for pure alphabetic patterns)
        def _matches_pattern(text: str, pattern: str) -> bool:
            if pattern.isalpha():
                return re.search(rf"\b{re.escape(pattern)}\b", text) is not None
            return pattern in text

        for pattern_name, patterns in Config.SUSPICIOUS_PATTERNS.items():
            for pattern in patterns:
                if _matches_pattern(text_content, pattern):
                    detected_patterns.append((pattern_name, pattern))
        
        if detected_patterns:
            # Group by category
            categories = set(p[0] for p in detected_patterns)

            base_phishing_score = scores.get("phishing", 60)
            
            if len(categories) >= 3:
                dimension["score"] += base_phishing_score + 10
                dimension["reasons"].append("Multiple phishing indicators detected")
            elif len(categories) >= 2:
                dimension["score"] += base_phishing_score
                dimension["reasons"].append("Suspicious message patterns detected")
            else:
                dimension["score"] += max(0, base_phishing_score - 10)
                category = detected_patterns[0][0]
                dimension["reasons"].append(f"Warning: {category.replace('_', ' ')} pattern detected")
        
        # Check for delegation risks
        if structure.action.raw_value == "governance_delegation":
            dimension["score"] += scores.get("delegation", 25)
            dimension["reasons"].append("Voting power delegation")
    
    @staticmethod
    def _assess_action_specific(
        ir: IntermediateRepresentation,
        structure: SemanticStructure,
        breakdown: Dict,
        scores: Dict
    ):
        """Assess action-specific risks."""
        action = structure.action.raw_value
        
        # Safe actions that reduce overall risk
        if action in ["authentication", "sign_in_with_ethereum"]:
            breakdown["permission"]["score"] = max(0, breakdown["permission"]["score"] - 15)
            breakdown["financial"]["score"] = max(0, breakdown["financial"]["score"] - 10)
            breakdown["technical"]["reasons"].append("Identity verification only - generally safe")
        
        # NFT-specific risks
        if action in ["nft_approve", "nft_approval"]:
            breakdown["permission"]["score"] += 20
            breakdown["permission"]["reasons"].append("NFT collection approval - grants access to all NFTs")
        
        # DeFi-specific risks
        if action in ["defi_borrow", "defi_liquidate"]:
            breakdown["financial"]["score"] += 15
            breakdown["financial"]["reasons"].append("DeFi borrowing/liquidation operation")

        # Seaport-style zero-consideration NFT orders (phishing pattern)
        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            if RiskEngine._detect_zero_consideration_nft_order(ir):
                breakdown["behavioral"]["score"] += scores.get("phishing", 60)
                breakdown["behavioral"]["reasons"].append(
                    "NFT order with zero consideration - potential phishing"
                )
                breakdown["technical"]["score"] += 15
                breakdown["technical"]["reasons"].append(
                    "Zero-value consideration detected in NFT order"
                )
    
    @staticmethod
    @lru_cache(maxsize=100)
    def get_risk_explanation(level: str) -> Dict[str, str]:
        """Get human-readable explanation for risk level."""
        explanations = {
            "low": {
                "title": "Low Risk",
                "description": "This operation appears to be safe with minimal risk.",
                "recommendation": "You can proceed with normal caution."
            },
            "medium": {
                "title": "Medium Risk",
                "description": "This operation has some risk factors that require attention.",
                "recommendation": "Review the details carefully before signing."
            },
            "high": {
                "title": "High Risk",
                "description": "This operation has significant risk factors.",
                "recommendation": "Verify all details and the source before proceeding."
            },
            "critical": {
                "title": "Critical Risk",
                "description": "This operation has critical security concerns.",
                "recommendation": "Do not proceed unless you are absolutely certain of the source."
            }
        }
        return explanations.get(level, explanations["medium"])
    
    @staticmethod
    def reload_blacklist():
        """Reload blacklist from file."""
        RiskEngine.ADDRESS_BLACKLIST = _load_blacklist()

    @staticmethod
    def _detect_zero_consideration_nft_order(ir: IntermediateRepresentation) -> bool:
        """
        Detect Seaport-style orders where an NFT is offered for zero consideration.
        This is a common phishing pattern.
        """
        params = ir.params or {}

        offer_items = RiskEngine._extract_eip712_array_items(params, "offer")
        consideration_items = RiskEngine._extract_eip712_array_items(params, "consideration")

        if not offer_items or not consideration_items:
            return False

        def _as_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                if isinstance(value, str) and value.startswith("0x"):
                    return int(value, 16)
                return int(value)
            except Exception:
                return None

        def _is_nft(item: Dict[str, Any]) -> bool:
            item_type = item.get("itemtype")
            item_type_int = _as_int(item_type)
            return item_type_int in {2, 3, 4, 5}  # ERC721/1155 (+ criteria variants)

        def _is_zero_consideration(item: Dict[str, Any]) -> bool:
            amount = _as_int(item.get("startamount") or item.get("endamount") or item.get("amount"))
            if amount is None or amount != 0:
                return False

            token = item.get("token")
            token_zero = isinstance(token, str) and token.lower() == ("0x" + "0" * 40)
            item_type_int = _as_int(item.get("itemtype"))

            return token_zero or item_type_int in {0, 1}  # Native ETH or ERC20

        has_nft_offer = any(_is_nft(item) for item in offer_items)
        has_zero_consideration = any(_is_zero_consideration(item) for item in consideration_items)

        return has_nft_offer and has_zero_consideration

    @staticmethod
    def _extract_eip712_array_items(params: Dict[str, Any], prefix: str) -> List[Dict[str, Any]]:
        """
        Extract array-like EIP-712 fields into a list of dicts.
        Expected keys: "{prefix}[0].field", "{prefix}[1].field", etc.
        """
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

        # Return items in index order
        return [items[i] for i in sorted(items.keys())]
