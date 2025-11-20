"""
Dynamic EIP712 Parser
A universal tool capable of parsing arbitrary EIP712 signature structures and semantics
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import datetime


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
    confidence: float = 0.0            # Recognition confidence (0-1)
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


class DynamicEIP712Parser:
    """Dynamic EIP712 parser"""
    
    def __init__(self):
        self.types: Dict[str, List[Dict[str, str]]] = {}
        self.semantic_patterns = self._init_semantic_patterns()
        self.type_patterns = self._init_type_patterns()
        self.context_keywords = self._init_context_keywords()
        self.value_analyzers = self._init_value_analyzers()
    
    def _init_semantic_patterns(self) -> List[Tuple[str, FieldSemantic, float]]:
        """Initialize semantic patterns - returns list of (pattern, semantic, confidence)"""
        return [
            # High confidence patterns (0.9+)
            (r"^tokenid$", FieldSemantic.TOKEN_ID, 0.95),
            (r"^nonce$", FieldSemantic.NONCE, 0.95),
            (r"^chainid$", FieldSemantic.CHAIN_ID, 0.95),
            (r"^deadline$", FieldSemantic.DEADLINE, 0.95),
            (r"^timestamp$", FieldSemantic.TIMESTAMP, 0.95),
            (r"^spender$", FieldSemantic.SPENDER, 0.95),
            (r"^owner$", FieldSemantic.OWNER, 0.95),
            (r"^recipient$", FieldSemantic.RECIPIENT, 0.95),
            (r"^amount$", FieldSemantic.AMOUNT, 0.95),
            (r"^value$", FieldSemantic.VALUE, 0.95),
            (r"^price$", FieldSemantic.PRICE, 0.95),
            (r"^fee$", FieldSemantic.FEE, 0.95),
            
            # Medium-high confidence patterns (0.8+)
            (r".*token.*id.*", FieldSemantic.TOKEN_ID, 0.85),
            (r".*proposal.*id.*", FieldSemantic.PROPOSAL_ID, 0.85),
            (r".*chain.*id.*", FieldSemantic.CHAIN_ID, 0.85),
            (r".*voting.*power.*", FieldSemantic.VOTING_POWER, 0.85),
            (r".*merkle.*root.*", FieldSemantic.MERKLE_ROOT, 0.85),
            
            # Identity related (0.7+)
            (r".*holder.*", FieldSemantic.OWNER, 0.8),
            (r".*minter.*", FieldSemantic.OWNER, 0.8),
            (r".*creator.*", FieldSemantic.CREATOR, 0.8),
            (r".*from.*", FieldSemantic.OWNER, 0.75),
            (r".*approved.*", FieldSemantic.SPENDER, 0.8),
            (r".*to.*", FieldSemantic.RECIPIENT, 0.75),
            (r".*beneficiary.*", FieldSemantic.RECIPIENT, 0.8),
            (r".*trader.*", FieldSemantic.TRADER, 0.8),
            (r".*offerer.*", FieldSemantic.OFFERER, 0.85),
            (r".*maker.*", FieldSemantic.OFFERER, 0.8),
            (r".*bidder.*", FieldSemantic.BIDDER, 0.8),
            (r".*seller.*", FieldSemantic.SELLER, 0.8),
            (r".*buyer.*", FieldSemantic.BUYER, 0.8),
            (r".*validator.*", FieldSemantic.VALIDATOR, 0.8),
            (r".*delegate.*", FieldSemantic.DELEGATE, 0.8),
            
            # Amount related (0.7+)
            (r".*quantity.*", FieldSemantic.AMOUNT, 0.8),
            (r".*cost.*", FieldSemantic.FEE, 0.75),
            (r".*reward.*", FieldSemantic.REWARD, 0.8),
            (r".*penalty.*", FieldSemantic.PENALTY, 0.8),
            (r".*balance.*", FieldSemantic.BALANCE, 0.8),
            (r".*allowance.*", FieldSemantic.ALLOWANCE, 0.8),
            (r".*minimum.*", FieldSemantic.MINIMUM, 0.75),
            (r".*maximum.*", FieldSemantic.MAXIMUM, 0.75),
            (r".*min.*", FieldSemantic.MINIMUM, 0.7),
            (r".*max.*", FieldSemantic.MAXIMUM, 0.7),
            (r".*liquidity.*", FieldSemantic.LIQUIDITY, 0.8),
            (r".*slippage.*", FieldSemantic.SLIPPAGE, 0.8),
            (r".*rate.*", FieldSemantic.RATE, 0.75),
            (r".*yield.*", FieldSemantic.YIELD, 0.8),
            (r".*royalty.*", FieldSemantic.ROYALTY, 0.8),
            
            # Time related (0.7+)
            (r".*expiry.*", FieldSemantic.DEADLINE, 0.85),
            (r".*expires.*", FieldSemantic.DEADLINE, 0.85),
            (r".*time.*", FieldSemantic.TIMESTAMP, 0.7),
            (r".*start.*time.*", FieldSemantic.START_TIME, 0.85),
            (r".*end.*time.*", FieldSemantic.END_TIME, 0.85),
            (r".*duration.*", FieldSemantic.DURATION, 0.8),
            (r".*delay.*", FieldSemantic.DELAY, 0.8),
            (r".*period.*", FieldSemantic.PERIOD, 0.8),
            
            # Identifier related (0.7+)
            (r".*salt.*", FieldSemantic.SALT, 0.9),
            (r".*index.*", FieldSemantic.INDEX, 0.8),
            (r".*counter.*", FieldSemantic.COUNTER, 0.8),
            (r".*key.*", FieldSemantic.KEY, 0.7),
            (r"^id$", FieldSemantic.ID, 0.8),
            (r".*_id$", FieldSemantic.ID, 0.75),
            
            # Data related (0.7+)
            (r".*data.*", FieldSemantic.DATA, 0.75),
            (r".*payload.*", FieldSemantic.DATA, 0.8),
            (r".*hash.*", FieldSemantic.HASH, 0.8),
            (r".*signature.*", FieldSemantic.SIGNATURE, 0.85),
            (r".*proof.*", FieldSemantic.PROOF, 0.8),
            (r".*metadata.*", FieldSemantic.METADATA, 0.8),
            
            # Configuration related (0.7+)
            (r".*version.*", FieldSemantic.VERSION, 0.8),
            (r".*type.*", FieldSemantic.TYPE, 0.7),
            (r".*status.*", FieldSemantic.STATUS, 0.8),
            (r".*flag.*", FieldSemantic.FLAG, 0.75),
            (r".*option.*", FieldSemantic.OPTION, 0.75),
            
            # Governance related (0.7+)
            (r".*vote.*type.*", FieldSemantic.VOTE_TYPE, 0.85),
            (r".*support.*", FieldSemantic.VOTE_TYPE, 0.8),
            
            # NFT related (0.7+)
            (r".*collection.*", FieldSemantic.COLLECTION, 0.8),
            (r".*pool.*", FieldSemantic.POOL, 0.75),
        ]
    
    def _init_type_patterns(self) -> List[Tuple[str, str, FieldType, float]]:
        """Initialize type inference patterns - returns list of (field name pattern, type pattern, inferred type, confidence)"""
        return [
            # Amount type
            (r".*amount.*|.*value.*|.*price.*|.*fee.*|.*cost.*|.*quantity.*", r"uint.*", FieldType.AMOUNT, 0.9),
            (r".*balance.*|.*allowance.*|.*reward.*|.*penalty.*", r"uint.*", FieldType.AMOUNT, 0.85),
            (r".*liquidity.*|.*slippage.*|.*rate.*|.*yield.*", r"uint.*", FieldType.AMOUNT, 0.8),
            
            # Timestamp type
            (r".*time.*|.*deadline.*|.*expiry.*|.*expires.*|.*timestamp.*", r"uint.*", FieldType.TIMESTAMP, 0.9),
            (r".*duration.*|.*delay.*|.*period.*", r"uint.*", FieldType.TIMESTAMP, 0.8),
            
            # Nonce type
            (r".*nonce.*", r"uint.*", FieldType.NONCE, 0.95),
            (r".*counter.*|.*index.*", r"uint.*", FieldType.NONCE, 0.8),
            
            # Address type
            (r".*token.*|.*erc20.*|.*erc721.*|.*erc1155.*", r"address", FieldType.TOKEN_ADDRESS, 0.9),
            (r".*contract.*|.*verifying.*", r"address", FieldType.CONTRACT_ADDRESS, 0.85),
            
            # Hash type
            (r".*hash.*|.*root.*|.*digest.*", r"bytes32", FieldType.HASH, 0.9),
            
            # Signature type
            (r".*signature.*|.*sig.*", r"bytes.*", FieldType.SIGNATURE, 0.9),
            
            # Percentage type
            (r".*percent.*|.*ratio.*|.*bps.*", r"uint.*", FieldType.PERCENTAGE, 0.85),
        ]
    
    def _init_context_keywords(self) -> Dict[str, Set[str]]:
        """Initialize context keywords"""
        return {
            "permit": {"spender", "owner", "value", "deadline", "nonce"},
            "order": {"offerer", "offer", "consideration", "orderType", "startTime", "endTime"},
            "vote": {"voter", "proposalId", "support", "reason"},
            "transfer": {"from", "to", "amount", "tokenId"},
            "mint": {"to", "tokenId", "amount", "data"},
            "burn": {"from", "tokenId", "amount"},
            "governance": {"proposer", "targets", "values", "signatures", "calldatas"},
            "auction": {"bidder", "bid", "deadline", "reserve"},
            "swap": {"tokenIn", "tokenOut", "amountIn", "amountOut", "slippage"},
            "liquidity": {"token0", "token1", "liquidity", "amount0", "amount1"},
        }
    
    def _init_value_analyzers(self) -> List[callable]:
        """Initialize value analyzers"""
        return [
            self._analyze_timestamp_value,
            self._analyze_amount_value,
            self._analyze_address_value,
            self._analyze_percentage_value,
            self._analyze_enum_value,
        ]
    
    def parse(self, eip712_data: Dict[str, Any]) -> EIP712ParseResult:
        """
        Parse EIP712 data
        
        Args:
            eip712_data: EIP712 format data
            
        Returns:
            Parsing result
        """
        if not self._validate_eip712_data(eip712_data):
            raise ValueError("Invalid EIP712 data format")
        
        self.types = eip712_data['types']
        
        # Parse domain information
        domain_struct = self._parse_struct("EIP712Domain", eip712_data['domain'])
        
        # Parse primary message
        primary_type = eip712_data['primaryType']
        message_struct = self._parse_struct(primary_type, eip712_data['message'])
        
        return EIP712ParseResult(
            domain=domain_struct,
            primary_type=primary_type,
            message=message_struct,
            raw_data=eip712_data
        )
    
    def _validate_eip712_data(self, data: Dict[str, Any]) -> bool:
        """Validate EIP712 data format"""
        required_fields = ['types', 'domain', 'primaryType', 'message']
        
        for field in required_fields:
            if field not in data:
                return False
        
        if 'EIP712Domain' not in data['types']:
            return False
        
        if data['primaryType'] not in data['types']:
            return False
        
        return True
    
    def _parse_struct(self, struct_name: str, struct_data: Dict[str, Any]) -> StructInfo:
        """
        Parse struct (enhanced version)
        
        Args:
            struct_name: Struct name
            struct_data: Struct data
            
        Returns:
            Struct information
        """
        if struct_name not in self.types:
            raise ValueError(f"Struct definition not found: {struct_name}")
        
        struct_definition = self.types[struct_name]
        field_names = [field_def['name'] for field_def in struct_definition]
        
        # Detect struct context type
        struct_context = self._detect_struct_context(struct_name, field_names)
        
        fields = []
        for field_def in struct_definition:
            field_name = field_def['name']
            field_type = field_def['type']
            field_value = struct_data.get(field_name)
            
            field_info = self._parse_field(field_name, field_type, field_value, struct_context)
            fields.append(field_info)
        
        description = self._generate_struct_description(struct_name, fields, struct_context)
        
        return StructInfo(
            name=struct_name,
            fields=fields,
            description=description,
            struct_type=struct_context
        )
    
    def _parse_field(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> FieldInfo:
        """
        Parse field (enhanced version)
        
        Args:
            field_name: Field name
            field_type: Field type
            field_value: Field value
            struct_context: Struct context
            
        Returns:
            Field information
        """
        # Parse type
        is_array = field_type.endswith('[]')
        array_element_type = None
        base_type = field_type
        
        if is_array:
            base_type = field_type[:-2]
            array_element_type = base_type
        
        # Infer field type
        inferred_type = self._infer_field_type(field_name, base_type, field_value)
        
        # Infer semantic (with confidence)
        semantic, confidence = self._infer_semantic(field_name, base_type, field_value, struct_context)
        
        # Handle child structures
        children = []
        if base_type in self.types and field_value is not None:
            if is_array and isinstance(field_value, list):
                for i, item in enumerate(field_value):
                    if isinstance(item, dict):
                        child_struct = self._parse_struct(base_type, item)
                        child_field = FieldInfo(
                            name=f"[{i}]",
                            type_name=base_type,
                            field_type=FieldType.STRUCT,
                            semantic=None,
                            value=item,
                            description=f"Array element {i}",
                            confidence=0.9,
                            children=[FieldInfo(
                                name=child.name,
                                type_name=child.type_name,
                                field_type=child.field_type,
                                semantic=child.semantic,
                                value=child.value,
                                description=child.description,
                                confidence=child.confidence
                            ) for child in child_struct.fields]
                        )
                        children.append(child_field)
            elif isinstance(field_value, dict):
                child_struct = self._parse_struct(base_type, field_value)
                children = [FieldInfo(
                    name=child.name,
                    type_name=child.type_name,
                    field_type=child.field_type,
                    semantic=child.semantic,
                    value=child.value,
                    description=child.description,
                    confidence=child.confidence
                ) for child in child_struct.fields]
        
        # Collect context hints
        context_hints = []
        if struct_context:
            context_hints.append(f"Struct type: {struct_context}")
        if confidence >= 0.8:
            context_hints.append(f"High confidence recognition")
        
        # Generate description
        description = self._generate_field_description(field_name, inferred_type, semantic, field_value, confidence)
        
        return FieldInfo(
            name=field_name,
            type_name=field_type,
            field_type=inferred_type,
            semantic=semantic,
            value=field_value,
            description=description,
            confidence=confidence,
            is_array=is_array,
            array_element_type=array_element_type,
            children=children,
            context_hints=context_hints
        )
    
    def _analyze_timestamp_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """Analyze timestamp value"""
        if not isinstance(field_value, (int, str)):
            return None
        
        try:
            timestamp = int(field_value)
            # Check if it's a reasonable timestamp range (2000 - 2100)
            if 946684800 <= timestamp <= 4102444800:
                confidence = 0.8
                # Check if it's a deadline
                if any(keyword in field_name.lower() for keyword in ['deadline', 'expiry', 'expires']):
                    return (FieldType.DEADLINE, FieldSemantic.DEADLINE, confidence + 0.1)
                else:
                    return (FieldType.TIMESTAMP, FieldSemantic.TIMESTAMP, confidence)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _analyze_amount_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """Analyze amount value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            amount = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a typical ERC20 amount (18 decimal places)
            if amount > 10**15:  # Greater than 0.001 ETH
                confidence = 0.8
                if any(keyword in field_name_lower for keyword in ['amount', 'value', 'quantity']):
                    return (FieldType.AMOUNT, FieldSemantic.AMOUNT, confidence + 0.1)
                elif any(keyword in field_name_lower for keyword in ['price', 'cost']):
                    return (FieldType.AMOUNT, FieldSemantic.PRICE, confidence + 0.1)
                elif any(keyword in field_name_lower for keyword in ['fee', 'commission']):
                    return (FieldType.AMOUNT, FieldSemantic.FEE, confidence + 0.1)
                else:
                    return (FieldType.AMOUNT, FieldSemantic.VALUE, confidence)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _analyze_address_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """Analyze address value"""
        if field_type != 'address' or not isinstance(field_value, str):
            return None
        
        # Check if it's a valid Ethereum address
        if not (field_value.startswith('0x') and len(field_value) == 42):
            return None
        
        field_name_lower = field_name.lower()
        confidence = 0.8
        
        # Check if it's zero address
        if field_value == '0x0000000000000000000000000000000000000000':
            confidence = 0.6
        
        # Infer address type based on field name
        if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
            return (FieldType.TOKEN_ADDRESS, FieldSemantic.COLLECTION, confidence + 0.1)
        elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
            return (FieldType.CONTRACT_ADDRESS, FieldSemantic.TYPE, confidence + 0.1)
        else:
            return (FieldType.USER_ADDRESS, None, confidence)
    
    def _analyze_percentage_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """Analyze percentage value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a percentage (range 0-100 or 0-10000)
            if (0 <= value <= 100 and any(keyword in field_name_lower for keyword in ['percent', 'ratio'])) or \
               (0 <= value <= 10000 and 'bps' in field_name_lower):
                return (FieldType.PERCENTAGE, FieldSemantic.RATE, 0.85)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _analyze_enum_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """Analyze enum value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a small range integer (might be an enum)
            if 0 <= value <= 20:
                if any(keyword in field_name_lower for keyword in ['type', 'kind', 'status', 'state', 'mode']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.TYPE, 0.75)
                elif any(keyword in field_name_lower for keyword in ['support', 'vote']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.VOTE_TYPE, 0.8)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _detect_struct_context(self, struct_name: str, field_names: List[str]) -> Optional[str]:
        """Detect struct context type"""
        field_names_lower = [name.lower() for name in field_names]
        field_set = set(field_names_lower)
        
        # Calculate match score for each context
        context_scores = {}
        for context_type, keywords in self.context_keywords.items():
            match_count = len(keywords.intersection(field_set))
            if match_count > 0:
                context_scores[context_type] = match_count / len(keywords)
        
        # Return context with highest match score
        if context_scores:
            best_context = max(context_scores, key=context_scores.get)
            if context_scores[best_context] >= 0.5:  # At least 50% match
                return best_context
        
        return None
    
    def _infer_field_type(self, field_name: str, field_type: str, field_value: Any) -> FieldType:
        """Infer field type (enhanced version)"""
        field_name_lower = field_name.lower()
        
        # First use value analyzers
        for analyzer in self.value_analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result:
                return result[0]
        
        # Use type pattern matching
        for name_pattern, type_pattern, inferred_type, confidence in self.type_patterns:
            if re.match(name_pattern, field_name_lower) and re.match(type_pattern, field_type):
                return inferred_type
        
        # Default inference based on field type
        if field_type.startswith('uint') or field_type.startswith('int'):
            # Further infer if it's amount, timestamp, etc.
            if any(keyword in field_name_lower for keyword in ['amount', 'value', 'price', 'fee', 'cost', 'quantity']):
                return FieldType.AMOUNT
            elif any(keyword in field_name_lower for keyword in ['time', 'deadline', 'expiry', 'expires', 'timestamp']):
                return FieldType.TIMESTAMP
            elif 'nonce' in field_name_lower:
                return FieldType.NONCE
            else:
                return FieldType.UINT if field_type.startswith('uint') else FieldType.INT
        
        elif field_type == 'address':
            # Infer address type based on field name
            if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
                return FieldType.TOKEN_ADDRESS
            elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
                return FieldType.CONTRACT_ADDRESS
            else:
                return FieldType.USER_ADDRESS
        
        elif field_type == 'string':
            return FieldType.STRING
        
        elif field_type == 'bool':
            return FieldType.BOOL
        
        elif field_type.startswith('bytes'):
            if 'hash' in field_name_lower:
                return FieldType.HASH
            elif 'signature' in field_name_lower:
                return FieldType.SIGNATURE
            else:
                return FieldType.BYTES
        
        elif field_type in self.types:
            return FieldType.STRUCT
        
        elif field_type.endswith('[]'):
            return FieldType.ARRAY
        
        else:
            return FieldType.STRING  # Default type
    
    def _infer_semantic(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> Tuple[Optional[FieldSemantic], float]:
        """Infer field semantic (enhanced version)"""
        field_name_lower = field_name.lower()
        best_semantic = None
        best_confidence = 0.0
        
        # First use value analyzers
        for analyzer in self.value_analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result and result[1] and result[2] > best_confidence:
                best_semantic = result[1]
                best_confidence = result[2]
        
        # Use semantic pattern matching
        for pattern, semantic, confidence in self.semantic_patterns:
            if re.match(pattern, field_name_lower) and confidence > best_confidence:
                best_semantic = semantic
                best_confidence = confidence
        
        # Context enhancement
        if struct_context and best_semantic:
            context_boost = self._get_context_boost(best_semantic, struct_context)
            best_confidence = min(0.95, best_confidence + context_boost)
        
        return (best_semantic, best_confidence)
    
    def _get_context_boost(self, semantic: FieldSemantic, struct_context: str) -> float:
        """Calculate semantic confidence boost based on struct context"""
        context_boosts = {
            "permit": {
                FieldSemantic.OWNER: 0.1,
                FieldSemantic.SPENDER: 0.1,
                FieldSemantic.VALUE: 0.1,
                FieldSemantic.DEADLINE: 0.1,
                FieldSemantic.NONCE: 0.1,
            },
            "order": {
                FieldSemantic.OFFERER: 0.1,
                FieldSemantic.PRICE: 0.1,
                FieldSemantic.START_TIME: 0.1,
                FieldSemantic.END_TIME: 0.1,
                FieldSemantic.FEE: 0.1,
            },
            "vote": {
                FieldSemantic.PROPOSAL_ID: 0.15,
                FieldSemantic.VOTE_TYPE: 0.15,
                FieldSemantic.VOTING_POWER: 0.1,
            },
            "transfer": {
                FieldSemantic.OWNER: 0.1,
                FieldSemantic.RECIPIENT: 0.1,
                FieldSemantic.AMOUNT: 0.1,
                FieldSemantic.TOKEN_ID: 0.1,
            },
            "mint": {
                FieldSemantic.RECIPIENT: 0.1,
                FieldSemantic.TOKEN_ID: 0.1,
                FieldSemantic.AMOUNT: 0.1,
            },
            "auction": {
                FieldSemantic.BIDDER: 0.1,
                FieldSemantic.PRICE: 0.1,
                FieldSemantic.DEADLINE: 0.1,
            },
            "swap": {
                FieldSemantic.AMOUNT: 0.1,
                FieldSemantic.SLIPPAGE: 0.15,
                FieldSemantic.RATE: 0.1,
            },
            "liquidity": {
                FieldSemantic.LIQUIDITY: 0.15,
                FieldSemantic.AMOUNT: 0.1,
                FieldSemantic.POOL: 0.1,
            },
        }
        
        return context_boosts.get(struct_context, {}).get(semantic, 0.0)
    
    def _generate_field_description(self, field_name: str, field_type: FieldType, semantic: Optional[FieldSemantic], field_value: Any, confidence: float = 0.0) -> str:
        """Generate field description"""
        base_desc = f"Field '{field_name}'"
        
        # Add semantic description
        if semantic:
            semantic_desc = {
                # Identity related
                FieldSemantic.OWNER: "Owner address",
                FieldSemantic.SPENDER: "Authorized spender address", 
                FieldSemantic.RECIPIENT: "Recipient address",
                FieldSemantic.TRADER: "Trader address",
                FieldSemantic.OFFERER: "Offerer address",
                FieldSemantic.BIDDER: "Bidder address",
                FieldSemantic.SELLER: "Seller address",
                FieldSemantic.BUYER: "Buyer address",
                FieldSemantic.VALIDATOR: "Validator address",
                FieldSemantic.DELEGATE: "Delegate address",
                FieldSemantic.CREATOR: "Creator address",
                
                # Amount related
                FieldSemantic.VALUE: "Value",
                FieldSemantic.AMOUNT: "Amount",
                FieldSemantic.PRICE: "Price",
                FieldSemantic.FEE: "Fee",
                FieldSemantic.REWARD: "Reward amount",
                FieldSemantic.PENALTY: "Penalty amount",
                FieldSemantic.BALANCE: "Balance",
                FieldSemantic.ALLOWANCE: "Allowance",
                FieldSemantic.MINIMUM: "Minimum value",
                FieldSemantic.MAXIMUM: "Maximum value",
                FieldSemantic.LIQUIDITY: "Liquidity",
                FieldSemantic.SLIPPAGE: "Slippage",
                FieldSemantic.RATE: "Rate",
                FieldSemantic.YIELD: "Yield",
                FieldSemantic.ROYALTY: "Royalty",
                
                # Time related
                FieldSemantic.TIMESTAMP: "Timestamp",
                FieldSemantic.DEADLINE: "Deadline",
                FieldSemantic.START_TIME: "Start time",
                FieldSemantic.END_TIME: "End time",
                FieldSemantic.DURATION: "Duration",
                FieldSemantic.DELAY: "Delay",
                FieldSemantic.PERIOD: "Period",
                
                # Identifier related
                FieldSemantic.TOKEN_ID: "Token ID",
                FieldSemantic.NONCE: "Nonce",
                FieldSemantic.SALT: "Salt",
                FieldSemantic.INDEX: "Index",
                FieldSemantic.ID: "Identifier",
                FieldSemantic.KEY: "Key",
                FieldSemantic.COUNTER: "Counter",
                
                # Data related
                FieldSemantic.DATA: "Data",
                FieldSemantic.HASH: "Hash value",
                FieldSemantic.SIGNATURE: "Signature",
                FieldSemantic.PROOF: "Proof",
                FieldSemantic.MERKLE_ROOT: "Merkle root",
                FieldSemantic.METADATA: "Metadata",
                
                # Configuration related
                FieldSemantic.VERSION: "Version",
                FieldSemantic.CHAIN_ID: "Chain ID",
                FieldSemantic.TYPE: "Type",
                FieldSemantic.STATUS: "Status",
                FieldSemantic.FLAG: "Flag",
                FieldSemantic.OPTION: "Option",
                
                # Governance related
                FieldSemantic.PROPOSAL_ID: "Proposal ID",
                FieldSemantic.VOTE_TYPE: "Vote type",
                FieldSemantic.VOTING_POWER: "Voting power",
                
                # NFT related
                FieldSemantic.COLLECTION: "Collection address",
                FieldSemantic.POOL: "Pool",
            }.get(semantic, semantic.value)
            
            # Add confidence display (shown when high confidence)
            confidence_str = ""
            if confidence >= 0.8:
                confidence_str = f" [{confidence:.0%} confidence]"
            
            base_desc += f" ({semantic_desc}{confidence_str})"
        
        # Add type description
        type_desc = {
            FieldType.TOKEN_ADDRESS: "Token contract address",
            FieldType.USER_ADDRESS: "User address", 
            FieldType.CONTRACT_ADDRESS: "Contract address",
            FieldType.AMOUNT: "Amount value",
            FieldType.TIMESTAMP: "Timestamp",
            FieldType.NONCE: "Nonce",
            FieldType.HASH: "Hash value",
            FieldType.SIGNATURE: "Signature data",
        }.get(field_type)
        
        if type_desc:
            base_desc += f" - {type_desc}"
        
        # Add value description
        if field_value is not None:
            if field_type == FieldType.TIMESTAMP and isinstance(field_value, (int, str)):
                try:
                    timestamp = int(field_value)
                    if timestamp > 1000000000:  # Looks like a timestamp
                        dt = datetime.datetime.fromtimestamp(timestamp)
                        base_desc += f" (Time: {dt.strftime('%Y-%m-%d %H:%M:%S')})"
                except:
                    pass
            elif field_type in [FieldType.TOKEN_ADDRESS, FieldType.USER_ADDRESS, FieldType.CONTRACT_ADDRESS]:
                base_desc += f" ({field_value})"
            elif field_type == FieldType.AMOUNT and isinstance(field_value, (int, str)):
                try:
                    # Try to convert to ETH unit for display
                    amount = int(field_value)
                    if amount > 10**15:  # If greater than 0.001 ETH
                        eth_amount = amount / 10**18
                        base_desc += f" ({eth_amount:.6f} ETH)"
                except:
                    base_desc += f" ({field_value})"
            elif isinstance(field_value, (str, int)) and len(str(field_value)) < 50:
                base_desc += f" = {field_value}"
        
        return base_desc
    
    def _generate_struct_description(self, struct_name: str, fields: List[FieldInfo], struct_context: Optional[str] = None) -> str:
        """Generate struct description (enhanced version)"""
        # Infer purpose based on struct name and fields
        if struct_name == "EIP712Domain":
            return "EIP712 domain information - defines the domain and verification context of the signature"
        
        # Use detected context
        if struct_context:
            context_descriptions = {
                "permit": f"Authorization permit structure '{struct_name}' - allows third parties to operate tokens on behalf of users",
                "order": f"Market order structure '{struct_name}' - defines offer conditions and expectations for transactions",
                "vote": f"Governance voting structure '{struct_name}' - records voting decisions on proposals",
                "transfer": f"Transfer structure '{struct_name}' - defines detailed information for asset transfers",
                "mint": f"Mint structure '{struct_name}' - defines parameters for creating new tokens",
                "burn": f"Burn structure '{struct_name}' - defines token burning operations",
                "governance": f"Governance structure '{struct_name}' - defines governance proposal and execution parameters",
                "auction": f"Auction structure '{struct_name}' - defines bidding and conditions for auctions",
                "swap": f"Swap structure '{struct_name}' - defines parameters for token swaps",
                "liquidity": f"Liquidity structure '{struct_name}' - defines parameters for liquidity operations",
            }
            
            if struct_context in context_descriptions:
                return context_descriptions[struct_context]
        
        # Infer struct purpose based on fields (fallback)
        field_names = [field.name.lower() for field in fields]
        high_confidence_fields = [field for field in fields if field.confidence >= 0.8]
        
        if any(name in field_names for name in ['offerer', 'offer', 'consideration']):
            return f"Market order structure '{struct_name}' - contains transaction offers and expected conditions"
        elif any(name in field_names for name in ['spender', 'value', 'deadline']):
            return f"Authorization permit structure '{struct_name}' - contains token authorization information"
        elif any(name in field_names for name in ['to', 'value', 'data']):
            return f"Transaction structure '{struct_name}' - contains transaction target and data"
        elif any(name in field_names for name in ['voter', 'proposal', 'support']):
            return f"Governance voting structure '{struct_name}' - contains voting decision information"
        else:
            confidence_desc = f" (with {len(high_confidence_fields)} high-confidence fields)" if high_confidence_fields else ""
            return f"Data structure '{struct_name}' - contains {len(fields)} fields{confidence_desc}"
    
    def format_result(self, result: EIP712ParseResult) -> str:
        """Format parsing result as readable text"""
        lines = []
        
        lines.append("=" * 60)
        lines.append("EIP712 Signature Structure Parsing Result")
        lines.append("=" * 60)
        
        # Domain information
        lines.append(f"\nDomain Information ({result.domain.name}):")
        lines.append(f"   Description: {result.domain.description}")
        for field in result.domain.fields:
            lines.append(f"   • {field.description}")
        
        # Primary message
        lines.append(f"\nPrimary Message ({result.primary_type}):")
        lines.append(f"   Description: {result.message.description}")
        lines.append(f"   Field count: {len(result.message.fields)}")
        
        lines.append(f"\nMessage Structure Tree:")
        self._format_struct_tree(result.message, lines, indent="   ")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _format_struct_tree(self, struct: StructInfo, lines: List[str], indent: str = ""):
        """Format struct tree"""
        for i, field in enumerate(struct.fields):
            is_last = i == len(struct.fields) - 1
            tree_char = "└── " if is_last else "├── "
            next_indent = indent + ("    " if is_last else "│   ")
            
            lines.append(f"{indent}{tree_char}{field.description}")
            
            # Recursively display child fields
            if field.children:
                for j, child in enumerate(field.children):
                    child_is_last = j == len(field.children) - 1
                    child_tree_char = "└── " if child_is_last else "├── "
                    lines.append(f"{next_indent}{child_tree_char}{child.description}") 