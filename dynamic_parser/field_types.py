"""
Dynamic Parser Type Definitions
Contains field types, semantic enumerations and data structure definitions
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class FieldType(str, Enum):
    """Field type enumeration"""
    # Basic types
    UINT = "uint"
    INT = "int"
    BOOL = "bool"
    BYTES = "bytes"
    STRING = "string"
    ADDRESS = "address"
    
    # Composite types
    ARRAY = "array"
    STRUCT = "struct"
    
    # Special types (inferred from semantics)
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
    
    # Unknown type
    UNKNOWN = "unknown"


class FieldSemantic(str, Enum):
    """Field semantic enumeration"""
    # Identity related
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
    
    # Amount related
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
    
    # Time related
    TIMESTAMP = "timestamp"
    DEADLINE = "deadline"
    START_TIME = "start_time"
    END_TIME = "end_time"
    DURATION = "duration"
    DELAY = "delay"
    PERIOD = "period"
    
    # Identifier related
    TOKEN_ID = "token_id"
    NONCE = "nonce"
    SALT = "salt"
    INDEX = "index"
    ID = "id"
    KEY = "key"
    COUNTER = "counter"
    
    # Data related
    DATA = "data"
    HASH = "hash"
    SIGNATURE = "signature"
    PROOF = "proof"
    MERKLE_ROOT = "merkle_root"
    
    # Configuration related
    VERSION = "version"
    CHAIN_ID = "chain_id"
    TYPE = "type"
    STATUS = "status"
    FLAG = "flag"
    OPTION = "option"
    
    # Governance related
    PROPOSAL_ID = "proposal_id"
    VOTE_TYPE = "vote_type"
    VOTING_POWER = "voting_power"
    
    # NFT related
    COLLECTION = "collection"
    CREATOR = "creator"
    ROYALTY = "royalty"
    METADATA = "metadata"
    
    # DeFi related
    LIQUIDITY = "liquidity"
    SLIPPAGE = "slippage"
    POOL = "pool"
    RATE = "rate"
    YIELD = "yield"


@dataclass
class FieldInfo:
    """Field information"""
    name: str                           # Field name
    type_name: str                      # Original type name
    field_type: FieldType              # Inferred field type
    semantic: Optional[FieldSemantic]   # Semantic annotation
    value: Any                         # Field value
    description: str                   # Field description
    is_array: bool = False             # Whether it's an array
    array_element_type: Optional[str] = None  # Array element type
    children: List['FieldInfo'] = field(default_factory=list)  # Child fields (for structs)
    context_hints: List[str] = field(default_factory=list)  # Context hints


@dataclass
class StructInfo:
    """Struct information"""
    name: str                          # Struct name
    fields: List[FieldInfo]            # Field list
    description: str                   # Struct description
    struct_type: Optional[str] = None  # Struct type classification


@dataclass
class EIP712ParseResult:
    """EIP712 parsing result"""
    domain: StructInfo                 # Domain information
    primary_type: str                  # Primary type
    message: StructInfo                # Message structure
    raw_data: Dict[str, Any]          # Raw data 