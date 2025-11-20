"""
EIP712 Parser Type Definitions
"""

from typing import Dict, List, Optional, Union, Any, TypedDict
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel


class OrderType(str, Enum):
    """Order type enumeration"""
    LISTING = "listing"
    OFFER = "offer"


class NFTProtocolType(str, Enum):
    """NFT protocol type enumeration"""
    SEAPORT = "seaport"
    BLUR = "blur"
    BLEND = "blend"
    LOOKSRARE = "looksrare"


class PersonalSignTemplateType(str, Enum):
    """PersonalSign template type enumeration"""
    LOGIN = "login"
    BINDING = "binding" 
    AUTHORIZATION = "authorization"
    VERIFICATION = "verification"
    CUSTOM_MESSAGE = "custom_message"
    UNKNOWN = "unknown"


@dataclass
class NFTDetail:
    """NFT details"""
    collection: str
    amount: str
    type: Optional[str] = None  # 'erc721' | 'erc1155'
    token_id: Optional[str] = None


@dataclass
class FTDetail:
    """Fungible token details"""
    currency: str
    amount: str
    type: Optional[str] = None  # 'native' | 'erc20'


@dataclass
class ParsedDetail:
    """Parsed details"""
    kind: str  # "nft" | "token"
    detail: Union[NFTDetail, FTDetail]


# Balance change type definition
BalanceChangeDetail = Dict[str, str]  # {keyId: amount}
BalanceChange = Dict[str, BalanceChangeDetail]  # {address: BalanceChangeDetail}


@dataclass
class NFTMessage:
    """NFT message"""
    offerer: str
    offer: List[ParsedDetail]
    order_type: OrderType
    balance_change: BalanceChange
    consideration: List[ParsedDetail]
    start_time: Union[str, int]
    end_time: Union[str, int]
    type: NFTProtocolType


@dataclass
class NFTMessageBulk:
    """Bulk NFT message"""
    balance_change: BalanceChange
    messages: List[NFTMessage]


@dataclass
class Approval:
    """Approval information"""
    spender: str
    amount: Union[str, int]
    nonce: Union[str, int]
    expiration: Union[str, int]
    owner: Optional[str] = None
    token: Optional[str] = None


@dataclass
class PermitMessage:
    """Permit message"""
    permits: List[Approval]


@dataclass
class TransactionLike:
    """Transaction-like information"""
    from_address: str
    to: Optional[str]
    data: Optional[str] = None
    value: Optional[Union[str, int]] = None


class EIP712Like(TypedDict):
    """EIP712 message structure"""
    types: Dict[str, Any]
    domain: Dict[str, Any]
    primaryType: str
    message: Dict[str, Any]


@dataclass
class ParsedMessage:
    """Parsed message"""
    kind: str  # "nft" | "permit"
    detail: Union[NFTMessage, NFTMessageBulk, PermitMessage]


def is_bulk_message(message: Union[NFTMessage, NFTMessageBulk]) -> bool:
    """Check if message is bulk message"""
    return isinstance(message, NFTMessageBulk)


def calculate_balance_change(
    balance_change: BalanceChange, 
    address: str, 
    parsed: ParsedDetail, 
    is_received: bool
) -> None:
    """Calculate balance change"""
    if parsed.kind == "token":
        detail = parsed.detail
        key_id = f"{getattr(detail, 'type', 'token')}:{detail.currency}"
    else:
        detail = parsed.detail
        key_id = f"{getattr(detail, 'type', 'nft')}:{detail.collection}:{getattr(detail, 'token_id', '')}"
    
    address = address.lower()
    
    if address not in balance_change:
        balance_change[address] = {}
    
    if key_id not in balance_change[address]:
        balance_change[address][key_id] = "0"
    
    current_amount = int(balance_change[address][key_id])
    change_amount = int(detail.amount)
    
    if is_received:
        new_amount = current_amount + change_amount
    else:
        new_amount = current_amount - change_amount
    
    balance_change[address][key_id] = str(new_amount) 