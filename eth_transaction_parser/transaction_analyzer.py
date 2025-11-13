"""
ETH Transaction 交易分析器
"""

from typing import Dict, Any, List, Optional
from .models import (
    EthTransaction, 
    TransactionAnalysis, 
    TransactionType, 
    RiskLevel,
    FunctionSelectors,
    KnownContracts,
    RiskKeywords
)
from .parameter_extractor import TransactionParameterExtractor


class TransactionAnalyzer:
    """交易分析器"""
    
    def __init__(self):
        self.parameter_extractor = TransactionParameterExtractor()
    
    def analyze(self, transaction: EthTransaction) -> TransactionAnalysis:
        """
        分析交易
        
        Args:
            transaction: 交易对象
            
        Returns:
            TransactionAnalysis: 分析结果
        """
        # 基础分析
        tx_type, confidence = self._classify_transaction_type(transaction)
        
        # 提取合约调用信息
        contract_call = None
        if transaction.is_contract_call and transaction.data:
            contract_call = self.parameter_extractor.extract_contract_call_info(transaction.data)
        
        # 提取代币信息
        token_info = None
        if contract_call and transaction.to_address:
            token_info = self.parameter_extractor.extract_token_transfer_info(
                contract_call, transaction.to_address
            )
        
        # 风险分析
        risk_level, risk_factors, security_warnings = self._analyze_risks(
            transaction, contract_call, token_info
        )
        
        # 生成描述
        description = self._generate_description(transaction, tx_type, contract_call, token_info)
        summary = self._generate_summary(transaction, tx_type, contract_call, token_info)
        
        return TransactionAnalysis(
            transaction=transaction,
            transaction_type=tx_type,
            confidence=confidence,
            contract_call=contract_call,
            token_info=token_info,
            risk_level=risk_level,
            risk_factors=risk_factors,
            security_warnings=security_warnings,
            description=description,
            summary=summary
        )
    
    def _classify_transaction_type(self, transaction: EthTransaction) -> tuple[TransactionType, float]:
        """
        分类交易类型
        
        Args:
            transaction: 交易对象
            
        Returns:
            tuple: (交易类型, 置信度)
        """
        # ETH转账
        if transaction.is_value_transfer and not transaction.is_contract_call:
            return TransactionType.ETH_TRANSFER, 1.0
        
        # 合约部署
        if not transaction.to_address and transaction.is_contract_call:
            return TransactionType.CONTRACT_DEPLOY, 1.0
        
        # 合约调用分析
        if transaction.is_contract_call and transaction.data:
            return self._classify_contract_call(transaction)
        
        # 包含ETH转账的合约调用
        if transaction.is_value_transfer and transaction.is_contract_call:
            return TransactionType.CONTRACT_CALL, 0.8
        
        return TransactionType.UNKNOWN, 0.0
    
    def _classify_contract_call(self, transaction: EthTransaction) -> tuple[TransactionType, float]:
        """
        分类合约调用类型
        
        Args:
            transaction: 交易对象
            
        Returns:
            tuple: (交易类型, 置信度)
        """
        if not transaction.data or len(transaction.data) < 10:
            return TransactionType.CONTRACT_CALL, 0.5
        
        function_selector = transaction.data[:10]
        
        # ERC20 代币操作
        if function_selector == FunctionSelectors.ERC20_TRANSFER:
            return TransactionType.TOKEN_TRANSFER, 0.95
        elif function_selector == FunctionSelectors.ERC20_APPROVE:
            return TransactionType.TOKEN_APPROVAL, 0.95
        elif function_selector == FunctionSelectors.ERC20_TRANSFER_FROM:
            return TransactionType.TOKEN_TRANSFER, 0.9
        
        # ERC721 NFT操作
        elif function_selector in [
            FunctionSelectors.ERC721_TRANSFER_FROM,
            FunctionSelectors.ERC721_SAFE_TRANSFER_FROM
        ]:
            return TransactionType.NFT_TRANSFER, 0.9
        elif function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
            return TransactionType.NFT_APPROVAL, 0.95
        
        # DeFi操作
        elif function_selector in [
            FunctionSelectors.UNISWAP_SWAP_EXACT_TOKENS,
            FunctionSelectors.UNISWAP_SWAP_EXACT_ETH
        ]:
            return TransactionType.DEFI_SWAP, 0.9
        elif function_selector == FunctionSelectors.UNISWAP_ADD_LIQUIDITY:
            return TransactionType.DEFI_LIQUIDITY, 0.9
        
        # 根据合约地址推断
        if transaction.to_address:
            contract_type = self._get_contract_type(transaction.to_address)
            if contract_type:
                return contract_type, 0.7
        
        return TransactionType.CONTRACT_CALL, 0.6
    
    def _get_contract_type(self, contract_address: str) -> Optional[TransactionType]:
        """根据合约地址推断类型"""
        known_contracts = {
            KnownContracts.UNISWAP_V2_ROUTER: TransactionType.DEFI_SWAP,
            KnownContracts.UNISWAP_V3_ROUTER: TransactionType.DEFI_SWAP,
        }
        
        return known_contracts.get(contract_address)
    
    def _analyze_risks(self, transaction: EthTransaction, contract_call, token_info) -> tuple[RiskLevel, List[str], List[str]]:
        """
        分析风险
        
        Args:
            transaction: 交易对象
            contract_call: 合约调用信息
            token_info: 代币信息
            
        Returns:
            tuple: (风险级别, 风险因素, 安全警告)
        """
        risk_factors = []
        security_warnings = []
        risk_level = RiskLevel.LOW
        
        # 基础风险检查
        if transaction.value_eth and transaction.value_eth > 10:
            risk_factors.append("大额ETH转账")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # 合约调用风险
        if contract_call:
            # 函数风险检查
            if contract_call.function_name in RiskKeywords.HIGH_RISK_FUNCTIONS:
                risk_factors.append(f"高风险函数调用: {contract_call.function_name}")
                risk_level = max(risk_level, RiskLevel.HIGH)
            
            # 授权风险
            if contract_call.function_selector == FunctionSelectors.ERC20_APPROVE:
                amount = contract_call.parameters.get('param_1', 0)
                if isinstance(amount, int) and amount > 10**30:  # 极大数值，可能是无限授权
                    risk_factors.append("疑似无限代币授权")
                    security_warnings.append("检测到可能的无限授权，请谨慎确认")
                    risk_level = max(risk_level, RiskLevel.HIGH)
            
            # NFT全部授权
            if contract_call.function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
                risk_factors.append("NFT全部授权")
                security_warnings.append("将授权操作者管理您的所有NFT")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # 代币风险
        if token_info:
            # 未知代币
            if not token_info.symbol:
                risk_factors.append("未知代币合约")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
            
            # 大额代币转移
            if token_info.amount_formatted:
                try:
                    amount_float = float(token_info.amount_formatted.replace(',', ''))
                    if amount_float > 100000:  # 大额转移
                        risk_factors.append("大额代币转移")
                        risk_level = max(risk_level, RiskLevel.MEDIUM)
                except (ValueError, AttributeError):
                    pass
        
        # 未知合约风险
        if transaction.to_address and not self._is_known_contract(transaction.to_address):
            if transaction.is_contract_call:
                risk_factors.append("未知合约调用")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Gas费用风险
        if hasattr(transaction, 'gas_fee_eth') and transaction.gas_fee_eth:
            if transaction.gas_fee_eth > 0.1:  # 高Gas费
                risk_factors.append("高Gas费用")
                security_warnings.append(f"预估Gas费用较高: {transaction.gas_fee_eth:.4f} ETH")
        
        return risk_level, risk_factors, security_warnings
    
    def _is_known_contract(self, address: str) -> bool:
        """检查是否为已知合约"""
        return address.lower() in [addr.lower() for addr in KnownContracts.CONTRACT_NAMES.keys()]
    
    def _generate_description(self, transaction: EthTransaction, tx_type: TransactionType, 
                            contract_call, token_info) -> str:
        """生成交易描述"""
        descriptions = {
            TransactionType.ETH_TRANSFER: self._describe_eth_transfer,
            TransactionType.TOKEN_TRANSFER: self._describe_token_transfer,
            TransactionType.TOKEN_APPROVAL: self._describe_token_approval,
            TransactionType.CONTRACT_DEPLOY: self._describe_contract_deploy,
            TransactionType.CONTRACT_CALL: self._describe_contract_call,
            TransactionType.NFT_TRANSFER: self._describe_nft_transfer,
            TransactionType.NFT_APPROVAL: self._describe_nft_approval,
            TransactionType.DEFI_SWAP: self._describe_defi_swap,
            TransactionType.DEFI_LIQUIDITY: self._describe_defi_liquidity,
        }
        
        describe_func = descriptions.get(tx_type, self._describe_unknown)
        return describe_func(transaction, contract_call, token_info)
    
    def _describe_eth_transfer(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述ETH转账"""
        amount = transaction.value_eth or 0
        to_addr = transaction.to_address or "未知地址"
        return f"向 {to_addr} 转账 {amount:.6f} ETH"
    
    def _describe_token_transfer(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述代币转账"""
        if not token_info:
            return "代币转账操作"
        
        symbol = token_info.symbol or "未知代币"
        amount = token_info.amount_formatted or "未知数量"
        
        if contract_call and contract_call.function_name == "transferFrom":
            return f"从其他地址转移 {amount} {symbol}"
        else:
            return f"转账 {amount} {symbol}"
    
    def _describe_token_approval(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述代币授权"""
        if not token_info:
            return "代币授权操作"
        
        symbol = token_info.symbol or "未知代币"
        amount = token_info.amount_formatted or "未知数量"
        
        # 检查是否为无限授权
        if contract_call and contract_call.parameters.get('param_1', 0) > 10**30:
            return f"无限授权 {symbol} 代币"
        else:
            return f"授权 {amount} {symbol} 代币"
    
    def _describe_contract_deploy(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述合约部署"""
        return "部署新智能合约"
    
    def _describe_contract_call(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述合约调用"""
        if contract_call and contract_call.function_name:
            return f"调用合约函数: {contract_call.function_name}"
        
        contract_name = KnownContracts.CONTRACT_NAMES.get(transaction.to_address or "", "未知合约")
        return f"调用 {contract_name} 合约"
    
    def _describe_nft_transfer(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述NFT转移"""
        return "转移NFT"
    
    def _describe_nft_approval(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述NFT授权"""
        if contract_call and contract_call.function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
            return "授权管理所有NFT"
        return "授权NFT"
    
    def _describe_defi_swap(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述DeFi交换"""
        contract_name = KnownContracts.CONTRACT_NAMES.get(transaction.to_address or "", "DEX")
        return f"在 {contract_name} 上交换代币"
    
    def _describe_defi_liquidity(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述DeFi流动性"""
        return "添加流动性"
    
    def _describe_unknown(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """描述未知交易"""
        return "未知类型的交易"
    
    def _generate_summary(self, transaction: EthTransaction, tx_type: TransactionType, 
                         contract_call, token_info) -> str:
        """生成交易摘要"""
        parts = []
        parts.append(f"类型: {tx_type.value}")
        
        if transaction.value_eth and transaction.value_eth > 0:
            parts.append(f"ETH: {transaction.value_eth:.6f}")
        
        if token_info and token_info.amount_formatted:
            symbol = token_info.symbol or "代币"
            parts.append(f"{symbol}: {token_info.amount_formatted}")
        
        if contract_call and contract_call.function_name:
            parts.append(f"函数: {contract_call.function_name}")
        
        return " | ".join(parts)
    
    def get_transaction_risks(self, analysis: TransactionAnalysis) -> Dict[str, Any]:
        """
        获取交易风险详情
        
        Args:
            analysis: 交易分析结果
            
        Returns:
            Dict: 风险详情
        """
        return {
            "risk_level": analysis.risk_level.value,
            "risk_score": self._calculate_risk_score(analysis),
            "risk_factors": analysis.risk_factors,
            "security_warnings": analysis.security_warnings,
            "recommendations": self._get_security_recommendations(analysis)
        }
    
    def _calculate_risk_score(self, analysis: TransactionAnalysis) -> int:
        """计算风险分数 (0-100)"""
        base_score = {
            RiskLevel.LOW: 10,
            RiskLevel.MEDIUM: 40,
            RiskLevel.HIGH: 70,
            RiskLevel.CRITICAL: 90
        }.get(analysis.risk_level, 0)
        
        # 根据风险因素数量调整
        factor_penalty = min(len(analysis.risk_factors) * 5, 20)
        
        return min(base_score + factor_penalty, 100)
    
    def _get_security_recommendations(self, analysis: TransactionAnalysis) -> List[str]:
        """获取安全建议"""
        recommendations = []
        
        if analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("请仔细审查交易详情再确认")
        
        if "无限授权" in str(analysis.risk_factors):
            recommendations.append("考虑设置有限的授权数量而非无限授权")
        
        if "未知合约" in str(analysis.risk_factors):
            recommendations.append("请验证合约地址的可信度")
        
        if analysis.transaction.value_eth and analysis.transaction.value_eth > 5:
            recommendations.append("大额转账请再次确认接收地址")
        
        if analysis.risk_level == RiskLevel.LOW:
            recommendations.append("交易风险较低，可以正常进行")
        
        return recommendations 