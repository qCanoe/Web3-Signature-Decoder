"""
Risk Analyzer - Assesses signature security risks
"""

from typing import Dict, List, Any, Union, Optional
from dataclasses import dataclass
from enum import Enum

from .signature_types import SignatureType, SecurityLevel


class RiskCategory(str, Enum):
    """Risk category"""
    FINANCIAL = "financial"  # Financial risk
    PRIVACY = "privacy"      # Privacy risk
    PHISHING = "phishing"    # Phishing risk
    TECHNICAL = "technical"  # Technical risk


@dataclass
class RiskFactor:
    """Risk factor"""
    category: RiskCategory
    level: SecurityLevel
    description: str
    impact: str
    mitigation: str


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    overall_risk: SecurityLevel
    risk_score: float  # 0-100
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    should_proceed: bool
    warnings: List[str]


class RiskAnalyzer:
    """Risk analyzer"""
    
    def __init__(self):
        """Initialize risk analyzer"""
        self._init_risk_rules()
    
    def _init_risk_rules(self):
        """Initialize risk rules"""
        
        # Phishing keywords
        self.phishing_keywords = {
            "urgent": ["urgent", "urgently", "immediately", "asap", "紧急", "立即", "马上"],
            "time_pressure": ["expires", "deadline", "limited time", "act now", "过期", "截止", "限时"],
            "authority": ["verify", "confirm", "validate", "verification required", "验证", "确认", "需要验证"],
            "reward": ["claim", "reward", "bonus", "prize", "free", "领取", "奖励", "免费"],
            "threat": ["suspend", "block", "disable", "freeze", "暂停", "冻结", "禁用"]
        }
        
        # High-risk contract address patterns (examples)
        self.high_risk_patterns = {
            "known_scam_contracts": [],  # Can add known scam contract addresses
            "suspicious_domains": ["bit.ly", "tinyurl.com", "t.co"]  # Short link domains
        }
        
        # Financial risk thresholds
        self.financial_thresholds = {
            "high_value_eth": 1000000000000000000,  # 1 ETH in wei
            "high_value_usd": 1000  # $1000 USD
        }
    
    def analyze_risk(self, 
                    signature_type: SignatureType, 
                    data: Union[str, Dict[str, Any]], 
                    context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        Analyze signature risk
        
        Args:
            signature_type: Signature type
            data: Signature data
            context: Context information (optional)
            
        Returns:
            Risk assessment result
        """
        risk_factors = []
        warnings = []
        
        # Base risk assessment based on signature type
        base_risks = self._assess_base_risks(signature_type)
        risk_factors.extend(base_risks)
        
        # Data content risk analysis
        content_risks = self._analyze_content_risks(signature_type, data)
        risk_factors.extend(content_risks)
        
        # Phishing risk detection
        phishing_risks = self._detect_phishing_risks(data)
        risk_factors.extend(phishing_risks)
        
        # Technical risk assessment
        technical_risks = self._assess_technical_risks(signature_type, data)
        risk_factors.extend(technical_risks)
        
        # Context risk analysis
        if context:
            context_risks = self._analyze_context_risks(context)
            risk_factors.extend(context_risks)
        
        # Calculate overall risk
        overall_risk, risk_score = self._calculate_overall_risk(risk_factors)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(signature_type, risk_factors, overall_risk)
        
        # Determine if should proceed
        should_proceed = self._should_proceed(overall_risk, risk_score)
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            should_proceed=should_proceed,
            warnings=warnings
        )
    
    def _assess_base_risks(self, signature_type: SignatureType) -> List[RiskFactor]:
        """Base risk assessment based on signature type"""
        risks = []
        
        if signature_type == SignatureType.ETH_SEND_TRANSACTION:
            risks.append(RiskFactor(
                category=RiskCategory.FINANCIAL,
                level=SecurityLevel.HIGH_RISK,
                description="On-chain transaction will directly consume gas fees and may transfer assets",
                impact="May cause asset loss and irreversible state changes",
                mitigation="Carefully check transaction details, confirm recipient address and amount"
            ))
        
        elif signature_type == SignatureType.ETH_SIGN:
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.HIGH_RISK,
                description="eth_sign method has serious security vulnerabilities",
                impact="May be maliciously exploited to sign arbitrary data",
                mitigation="Avoid using wallets that support eth_sign, recommend upgrading to modern wallets"
            ))
        
        elif signature_type == SignatureType.PERSONAL_SIGN:
            risks.append(RiskFactor(
                category=RiskCategory.PHISHING,
                level=SecurityLevel.MEDIUM_RISK,
                description="Personal signatures are frequently abused by phishing sites",
                impact="May leak identity information or be used for malicious authorization",
                mitigation="Confirm website authenticity, avoid signing on suspicious websites"
            ))
        
        elif signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.MEDIUM_RISK,
                description="Structured signatures may contain complex authorization logic",
                impact="May grant third parties permissions beyond expectations",
                mitigation="Carefully read signature content, pay special attention to authorization scope and validity period"
            ))
        
        return risks
    
    def _analyze_content_risks(self, signature_type: SignatureType, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """Analyze data content risks"""
        risks = []
        
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4 and isinstance(data, dict):
            # Check risks in EIP-712 data
            message = data.get("message", {})
            
            # Check authorization amount
            if isinstance(message, dict):
                for key, value in message.items():
                    if key.lower() in ["amount", "value"] and isinstance(value, (str, int)):
                        try:
                            amount = int(value) if isinstance(value, int) else int(value, 16 if value.startswith("0x") else 10)
                            if amount > self.financial_thresholds["high_value_eth"]:
                                risks.append(RiskFactor(
                                    category=RiskCategory.FINANCIAL,
                                    level=SecurityLevel.HIGH_RISK,
                                    description=f"Detected high authorization amount: {amount}",
                                    impact="May cause large asset loss",
                                    mitigation="Confirm if authorization amount is reasonable"
                                ))
                        except (ValueError, TypeError):
                            pass
                
                # Check time-related risks
                time_fields = ["endTime", "deadline", "expiry", "validUntil"]
                for field in time_fields:
                    if field in message:
                        risks.append(RiskFactor(
                            category=RiskCategory.TECHNICAL,
                            level=SecurityLevel.LOW_RISK,
                            description=f"Signature contains time limit: {field}",
                            impact="May face time window attacks",
                            mitigation="Pay attention to signature validity period limits"
                        ))
        
        return risks
    
    def _detect_phishing_risks(self, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """Detect phishing risks"""
        risks = []
        
        # Convert data to text for keyword detection
        text_data = str(data).lower()
        
        # Check phishing keywords
        for category, keywords in self.phishing_keywords.items():
            for keyword in keywords:
                if keyword in text_data:
                    risks.append(RiskFactor(
                        category=RiskCategory.PHISHING,
                        level=SecurityLevel.HIGH_RISK,
                        description=f"Detected phishing-related keyword: '{keyword}' (category: {category})",
                        impact="May be a phishing attack attempt",
                        mitigation="Carefully verify website authenticity, avoid signing in suspicious environments"
                    ))
        
        return risks
    
    def _assess_technical_risks(self, signature_type: SignatureType, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """Assess technical risks"""
        risks = []
        
        # Check data complexity
        if isinstance(data, dict):
            depth = self._calculate_dict_depth(data)
            if depth > 3:
                risks.append(RiskFactor(
                    category=RiskCategory.TECHNICAL,
                    level=SecurityLevel.MEDIUM_RISK,
                    description=f"Data structure complexity is high (nesting level: {depth})",
                    impact="Complex structures may hide malicious content",
                    mitigation="Carefully check the meaning of each field"
                ))
        
        # Check data size
        data_size = len(str(data))
        if data_size > 10000:  # 10KB
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.LOW_RISK,
                description=f"Large data volume ({data_size} characters)",
                impact="Large amounts of data may affect review efficiency",
                mitigation="Ensure sufficient time to review all content"
            ))
        
        return risks
    
    def _analyze_context_risks(self, context: Dict[str, Any]) -> List[RiskFactor]:
        """Analyze context risks"""
        risks = []
        
        # Check origin domain
        origin = context.get("origin", "")
        if origin:
            for suspicious_domain in self.high_risk_patterns["suspicious_domains"]:
                if suspicious_domain in origin:
                    risks.append(RiskFactor(
                        category=RiskCategory.PHISHING,
                        level=SecurityLevel.HIGH_RISK,
                        description=f"Suspicious origin domain: {origin}",
                        impact="May come from phishing website",
                        mitigation="Verify website authenticity"
                    ))
        
        # Check user agent
        user_agent = context.get("userAgent", "")
        if user_agent and "bot" in user_agent.lower():
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.MEDIUM_RISK,
                description="Detected automated request",
                impact="May be a script attack",
                mitigation="Confirm if operation is user-initiated"
            ))
        
        return risks
    
    def _calculate_dict_depth(self, d: Dict[str, Any], depth: int = 0) -> int:
        """Calculate dictionary nesting depth"""
        if not isinstance(d, dict):
            return depth
        
        max_depth = depth
        for value in d.values():
            if isinstance(value, dict):
                max_depth = max(max_depth, self._calculate_dict_depth(value, depth + 1))
        
        return max_depth
    
    def _calculate_overall_risk(self, risk_factors: List[RiskFactor]) -> tuple[SecurityLevel, float]:
        """Calculate overall risk level and score"""
        if not risk_factors:
            return SecurityLevel.MINIMAL_RISK, 0.0
        
        # Risk level weights
        risk_weights = {
            SecurityLevel.HIGH_RISK: 80,
            SecurityLevel.MEDIUM_RISK: 50,
            SecurityLevel.LOW_RISK: 20,
            SecurityLevel.MINIMAL_RISK: 5
        }
        
        # Calculate risk score
        total_score = 0
        max_risk_level = SecurityLevel.MINIMAL_RISK
        
        for factor in risk_factors:
            score = risk_weights.get(factor.level, 0)
            total_score += score
            
            # Update highest risk level
            if factor.level == SecurityLevel.HIGH_RISK:
                max_risk_level = SecurityLevel.HIGH_RISK
            elif factor.level == SecurityLevel.MEDIUM_RISK and max_risk_level != SecurityLevel.HIGH_RISK:
                max_risk_level = SecurityLevel.MEDIUM_RISK
            elif factor.level == SecurityLevel.LOW_RISK and max_risk_level == SecurityLevel.MINIMAL_RISK:
                max_risk_level = SecurityLevel.LOW_RISK
        
        # Normalize score to 0-100
        normalized_score = min(100, total_score)
        
        # Adjust risk level based on score
        if normalized_score >= 80:
            overall_risk = SecurityLevel.HIGH_RISK
        elif normalized_score >= 50:
            overall_risk = SecurityLevel.MEDIUM_RISK
        elif normalized_score >= 20:
            overall_risk = SecurityLevel.LOW_RISK
        else:
            overall_risk = SecurityLevel.MINIMAL_RISK
        
        return overall_risk, normalized_score
    
    def _generate_recommendations(self, signature_type: SignatureType, risk_factors: List[RiskFactor], overall_risk: SecurityLevel) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Recommendations based on overall risk level
        if overall_risk == SecurityLevel.HIGH_RISK:
            recommendations.append("🚨 Recommend pausing operation, carefully assess risks before deciding whether to continue")
            recommendations.append("🔍 Recommend seeking professional advice")
        elif overall_risk == SecurityLevel.MEDIUM_RISK:
            recommendations.append("⚠️ Please proceed with caution, confirm all details are correct before continuing")
            recommendations.append("🔍 Recommend testing in a test environment first")
        
        # Recommendations based on signature type
        if signature_type == SignatureType.ETH_SEND_TRANSACTION:
            recommendations.append("💰 Carefully check transaction amount and recipient address")
            recommendations.append("⛽ Pay attention to whether gas fee settings are reasonable")
        elif signature_type == SignatureType.ETH_SIGN:
            recommendations.append("🚫 Strongly recommend avoiding eth_sign method")
            recommendations.append("🔄 Consider using safer signature methods")
        elif signature_type == SignatureType.PERSONAL_SIGN:
            recommendations.append("🌐 Confirm website domain and SSL certificate")
            recommendations.append("👁️ Carefully read the message content to be signed")
        elif signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            recommendations.append("📋 Carefully check each field of structured data")
            recommendations.append("⏰ Pay attention to signature validity period and authorization scope")
        
        # Recommendations based on specific risk factors
        risk_categories = {factor.category for factor in risk_factors}
        
        if RiskCategory.PHISHING in risk_categories:
            recommendations.append("🎣 Phishing risk detected, please verify website authenticity")
        
        if RiskCategory.FINANCIAL in risk_categories:
            recommendations.append("💸 Financial operations involved, please confirm amount and authorization scope")
        
        # Deduplicate and limit quantity
        recommendations = list(dict.fromkeys(recommendations))  # Deduplicate
        return recommendations[:8]  # Limit to maximum 8 recommendations
    
    def _should_proceed(self, overall_risk: SecurityLevel, risk_score: float) -> bool:
        """Determine if operation should proceed"""
        
        # Do not recommend continuing in high-risk situations
        if overall_risk == SecurityLevel.HIGH_RISK:
            return False
        
        # Medium risk situations require user careful consideration
        if overall_risk == SecurityLevel.MEDIUM_RISK and risk_score > 70:
            return False
        
        return True
    
    def get_risk_summary(self, risk_assessment: RiskAssessment) -> str:
        """Get risk summary"""
        
        risk_level_emoji = {
            SecurityLevel.HIGH_RISK: "🔴",
            SecurityLevel.MEDIUM_RISK: "🟡", 
            SecurityLevel.LOW_RISK: "🟢",
            SecurityLevel.MINIMAL_RISK: "🟢"
        }
        
        emoji = risk_level_emoji.get(risk_assessment.overall_risk, "⚪")
        
        summary = f"{emoji} Risk level: {risk_assessment.overall_risk}\n"
        summary += f"Risk score: {risk_assessment.risk_score:.1f}/100\n"
        summary += f"Number of risk factors: {len(risk_assessment.risk_factors)}\n"
        
        if not risk_assessment.should_proceed:
            summary += "⚠️ Do not recommend continuing operation"
        else:
            summary += "✅ Can proceed with caution"
        
        return summary 