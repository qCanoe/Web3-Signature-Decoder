from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from ..input.definitions import IntermediateRepresentation
from .structure import SemanticStructure

@dataclass
class RiskAssessment:
    level: str # "low", "medium", "high"
    reasons: List[str]

class RiskEngine:
    """
    Evaluates the risk level of the operation.
    Integrated with rules from legacy RiskAnalyzer.
    """

    # Phishing keywords from legacy RiskAnalyzer
    PHISHING_KEYWORDS = {
        "urgent": ["urgent", "urgently", "immediately", "asap"],
        "time_pressure": ["expires", "deadline", "limited time", "act now"],
        "authority": ["verify", "confirm", "validate", "verification required"],
        "reward": ["claim", "reward", "bonus", "prize", "free"],
        "threat": ["suspend", "block", "disable", "freeze"]
    }

    # Financial thresholds from legacy RiskAnalyzer
    FINANCIAL_THRESHOLDS = {
        "high_value_eth": 1000000000000000000,  # 1 ETH in wei
        "high_value_usd": 1000  # $1000 USD reference
    }
    
    @staticmethod
    def assess(ir: IntermediateRepresentation, structure: SemanticStructure) -> RiskAssessment:
        reasons = []
        score = 0 # 0=Low, 1=Medium, 2=High
        
        # 1. Check Context Risks (e.g. Infinite Approval)
        for ctx in structure.context:
            if ctx.risk_factor == "high":
                score = max(score, 2)
                reasons.append(f"High Risk Param: {ctx.description}")
            elif ctx.risk_factor == "medium":
                score = max(score, 1)
                reasons.append(f"Warning: {ctx.description}")

        # 2. Action-based Risks
        action = structure.action.raw_value
        if action == "approve":
            # Approval is inherently risky if not infinite, but standard
            if score < 1: score = 1 
            if not any("Infinite" in r for r in reasons):
                reasons.append("Grants spending permission to contract")
        
        elif action == "transfer_asset":
             # Direct transfers are irreversible
             if score < 1: score = 1
             reasons.append("Irreversible asset transfer")
             
             # Check amount
             amount_str = next((c.raw_value for c in structure.context if "Amount" in c.description), "0")
             if RiskEngine._check_high_value(amount_str):
                 score = max(score, 2)
                 reasons.append("High value transfer detected (> 1 ETH equivalent)")

        elif action == "authentication":
             # Generally safe
             reasons.append("Safe: Identity verification only")
             
        elif action == "authorization":
             # Permit/SignTypedData general auth
             score = max(score, 1)
             reasons.append("Off-chain authorization can be used for on-chain actions")

        # 3. Phishing Detection (New)
        phishing_warnings = RiskEngine._detect_phishing_keywords(ir, structure)
        if phishing_warnings:
            score = max(score, 2) # Phishing is always high risk
            reasons.extend(phishing_warnings)

        # 4. Technical Heuristics
        if ir.signature_type == "eth_sign":
            score = max(score, 2)
            reasons.append("Dangerous Signature Type: eth_sign (Blind Signing)")

        if ir.dapp_url:
             # In a real extension, we'd check whitelist/blacklist
             pass
             
        # Map score to level
        level = "low"
        if score == 1: level = "medium"
        if score >= 2: level = "high"
        
        if not reasons:
            reasons.append("Standard operation")

        return RiskAssessment(level=level, reasons=reasons)

    @staticmethod
    def _detect_phishing_keywords(ir: IntermediateRepresentation, structure: SemanticStructure) -> List[str]:
        warnings = []
        # Gather all text content
        text_content = str(ir.params).lower() + " " + structure.action.description.lower()
        
        for category, keywords in RiskEngine.PHISHING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_content:
                    warnings.append(f"Phishing Warning: Detected '{keyword}' ({category})")
        return warnings

    @staticmethod
    def _check_high_value(amount: Any) -> bool:
        try:
            val = float(amount)
            # Simple heuristic: if > 10^18 (1 ETH) or clearly stated as high USD
            # This is rough because we don't know decimals here always
            # Assuming raw uint256 for tokens/ETH
            if val > RiskEngine.FINANCIAL_THRESHOLDS["high_value_eth"]:
                return True
        except:
            pass
        return False
