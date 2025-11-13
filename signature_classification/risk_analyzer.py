"""
风险分析器 - 评估签名安全风险
"""

from typing import Dict, List, Any, Union, Optional
from dataclasses import dataclass
from enum import Enum

from .signature_types import SignatureType, SecurityLevel


class RiskCategory(str, Enum):
    """风险类别"""
    FINANCIAL = "financial"  # 财务风险
    PRIVACY = "privacy"      # 隐私风险
    PHISHING = "phishing"    # 钓鱼风险
    TECHNICAL = "technical"  # 技术风险


@dataclass
class RiskFactor:
    """风险因子"""
    category: RiskCategory
    level: SecurityLevel
    description: str
    impact: str
    mitigation: str


@dataclass
class RiskAssessment:
    """风险评估结果"""
    overall_risk: SecurityLevel
    risk_score: float  # 0-100
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    should_proceed: bool
    warnings: List[str]


class RiskAnalyzer:
    """风险分析器"""
    
    def __init__(self):
        """初始化风险分析器"""
        self._init_risk_rules()
    
    def _init_risk_rules(self):
        """初始化风险规则"""
        
        # 钓鱼关键词
        self.phishing_keywords = {
            "urgent": ["urgent", "urgently", "immediately", "asap", "紧急", "立即", "马上"],
            "time_pressure": ["expires", "deadline", "limited time", "act now", "过期", "截止", "限时"],
            "authority": ["verify", "confirm", "validate", "verification required", "验证", "确认", "需要验证"],
            "reward": ["claim", "reward", "bonus", "prize", "free", "领取", "奖励", "免费"],
            "threat": ["suspend", "block", "disable", "freeze", "暂停", "冻结", "禁用"]
        }
        
        # 高风险合约地址模式（示例）
        self.high_risk_patterns = {
            "known_scam_contracts": [],  # 可以添加已知诈骗合约地址
            "suspicious_domains": ["bit.ly", "tinyurl.com", "t.co"]  # 短链接域名
        }
        
        # 财务风险阈值
        self.financial_thresholds = {
            "high_value_eth": 1000000000000000000,  # 1 ETH in wei
            "high_value_usd": 1000  # $1000 USD
        }
    
    def analyze_risk(self, 
                    signature_type: SignatureType, 
                    data: Union[str, Dict[str, Any]], 
                    context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        分析签名风险
        
        Args:
            signature_type: 签名类型
            data: 签名数据
            context: 上下文信息（可选）
            
        Returns:
            风险评估结果
        """
        risk_factors = []
        warnings = []
        
        # 基于签名类型的基础风险评估
        base_risks = self._assess_base_risks(signature_type)
        risk_factors.extend(base_risks)
        
        # 数据内容风险分析
        content_risks = self._analyze_content_risks(signature_type, data)
        risk_factors.extend(content_risks)
        
        # 钓鱼风险检测
        phishing_risks = self._detect_phishing_risks(data)
        risk_factors.extend(phishing_risks)
        
        # 技术风险评估
        technical_risks = self._assess_technical_risks(signature_type, data)
        risk_factors.extend(technical_risks)
        
        # 上下文风险分析
        if context:
            context_risks = self._analyze_context_risks(context)
            risk_factors.extend(context_risks)
        
        # 计算总体风险
        overall_risk, risk_score = self._calculate_overall_risk(risk_factors)
        
        # 生成建议
        recommendations = self._generate_recommendations(signature_type, risk_factors, overall_risk)
        
        # 判断是否应该继续
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
        """基于签名类型的基础风险评估"""
        risks = []
        
        if signature_type == SignatureType.ETH_SEND_TRANSACTION:
            risks.append(RiskFactor(
                category=RiskCategory.FINANCIAL,
                level=SecurityLevel.HIGH_RISK,
                description="链上交易将直接消耗Gas费用并可能转移资产",
                impact="可能导致资产损失和不可逆的状态变更",
                mitigation="仔细检查交易详情，确认接收地址和金额"
            ))
        
        elif signature_type == SignatureType.ETH_SIGN:
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.HIGH_RISK,
                description="eth_sign方法存在严重安全漏洞",
                impact="可能被恶意利用签署任意数据",
                mitigation="避免使用支持eth_sign的钱包，建议升级到现代钱包"
            ))
        
        elif signature_type == SignatureType.PERSONAL_SIGN:
            risks.append(RiskFactor(
                category=RiskCategory.PHISHING,
                level=SecurityLevel.MEDIUM_RISK,
                description="个人签名常被钓鱼网站滥用",
                impact="可能泄露身份信息或被用于恶意授权",
                mitigation="确认网站真实性，避免在可疑网站上签名"
            ))
        
        elif signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.MEDIUM_RISK,
                description="结构化签名可能包含复杂的授权逻辑",
                impact="可能授予第三方超出预期的权限",
                mitigation="仔细阅读签名内容，特别注意授权范围和有效期"
            ))
        
        return risks
    
    def _analyze_content_risks(self, signature_type: SignatureType, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """分析数据内容风险"""
        risks = []
        
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4 and isinstance(data, dict):
            # 检查EIP-712数据的风险
            message = data.get("message", {})
            
            # 检查授权金额
            if isinstance(message, dict):
                for key, value in message.items():
                    if key.lower() in ["amount", "value"] and isinstance(value, (str, int)):
                        try:
                            amount = int(value) if isinstance(value, int) else int(value, 16 if value.startswith("0x") else 10)
                            if amount > self.financial_thresholds["high_value_eth"]:
                                risks.append(RiskFactor(
                                    category=RiskCategory.FINANCIAL,
                                    level=SecurityLevel.HIGH_RISK,
                                    description=f"检测到高额授权金额: {amount}",
                                    impact="可能导致大额资产损失",
                                    mitigation="确认授权金额是否合理"
                                ))
                        except (ValueError, TypeError):
                            pass
                
                # 检查时间相关风险
                time_fields = ["endTime", "deadline", "expiry", "validUntil"]
                for field in time_fields:
                    if field in message:
                        risks.append(RiskFactor(
                            category=RiskCategory.TECHNICAL,
                            level=SecurityLevel.LOW_RISK,
                            description=f"签名包含时效限制: {field}",
                            impact="可能面临时间窗口攻击",
                            mitigation="注意签名的有效期限制"
                        ))
        
        return risks
    
    def _detect_phishing_risks(self, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """检测钓鱼风险"""
        risks = []
        
        # 将数据转换为文本进行关键词检测
        text_data = str(data).lower()
        
        # 检查钓鱼关键词
        for category, keywords in self.phishing_keywords.items():
            for keyword in keywords:
                if keyword in text_data:
                    risks.append(RiskFactor(
                        category=RiskCategory.PHISHING,
                        level=SecurityLevel.HIGH_RISK,
                        description=f"检测到钓鱼相关关键词: '{keyword}' (类别: {category})",
                        impact="可能是钓鱼攻击尝试",
                        mitigation="仔细核实网站真实性，避免在可疑环境中签名"
                    ))
        
        return risks
    
    def _assess_technical_risks(self, signature_type: SignatureType, data: Union[str, Dict[str, Any]]) -> List[RiskFactor]:
        """评估技术风险"""
        risks = []
        
        # 检查数据复杂度
        if isinstance(data, dict):
            depth = self._calculate_dict_depth(data)
            if depth > 3:
                risks.append(RiskFactor(
                    category=RiskCategory.TECHNICAL,
                    level=SecurityLevel.MEDIUM_RISK,
                    description=f"数据结构复杂度较高 (嵌套层级: {depth})",
                    impact="复杂结构可能隐藏恶意内容",
                    mitigation="仔细检查每个字段的含义"
                ))
        
        # 检查数据大小
        data_size = len(str(data))
        if data_size > 10000:  # 10KB
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.LOW_RISK,
                description=f"数据量较大 ({data_size} 字符)",
                impact="大量数据可能影响审查效率",
                mitigation="确保有足够时间审查所有内容"
            ))
        
        return risks
    
    def _analyze_context_risks(self, context: Dict[str, Any]) -> List[RiskFactor]:
        """分析上下文风险"""
        risks = []
        
        # 检查来源域名
        origin = context.get("origin", "")
        if origin:
            for suspicious_domain in self.high_risk_patterns["suspicious_domains"]:
                if suspicious_domain in origin:
                    risks.append(RiskFactor(
                        category=RiskCategory.PHISHING,
                        level=SecurityLevel.HIGH_RISK,
                        description=f"来源域名可疑: {origin}",
                        impact="可能来自钓鱼网站",
                        mitigation="验证网站的真实性"
                    ))
        
        # 检查用户代理
        user_agent = context.get("userAgent", "")
        if user_agent and "bot" in user_agent.lower():
            risks.append(RiskFactor(
                category=RiskCategory.TECHNICAL,
                level=SecurityLevel.MEDIUM_RISK,
                description="检测到自动化请求",
                impact="可能是脚本攻击",
                mitigation="确认操作是否为用户主动发起"
            ))
        
        return risks
    
    def _calculate_dict_depth(self, d: Dict[str, Any], depth: int = 0) -> int:
        """计算字典嵌套深度"""
        if not isinstance(d, dict):
            return depth
        
        max_depth = depth
        for value in d.values():
            if isinstance(value, dict):
                max_depth = max(max_depth, self._calculate_dict_depth(value, depth + 1))
        
        return max_depth
    
    def _calculate_overall_risk(self, risk_factors: List[RiskFactor]) -> tuple[SecurityLevel, float]:
        """计算总体风险级别和分数"""
        if not risk_factors:
            return SecurityLevel.MINIMAL_RISK, 0.0
        
        # 风险级别权重
        risk_weights = {
            SecurityLevel.HIGH_RISK: 80,
            SecurityLevel.MEDIUM_RISK: 50,
            SecurityLevel.LOW_RISK: 20,
            SecurityLevel.MINIMAL_RISK: 5
        }
        
        # 计算风险分数
        total_score = 0
        max_risk_level = SecurityLevel.MINIMAL_RISK
        
        for factor in risk_factors:
            score = risk_weights.get(factor.level, 0)
            total_score += score
            
            # 更新最高风险级别
            if factor.level == SecurityLevel.HIGH_RISK:
                max_risk_level = SecurityLevel.HIGH_RISK
            elif factor.level == SecurityLevel.MEDIUM_RISK and max_risk_level != SecurityLevel.HIGH_RISK:
                max_risk_level = SecurityLevel.MEDIUM_RISK
            elif factor.level == SecurityLevel.LOW_RISK and max_risk_level == SecurityLevel.MINIMAL_RISK:
                max_risk_level = SecurityLevel.LOW_RISK
        
        # 归一化分数到0-100
        normalized_score = min(100, total_score)
        
        # 根据分数调整风险级别
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
        """生成安全建议"""
        recommendations = []
        
        # 基于整体风险级别的建议
        if overall_risk == SecurityLevel.HIGH_RISK:
            recommendations.append("🚨 建议暂停操作，仔细评估风险后再决定是否继续")
            recommendations.append("🔍 建议寻求专业人士的意见")
        elif overall_risk == SecurityLevel.MEDIUM_RISK:
            recommendations.append("⚠️ 请谨慎操作，确认所有细节无误后再继续")
            recommendations.append("🔍 建议在测试环境中先行验证")
        
        # 基于签名类型的建议
        if signature_type == SignatureType.ETH_SEND_TRANSACTION:
            recommendations.append("💰 仔细检查交易金额和接收地址")
            recommendations.append("⛽ 注意Gas费用设置是否合理")
        elif signature_type == SignatureType.ETH_SIGN:
            recommendations.append("🚫 强烈建议避免使用eth_sign方法")
            recommendations.append("🔄 考虑使用更安全的签名方法")
        elif signature_type == SignatureType.PERSONAL_SIGN:
            recommendations.append("🌐 确认网站域名和SSL证书")
            recommendations.append("👁️ 仔细阅读要签名的消息内容")
        elif signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            recommendations.append("📋 仔细检查结构化数据的每个字段")
            recommendations.append("⏰ 注意签名的有效期和授权范围")
        
        # 基于具体风险因子的建议
        risk_categories = {factor.category for factor in risk_factors}
        
        if RiskCategory.PHISHING in risk_categories:
            recommendations.append("🎣 检测到钓鱼风险，请验证网站真实性")
        
        if RiskCategory.FINANCIAL in risk_categories:
            recommendations.append("💸 涉及财务操作，请确认金额和授权范围")
        
        # 去重并限制数量
        recommendations = list(dict.fromkeys(recommendations))  # 去重
        return recommendations[:8]  # 限制最多8条建议
    
    def _should_proceed(self, overall_risk: SecurityLevel, risk_score: float) -> bool:
        """判断是否应该继续操作"""
        
        # 高风险情况下不建议继续
        if overall_risk == SecurityLevel.HIGH_RISK:
            return False
        
        # 中等风险情况下需要用户仔细考虑
        if overall_risk == SecurityLevel.MEDIUM_RISK and risk_score > 70:
            return False
        
        return True
    
    def get_risk_summary(self, risk_assessment: RiskAssessment) -> str:
        """获取风险摘要"""
        
        risk_level_emoji = {
            SecurityLevel.HIGH_RISK: "🔴",
            SecurityLevel.MEDIUM_RISK: "🟡", 
            SecurityLevel.LOW_RISK: "🟢",
            SecurityLevel.MINIMAL_RISK: "🟢"
        }
        
        emoji = risk_level_emoji.get(risk_assessment.overall_risk, "⚪")
        
        summary = f"{emoji} 风险级别: {risk_assessment.overall_risk}\n"
        summary += f"风险评分: {risk_assessment.risk_score:.1f}/100\n"
        summary += f"风险因子数量: {len(risk_assessment.risk_factors)}\n"
        
        if not risk_assessment.should_proceed:
            summary += "⚠️ 不建议继续操作"
        else:
            summary += "✅ 可以谨慎继续"
        
        return summary 