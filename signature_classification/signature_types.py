"""
Signature type definitions and classification enumerations
"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class SignatureType(str, Enum):
    """Signature type enumeration - mainstream signature methods"""
    
    # On-chain transaction - most common signature type
    ETH_SEND_TRANSACTION = "eth_sendTransaction"
    
    # Off-chain text authorization - often exploited by phishing attacks
    PERSONAL_SIGN = "personal_sign"
    
    # EIP-712 structured off-chain authorization - commonly used by modern DApps
    ETH_SIGN_TYPED_DATA_V4 = "eth_signTypedData_v4"
    
    # Raw signature - disabled by most wallets, but still poses risks
    ETH_SIGN = "eth_sign"
    
    # Unknown type
    UNKNOWN = "unknown"


class SignatureCategory(str, Enum):
    """Signature category - classified by purpose"""
    
    # Asset transfer category
    ASSET_TRANSFER = "asset_transfer"
    
    # Authorization category  
    AUTHORIZATION = "authorization"
    
    # Authentication category
    AUTHENTICATION = "authentication"
    
    # Transaction execution category
    TRANSACTION_EXECUTION = "transaction_execution"
    
    # Uncategorized
    UNCATEGORIZED = "uncategorized"


class SecurityLevel(str, Enum):
    """Security level - classified by risk degree"""
    
    # High risk - may cause asset loss
    HIGH_RISK = "high_risk"
    
    # Medium risk - requires user careful confirmation
    MEDIUM_RISK = "medium_risk"
    
    # Low risk - relatively safe operations
    LOW_RISK = "low_risk"
    
    # Minimal risk - almost no risk
    MINIMAL_RISK = "minimal_risk"


@dataclass
class SignatureMetadata:
    """Signature metadata"""
    signature_type: SignatureType
    category: SignatureCategory
    security_level: SecurityLevel
    description: str
    common_use_cases: List[str]
    risk_factors: List[str]
    wallet_support: Dict[str, bool]  # Wallet support status


# Signature type mapping configuration
SIGNATURE_TYPE_CONFIG: Dict[SignatureType, SignatureMetadata] = {
    SignatureType.ETH_SEND_TRANSACTION: SignatureMetadata(
        signature_type=SignatureType.ETH_SEND_TRANSACTION,
        category=SignatureCategory.TRANSACTION_EXECUTION,
        security_level=SecurityLevel.HIGH_RISK,
        description="On-chain transaction signature, directly modifies blockchain state",
        common_use_cases=[
            "Token transfer",
            "Smart contract call", 
            "NFT transaction",
            "DeFi operations"
        ],
        risk_factors=[
            "Directly consumes gas fees",
            "Irreversible asset transfer",
            "May trigger complex contract logic"
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
        description="Personal message signature, commonly used for authentication and authorization",
        common_use_cases=[
            "Login verification",
            "Message confirmation",
            "Identity proof",
            "Free authorization"
        ],
        risk_factors=[
            "Frequently exploited by phishing sites",
            "Users find it difficult to understand message content",
            "May be misused for privilege escalation"
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
        description="EIP-712 structured data signature, provides better readability and security",
        common_use_cases=[
            "NFT marketplace orders",
            "DeFi protocol authorization",
            "Multi-sig wallet operations",
            "Cross-chain bridge authorization"
        ],
        risk_factors=[
            "Complex data structures are difficult to understand",
            "May contain hidden authorization terms",
            "Time-sensitive signatures may be front-run"
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
        description="Raw signature method, disabled by most wallets",
        common_use_cases=[
            "Legacy DApp compatibility",
            "Low-level signature operations"
        ],
        risk_factors=[
            "Highly vulnerable to malicious exploitation",
            "Cannot provide signature content preview",
            "May sign arbitrary data"
        ],
        wallet_support={
            "MetaMask": False,  # Disabled
            "Trust Wallet": False,
            "Coinbase Wallet": False,
            "WalletConnect": False
        }
    )
}


def get_signature_metadata(signature_type: SignatureType) -> SignatureMetadata:
    """Get signature type metadata"""
    return SIGNATURE_TYPE_CONFIG.get(signature_type, SignatureMetadata(
        signature_type=SignatureType.UNKNOWN,
        category=SignatureCategory.UNCATEGORIZED,
        security_level=SecurityLevel.HIGH_RISK,
        description="Unknown signature type",
        common_use_cases=[],
        risk_factors=["Unknown risks"],
        wallet_support={}
    )) 