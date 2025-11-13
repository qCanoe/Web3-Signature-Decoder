"""
ETH Transaction 参数提取器
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from .models import (
    FunctionSelectors, 
    KnownContracts, 
    RegexPatterns, 
    ContractCallInfo,
    TokenInfo
)


class TransactionParameterExtractor:
    """交易参数提取器"""
    
    def __init__(self):
        self.function_signatures = self._load_function_signatures()
    
    def extract_contract_call_info(self, data: str) -> Optional[ContractCallInfo]:
        """
        提取合约调用信息
        
        Args:
            data: 交易数据 (hex格式)
            
        Returns:
            ContractCallInfo: 合约调用信息，如果不是合约调用则返回None
        """
        if not data or len(data) < 10:  # 至少要有函数选择器 (4字节 = 8位hex + 0x)
            return None
        
        # 提取函数选择器
        function_selector = data[:10]  # 0x + 8位hex
        
        # 获取函数信息
        function_name = self._get_function_name(function_selector)
        function_signature = self._get_function_signature(function_selector)
        
        # 提取参数
        parameters = {}
        if len(data) > 10:
            raw_params = data[10:]  # 去掉函数选择器
            parameters = self._decode_parameters(function_selector, raw_params)
        
        return ContractCallInfo(
            function_selector=function_selector,
            function_name=function_name,
            function_signature=function_signature,
            parameters=parameters,
            raw_data=data
        )
    
    def extract_token_transfer_info(self, call_info: ContractCallInfo, to_address: str) -> Optional[TokenInfo]:
        """
        提取代币转账信息
        
        Args:
            call_info: 合约调用信息
            to_address: 合约地址
            
        Returns:
            TokenInfo: 代币信息
        """
        if not call_info or not call_info.function_selector:
            return None
        
        selector = call_info.function_selector
        
        # ERC20 transfer
        if selector == FunctionSelectors.ERC20_TRANSFER:
            return self._extract_erc20_transfer(call_info, to_address)
        
        # ERC20 approve
        elif selector == FunctionSelectors.ERC20_APPROVE:
            return self._extract_erc20_approve(call_info, to_address)
        
        # ERC20 transferFrom
        elif selector == FunctionSelectors.ERC20_TRANSFER_FROM:
            return self._extract_erc20_transfer_from(call_info, to_address)
        
        return None
    
    def extract_gas_info(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取Gas相关信息
        
        Args:
            transaction: 交易数据
            
        Returns:
            Dict: Gas信息
        """
        gas_info = {}
        
        # Gas限制
        if 'gas' in transaction:
            gas_limit = self._parse_hex_number(transaction['gas'])
            gas_info['gas_limit'] = gas_limit
        
        # Gas价格 (Legacy)
        if 'gasPrice' in transaction:
            gas_price = self._parse_hex_number(transaction['gasPrice'])
            gas_info['gas_price'] = gas_price
            gas_info['gas_price_gwei'] = gas_price / (10**9) if gas_price else 0
        
        # EIP-1559 费用
        if 'maxFeePerGas' in transaction:
            max_fee = self._parse_hex_number(transaction['maxFeePerGas'])
            gas_info['max_fee_per_gas'] = max_fee
            gas_info['max_fee_per_gas_gwei'] = max_fee / (10**9) if max_fee else 0
        
        if 'maxPriorityFeePerGas' in transaction:
            priority_fee = self._parse_hex_number(transaction['maxPriorityFeePerGas'])
            gas_info['max_priority_fee_per_gas'] = priority_fee
            gas_info['max_priority_fee_per_gas_gwei'] = priority_fee / (10**9) if priority_fee else 0
        
        # 估算总费用
        if 'gas_limit' in gas_info:
            if 'gas_price' in gas_info:
                total_fee = gas_info['gas_limit'] * gas_info['gas_price']
                gas_info['estimated_fee_wei'] = total_fee
                gas_info['estimated_fee_eth'] = total_fee / (10**18)
            elif 'max_fee_per_gas' in gas_info:
                total_fee = gas_info['gas_limit'] * gas_info['max_fee_per_gas']
                gas_info['estimated_max_fee_wei'] = total_fee
                gas_info['estimated_max_fee_eth'] = total_fee / (10**18)
        
        return gas_info
    
    def _load_function_signatures(self) -> Dict[str, Dict[str, str]]:
        """加载函数签名数据"""
        return {
            FunctionSelectors.ERC20_TRANSFER: {
                'name': 'transfer',
                'signature': 'transfer(address,uint256)',
                'params': ['address', 'uint256']
            },
            FunctionSelectors.ERC20_APPROVE: {
                'name': 'approve',
                'signature': 'approve(address,uint256)',
                'params': ['address', 'uint256']
            },
            FunctionSelectors.ERC20_TRANSFER_FROM: {
                'name': 'transferFrom',
                'signature': 'transferFrom(address,address,uint256)',
                'params': ['address', 'address', 'uint256']
            },
            FunctionSelectors.ERC721_TRANSFER_FROM: {
                'name': 'transferFrom',
                'signature': 'transferFrom(address,address,uint256)',
                'params': ['address', 'address', 'uint256']
            },
            FunctionSelectors.ERC721_SAFE_TRANSFER_FROM: {
                'name': 'safeTransferFrom',
                'signature': 'safeTransferFrom(address,address,uint256)',
                'params': ['address', 'address', 'uint256']
            },
            FunctionSelectors.ERC721_APPROVE: {
                'name': 'approve',
                'signature': 'approve(address,uint256)',
                'params': ['address', 'uint256']
            },
            FunctionSelectors.ERC721_SET_APPROVAL_FOR_ALL: {
                'name': 'setApprovalForAll',
                'signature': 'setApprovalForAll(address,bool)',
                'params': ['address', 'bool']
            },
            FunctionSelectors.UNISWAP_SWAP_EXACT_TOKENS: {
                'name': 'swapExactTokensForTokens',
                'signature': 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)',
                'params': ['uint256', 'uint256', 'address[]', 'address', 'uint256']
            },
            FunctionSelectors.UNISWAP_SWAP_EXACT_ETH: {
                'name': 'swapExactETHForTokens',
                'signature': 'swapExactETHForTokens(uint256,address[],address,uint256)',
                'params': ['uint256', 'address[]', 'address', 'uint256']
            },
        }
    
    def _get_function_name(self, selector: str) -> Optional[str]:
        """获取函数名称"""
        sig_info = self.function_signatures.get(selector)
        return sig_info['name'] if sig_info else None
    
    def _get_function_signature(self, selector: str) -> Optional[str]:
        """获取函数签名"""
        sig_info = self.function_signatures.get(selector)
        return sig_info['signature'] if sig_info else None
    
    def _decode_parameters(self, selector: str, raw_params: str) -> Dict[str, Any]:
        """
        解码函数参数
        
        Args:
            selector: 函数选择器
            raw_params: 原始参数数据
            
        Returns:
            Dict: 解码后的参数
        """
        sig_info = self.function_signatures.get(selector)
        if not sig_info:
            return {'raw': raw_params}
        
        params = {}
        param_types = sig_info.get('params', [])
        
        try:
            # 简单的参数解码 (每个参数32字节)
            for i, param_type in enumerate(param_types):
                start = i * 64  # 32字节 = 64位hex
                end = start + 64
                
                if start >= len(raw_params):
                    break
                
                param_hex = raw_params[start:end]
                param_name = f"param_{i}"
                
                if param_type == 'address':
                    # 地址类型：取后40位
                    address = '0x' + param_hex[-40:]
                    params[param_name] = address
                    
                elif param_type == 'uint256':
                    # 256位无符号整数
                    value = int(param_hex, 16)
                    params[param_name] = value
                    
                elif param_type == 'bool':
                    # 布尔值
                    value = int(param_hex, 16) > 0
                    params[param_name] = value
                    
                else:
                    # 其他类型保持原始hex
                    params[param_name] = '0x' + param_hex
            
            return params
            
        except Exception as e:
            return {'raw': raw_params, 'decode_error': str(e)}
    
    def _extract_erc20_transfer(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """提取ERC20 transfer信息"""
        params = call_info.parameters
        
        # 获取接收地址和数量
        to_address = params.get('param_0')  # address to
        amount = params.get('param_1')      # uint256 amount
        
        # 获取代币符号
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _extract_erc20_approve(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """提取ERC20 approve信息"""
        params = call_info.parameters
        
        # 获取授权地址和数量
        spender = params.get('param_0')     # address spender
        amount = params.get('param_1')      # uint256 amount
        
        # 获取代币符号
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _extract_erc20_transfer_from(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """提取ERC20 transferFrom信息"""
        params = call_info.parameters
        
        # 获取发送地址、接收地址和数量
        from_address = params.get('param_0')  # address from
        to_address = params.get('param_1')    # address to
        amount = params.get('param_2')        # uint256 amount
        
        # 获取代币符号
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _get_token_symbol(self, contract_address: str) -> Optional[str]:
        """获取代币符号"""
        if not contract_address:
            return None
        
        # 从已知合约获取
        for addr, name in KnownContracts.CONTRACT_NAMES.items():
            if addr.lower() == contract_address.lower():
                return name
        
        return None
    
    def _format_token_amount(self, amount: Optional[int], symbol: Optional[str]) -> Optional[str]:
        """格式化代币数量"""
        if amount is None:
            return None
        
        # 根据代币类型使用不同的精度
        if symbol in ['USDT', 'USDC']:
            decimals = 6
        elif symbol in ['WETH']:
            decimals = 18
        else:
            decimals = 18  # 默认18位精度
        
        # 格式化数量
        formatted = amount / (10 ** decimals)
        
        # 如果数量很大，使用科学计数法
        if formatted >= 1e6:
            return f"{formatted:.2e}"
        elif formatted >= 1000:
            return f"{formatted:,.2f}"
        else:
            return f"{formatted:.6f}".rstrip('0').rstrip('.')
    
    def _parse_hex_number(self, hex_str: str) -> Optional[int]:
        """解析十六进制数字"""
        if not hex_str:
            return None
        
        try:
            if hex_str.startswith('0x'):
                return int(hex_str, 16)
            else:
                return int(hex_str)
        except (ValueError, TypeError):
            return None
    
    def validate_address(self, address: str) -> bool:
        """验证以太坊地址格式"""
        if not address:
            return False
        return bool(RegexPatterns.ETH_ADDRESS.match(address))
    
    def validate_hex_data(self, data: str) -> bool:
        """验证十六进制数据格式"""
        if not data:
            return False
        return bool(RegexPatterns.HEX_DATA.match(data))
    
    def extract_addresses_from_data(self, data: str) -> List[str]:
        """从交易数据中提取所有地址"""
        addresses = []
        
        if not data or len(data) < 10:
            return addresses
        
        # 移除函数选择器
        param_data = data[10:]
        
        # 每32字节检查一次，看是否是地址
        for i in range(0, len(param_data), 64):
            chunk = param_data[i:i+64]
            if len(chunk) == 64:
                # 检查是否可能是地址 (前24字节为0)
                if chunk[:24] == '0' * 24:
                    potential_address = '0x' + chunk[24:]
                    if self.validate_address(potential_address):
                        addresses.append(potential_address)
        
        return addresses 