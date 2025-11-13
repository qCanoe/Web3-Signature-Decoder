"""
ETH Transaction 解析器的数据模型
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
import re


class TransactionType(str, Enum):
    """交易类型枚举"""
    ETH_TRANSFER = "eth_transfer"           # ETH转账
    TOKEN_TRANSFER = "token_transfer"       # 代币转账
    TOKEN_APPROVAL = "token_approval"       # 代币授权
    CONTRACT_DEPLOY = "contract_deploy"     # 合约部署
    CONTRACT_CALL = "contract_call"         # 合约调用
    NFT_TRANSFER = "nft_transfer"          # NFT转移
    NFT_APPROVAL = "nft_approval"          # NFT授权
    DEFI_SWAP = "defi_swap"                # DeFi交换
    DEFI_LIQUIDITY = "defi_liquidity"      # DeFi流动性
    UNKNOWN = "unknown"                     # 未知类型


class RiskLevel(str, Enum):
    """风险级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContractCallInfo:
    """合约调用信息"""
    function_selector: Optional[str] = None      # 函数选择器
    function_name: Optional[str] = None          # 函数名称
    function_signature: Optional[str] = None     # 函数签名
    parameters: Dict[str, Any] = None            # 解析的参数
    raw_data: Optional[str] = None               # 原始calldata
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class TokenInfo:
    """代币信息"""
    address: Optional[str] = None                # 代币合约地址
    symbol: Optional[str] = None                 # 代币符号
    name: Optional[str] = None                   # 代币名称
    decimals: Optional[int] = None               # 精度
    amount: Optional[str] = None                 # 数量
    amount_formatted: Optional[str] = None       # 格式化后的数量


@dataclass
class EthTransaction:
    """ETH交易数据"""
    # 基本交易字段
    from_address: Optional[str] = None           # 发送方地址
    to_address: Optional[str] = None             # 接收方地址
    value: Optional[str] = None                  # 转账金额 (wei)
    gas: Optional[str] = None                    # Gas限制
    gas_price: Optional[str] = None              # Gas价格
    max_fee_per_gas: Optional[str] = None        # EIP-1559 最大费用
    max_priority_fee_per_gas: Optional[str] = None  # EIP-1559 优先费用
    nonce: Optional[str] = None                  # Nonce
    data: Optional[str] = None                   # 交易数据
    
    # 解析后的信息
    value_eth: Optional[float] = None            # ETH金额
    gas_fee_eth: Optional[float] = None          # 预估Gas费用(ETH)
    is_contract_call: bool = False               # 是否为合约调用
    is_value_transfer: bool = False              # 是否包含ETH转账
    
    def __post_init__(self):
        # 计算ETH金额
        if self.value and self.value != "0x0":
            try:
                value_wei = int(self.value, 16) if self.value.startswith("0x") else int(self.value)
                self.value_eth = value_wei / (10**18)
            except (ValueError, TypeError):
                self.value_eth = 0.0
        
        # 判断是否为合约调用
        self.is_contract_call = bool(self.data and len(self.data) > 2)
        
        # 判断是否包含价值转移
        self.is_value_transfer = bool(self.value_eth and self.value_eth > 0)


@dataclass
class TransactionAnalysis:
    """交易分析结果"""
    # 原始交易
    transaction: EthTransaction
    
    # 分析结果
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