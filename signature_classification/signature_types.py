"""
签名类型定义和分类枚举
"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class SignatureType(str, Enum):
    """签名类型枚举 - 主流签名方法"""
    
    # 链上交易 - 最常见的签名类型
    ETH_SEND_TRANSACTION = "eth_sendTransaction"
    
    # 链下文本授权 - 常被钓鱼攻击利用
    PERSONAL_SIGN = "personal_sign"
    
    # EIP-712结构化链下授权 - 现代DApp常用
    ETH_SIGN_TYPED_DATA_V4 = "eth_signTypedData_v4"
    
    # 原始签名 - 已被多数钱包禁用，但仍存在风险
    ETH_SIGN = "eth_sign"
    
    # 未知类型
    UNKNOWN = "unknown"


class SignatureCategory(str, Enum):
    """签名分类 - 按用途分类"""
    
    # 资产转移类
    ASSET_TRANSFER = "asset_transfer"
    
    # 授权许可类  
    AUTHORIZATION = "authorization"
    
    # 身份验证类
    AUTHENTICATION = "authentication"
    
    # 交易执行类
    TRANSACTION_EXECUTION = "transaction_execution"
    
    # 未分类
    UNCATEGORIZED = "uncategorized"


class SecurityLevel(str, Enum):
    """安全级别 - 按风险程度分级"""
    
    # 高危险 - 可能导致资产损失
    HIGH_RISK = "high_risk"
    
    # 中等风险 - 需要用户谨慎确认
    MEDIUM_RISK = "medium_risk"
    
    # 低风险 - 相对安全的操作
    LOW_RISK = "low_risk"
    
    # 极低风险 - 几乎无风险
    MINIMAL_RISK = "minimal_risk"


@dataclass
class SignatureMetadata:
    """签名元数据"""
    signature_type: SignatureType
    category: SignatureCategory
    security_level: SecurityLevel
    description: str
    common_use_cases: List[str]
    risk_factors: List[str]
    wallet_support: Dict[str, bool]  # 钱包支持情况


# 签名类型映射配置
SIGNATURE_TYPE_CONFIG: Dict[SignatureType, SignatureMetadata] = {
    SignatureType.ETH_SEND_TRANSACTION: SignatureMetadata(
        signature_type=SignatureType.ETH_SEND_TRANSACTION,
        category=SignatureCategory.TRANSACTION_EXECUTION,
        security_level=SecurityLevel.HIGH_RISK,
        description="链上交易签名，直接修改区块链状态",
        common_use_cases=[
            "代币转账",
            "智能合约调用", 
            "NFT交易",
            "DeFi操作"
        ],
        risk_factors=[
            "直接消耗Gas费用",
            "不可逆转的资产转移",
            "可能触发复杂的合约逻辑"
        ],
        wallet_support={
            "MetaMask": True,
            "Trust Wallet": True,
            "Coinbase Wallet": True,
            "WalletConnect": True
        }
    ),
    
    SignatureType.PERSONAL_SIGN: SignatureMetadata(
        signature_type=SignatureType.PERSONAL_SIGN,
        category=SignatureCategory.AUTHENTICATION,
        security_level=SecurityLevel.MEDIUM_RISK,
        description="个人消息签名，常用于身份验证和授权",
        common_use_cases=[
            "登录验证",
            "消息确认",
            "身份证明",
            "免费授权"
        ],
        risk_factors=[
            "钓鱼网站利用频繁",
            "用户难以理解消息内容",
            "可能被误用于权限提升"
        ],
        wallet_support={
            "MetaMask": True,
            "Trust Wallet": True,
            "Coinbase Wallet": True,
            "WalletConnect": True
        }
    ),
    
    SignatureType.ETH_SIGN_TYPED_DATA_V4: SignatureMetadata(
        signature_type=SignatureType.ETH_SIGN_TYPED_DATA_V4,
        category=SignatureCategory.AUTHORIZATION,
        security_level=SecurityLevel.MEDIUM_RISK,
        description="EIP-712结构化数据签名，提供更好的可读性和安全性",
        common_use_cases=[
            "NFT市场订单",
            "DeFi协议授权",
            "多签钱包操作",
            "跨链桥授权"
        ],
        risk_factors=[
            "复杂的数据结构难以理解",
            "可能包含隐藏的授权条款",
            "时间敏感的签名可能被抢跑"
        ],
        wallet_support={
            "MetaMask": True,
            "Trust Wallet": True,
            "Coinbase Wallet": True,
            "WalletConnect": True
        }
    ),
    
    SignatureType.ETH_SIGN: SignatureMetadata(
        signature_type=SignatureType.ETH_SIGN,
        category=SignatureCategory.UNCATEGORIZED,
        security_level=SecurityLevel.HIGH_RISK,
        description="原始签名方法，已被多数钱包禁用",
        common_use_cases=[
            "旧版DApp兼容",
            "底层签名操作"
        ],
        risk_factors=[
            "极易被恶意利用",
            "无法提供签名内容预览",
            "可能签署任意数据"
        ],
        wallet_support={
            "MetaMask": False,  # 已禁用
            "Trust Wallet": False,
            "Coinbase Wallet": False,
            "WalletConnect": False
        }
    )
}


def get_signature_metadata(signature_type: SignatureType) -> SignatureMetadata:
    """获取签名类型的元数据"""
    return SIGNATURE_TYPE_CONFIG.get(signature_type, SignatureMetadata(
        signature_type=SignatureType.UNKNOWN,
        category=SignatureCategory.UNCATEGORIZED,
        security_level=SecurityLevel.HIGH_RISK,
        description="未知签名类型",
        common_use_cases=[],
        risk_factors=["未知风险"],
        wallet_support={}
    )) 