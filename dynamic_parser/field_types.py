"""
动态解析器类型定义
包含字段类型、语义枚举和数据结构定义
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class FieldType(str, Enum):
    """字段类型枚举"""
    # 基础类型
    UINT = "uint"
    INT = "int"
    BOOL = "bool"
    BYTES = "bytes"
    STRING = "string"
    ADDRESS = "address"
    
    # 复合类型
    ARRAY = "array"
    STRUCT = "struct"
    
    # 特殊类型（根据语义推断）
    TOKEN_ADDRESS = "token_address"
    USER_ADDRESS = "user_address"
    CONTRACT_ADDRESS = "contract_address"
    AMOUNT = "amount"
    TIMESTAMP = "timestamp"
    DEADLINE = "deadline"
    NONCE = "nonce"
    HASH = "hash"
    SIGNATURE = "signature"
    PERCENTAGE = "percentage"
    ENUM_VALUE = "enum_value"
    
    # 未知类型
    UNKNOWN = "unknown"


class FieldSemantic(str, Enum):
    """字段语义枚举"""
    # 身份相关
    OWNER = "owner"
    SPENDER = "spender"
    RECIPIENT = "recipient"
    TRADER = "trader"
    OFFERER = "offerer"
    BIDDER = "bidder"
    SELLER = "seller"
    BUYER = "buyer"
    VALIDATOR = "validator"
    DELEGATE = "delegate"
    
    # 金额相关
    VALUE = "value"
    AMOUNT = "amount"
    PRICE = "price"
    FEE = "fee"
    REWARD = "reward"
    PENALTY = "penalty"
    BALANCE = "balance"
    ALLOWANCE = "allowance"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    
    # 时间相关
    TIMESTAMP = "timestamp"
    DEADLINE = "deadline"
    START_TIME = "start_time"
    END_TIME = "end_time"
    DURATION = "duration"
    DELAY = "delay"
    PERIOD = "period"
    
    # 标识相关
    TOKEN_ID = "token_id"
    NONCE = "nonce"
    SALT = "salt"
    INDEX = "index"
    ID = "id"
    KEY = "key"
    COUNTER = "counter"
    
    # 数据相关
    DATA = "data"
    HASH = "hash"
    SIGNATURE = "signature"
    PROOF = "proof"
    MERKLE_ROOT = "merkle_root"
    
    # 配置相关
    VERSION = "version"
    CHAIN_ID = "chain_id"
    TYPE = "type"
    STATUS = "status"
    FLAG = "flag"
    OPTION = "option"
    
    # 治理相关
    PROPOSAL_ID = "proposal_id"
    VOTE_TYPE = "vote_type"
    VOTING_POWER = "voting_power"
    
    # NFT相关
    COLLECTION = "collection"
    CREATOR = "creator"
    ROYALTY = "royalty"
    METADATA = "metadata"
    
    # DeFi相关
    LIQUIDITY = "liquidity"
    SLIPPAGE = "slippage"
    POOL = "pool"
    RATE = "rate"
    YIELD = "yield"


@dataclass
class FieldInfo:
    """字段信息"""
    name: str                           # 字段名
    type_name: str                      # 原始类型名
    field_type: FieldType              # 推断的字段类型
    semantic: Optional[FieldSemantic]   # 语义标注
    value: Any                         # 字段值
    description: str                   # 字段描述
    is_array: bool = False             # 是否为数组
    array_element_type: Optional[str] = None  # 数组元素类型
    children: List['FieldInfo'] = field(default_factory=list)  # 子字段（用于结构体）
    context_hints: List[str] = field(default_factory=list)  # 上下文提示


@dataclass
class StructInfo:
    """结构体信息"""
    name: str                          # 结构体名称
    fields: List[FieldInfo]            # 字段列表
    description: str                   # 结构体描述
    struct_type: Optional[str] = None  # 结构体类型分类


@dataclass
class EIP712ParseResult:
    """EIP712解析结果"""
    domain: StructInfo                 # 域信息
    primary_type: str                  # 主要类型
    message: StructInfo                # 消息结构
    raw_data: Dict[str, Any]          # 原始数据 