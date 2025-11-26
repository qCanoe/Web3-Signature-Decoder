from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from ..input.definitions import IntermediateRepresentation
from .structure import SemanticStructure
from ..config import Config
from .knowledge_base import KnowledgeBase

@dataclass
class RiskAssessment:
    level: str # "low", "medium", "high"
    reasons: List[str]

class RiskEngine:
    """
    Evaluates the risk level of the operation.
    Integrated with rules from legacy RiskAnalyzer.
    """
    
    @staticmethod
    def assess(ir: IntermediateRepresentation, structure: SemanticStructure) -> RiskAssessment:
        """
        Comprehensive risk assessment using multiple dimensions.
        Returns a risk score from 0-100 and detailed reasons.
        """
        reasons = []
        risk_score = 0  # 0-100 score
        scores = Config.RISK_SCORES
        
        # 1. Context Risks (e.g. Infinite Approval)
        for ctx in structure.context:
            if ctx.risk_factor == "high":
                risk_score += scores.get("high_risk_param", 40)
                reasons.append(f"High Risk Param: {ctx.description}")
            elif ctx.risk_factor == "medium":
                risk_score += scores.get("medium_risk_param", 20)
                reasons.append(f"Warning: {ctx.description}")

        # 2. Action-based Risks
        action = structure.action.raw_value
        if action == "approve":
            risk_score += scores.get("approve", 15)
            if not any("Infinite" in r for r in reasons):
                reasons.append("Grants spending permission to contract")
        
        elif action == "transfer_asset":
             risk_score += scores.get("transfer", 25)
             reasons.append("Irreversible asset transfer")
             
             # Check amount
             amount_str = next((c.raw_value for c in structure.context if "Amount" in c.description), "0")
             if RiskEngine._check_high_value(amount_str):
                 risk_score += scores.get("high_value_transfer", 30)
                 reasons.append("High value transfer detected (> 1 ETH equivalent)")

        elif action == "authentication":
             # Generally safe, reduce risk
             risk_score = max(0, risk_score + scores.get("authentication", -10))
             reasons.append("Safe: Identity verification only")
             
        elif action == "authorization":
             risk_score += scores.get("authorization", 20)
             reasons.append("Off-chain authorization can be used for on-chain actions")
        
        elif action in ["bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"]:
            risk_score += scores.get("bridge", 30)
            reasons.append("Cross-chain bridge operation - verify destination chain")
        
        elif action == "governance_delegation":
            risk_score += scores.get("delegation", 25)
            reasons.append("Voting power delegation - delegate can vote on your behalf")
        
        elif action == "cross_contract_interaction":
            risk_score += scores.get("cross_contract", 20)
            reasons.append("Cross-contract operation - verify all involved contracts")

        # 3. Contract Reputation Assessment
        contract_risk, contract_reasons = RiskEngine._assess_contract_reputation(ir, structure)
        risk_score += contract_risk
        reasons.extend(contract_reasons)

        # 4. Amount Risk Assessment
        amount_risk, amount_reasons = RiskEngine._assess_amount_risk(ir, structure)
        risk_score += amount_risk
        reasons.extend(amount_reasons)

        # 5. Cross-chain Risk Assessment
        cross_chain_risk, cross_chain_reasons = RiskEngine._assess_cross_chain_risk(ir, structure)
        risk_score += cross_chain_risk
        reasons.extend(cross_chain_reasons)

        # 6. Delegation Risk Assessment
        delegation_risk, delegation_reasons = RiskEngine._assess_delegation_risk(ir, structure)
        risk_score += delegation_risk
        reasons.extend(delegation_reasons)

        # 7. Permission Scope Risk
        permission_scope = structure.permission_scope
        if permission_scope == "unlimited_permanent":
            risk_score += scores.get("unlimited_permanent", 50)
            reasons.append("Unlimited permanent permission - highest risk level")
        elif permission_scope == "unlimited_time_limited":
            risk_score += scores.get("unlimited_time_limited", 35)
            reasons.append("Unlimited time-limited permission - high risk")
        elif permission_scope == "specific_amount_permanent":
            risk_score += scores.get("permanent", 25)
            reasons.append("Permanent permission - requires manual revocation")

        # 8. Phishing Detection
        phishing_warnings = RiskEngine._detect_phishing_keywords(ir, structure)
        if phishing_warnings:
            risk_score += scores.get("phishing", 60)  # Phishing is always high risk
            reasons.extend(phishing_warnings)

        # 9. Technical Heuristics
        if ir.signature_type == "eth_sign":
            risk_score += scores.get("blind_signing", 50)
            reasons.append("Dangerous Signature Type: eth_sign (Blind Signing)")

        # 10. Unknown Contract Risk
        if ir.contract and not KnowledgeBase.get_contract_name(ir.chain_id, ir.contract):
            risk_score += scores.get("unknown_contract", 20)
            reasons.append("Unknown contract - verify contract address before proceeding")

        # Cap score at 100
        risk_score = min(100, risk_score)
        
        # Map score to level
        thresholds = Config.RISK_THRESHOLDS
        if risk_score >= thresholds["high"]:
            level = "high"
        elif risk_score >= thresholds["medium"]:
            level = "medium"
        else:
            level = "low"
        
        if not reasons:
            reasons.append("Standard operation")

        return RiskAssessment(level=level, reasons=reasons)

    @staticmethod
    def _detect_phishing_keywords(ir: IntermediateRepresentation, structure: SemanticStructure) -> List[str]:
        warnings = []
        # Gather all text content
        text_content = str(ir.params).lower() + " " + structure.action.description.lower()
        
        phishing_keywords = Config.PHISHING_KEYWORDS
        
        for category, keywords in phishing_keywords.items():
            for keyword in keywords:
                if keyword in text_content:
                    warnings.append(f"Phishing Warning: Detected '{keyword}' ({category})")
        return warnings

    @staticmethod
    def _assess_contract_reputation(ir: IntermediateRepresentation, structure: SemanticStructure) -> tuple[int, List[str]]:
        """
        Assess contract reputation based on known contracts database.
        """
        risk_score = 0
        reasons = []
        
        if not ir.contract:
            return risk_score, reasons
        
        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract)
        
        if contract_name:
            # Known reputable contracts reduce risk
            contract_lower = contract_name.lower()
            
            # Check for well-known protocols (negative risk = safer)
            reputable_patterns = [
                "uniswap", "aave", "compound", "opensea", "seaport", 
                "permit2", "1inch", "sushiswap"
            ]
            
            if any(pattern in contract_lower for pattern in reputable_patterns):
                risk_score -= 15  # Reduce risk for known protocols
                reasons.append(f"Known protocol: {contract_name}")
            else:
                risk_score += 10
                reasons.append(f"Lesser-known contract: {contract_name}")
        else:
            # Unknown contract increases risk
            risk_score += 20
            reasons.append("Unknown contract address")
        
        return max(0, risk_score), reasons
    
    @staticmethod
    def _assess_amount_risk(ir: IntermediateRepresentation, structure: SemanticStructure) -> tuple[int, List[str]]:
        """
        Assess risk based on amount and token type.
        """
        risk_score = 0
        reasons = []
        scores = Config.RISK_SCORES
        
        # Find amount values
        amount_ctx = [c for c in structure.context if "Amount" in c.description or "value" in c.description.lower()]
        
        for ctx in amount_ctx:
            amount = ctx.raw_value
            
            # Check for infinite amounts
            if KnowledgeBase.is_infinite_allowance(amount):
                risk_score += scores.get("high_risk_param", 40)
                reasons.append("Infinite amount - highest risk")
                continue
            
            # Check for high values
            try:
                amount_val = float(amount)
                if amount_val > Config.FINANCIAL_THRESHOLDS["high_value_eth"]:
                    risk_score += scores.get("high_value_transfer", 25)
                    reasons.append(f"High value operation: {amount_val / 1e18:.2f} ETH equivalent")
            except:
                pass
        
        return risk_score, reasons
    
    @staticmethod
    def _assess_cross_chain_risk(ir: IntermediateRepresentation, structure: SemanticStructure) -> tuple[int, List[str]]:
        """
        Assess risk for cross-chain operations.
        """
        risk_score = 0
        reasons = []
        scores = Config.RISK_SCORES
        
        # Check for bridge operations
        if structure.action.raw_value in ["bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"]:
            risk_score += scores.get("bridge", 30)
            reasons.append("Cross-chain bridge operation - verify destination chain")
        
        # Check for destination chain indicators
        for ctx in structure.context:
            if "Destination Chain" in ctx.description or "targetChain" in ctx.description.lower():
                risk_score += 25
                reasons.append(f"Cross-chain operation to chain: {ctx.raw_value}")
                break
        
        return risk_score, reasons
    
    @staticmethod
    def _assess_delegation_risk(ir: IntermediateRepresentation, structure: SemanticStructure) -> tuple[int, List[str]]:
        """
        Assess risk for delegation operations.
        """
        risk_score = 0
        reasons = []
        scores = Config.RISK_SCORES
        
        if structure.action.raw_value == "governance_delegation":
            risk_score += scores.get("delegation", 25)
            reasons.append("Voting power delegation - delegate can vote on your behalf")
        
        # Check for implicit delegation through permit
        if structure.action.raw_value == "authorization" and structure.permission_scope == "unlimited_permanent":
            risk_score += 20
            reasons.append("Implicit delegation - unlimited permanent permit can enable delegation")
        
        return risk_score, reasons
    
    @staticmethod
    def _check_high_value(amount: Any) -> bool:
        try:
            val = float(amount)
            if val > Config.FINANCIAL_THRESHOLDS["high_value_eth"]:
                return True
        except:
            pass
        return False
