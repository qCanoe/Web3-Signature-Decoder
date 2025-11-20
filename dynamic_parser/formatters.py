"""
Dynamic Parser Formatter
Contains field description generation, struct description generation and result formatting functions
"""

import datetime
from typing import Any, List, Optional
from .field_types import FieldInfo, StructInfo, EIP712ParseResult, FieldType, FieldSemantic


class DescriptionFormatter:
    """Description formatter"""
    
    def __init__(self):
        self.semantic_descriptions = self._init_semantic_descriptions()
        self.type_descriptions = self._init_type_descriptions()
        self.context_descriptions = self._init_context_descriptions()
    
    def _init_semantic_descriptions(self) -> dict:
        """Initialize semantic description mapping"""
        return {
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
            FieldSemantic.MINIMUM: "Minimum",
            FieldSemantic.MAXIMUM: "Maximum",
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
            FieldSemantic.HASH: "Hash",
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
        }
    
    def _init_type_descriptions(self) -> dict:
        """Initialize type description mapping"""
        return {
            FieldType.TOKEN_ADDRESS: "Token contract address",
            FieldType.USER_ADDRESS: "User address", 
            FieldType.CONTRACT_ADDRESS: "Contract address",
            FieldType.AMOUNT: "Amount value",
            FieldType.TIMESTAMP: "Timestamp",
            FieldType.NONCE: "Nonce",
            FieldType.HASH: "Hash value",
            FieldType.SIGNATURE: "Signature data",
        }
    
    def _init_context_descriptions(self) -> dict:
        """Initialize context description mapping"""
        return {
            "permit": "Allow third party to operate tokens on behalf of user",
            "order": "Define trade offer conditions and expectations",
            "vote": "Record voting decision on proposal",
            "transfer": "Define asset transfer details",
            "mint": "Define new token creation parameters",
            "burn": "Define token burning operation",
            "governance": "Define governance proposal and execution parameters",
            "auction": "Define auction bidding and conditions",
            "swap": "Define token swap parameters",
            "liquidity": "Define liquidity operation parameters",
        }
    
    def generate_field_description(self, field_name: str, field_type: FieldType, semantic: Optional[FieldSemantic], field_value: Any) -> str:
        """Generate field description"""
        base_desc = f"Field '{field_name}'"
        
        # Add semantic description
        if semantic:
            semantic_desc = self.semantic_descriptions.get(semantic, semantic.value)
            base_desc += f" ({semantic_desc})"
        
        # Add type description
        type_desc = self.type_descriptions.get(field_type)
        if type_desc:
            base_desc += f" - {type_desc}"
        
        # Add value description
        if field_value is not None:
            value_desc = self._format_field_value(field_type, field_value)
            if value_desc:
                base_desc += f" {value_desc}"
        
        return base_desc
    
    def _format_field_value(self, field_type: FieldType, field_value: Any) -> str:
        """Format field value"""
        if field_type == FieldType.TIMESTAMP and isinstance(field_value, (int, str)):
            try:
                timestamp = int(field_value)
                if timestamp > 1000000000:  # Looks like timestamp
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    return f"(Time: {dt.strftime('%Y-%m-%d %H:%M:%S')})"
            except:
                pass
        
        elif field_type in [FieldType.TOKEN_ADDRESS, FieldType.USER_ADDRESS, FieldType.CONTRACT_ADDRESS]:
            return f"({field_value})"
        
        elif field_type == FieldType.AMOUNT and isinstance(field_value, (int, str)):
            try:
                # Try to convert to ETH unit display
                amount = int(field_value)
                
                # Detect unlimited approval (common unlimited approval values)
                # uint256 max: 2^256 - 1
                # Also detect common "near infinite" values like 2^255, 2^128, etc.
                MAX_UINT256 = 2**256 - 1
                NEAR_MAX_THRESHOLD = MAX_UINT256 - 10**15  # Allow some floating
                
                # Common "unlimited approval" patterns
                COMMON_UNLIMITED_VALUES = [
                    MAX_UINT256,  # Full uint256 maximum value
                    2**255 - 1,   # Values used by some protocols
                    2**128 - 1,   # More conservative infinite value
                ]
                
                # Check if unlimited approval
                if amount >= NEAR_MAX_THRESHOLD:
                    return "⚠️ Unlimited approval (UNLIMITED)"
                elif amount in COMMON_UNLIMITED_VALUES:
                    return "⚠️ Unlimited approval (UNLIMITED)"
                elif amount > 10**50:  # Any value over 10^50 is considered "effectively infinite"
                    return "⚠️ Unlimited approval (UNLIMITED - Very large value)"
                elif amount > 10**15:  # If greater than 0.001 ETH
                    eth_amount = amount / 10**18
                    return f"({eth_amount:.6f} tokens)"
                else:
                    return f"({amount} units)"
            except:
                return f"({field_value})"
        
        elif isinstance(field_value, (str, int)) and len(str(field_value)) < 50:
            return f"= {field_value}"
        
        return ""
    
    def generate_struct_description(self, struct_name: str, fields: List[FieldInfo], struct_context: Optional[str] = None) -> str:
        """Generate struct description"""
        # Infer purpose from struct name and fields
        if struct_name == "EIP712Domain":
            return "EIP712 Domain Information - Define signature domain and verification context"
        
        # Use detected context
        if struct_context and struct_context in self.context_descriptions:
            context_desc = self.context_descriptions[struct_context]
            return f"{self._get_struct_type_name(struct_context)} structure '{struct_name}' - {context_desc}"
        
        # Infer struct purpose from fields (fallback)
        field_names = [field.name.lower() for field in fields]
        
        if any(name in field_names for name in ['offerer', 'offer', 'consideration']):
            return f"Market order structure '{struct_name}' - Contains trade offer and expected conditions"
        elif any(name in field_names for name in ['spender', 'value', 'deadline']):
            return f"Authorization permit structure '{struct_name}' - Contains token authorization information"
        elif any(name in field_names for name in ['to', 'value', 'data']):
            return f"Transaction structure '{struct_name}' - Contains transaction target and data"
        elif any(name in field_names for name in ['voter', 'proposal', 'support']):
            return f"Governance vote structure '{struct_name}' - Contains voting decision information"
        else:
            return f"Data structure '{struct_name}' - Contains {len(fields)} fields"
    
    def _get_struct_type_name(self, struct_context: str) -> str:
        """Get struct type name"""
        type_names = {
            "permit": "Authorization permit",
            "order": "Market order",
            "vote": "Governance vote",
            "transfer": "Transfer",
            "mint": "Mint",
            "burn": "Burn",
            "governance": "Governance",
            "auction": "Auction",
            "swap": "Swap",
            "liquidity": "Liquidity",
        }
        return type_names.get(struct_context, "Data")


class ResultFormatter:
    """Result formatter"""
    
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
        
        lines.append(f"\nMessage structure tree:")
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
    
    def format_structured_analysis(self, result: EIP712ParseResult) -> dict:
        """Format as structured analysis result"""
        return {
            "primary_type": result.primary_type,
            "message_description": result.message.description,
            "field_count": len(result.message.fields),
            "fields": [
                {
                    "name": field.name,
                    "type": field.type_name,
                    "semantic": field.semantic.value if field.semantic else None,
                    "value": field.value,
                    "description": field.description,
                    "context_hints": field.context_hints
                }
                for field in result.message.fields
            ],
            "domain": {
                "name": result.domain.name,
                "description": result.domain.description,
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "description": field.description
                    }
                    for field in result.domain.fields
                ]
            }
        } 