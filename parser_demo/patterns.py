"""
Dynamic Parser Pattern Matching
Contains semantic recognition patterns, type inference patterns and context keywords
"""

from typing import Dict, List, Tuple, Set
from .field_types import FieldSemantic, FieldType


class PatternMatcher:
    """Pattern matcher"""
    
    def __init__(self):
        self.semantic_patterns = self._init_semantic_patterns()
        self.type_patterns = self._init_type_patterns()
        self.context_keywords = self._init_context_keywords()
    
    def _init_semantic_patterns(self) -> List[Tuple[str, FieldSemantic]]:
        """Initialize semantic patterns - returns list of (pattern, semantic)"""
        return [
            # Exact match patterns
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
            
            # Composite match patterns
            (r".*token.*id.*", FieldSemantic.TOKEN_ID),
            (r".*proposal.*id.*", FieldSemantic.PROPOSAL_ID),
            (r".*chain.*id.*", FieldSemantic.CHAIN_ID),
            (r".*voting.*power.*", FieldSemantic.VOTING_POWER),
            (r".*merkle.*root.*", FieldSemantic.MERKLE_ROOT),
            
            # Identity related
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
            
            # Amount related
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
            
            # Time related
            (r".*expiry.*", FieldSemantic.DEADLINE),
            (r".*expires.*", FieldSemantic.DEADLINE),
            (r".*time.*", FieldSemantic.TIMESTAMP),
            (r".*start.*time.*", FieldSemantic.START_TIME),
            (r".*end.*time.*", FieldSemantic.END_TIME),
            (r".*duration.*", FieldSemantic.DURATION),
            (r".*delay.*", FieldSemantic.DELAY),
            (r".*period.*", FieldSemantic.PERIOD),
            
            # Identifier related
            (r".*salt.*", FieldSemantic.SALT),
            (r".*index.*", FieldSemantic.INDEX),
            (r".*counter.*", FieldSemantic.COUNTER),
            (r".*key.*", FieldSemantic.KEY),
            (r"^id$", FieldSemantic.ID),
            (r".*_id$", FieldSemantic.ID),
            
            # Data related
            (r".*data.*", FieldSemantic.DATA),
            (r".*payload.*", FieldSemantic.DATA),
            (r".*hash.*", FieldSemantic.HASH),
            (r".*signature.*", FieldSemantic.SIGNATURE),
            (r".*proof.*", FieldSemantic.PROOF),
            (r".*metadata.*", FieldSemantic.METADATA),
            
            # Configuration related
            (r".*version.*", FieldSemantic.VERSION),
            (r".*type.*", FieldSemantic.TYPE),
            (r".*status.*", FieldSemantic.STATUS),
            (r".*flag.*", FieldSemantic.FLAG),
            (r".*option.*", FieldSemantic.OPTION),
            
            # Governance related
            (r".*vote.*type.*", FieldSemantic.VOTE_TYPE),
            (r".*support.*", FieldSemantic.VOTE_TYPE),
            
            # NFT related
            (r".*collection.*", FieldSemantic.COLLECTION),
            (r".*pool.*", FieldSemantic.POOL),
        ]
    
    def _init_type_patterns(self) -> List[Tuple[str, str, FieldType]]:
        """Initialize type inference patterns - returns list of (field name pattern, type pattern, inferred type)"""
        return [
            # Amount type
            (r".*amount.*|.*value.*|.*price.*|.*fee.*|.*cost.*|.*quantity.*", r"uint.*", FieldType.AMOUNT),
            (r".*balance.*|.*allowance.*|.*reward.*|.*penalty.*", r"uint.*", FieldType.AMOUNT),
            (r".*liquidity.*|.*slippage.*|.*rate.*|.*yield.*", r"uint.*", FieldType.AMOUNT),
            
            # Timestamp type
            (r".*time.*|.*deadline.*|.*expiry.*|.*expires.*|.*timestamp.*", r"uint.*", FieldType.TIMESTAMP),
            (r".*duration.*|.*delay.*|.*period.*", r"uint.*", FieldType.TIMESTAMP),
            
            # Nonce type
            (r".*nonce.*", r"uint.*", FieldType.NONCE),
            (r".*counter.*|.*index.*", r"uint.*", FieldType.NONCE),
            
            # Address type
            (r".*token.*|.*erc20.*|.*erc721.*|.*erc1155.*", r"address", FieldType.TOKEN_ADDRESS),
            (r".*contract.*|.*verifying.*", r"address", FieldType.CONTRACT_ADDRESS),
            
            # Hash type
            (r".*hash.*|.*root.*|.*digest.*", r"bytes32", FieldType.HASH),
            
            # Signature type
            (r".*signature.*|.*sig.*", r"bytes.*", FieldType.SIGNATURE),
            
            # Percentage type
            (r".*percent.*|.*ratio.*|.*bps.*", r"uint.*", FieldType.PERCENTAGE),
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
    
    def infer_semantic(self, field_name: str) -> FieldSemantic:
        """Infer semantic based on field name"""
        import re
        
        field_name_lower = field_name.lower()
        
        for pattern, semantic in self.semantic_patterns:
            if re.match(pattern, field_name_lower):
                return semantic
        
        return None
    
    def infer_field_type(self, field_name: str, type_name: str) -> FieldType:
        """Infer field type based on field name and type"""
        import re
        
        field_name_lower = field_name.lower()
        type_name_lower = type_name.lower()
        
        for name_pattern, type_pattern, field_type in self.type_patterns:
            if re.match(name_pattern, field_name_lower) and re.match(type_pattern, type_name_lower):
                return field_type
        
        # Basic inference based on type
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
        """Detect struct context"""
        struct_name_lower = struct_name.lower()
        field_names_lower = [name.lower() for name in field_names]
        
        # Direct match with struct name
        for context_name in self.context_keywords:
            if context_name in struct_name_lower:
                return context_name
        
        # Match based on field names
        context_scores = {}
        for context_name, keywords in self.context_keywords.items():
            score = len(keywords.intersection(set(field_names_lower)))
            if score > 0:
                context_scores[context_name] = score
        
        if context_scores:
            return max(context_scores, key=context_scores.get)
        
        return "unknown"