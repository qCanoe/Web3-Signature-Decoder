"""
ETH Transaction Analyzer
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
    """Transaction analyzer"""
    
    def __init__(self):
        self.parameter_extractor = TransactionParameterExtractor()
    
    def analyze(self, transaction: EthTransaction) -> TransactionAnalysis:
        """
        Analyze transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            TransactionAnalysis: Analysis result
        """
        # Basic analysis
        tx_type, confidence = self._classify_transaction_type(transaction)
        
        # Extract contract call information
        contract_call = None
        if transaction.is_contract_call and transaction.data:
            contract_call = self.parameter_extractor.extract_contract_call_info(transaction.data)
        
        # Extract token information
        token_info = None
        if contract_call and transaction.to_address:
            token_info = self.parameter_extractor.extract_token_transfer_info(
                contract_call, transaction.to_address
            )
        
        # Risk analysis
        risk_level, risk_factors, security_warnings = self._analyze_risks(
            transaction, contract_call, token_info
        )
        
        # Generate description
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
        Classify transaction type
        
        Args:
            transaction: Transaction object
            
        Returns:
            tuple: (Transaction type, confidence)
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
        Classify contract call type
        
        Args:
            transaction: Transaction object
            
        Returns:
            tuple: (Transaction type, confidence)
        """
        if not transaction.data or len(transaction.data) < 10:
            return TransactionType.CONTRACT_CALL, 0.5
        
        function_selector = transaction.data[:10]
        
        # ERC20 token operations
        if function_selector == FunctionSelectors.ERC20_TRANSFER:
            return TransactionType.TOKEN_TRANSFER, 0.95
        elif function_selector == FunctionSelectors.ERC20_APPROVE:
            return TransactionType.TOKEN_APPROVAL, 0.95
        elif function_selector == FunctionSelectors.ERC20_TRANSFER_FROM:
            return TransactionType.TOKEN_TRANSFER, 0.9
        
        # ERC721 NFT operations
        elif function_selector in [
            FunctionSelectors.ERC721_TRANSFER_FROM,
            FunctionSelectors.ERC721_SAFE_TRANSFER_FROM
        ]:
            return TransactionType.NFT_TRANSFER, 0.9
        elif function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
            return TransactionType.NFT_APPROVAL, 0.95
        
        # DeFi operations
        elif function_selector in [
            FunctionSelectors.UNISWAP_SWAP_EXACT_TOKENS,
            FunctionSelectors.UNISWAP_SWAP_EXACT_ETH
        ]:
            return TransactionType.DEFI_SWAP, 0.9
        elif function_selector == FunctionSelectors.UNISWAP_ADD_LIQUIDITY:
            return TransactionType.DEFI_LIQUIDITY, 0.9
        
        # Infer from contract address
        if transaction.to_address:
            contract_type = self._get_contract_type(transaction.to_address)
            if contract_type:
                return contract_type, 0.7
        
        return TransactionType.CONTRACT_CALL, 0.6
    
    def _get_contract_type(self, contract_address: str) -> Optional[TransactionType]:
        """Infer type from contract address"""
        known_contracts = {
            KnownContracts.UNISWAP_V2_ROUTER: TransactionType.DEFI_SWAP,
            KnownContracts.UNISWAP_V3_ROUTER: TransactionType.DEFI_SWAP,
        }
        
        return known_contracts.get(contract_address)
    
    def _analyze_risks(self, transaction: EthTransaction, contract_call, token_info) -> tuple[RiskLevel, List[str], List[str]]:
        """
        Analyze risks
        
        Args:
            transaction: Transaction object
            contract_call: Contract call information
            token_info: Token information
            
        Returns:
            tuple: (Risk level, risk factors, security warnings)
        """
        risk_factors = []
        security_warnings = []
        risk_level = RiskLevel.LOW
        
        # Basic risk checks
        if transaction.value_eth and transaction.value_eth > 10:
            risk_factors.append("Large ETH transfer")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Contract call risks
        if contract_call:
            # Function risk checks
            if contract_call.function_name in RiskKeywords.HIGH_RISK_FUNCTIONS:
                risk_factors.append(f"High-risk function call: {contract_call.function_name}")
                risk_level = max(risk_level, RiskLevel.HIGH)
            
            # Approval risks
            if contract_call.function_selector == FunctionSelectors.ERC20_APPROVE:
                amount = contract_call.parameters.get('param_1', 0)
                if isinstance(amount, int) and amount > 10**30:  # Very large value, possibly unlimited approval
                    risk_factors.append("Suspected unlimited token approval")
                    security_warnings.append("Detected possible unlimited approval, please confirm carefully")
                    risk_level = max(risk_level, RiskLevel.HIGH)
            
            # NFT full approval
            if contract_call.function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
                risk_factors.append("NFT full approval")
                security_warnings.append("Will authorize operator to manage all your NFTs")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Token risks
        if token_info:
            # Unknown token
            if not token_info.symbol:
                risk_factors.append("Unknown token contract")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
            
            # Large token transfer
            if token_info.amount_formatted:
                try:
                    amount_float = float(token_info.amount_formatted.replace(',', ''))
                    if amount_float > 100000:  # Large transfer
                        risk_factors.append("Large token transfer")
                        risk_level = max(risk_level, RiskLevel.MEDIUM)
                except (ValueError, AttributeError):
                    pass
        
        # Unknown contract risks
        if transaction.to_address and not self._is_known_contract(transaction.to_address):
            if transaction.is_contract_call:
                risk_factors.append("Unknown contract call")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Gas fee risks
        if hasattr(transaction, 'gas_fee_eth') and transaction.gas_fee_eth:
            if transaction.gas_fee_eth > 0.1:  # High gas fee
                risk_factors.append("High gas fee")
                security_warnings.append(f"Estimated gas fee is high: {transaction.gas_fee_eth:.4f} ETH")
        
        return risk_level, risk_factors, security_warnings
    
    def _is_known_contract(self, address: str) -> bool:
        """Check if it's a known contract"""
        return address.lower() in [addr.lower() for addr in KnownContracts.CONTRACT_NAMES.keys()]
    
    def _generate_description(self, transaction: EthTransaction, tx_type: TransactionType, 
                            contract_call, token_info) -> str:
        """Generate transaction description"""
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
        """Describe ETH transfer"""
        amount = transaction.value_eth or 0
        to_addr = transaction.to_address or "Unknown address"
        return f"Transfer {amount:.6f} ETH to {to_addr}"
    
    def _describe_token_transfer(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe token transfer"""
        if not token_info:
            return "Token transfer operation"
        
        symbol = token_info.symbol or "Unknown token"
        amount = token_info.amount_formatted or "Unknown amount"
        
        if contract_call and contract_call.function_name == "transferFrom":
            return f"Transfer {amount} {symbol} from another address"
        else:
            return f"Transfer {amount} {symbol}"
    
    def _describe_token_approval(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe token approval"""
        if not token_info:
            return "Token approval operation"
        
        symbol = token_info.symbol or "Unknown token"
        amount = token_info.amount_formatted or "Unknown amount"
        
        # Check if it's unlimited approval
        if contract_call and contract_call.parameters.get('param_1', 0) > 10**30:
            return f"Unlimited approval for {symbol} token"
        else:
            return f"Approve {amount} {symbol} token"
    
    def _describe_contract_deploy(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe contract deployment"""
        return "Deploy new smart contract"
    
    def _describe_contract_call(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe contract call"""
        if contract_call and contract_call.function_name:
            return f"Call contract function: {contract_call.function_name}"
        
        contract_name = KnownContracts.CONTRACT_NAMES.get(transaction.to_address or "", "Unknown contract")
        return f"Call {contract_name} contract"
    
    def _describe_nft_transfer(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe NFT transfer"""
        return "Transfer NFT"
    
    def _describe_nft_approval(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe NFT approval"""
        if contract_call and contract_call.function_selector == FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL:
            return "Approve operator to manage all NFTs"
        return "Approve NFT"
    
    def _describe_defi_swap(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe DeFi swap"""
        contract_name = KnownContracts.CONTRACT_NAMES.get(transaction.to_address or "", "DEX")
        return f"Swap tokens on {contract_name}"
    
    def _describe_defi_liquidity(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe DeFi liquidity"""
        return "Add liquidity"
    
    def _describe_unknown(self, transaction: EthTransaction, contract_call, token_info) -> str:
        """Describe unknown transaction"""
        return "Unknown transaction type"
    
    def _generate_summary(self, transaction: EthTransaction, tx_type: TransactionType, 
                         contract_call, token_info) -> str:
        """Generate transaction summary"""
        parts = []
        parts.append(f"Type: {tx_type.value}")
        
        if transaction.value_eth and transaction.value_eth > 0:
            parts.append(f"ETH: {transaction.value_eth:.6f}")
        
        if token_info and token_info.amount_formatted:
            symbol = token_info.symbol or "Token"
            parts.append(f"{symbol}: {token_info.amount_formatted}")
        
        if contract_call and contract_call.function_name:
            parts.append(f"Function: {contract_call.function_name}")
        
        return " | ".join(parts)
    
    def get_transaction_risks(self, analysis: TransactionAnalysis) -> Dict[str, Any]:
        """
        Get transaction risk details
        
        Args:
            analysis: Transaction analysis result
            
        Returns:
            Dict: Risk details
        """
        return {
            "risk_level": analysis.risk_level.value,
            "risk_score": self._calculate_risk_score(analysis),
            "risk_factors": analysis.risk_factors,
            "security_warnings": analysis.security_warnings,
            "recommendations": self._get_security_recommendations(analysis)
        }
    
    def _calculate_risk_score(self, analysis: TransactionAnalysis) -> int:
        """Calculate risk score (0-100)"""
        base_score = {
            RiskLevel.LOW: 10,
            RiskLevel.MEDIUM: 40,
            RiskLevel.HIGH: 70,
            RiskLevel.CRITICAL: 90
        }.get(analysis.risk_level, 0)
        
        # Adjust based on number of risk factors
        factor_penalty = min(len(analysis.risk_factors) * 5, 20)
        
        return min(base_score + factor_penalty, 100)
    
    def _get_security_recommendations(self, analysis: TransactionAnalysis) -> List[str]:
        """Get security recommendations"""
        recommendations = []
        
        if analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Please carefully review transaction details before confirming")
        
        if "unlimited" in str(analysis.risk_factors).lower() or "Unlimited" in str(analysis.risk_factors):
            recommendations.append("Consider setting a limited approval amount instead of unlimited approval")
        
        if "Unknown contract" in str(analysis.risk_factors):
            recommendations.append("Please verify the trustworthiness of the contract address")
        
        if analysis.transaction.value_eth and analysis.transaction.value_eth > 5:
            recommendations.append("Please double-check the recipient address for large transfers")
        
        if analysis.risk_level == RiskLevel.LOW:
            recommendations.append("Transaction risk is low, can proceed normally")
        
        return recommendations 