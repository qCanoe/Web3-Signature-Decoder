"""
ETH Transaction Parser Data Models
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
import re


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    ETH_TRANSFER = "eth_transfer"           # ETH transfer
    TOKEN_TRANSFER = "token_transfer"       # Token transfer
    TOKEN_APPROVAL = "token_approval"       # Token approval
    CONTRACT_DEPLOY = "contract_deploy"     # Contract deployment
    CONTRACT_CALL = "contract_call"         # Contract call
    NFT_TRANSFER = "nft_transfer"          # NFT transfer
    NFT_APPROVAL = "nft_approval"          # NFT approval
    DEFI_SWAP = "defi_swap"                # DeFi swap
    DEFI_LIQUIDITY = "defi_liquidity"      # DeFi liquidity
    UNKNOWN = "unknown"                     # Unknown type


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContractCallInfo:
    """Contract call information"""
    function_selector: Optional[str] = None      # Function selector
    function_name: Optional[str] = None          # Function name
    function_signature: Optional[str] = None     # Function signature
    parameters: Dict[str, Any] = None            # Parsed parameters
    raw_data: Optional[str] = None               # Raw calldata
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class TokenInfo:
    """Token information"""
    address: Optional[str] = None                # Token contract address
    symbol: Optional[str] = None                 # Token symbol
    name: Optional[str] = None                   # Token name
    decimals: Optional[int] = None               # Decimals
    amount: Optional[str] = None                 # Amount
    amount_formatted: Optional[str] = None       # Formatted amount


@dataclass
class EthTransaction:
    """ETH transaction data"""
    # Basic transaction fields
    from_address: Optional[str] = None           # Sender address
    to_address: Optional[str] = None             # Recipient address
    value: Optional[str] = None                  # Transfer amount (wei)
    gas: Optional[str] = None                    # Gas limit
    gas_price: Optional[str] = None              # Gas price
    max_fee_per_gas: Optional[str] = None        # EIP-1559 max fee
    max_priority_fee_per_gas: Optional[str] = None  # EIP-1559 priority fee
    nonce: Optional[str] = None                  # Nonce
    data: Optional[str] = None                   # Transaction data
    
    # Parsed information
    value_eth: Optional[float] = None            # ETH amount
    gas_fee_eth: Optional[float] = None          # Estimated gas fee (ETH)
    is_contract_call: bool = False               # Whether it's a contract call
    is_value_transfer: bool = False              # Whether it contains ETH transfer
    
    def __post_init__(self):
        # Calculate ETH amount
        if self.value and self.value != "0x0":
            try:
                value_wei = int(self.value, 16) if self.value.startswith("0x") else int(self.value)
                self.value_eth = value_wei / (10**18)
            except (ValueError, TypeError):
                self.value_eth = 0.0
        
        # Determine if it's a contract call
        self.is_contract_call = bool(self.data and len(self.data) > 2)
        
        # Determine if it contains value transfer
        self.is_value_transfer = bool(self.value_eth and self.value_eth > 0)


@dataclass
class TransactionAnalysis:
    """Transaction analysis result"""
    # Original transaction
    transaction: EthTransaction
    
    # Analysis result
    transaction_type: TransactionType
    confidence: float                            # 置信度 0-1
    
    # 合约调用信息
    contract_call: Optional[ContractCallInfo] = None
    
    # 代币相关信息
    token_info: Optional[TokenInfo] = None
    
    # 风险分析
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: List[str] = None               # 风险因素
    security_warnings: List[str] = None          # 安全警告
    
    # 交易描述
    description: str = ""                        # 交易描述
    summary: str = ""                           # 交易摘要
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.security_warnings is None:
            self.security_warnings = []


# 常用的函数选择器
class FunctionSelectors:
    """常用函数选择器"""
    
    # ERC20 代币标准
    ERC20_TRANSFER = "0xa9059cbb"               # transfer(address,uint256)
    ERC20_APPROVE = "0x095ea7b3"                # approve(address,uint256)
    ERC20_TRANSFER_FROM = "0x23b872dd"          # transferFrom(address,address,uint256)
    ERC20_BALANCE_OF = "0x70a08231"             # balanceOf(address)
    
    # ERC721 NFT标准
    ERC721_TRANSFER_FROM = "0x23b872dd"         # transferFrom(address,address,uint256)
    ERC721_SAFE_TRANSFER_FROM = "0x42842e0e"    # safeTransferFrom(address,address,uint256)
    ERC721_APPROVE = "0x095ea7b3"               # approve(address,uint256)
    ERC721_SET_APPROVAL_FOR_ALL = "0xa22cb465"  # setApprovalForAll(address,bool)
    
    # Uniswap V2/V3
    UNISWAP_SWAP_EXACT_TOKENS = "0x38ed1739"    # swapExactTokensForTokens
    UNISWAP_SWAP_EXACT_ETH = "0x7ff36ab5"       # swapExactETHForTokens
    UNISWAP_ADD_LIQUIDITY = "0xe8e33700"        # addLiquidity
    
    # 常见的多签钱包
    MULTISIG_EXEC_TRANSACTION = "0x6a761202"    # execTransaction
    
    # Permit相关
    PERMIT = "0xd505accf"                       # permit(address,address,uint256,uint256,uint8,bytes32,bytes32)


class KnownContracts:
    """已知合约地址"""
    
    # 主要代币合约
    USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    USDC = "0xA0b86a33E6441d3e2d0a97c5907B18d5Be8e998e"
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    # DEX相关
    UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    
    # 知名合约标识
    CONTRACT_NAMES = {
        "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
        "0xA0b86a33E6441d3e2d0a97c5907B18d5Be8e998e": "USDC", 
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
        "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": "Uniswap V2 Router",
        "0xE592427A0AEce92De3Edee1F18E0157C05861564": "Uniswap V3 Router",
    }


class RegexPatterns:
    """正则表达式模式"""
    
    # 以太坊地址
    ETH_ADDRESS = re.compile(r'^0x[a-fA-F0-9]{40}$')
    
    # Hex数据
    HEX_DATA = re.compile(r'^0x[a-fA-F0-9]*$')
    
    # 数字格式
    HEX_NUMBER = re.compile(r'^0x[a-fA-F0-9]+$')
    DECIMAL_NUMBER = re.compile(r'^\d+$')


# 风险关键词
class RiskKeywords:
    """风险关键词"""
    
    HIGH_RISK_FUNCTIONS = [
        "approve",           # 无限授权风险
        "setApprovalForAll", # NFT无限授权
        "transfer",          # 转账操作
        "withdraw",          # 提取操作
    ]
    
    CRITICAL_RISK_FUNCTIONS = [
        "selfDestruct",      # 合约自毁
        "delegateCall",      # 委托调用
        "suicide",           # 合约销毁
    ]
    
    DEFI_FUNCTIONS = [
        "swap",              # 交换
        "addLiquidity",      # 添加流动性
        "removeLiquidity",   # 移除流动性
        "stake",             # 质押
        "unstake",           # 解除质押
    ] 