"""
ETH Transaction Parameter Extractor
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
    """Transaction parameter extractor"""
    
    def __init__(self):
        self.function_signatures = self._load_function_signatures()
    
    def extract_contract_call_info(self, data: str) -> Optional[ContractCallInfo]:
        """
        Extract contract call information
        
        Args:
            data: Transaction data (hex format)
            
        Returns:
            ContractCallInfo: Contract call information, returns None if not a contract call
        """
        if not data or len(data) < 10:  # At least need function selector (4 bytes = 8 hex digits + 0x)
            return None
        
        # Extract function selector
        function_selector = data[:10]  # 0x + 8 hex digits
        
        # Get function information
        function_name = self._get_function_name(function_selector)
        function_signature = self._get_function_signature(function_selector)
        
        # Extract parameters
        parameters = {}
        if len(data) > 10:
            raw_params = data[10:]  # Remove function selector
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
        Extract token transfer information
        
        Args:
            call_info: Contract call information
            to_address: Contract address
            
        Returns:
            TokenInfo: Token information
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
        Extract gas-related information
        
        Args:
            transaction: Transaction data
            
        Returns:
            Dict: Gas information
        """
        gas_info = {}
        
        # Gas limit
        if 'gas' in transaction:
            gas_limit = self._parse_hex_number(transaction['gas'])
            gas_info['gas_limit'] = gas_limit
        
        # Gas price (Legacy)
        if 'gasPrice' in transaction:
            gas_price = self._parse_hex_number(transaction['gasPrice'])
            gas_info['gas_price'] = gas_price
            gas_info['gas_price_gwei'] = gas_price / (10**9) if gas_price else 0
        
        # EIP-1559 fees
        if 'maxFeePerGas' in transaction:
            max_fee = self._parse_hex_number(transaction['maxFeePerGas'])
            gas_info['max_fee_per_gas'] = max_fee
            gas_info['max_fee_per_gas_gwei'] = max_fee / (10**9) if max_fee else 0
        
        if 'maxPriorityFeePerGas' in transaction:
            priority_fee = self._parse_hex_number(transaction['maxPriorityFeePerGas'])
            gas_info['max_priority_fee_per_gas'] = priority_fee
            gas_info['max_priority_fee_per_gas_gwei'] = priority_fee / (10**9) if priority_fee else 0
        
        # Estimate total fee
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
        """Load function signature data"""
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
        """Get function name"""
        sig_info = self.function_signatures.get(selector)
        return sig_info['name'] if sig_info else None
    
    def _get_function_signature(self, selector: str) -> Optional[str]:
        """Get function signature"""
        sig_info = self.function_signatures.get(selector)
        return sig_info['signature'] if sig_info else None
    
    def _decode_parameters(self, selector: str, raw_params: str) -> Dict[str, Any]:
        """
        Decode function parameters
        
        Args:
            selector: Function selector
            raw_params: Raw parameter data
            
        Returns:
            Dict: Decoded parameters
        """
        sig_info = self.function_signatures.get(selector)
        if not sig_info:
            return {'raw': raw_params}
        
        params = {}
        param_types = sig_info.get('params', [])
        
        try:
            # Simple parameter decoding (each parameter is 32 bytes)
            for i, param_type in enumerate(param_types):
                start = i * 64  # 32 bytes = 64 hex digits
                end = start + 64
                
                if start >= len(raw_params):
                    break
                
                param_hex = raw_params[start:end]
                param_name = f"param_{i}"
                
                if param_type == 'address':
                    # Address type: take last 40 digits
                    address = '0x' + param_hex[-40:]
                    params[param_name] = address
                    
                elif param_type == 'uint256':
                    # 256-bit unsigned integer
                    value = int(param_hex, 16)
                    params[param_name] = value
                    
                elif param_type == 'bool':
                    # Boolean value
                    value = int(param_hex, 16) > 0
                    params[param_name] = value
                    
                else:
                    # Other types keep raw hex
                    params[param_name] = '0x' + param_hex
            
            return params
            
        except Exception as e:
            return {'raw': raw_params, 'decode_error': str(e)}
    
    def _extract_erc20_transfer(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """Extract ERC20 transfer information"""
        params = call_info.parameters
        
        # Get recipient address and amount
        to_address = params.get('param_0')  # address to
        amount = params.get('param_1')      # uint256 amount
        
        # Get token symbol
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _extract_erc20_approve(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """Extract ERC20 approve information"""
        params = call_info.parameters
        
        # Get spender address and amount
        spender = params.get('param_0')     # address spender
        amount = params.get('param_1')      # uint256 amount
        
        # Get token symbol
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _extract_erc20_transfer_from(self, call_info: ContractCallInfo, contract_address: str) -> TokenInfo:
        """Extract ERC20 transferFrom information"""
        params = call_info.parameters
        
        # Get sender address, recipient address and amount
        from_address = params.get('param_0')  # address from
        to_address = params.get('param_1')    # address to
        amount = params.get('param_2')        # uint256 amount
        
        # Get token symbol
        symbol = self._get_token_symbol(contract_address)
        
        return TokenInfo(
            address=contract_address,
            symbol=symbol,
            amount=str(amount) if amount else None,
            amount_formatted=self._format_token_amount(amount, symbol)
        )
    
    def _get_token_symbol(self, contract_address: str) -> Optional[str]:
        """Get token symbol"""
        if not contract_address:
            return None
        
        # Get from known contracts
        for addr, name in KnownContracts.CONTRACT_NAMES.items():
            if addr.lower() == contract_address.lower():
                return name
        
        return None
    
    def _format_token_amount(self, amount: Optional[int], symbol: Optional[str]) -> Optional[str]:
        """Format token amount"""
        if amount is None:
            return None
        
        # Use different decimals based on token type
        if symbol in ['USDT', 'USDC']:
            decimals = 6
        elif symbol in ['WETH']:
            decimals = 18
        else:
            decimals = 18  # Default 18 decimals
        
        # Format amount
        formatted = amount / (10 ** decimals)
        
        # If amount is very large, use scientific notation
        if formatted >= 1e6:
            return f"{formatted:.2e}"
        elif formatted >= 1000:
            return f"{formatted:,.2f}"
        else:
            return f"{formatted:.6f}".rstrip('0').rstrip('.')
    
    def _parse_hex_number(self, hex_str: str) -> Optional[int]:
        """Parse hexadecimal number"""
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
        """Validate Ethereum address format"""
        if not address:
            return False
        return bool(RegexPatterns.ETH_ADDRESS.match(address))
    
    def validate_hex_data(self, data: str) -> bool:
        """Validate hexadecimal data format"""
        if not data:
            return False
        return bool(RegexPatterns.HEX_DATA.match(data))
    
    def extract_addresses_from_data(self, data: str) -> List[str]:
        """Extract all addresses from transaction data"""
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