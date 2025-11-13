"""
动态解析器模式匹配
包含语义识别模式、类型推断模式和上下文关键词
"""

from typing import Dict, List, Tuple, Set
from .field_types import FieldSemantic, FieldType


class PatternMatcher:
    """模式匹配器"""
    
    def __init__(self):
        self.semantic_patterns = self._init_semantic_patterns()
        self.type_patterns = self._init_type_patterns()
        self.context_keywords = self._init_context_keywords()
    
    def _init_semantic_patterns(self) -> List[Tuple[str, FieldSemantic]]:
        """初始化语义模式 - 返回 (模式, 语义) 的列表"""
        return [
            # 精确匹配模式
            (r"^tokenid$", FieldSemantic.TOKEN_ID),
            (r"^nonce$", FieldSemantic.NONCE),
            (r"^chainid$", FieldSemantic.CHAIN_ID),
            (r"^deadline$", FieldSemantic.DEADLINE),
            (r"^timestamp$", FieldSemantic.TIMESTAMP),
            (r"^spender$", FieldSemantic.SPENDER),
            (r"^owner$", FieldSemantic.OWNER),
            (r"^recipient$", FieldSemantic.RECIPIENT),
            (r"^amount$", FieldSemantic.AMOUNT),
            (r"^value$", FieldSemantic.VALUE),
            (r"^price$", FieldSemantic.PRICE),
            (r"^fee$", FieldSemantic.FEE),
            
            # 复合匹配模式
            (r".*token.*id.*", FieldSemantic.TOKEN_ID),
            (r".*proposal.*id.*", FieldSemantic.PROPOSAL_ID),
            (r".*chain.*id.*", FieldSemantic.CHAIN_ID),
            (r".*voting.*power.*", FieldSemantic.VOTING_POWER),
            (r".*merkle.*root.*", FieldSemantic.MERKLE_ROOT),
            
            # 身份相关
            (r".*holder.*", FieldSemantic.OWNER),
            (r".*minter.*", FieldSemantic.OWNER),
            (r".*creator.*", FieldSemantic.CREATOR),
            (r".*from.*", FieldSemantic.OWNER),
            (r".*approved.*", FieldSemantic.SPENDER),
            (r".*to.*", FieldSemantic.RECIPIENT),
            (r".*beneficiary.*", FieldSemantic.RECIPIENT),
            (r".*trader.*", FieldSemantic.TRADER),
            (r".*offerer.*", FieldSemantic.OFFERER),
            (r".*maker.*", FieldSemantic.OFFERER),
            (r".*bidder.*", FieldSemantic.BIDDER),
            (r".*seller.*", FieldSemantic.SELLER),
            (r".*buyer.*", FieldSemantic.BUYER),
            (r".*validator.*", FieldSemantic.VALIDATOR),
            (r".*delegate.*", FieldSemantic.DELEGATE),
            
            # 金额相关
            (r".*quantity.*", FieldSemantic.AMOUNT),
            (r".*cost.*", FieldSemantic.FEE),
            (r".*reward.*", FieldSemantic.REWARD),
            (r".*penalty.*", FieldSemantic.PENALTY),
            (r".*balance.*", FieldSemantic.BALANCE),
            (r".*allowance.*", FieldSemantic.ALLOWANCE),
            (r".*minimum.*", FieldSemantic.MINIMUM),
            (r".*maximum.*", FieldSemantic.MAXIMUM),
            (r".*min.*", FieldSemantic.MINIMUM),
            (r".*max.*", FieldSemantic.MAXIMUM),
            (r".*liquidity.*", FieldSemantic.LIQUIDITY),
            (r".*slippage.*", FieldSemantic.SLIPPAGE),
            (r".*rate.*", FieldSemantic.RATE),
            (r".*yield.*", FieldSemantic.YIELD),
            (r".*royalty.*", FieldSemantic.ROYALTY),
            
            # 时间相关
            (r".*expiry.*", FieldSemantic.DEADLINE),
            (r".*expires.*", FieldSemantic.DEADLINE),
            (r".*time.*", FieldSemantic.TIMESTAMP),
            (r".*start.*time.*", FieldSemantic.START_TIME),
            (r".*end.*time.*", FieldSemantic.END_TIME),
            (r".*duration.*", FieldSemantic.DURATION),
            (r".*delay.*", FieldSemantic.DELAY),
            (r".*period.*", FieldSemantic.PERIOD),
            
            # 标识相关
            (r".*salt.*", FieldSemantic.SALT),
            (r".*index.*", FieldSemantic.INDEX),
            (r".*counter.*", FieldSemantic.COUNTER),
            (r".*key.*", FieldSemantic.KEY),
            (r"^id$", FieldSemantic.ID),
            (r".*_id$", FieldSemantic.ID),
            
            # 数据相关
            (r".*data.*", FieldSemantic.DATA),
            (r".*payload.*", FieldSemantic.DATA),
            (r".*hash.*", FieldSemantic.HASH),
            (r".*signature.*", FieldSemantic.SIGNATURE),
            (r".*proof.*", FieldSemantic.PROOF),
            (r".*metadata.*", FieldSemantic.METADATA),
            
            # 配置相关
            (r".*version.*", FieldSemantic.VERSION),
            (r".*type.*", FieldSemantic.TYPE),
            (r".*status.*", FieldSemantic.STATUS),
            (r".*flag.*", FieldSemantic.FLAG),
            (r".*option.*", FieldSemantic.OPTION),
            
            # 治理相关
            (r".*vote.*type.*", FieldSemantic.VOTE_TYPE),
            (r".*support.*", FieldSemantic.VOTE_TYPE),
            
            # NFT相关
            (r".*collection.*", FieldSemantic.COLLECTION),
            (r".*pool.*", FieldSemantic.POOL),
        ]
    
    def _init_type_patterns(self) -> List[Tuple[str, str, FieldType]]:
        """初始化类型推断模式 - 返回 (字段名模式, 类型模式, 推断类型) 的列表"""
        return [
            # 金额类型
            (r".*amount.*|.*value.*|.*price.*|.*fee.*|.*cost.*|.*quantity.*", r"uint.*", FieldType.AMOUNT),
            (r".*balance.*|.*allowance.*|.*reward.*|.*penalty.*", r"uint.*", FieldType.AMOUNT),
            (r".*liquidity.*|.*slippage.*|.*rate.*|.*yield.*", r"uint.*", FieldType.AMOUNT),
            
            # 时间戳类型
            (r".*time.*|.*deadline.*|.*expiry.*|.*expires.*|.*timestamp.*", r"uint.*", FieldType.TIMESTAMP),
            (r".*duration.*|.*delay.*|.*period.*", r"uint.*", FieldType.TIMESTAMP),
            
            # 随机数类型
            (r".*nonce.*", r"uint.*", FieldType.NONCE),
            (r".*counter.*|.*index.*", r"uint.*", FieldType.NONCE),
            
            # 地址类型
            (r".*token.*|.*erc20.*|.*erc721.*|.*erc1155.*", r"address", FieldType.TOKEN_ADDRESS),
            (r".*contract.*|.*verifying.*", r"address", FieldType.CONTRACT_ADDRESS),
            
            # 哈希类型
            (r".*hash.*|.*root.*|.*digest.*", r"bytes32", FieldType.HASH),
            
            # 签名类型
            (r".*signature.*|.*sig.*", r"bytes.*", FieldType.SIGNATURE),
            
            # 百分比类型
            (r".*percent.*|.*ratio.*|.*bps.*", r"uint.*", FieldType.PERCENTAGE),
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
    
    def infer_semantic(self, field_name: str) -> FieldSemantic:
        """根据字段名推断语义"""
        import re
        
        field_name_lower = field_name.lower()
        
        for pattern, semantic in self.semantic_patterns:
            if re.match(pattern, field_name_lower):
                return semantic
        
        return None
    
    def infer_field_type(self, field_name: str, type_name: str) -> FieldType:
        """根据字段名和类型推断字段类型"""
        import re
        
        field_name_lower = field_name.lower()
        type_name_lower = type_name.lower()
        
        for name_pattern, type_pattern, field_type in self.type_patterns:
            if re.match(name_pattern, field_name_lower) and re.match(type_pattern, type_name_lower):
                return field_type
        
        # 基于类型的基本推断
        if type_name_lower == "address":
            return FieldType.ADDRESS
        elif "uint" in type_name_lower:
            return FieldType.UINT
        elif "bytes" in type_name_lower:
            return FieldType.BYTES
        elif type_name_lower == "bool":
            return FieldType.BOOL
        elif type_name_lower == "string":
            return FieldType.STRING
        
        return FieldType.UNKNOWN
    
    def detect_context(self, struct_name: str, field_names: List[str]) -> str:
        """检测结构体上下文"""
        struct_name_lower = struct_name.lower()
        field_names_lower = [name.lower() for name in field_names]
        
        # 直接匹配结构体名称
        for context_name in self.context_keywords:
            if context_name in struct_name_lower:
                return context_name
        
        # 根据字段名匹配
        context_scores = {}
        for context_name, keywords in self.context_keywords.items():
            score = len(keywords.intersection(set(field_names_lower)))
            if score > 0:
                context_scores[context_name] = score
        
        if context_scores:
            return max(context_scores, key=context_scores.get)
        
        return "unknown"