"""
动态 EIP712 解析器
能够解析任意 EIP712 签名结构和语义的通用工具
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import datetime


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
    confidence: float = 0.0            # 识别置信度 (0-1)
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


class DynamicEIP712Parser:
    """动态 EIP712 解析器"""
    
    def __init__(self):
        self.types: Dict[str, List[Dict[str, str]]] = {}
        self.semantic_patterns = self._init_semantic_patterns()
        self.type_patterns = self._init_type_patterns()
        self.context_keywords = self._init_context_keywords()
        self.value_analyzers = self._init_value_analyzers()
    
    def _init_semantic_patterns(self) -> List[Tuple[str, FieldSemantic, float]]:
        """初始化语义模式 - 返回 (模式, 语义, 置信度) 的列表"""
        return [
            # 高置信度模式 (0.9+)
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
            
            # 中高置信度模式 (0.8+)
            (r".*token.*id.*", FieldSemantic.TOKEN_ID, 0.85),
            (r".*proposal.*id.*", FieldSemantic.PROPOSAL_ID, 0.85),
            (r".*chain.*id.*", FieldSemantic.CHAIN_ID, 0.85),
            (r".*voting.*power.*", FieldSemantic.VOTING_POWER, 0.85),
            (r".*merkle.*root.*", FieldSemantic.MERKLE_ROOT, 0.85),
            
            # 身份相关 (0.7+)
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
            
            # 金额相关 (0.7+)
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
            
            # 时间相关 (0.7+)
            (r".*expiry.*", FieldSemantic.DEADLINE, 0.85),
            (r".*expires.*", FieldSemantic.DEADLINE, 0.85),
            (r".*time.*", FieldSemantic.TIMESTAMP, 0.7),
            (r".*start.*time.*", FieldSemantic.START_TIME, 0.85),
            (r".*end.*time.*", FieldSemantic.END_TIME, 0.85),
            (r".*duration.*", FieldSemantic.DURATION, 0.8),
            (r".*delay.*", FieldSemantic.DELAY, 0.8),
            (r".*period.*", FieldSemantic.PERIOD, 0.8),
            
            # 标识相关 (0.7+)
            (r".*salt.*", FieldSemantic.SALT, 0.9),
            (r".*index.*", FieldSemantic.INDEX, 0.8),
            (r".*counter.*", FieldSemantic.COUNTER, 0.8),
            (r".*key.*", FieldSemantic.KEY, 0.7),
            (r"^id$", FieldSemantic.ID, 0.8),
            (r".*_id$", FieldSemantic.ID, 0.75),
            
            # 数据相关 (0.7+)
            (r".*data.*", FieldSemantic.DATA, 0.75),
            (r".*payload.*", FieldSemantic.DATA, 0.8),
            (r".*hash.*", FieldSemantic.HASH, 0.8),
            (r".*signature.*", FieldSemantic.SIGNATURE, 0.85),
            (r".*proof.*", FieldSemantic.PROOF, 0.8),
            (r".*metadata.*", FieldSemantic.METADATA, 0.8),
            
            # 配置相关 (0.7+)
            (r".*version.*", FieldSemantic.VERSION, 0.8),
            (r".*type.*", FieldSemantic.TYPE, 0.7),
            (r".*status.*", FieldSemantic.STATUS, 0.8),
            (r".*flag.*", FieldSemantic.FLAG, 0.75),
            (r".*option.*", FieldSemantic.OPTION, 0.75),
            
            # 治理相关 (0.7+)
            (r".*vote.*type.*", FieldSemantic.VOTE_TYPE, 0.85),
            (r".*support.*", FieldSemantic.VOTE_TYPE, 0.8),
            
            # NFT相关 (0.7+)
            (r".*collection.*", FieldSemantic.COLLECTION, 0.8),
            (r".*pool.*", FieldSemantic.POOL, 0.75),
        ]
    
    def _init_type_patterns(self) -> List[Tuple[str, str, FieldType, float]]:
        """初始化类型推断模式 - 返回 (字段名模式, 类型模式, 推断类型, 置信度) 的列表"""
        return [
            # 金额类型
            (r".*amount.*|.*value.*|.*price.*|.*fee.*|.*cost.*|.*quantity.*", r"uint.*", FieldType.AMOUNT, 0.9),
            (r".*balance.*|.*allowance.*|.*reward.*|.*penalty.*", r"uint.*", FieldType.AMOUNT, 0.85),
            (r".*liquidity.*|.*slippage.*|.*rate.*|.*yield.*", r"uint.*", FieldType.AMOUNT, 0.8),
            
            # 时间戳类型
            (r".*time.*|.*deadline.*|.*expiry.*|.*expires.*|.*timestamp.*", r"uint.*", FieldType.TIMESTAMP, 0.9),
            (r".*duration.*|.*delay.*|.*period.*", r"uint.*", FieldType.TIMESTAMP, 0.8),
            
            # 随机数类型
            (r".*nonce.*", r"uint.*", FieldType.NONCE, 0.95),
            (r".*counter.*|.*index.*", r"uint.*", FieldType.NONCE, 0.8),
            
            # 地址类型
            (r".*token.*|.*erc20.*|.*erc721.*|.*erc1155.*", r"address", FieldType.TOKEN_ADDRESS, 0.9),
            (r".*contract.*|.*verifying.*", r"address", FieldType.CONTRACT_ADDRESS, 0.85),
            
            # 哈希类型
            (r".*hash.*|.*root.*|.*digest.*", r"bytes32", FieldType.HASH, 0.9),
            
            # 签名类型
            (r".*signature.*|.*sig.*", r"bytes.*", FieldType.SIGNATURE, 0.9),
            
            # 百分比类型
            (r".*percent.*|.*ratio.*|.*bps.*", r"uint.*", FieldType.PERCENTAGE, 0.85),
        ]
    
    def _init_context_keywords(self) -> Dict[str, Set[str]]:
        """初始化上下文关键词"""
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
        """初始化值分析器"""
        return [
            self._analyze_timestamp_value,
            self._analyze_amount_value,
            self._analyze_address_value,
            self._analyze_percentage_value,
            self._analyze_enum_value,
        ]
    
    def parse(self, eip712_data: Dict[str, Any]) -> EIP712ParseResult:
        """
        解析 EIP712 数据
        
        Args:
            eip712_data: EIP712 格式的数据
            
        Returns:
            解析结果
        """
        if not self._validate_eip712_data(eip712_data):
            raise ValueError("无效的 EIP712 数据格式")
        
        self.types = eip712_data['types']
        
        # 解析域信息
        domain_struct = self._parse_struct("EIP712Domain", eip712_data['domain'])
        
        # 解析主要消息
        primary_type = eip712_data['primaryType']
        message_struct = self._parse_struct(primary_type, eip712_data['message'])
        
        return EIP712ParseResult(
            domain=domain_struct,
            primary_type=primary_type,
            message=message_struct,
            raw_data=eip712_data
        )
    
    def _validate_eip712_data(self, data: Dict[str, Any]) -> bool:
        """验证 EIP712 数据格式"""
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
        解析结构体（增强版）
        
        Args:
            struct_name: 结构体名称
            struct_data: 结构体数据
            
        Returns:
            结构体信息
        """
        if struct_name not in self.types:
            raise ValueError(f"未找到结构体定义: {struct_name}")
        
        struct_definition = self.types[struct_name]
        field_names = [field_def['name'] for field_def in struct_definition]
        
        # 检测结构体上下文类型
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
        解析字段（增强版）
        
        Args:
            field_name: 字段名
            field_type: 字段类型
            field_value: 字段值
            struct_context: 结构体上下文
            
        Returns:
            字段信息
        """
        # 解析类型
        is_array = field_type.endswith('[]')
        array_element_type = None
        base_type = field_type
        
        if is_array:
            base_type = field_type[:-2]
            array_element_type = base_type
        
        # 推断字段类型
        inferred_type = self._infer_field_type(field_name, base_type, field_value)
        
        # 推断语义（带置信度）
        semantic, confidence = self._infer_semantic(field_name, base_type, field_value, struct_context)
        
        # 处理子结构
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
                            description=f"数组元素 {i}",
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
        
        # 收集上下文提示
        context_hints = []
        if struct_context:
            context_hints.append(f"结构体类型: {struct_context}")
        if confidence >= 0.8:
            context_hints.append(f"高置信度识别")
        
        # 生成描述
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
        """分析时间戳值"""
        if not isinstance(field_value, (int, str)):
            return None
        
        try:
            timestamp = int(field_value)
            # 检查是否是合理的时间戳范围 (2000年 - 2100年)
            if 946684800 <= timestamp <= 4102444800:
                confidence = 0.8
                # 检查是否是截止时间
                if any(keyword in field_name.lower() for keyword in ['deadline', 'expiry', 'expires']):
                    return (FieldType.DEADLINE, FieldSemantic.DEADLINE, confidence + 0.1)
                else:
                    return (FieldType.TIMESTAMP, FieldSemantic.TIMESTAMP, confidence)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _analyze_amount_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """分析金额值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            amount = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是典型的ERC20金额 (18位小数)
            if amount > 10**15:  # 大于 0.001 ETH
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
        """分析地址值"""
        if field_type != 'address' or not isinstance(field_value, str):
            return None
        
        # 检查是否是有效的以太坊地址
        if not (field_value.startswith('0x') and len(field_value) == 42):
            return None
        
        field_name_lower = field_name.lower()
        confidence = 0.8
        
        # 检查是否是零地址
        if field_value == '0x0000000000000000000000000000000000000000':
            confidence = 0.6
        
        # 根据字段名推断地址类型
        if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
            return (FieldType.TOKEN_ADDRESS, FieldSemantic.COLLECTION, confidence + 0.1)
        elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
            return (FieldType.CONTRACT_ADDRESS, FieldSemantic.TYPE, confidence + 0.1)
        else:
            return (FieldType.USER_ADDRESS, None, confidence)
    
    def _analyze_percentage_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """分析百分比值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是百分比（0-100或0-10000的范围）
            if (0 <= value <= 100 and any(keyword in field_name_lower for keyword in ['percent', 'ratio'])) or \
               (0 <= value <= 10000 and 'bps' in field_name_lower):
                return (FieldType.PERCENTAGE, FieldSemantic.RATE, 0.85)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _analyze_enum_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic, float]]:
        """分析枚举值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是小范围的整数（可能是枚举）
            if 0 <= value <= 20:
                if any(keyword in field_name_lower for keyword in ['type', 'kind', 'status', 'state', 'mode']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.TYPE, 0.75)
                elif any(keyword in field_name_lower for keyword in ['support', 'vote']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.VOTE_TYPE, 0.8)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _detect_struct_context(self, struct_name: str, field_names: List[str]) -> Optional[str]:
        """检测结构体上下文类型"""
        field_names_lower = [name.lower() for name in field_names]
        field_set = set(field_names_lower)
        
        # 计算每种上下文的匹配度
        context_scores = {}
        for context_type, keywords in self.context_keywords.items():
            match_count = len(keywords.intersection(field_set))
            if match_count > 0:
                context_scores[context_type] = match_count / len(keywords)
        
        # 返回匹配度最高的上下文
        if context_scores:
            best_context = max(context_scores, key=context_scores.get)
            if context_scores[best_context] >= 0.5:  # 至少50%匹配
                return best_context
        
        return None
    
    def _infer_field_type(self, field_name: str, field_type: str, field_value: Any) -> FieldType:
        """推断字段类型（增强版）"""
        field_name_lower = field_name.lower()
        
        # 首先使用值分析器
        for analyzer in self.value_analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result:
                return result[0]
        
        # 使用类型模式匹配
        for name_pattern, type_pattern, inferred_type, confidence in self.type_patterns:
            if re.match(name_pattern, field_name_lower) and re.match(type_pattern, field_type):
                return inferred_type
        
        # 基于字段类型的默认推断
        if field_type.startswith('uint') or field_type.startswith('int'):
            # 进一步推断是否为金额、时间戳等
            if any(keyword in field_name_lower for keyword in ['amount', 'value', 'price', 'fee', 'cost', 'quantity']):
                return FieldType.AMOUNT
            elif any(keyword in field_name_lower for keyword in ['time', 'deadline', 'expiry', 'expires', 'timestamp']):
                return FieldType.TIMESTAMP
            elif 'nonce' in field_name_lower:
                return FieldType.NONCE
            else:
                return FieldType.UINT if field_type.startswith('uint') else FieldType.INT
        
        elif field_type == 'address':
            # 根据字段名推断地址类型
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
            return FieldType.STRING  # 默认类型
    
    def _infer_semantic(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> Tuple[Optional[FieldSemantic], float]:
        """推断字段语义（增强版）"""
        field_name_lower = field_name.lower()
        best_semantic = None
        best_confidence = 0.0
        
        # 首先使用值分析器
        for analyzer in self.value_analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result and result[1] and result[2] > best_confidence:
                best_semantic = result[1]
                best_confidence = result[2]
        
        # 使用语义模式匹配
        for pattern, semantic, confidence in self.semantic_patterns:
            if re.match(pattern, field_name_lower) and confidence > best_confidence:
                best_semantic = semantic
                best_confidence = confidence
        
        # 上下文增强
        if struct_context and best_semantic:
            context_boost = self._get_context_boost(best_semantic, struct_context)
            best_confidence = min(0.95, best_confidence + context_boost)
        
        return (best_semantic, best_confidence)
    
    def _get_context_boost(self, semantic: FieldSemantic, struct_context: str) -> float:
        """根据结构体上下文计算语义置信度提升"""
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
        """生成字段描述"""
        base_desc = f"字段 '{field_name}'"
        
        # 添加语义描述
        if semantic:
            semantic_desc = {
                # 身份相关
                FieldSemantic.OWNER: "拥有者地址",
                FieldSemantic.SPENDER: "授权花费者地址", 
                FieldSemantic.RECIPIENT: "接收者地址",
                FieldSemantic.TRADER: "交易者地址",
                FieldSemantic.OFFERER: "报价者地址",
                FieldSemantic.BIDDER: "竞拍者地址",
                FieldSemantic.SELLER: "卖方地址",
                FieldSemantic.BUYER: "买方地址",
                FieldSemantic.VALIDATOR: "验证者地址",
                FieldSemantic.DELEGATE: "委托者地址",
                FieldSemantic.CREATOR: "创建者地址",
                
                # 金额相关
                FieldSemantic.VALUE: "数值",
                FieldSemantic.AMOUNT: "金额",
                FieldSemantic.PRICE: "价格",
                FieldSemantic.FEE: "手续费",
                FieldSemantic.REWARD: "奖励金额",
                FieldSemantic.PENALTY: "惩罚金额",
                FieldSemantic.BALANCE: "余额",
                FieldSemantic.ALLOWANCE: "授权额度",
                FieldSemantic.MINIMUM: "最小值",
                FieldSemantic.MAXIMUM: "最大值",
                FieldSemantic.LIQUIDITY: "流动性",
                FieldSemantic.SLIPPAGE: "滑点",
                FieldSemantic.RATE: "比率",
                FieldSemantic.YIELD: "收益率",
                FieldSemantic.ROYALTY: "版税",
                
                # 时间相关
                FieldSemantic.TIMESTAMP: "时间戳",
                FieldSemantic.DEADLINE: "截止时间",
                FieldSemantic.START_TIME: "开始时间",
                FieldSemantic.END_TIME: "结束时间",
                FieldSemantic.DURATION: "持续时间",
                FieldSemantic.DELAY: "延迟时间",
                FieldSemantic.PERIOD: "周期",
                
                # 标识相关
                FieldSemantic.TOKEN_ID: "代币ID",
                FieldSemantic.NONCE: "随机数",
                FieldSemantic.SALT: "盐值",
                FieldSemantic.INDEX: "索引",
                FieldSemantic.ID: "标识符",
                FieldSemantic.KEY: "键值",
                FieldSemantic.COUNTER: "计数器",
                
                # 数据相关
                FieldSemantic.DATA: "数据",
                FieldSemantic.HASH: "哈希值",
                FieldSemantic.SIGNATURE: "签名",
                FieldSemantic.PROOF: "证明",
                FieldSemantic.MERKLE_ROOT: "默克尔根",
                FieldSemantic.METADATA: "元数据",
                
                # 配置相关
                FieldSemantic.VERSION: "版本号",
                FieldSemantic.CHAIN_ID: "链ID",
                FieldSemantic.TYPE: "类型",
                FieldSemantic.STATUS: "状态",
                FieldSemantic.FLAG: "标志",
                FieldSemantic.OPTION: "选项",
                
                # 治理相关
                FieldSemantic.PROPOSAL_ID: "提案ID",
                FieldSemantic.VOTE_TYPE: "投票类型",
                FieldSemantic.VOTING_POWER: "投票权重",
                
                # NFT相关
                FieldSemantic.COLLECTION: "合集地址",
                FieldSemantic.POOL: "资金池",
            }.get(semantic, semantic.value)
            
            # 添加置信度显示（高置信度时显示）
            confidence_str = ""
            if confidence >= 0.8:
                confidence_str = f" [{confidence:.0%}置信度]"
            
            base_desc += f" ({semantic_desc}{confidence_str})"
        
        # 添加类型描述
        type_desc = {
            FieldType.TOKEN_ADDRESS: "代币合约地址",
            FieldType.USER_ADDRESS: "用户地址", 
            FieldType.CONTRACT_ADDRESS: "合约地址",
            FieldType.AMOUNT: "金额数值",
            FieldType.TIMESTAMP: "时间戳",
            FieldType.NONCE: "随机数",
            FieldType.HASH: "哈希值",
            FieldType.SIGNATURE: "签名数据",
        }.get(field_type)
        
        if type_desc:
            base_desc += f" - {type_desc}"
        
        # 添加值描述
        if field_value is not None:
            if field_type == FieldType.TIMESTAMP and isinstance(field_value, (int, str)):
                try:
                    timestamp = int(field_value)
                    if timestamp > 1000000000:  # 看起来像时间戳
                        dt = datetime.datetime.fromtimestamp(timestamp)
                        base_desc += f" (时间: {dt.strftime('%Y-%m-%d %H:%M:%S')})"
                except:
                    pass
            elif field_type in [FieldType.TOKEN_ADDRESS, FieldType.USER_ADDRESS, FieldType.CONTRACT_ADDRESS]:
                base_desc += f" ({field_value})"
            elif field_type == FieldType.AMOUNT and isinstance(field_value, (int, str)):
                try:
                    # 尝试转换为 ETH 单位显示
                    amount = int(field_value)
                    if amount > 10**15:  # 如果大于 0.001 ETH
                        eth_amount = amount / 10**18
                        base_desc += f" ({eth_amount:.6f} ETH)"
                except:
                    base_desc += f" ({field_value})"
            elif isinstance(field_value, (str, int)) and len(str(field_value)) < 50:
                base_desc += f" = {field_value}"
        
        return base_desc
    
    def _generate_struct_description(self, struct_name: str, fields: List[FieldInfo], struct_context: Optional[str] = None) -> str:
        """生成结构体描述（增强版）"""
        # 根据结构体名称和字段推断用途
        if struct_name == "EIP712Domain":
            return "EIP712 域信息 - 定义签名的域和验证上下文"
        
        # 使用检测到的上下文
        if struct_context:
            context_descriptions = {
                "permit": f"授权许可结构 '{struct_name}' - 允许第三方代表用户操作代币",
                "order": f"市场订单结构 '{struct_name}' - 定义交易的报价条件和期望",
                "vote": f"治理投票结构 '{struct_name}' - 记录对提案的投票决策",
                "transfer": f"转账结构 '{struct_name}' - 定义资产转移的详细信息",
                "mint": f"铸造结构 '{struct_name}' - 定义新代币的创建参数",
                "burn": f"销毁结构 '{struct_name}' - 定义代币销毁的操作",
                "governance": f"治理结构 '{struct_name}' - 定义治理提案和执行参数",
                "auction": f"拍卖结构 '{struct_name}' - 定义拍卖的竞价和条件",
                "swap": f"交换结构 '{struct_name}' - 定义代币交换的参数",
                "liquidity": f"流动性结构 '{struct_name}' - 定义流动性操作的参数",
            }
            
            if struct_context in context_descriptions:
                return context_descriptions[struct_context]
        
        # 根据字段推断结构体用途（后备方案）
        field_names = [field.name.lower() for field in fields]
        high_confidence_fields = [field for field in fields if field.confidence >= 0.8]
        
        if any(name in field_names for name in ['offerer', 'offer', 'consideration']):
            return f"市场订单结构 '{struct_name}' - 包含交易报价和期望条件"
        elif any(name in field_names for name in ['spender', 'value', 'deadline']):
            return f"授权许可结构 '{struct_name}' - 包含代币授权信息"
        elif any(name in field_names for name in ['to', 'value', 'data']):
            return f"交易结构 '{struct_name}' - 包含交易目标和数据"
        elif any(name in field_names for name in ['voter', 'proposal', 'support']):
            return f"治理投票结构 '{struct_name}' - 包含投票决策信息"
        else:
            confidence_desc = f" (其中 {len(high_confidence_fields)} 个高置信度字段)" if high_confidence_fields else ""
            return f"数据结构 '{struct_name}' - 包含 {len(fields)} 个字段{confidence_desc}"
    
    def format_result(self, result: EIP712ParseResult) -> str:
        """格式化解析结果为可读文本"""
        lines = []
        
        lines.append("=" * 60)
        lines.append("EIP712 签名结构解析结果")
        lines.append("=" * 60)
        
        # 域信息
        lines.append(f"\n域信息 ({result.domain.name}):")
        lines.append(f"   描述: {result.domain.description}")
        for field in result.domain.fields:
            lines.append(f"   • {field.description}")
        
        # 主要消息
        lines.append(f"\n主要消息 ({result.primary_type}):")
        lines.append(f"   描述: {result.message.description}")
        lines.append(f"   字段数量: {len(result.message.fields)}")
        
        lines.append(f"\n消息结构树:")
        self._format_struct_tree(result.message, lines, indent="   ")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _format_struct_tree(self, struct: StructInfo, lines: List[str], indent: str = ""):
        """格式化结构体树"""
        for i, field in enumerate(struct.fields):
            is_last = i == len(struct.fields) - 1
            tree_char = "└── " if is_last else "├── "
            next_indent = indent + ("    " if is_last else "│   ")
            
            lines.append(f"{indent}{tree_char}{field.description}")
            
            # 递归显示子字段
            if field.children:
                for j, child in enumerate(field.children):
                    child_is_last = j == len(field.children) - 1
                    child_tree_char = "└── " if child_is_last else "├── "
                    lines.append(f"{next_indent}{child_tree_char}{child.description}") 