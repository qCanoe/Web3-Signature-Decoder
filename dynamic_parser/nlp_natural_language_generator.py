"""
NLP Natural Language Generator
Uses template system to convert structured data into fluent English descriptions
"""

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NaturalLanguageOutput:
    """Natural language output result"""
    title: str  # Title description
    summary: str  # Brief summary
    detailed_description: str  # Detailed description
    field_descriptions: List[str]  # Field description list
    context: str  # Context explanation
    action_summary: str  # Action summary


class StructuredDataToNLConverter:
    """Structured data to natural language converter"""
    
    def __init__(self):
        """
        Initialize NLP generator
        """
        # Initialize templates and mappings
        self._init_templates()
        self._init_semantic_mappings()
    

    
    def _init_templates(self):
        """Initialize natural language templates"""
        self.action_templates = {
            "permit": "This is a token authorization operation, {owner} is authorizing {spender} to spend up to {value} tokens on their behalf, authorization valid until {deadline}.",
            "order": "This is a marketplace order, {offerer} is selling {offer_items}, expecting to receive {consideration_items} in exchange.",
            "vote": "This is a governance vote, {voter} voted {support} on proposal {proposal}.",
            "transfer": "This is a transfer operation, transferring {amount} from {from} to {to}.",
            "mint": "This is a minting operation, minting {amount} tokens for {recipient}.",
            "burn": "This is a burn operation, burning {amount} tokens.",
            "swap": "This is a token swap operation, exchanging {input_amount} {input_token} for {output_amount} {output_token}."
        }
        
        self.context_descriptions = {
            "permit": "Token authorization permit",
            "order": "Marketplace trading order", 
            "vote": "Governance voting decision",
            "transfer": "Asset transfer",
            "mint": "Token minting",
            "burn": "Token burning",
            "swap": "Token swap",
            "governance": "Governance operation",
            "auction": "Auction bidding",
            "liquidity": "Liquidity operation"
        }
    
    def _init_semantic_mappings(self):
        """Initialize semantic mappings"""
        self.field_semantic_map = {
            "owner": "Token holder",
            "spender": "Authorized spender", 
            "recipient": "Recipient",
            "offerer": "Offerer",
            "bidder": "Bidder",
            "voter": "Voter",
            "value": "Amount",
            "amount": "Amount",
            "price": "Price",
            "fee": "Fee",
            "deadline": "Deadline",
            "timestamp": "Timestamp",
            "startTime": "Start time",
            "endTime": "End time",
            "nonce": "Anti-replay nonce",
            "chainId": "Blockchain network ID",
            "verifyingContract": "Verifying contract address",
            "token": "Token contract address",
            "tokenId": "Token ID",
            "salt": "Salt value",
            "counter": "Counter"
        }
    
    def convert_to_natural_language(self, eip712_data: Dict[str, Any]) -> NaturalLanguageOutput:
        """
        Convert EIP712 structured data to natural language description
        
        Args:
            eip712_data: Structured data in EIP712 format
            
        Returns:
            NaturalLanguageOutput: Natural language output result
        """
        # Analyze data structure
        primary_type = eip712_data.get("primaryType", "")
        domain = eip712_data.get("domain", {})
        message = eip712_data.get("message", {})
        types = eip712_data.get("types", {})
        
        # Infer operation type
        operation_type = self._infer_operation_type(primary_type, message, types)
        
        # Generate descriptions for each part
        title = self._generate_title(operation_type, primary_type, domain)
        summary = self._generate_summary(operation_type, message, domain)
        detailed_description = self._generate_detailed_description(operation_type, message, types)
        field_descriptions = self._generate_field_descriptions(message, types.get(primary_type, []))
        context = self._generate_context_description(operation_type, domain)
        action_summary = self._generate_action_summary(operation_type, message)
        
        return NaturalLanguageOutput(
            title=title,
            summary=summary,
            detailed_description=detailed_description,
            field_descriptions=field_descriptions,
            context=context,
            action_summary=action_summary
        )
    
    def _infer_operation_type(self, primary_type: str, message: Dict, types: Dict) -> str:
        """Infer operation type"""
        primary_lower = primary_type.lower()
        
        # Infer based on primary type
        if "permit" in primary_lower:
            return "permit"
        elif "order" in primary_lower or "offer" in str(message):
            return "order"
        elif "vote" in primary_lower:
            return "vote"
        elif "transfer" in primary_lower:
            return "transfer"
        elif "mint" in primary_lower:
            return "mint"
        elif "burn" in primary_lower:
            return "burn"
        elif "swap" in primary_lower:
            return "swap"
        
        # Infer based on fields
        message_fields = set(message.keys())
        if {"owner", "spender", "value"}.issubset(message_fields):
            return "permit"
        elif {"offerer", "offer", "consideration"}.intersection(message_fields):
            return "order"
        elif {"voter", "proposal"}.intersection(message_fields):
            return "vote"
        
        return "general"
    
    def _generate_title(self, operation_type: str, primary_type: str, domain: Dict) -> str:
        """Generate title"""
        app_name = domain.get("name", "Unknown App")
        context_name = self.context_descriptions.get(operation_type, "Data Structure")
        return f"{app_name} - {context_name} ({primary_type})"
    
    def _generate_summary(self, operation_type: str, message: Dict, domain: Dict) -> str:
        """Generate summary"""
        app_name = domain.get("name", "App")
        
        if operation_type == "permit":
            owner = self._format_address(message.get("owner", ""))
            spender = self._format_address(message.get("spender", ""))
            value = self._format_amount(message.get("value", ""))
            return f"In {app_name}, address {owner} authorizes address {spender} to use up to {value} tokens on their behalf."
        
        elif operation_type == "order":
            offerer = self._format_address(message.get("offerer", ""))
            return f"In {app_name}, address {offerer} created a marketplace trading order."
        
        elif operation_type == "vote":
            voter = self._format_address(message.get("voter", ""))
            return f"In {app_name} governance system, address {voter} performed a voting operation."
        
        else:
            return f"{self.context_descriptions.get(operation_type, 'Data')} operation performed in {app_name}."
    
    def _generate_detailed_description(self, operation_type: str, message: Dict, types: Dict) -> str:
        """Generate detailed description"""
        return self._generate_template_description(operation_type, message)
    
    def _generate_template_description(self, operation_type: str, message: Dict) -> str:
        """Generate description based on template"""
        if operation_type == "permit":
            owner = self._format_address(message.get("owner"))
            spender = self._format_address(message.get("spender"))
            value = self._format_amount(message.get("value"))
            deadline = self._format_timestamp(message.get("deadline"))
            nonce = message.get("nonce", "Not specified")
            
            return f"""This is an ERC-20 token authorization permit operation. Details are as follows:

Authorizer: {owner}
Authorized: {spender}  
Authorization Amount: {value}
Authorization Deadline: {deadline}
Anti-replay Nonce: {nonce}

This authorization allows the authorized party to spend the specified amount of tokens on behalf of the authorizer before the deadline, commonly used in DeFi protocols for token swaps and liquidity operations."""

        elif operation_type == "order":
            offerer = self._format_address(message.get("offerer"))
            offer = message.get("offer", [])
            consideration = message.get("consideration", [])
            start_time = self._format_timestamp(message.get("startTime"))
            end_time = self._format_timestamp(message.get("endTime"))
            
            offer_desc = self._describe_items(offer, "selling")
            consideration_desc = self._describe_items(consideration, "expecting to receive")
            
            return f"""This is an NFT/Token marketplace trading order. Details are as follows:

Offerer: {offerer}
{offer_desc}
{consideration_desc}
Order Start Time: {start_time}
Order End Time: {end_time}

This order defines a trading intent in a decentralized marketplace, anyone can execute this order within the validity period to complete the transaction."""

        else:
            field_count = len(message)
            return f"This is a blockchain data structure containing {field_count} fields, used to execute specific operations or record important information in decentralized applications."
    

    
    def _generate_field_descriptions(self, message: Dict, type_fields: List[Dict]) -> List[str]:
        """Generate field description list"""
        descriptions = []
        
        for field_def in type_fields:
            field_name = field_def["name"]
            field_type = field_def["type"]
            field_value = message.get(field_name)
            
            if field_value is not None:
                semantic_name = self.field_semantic_map.get(field_name, field_name)
                formatted_value = self._format_field_value(field_name, field_value, field_type)
                descriptions.append(f"• {semantic_name}: {formatted_value}")
        
        return descriptions
    
    def _generate_context_description(self, operation_type: str, domain: Dict) -> str:
        """Generate context description"""
        app_name = domain.get("name", "Unknown App")
        version = domain.get("version", "")
        chain_id = domain.get("chainId", "")
        
        chain_name = self._get_chain_name(chain_id)
        version_text = f"v{version}" if version else ""
        
        return f"This operation occurs in {app_name}{version_text} application on the {chain_name} network."
    
    def _generate_action_summary(self, operation_type: str, message: Dict) -> str:
        """Generate action summary"""
        if operation_type == "permit":
            return f"Authorize token usage permission to third-party address"
        elif operation_type == "order":
            return f"Create decentralized marketplace trading order"
        elif operation_type == "vote":
            return f"Participate in decentralized governance voting"
        elif operation_type == "transfer":
            return f"Execute asset transfer operation"
        else:
            return f"Execute {self.context_descriptions.get(operation_type, 'blockchain')} operation"
    
    def _format_address(self, address: str) -> str:
        """Format address display"""
        if not address or len(address) < 10:
            return address
        return f"{address[:6]}...{address[-4:]}"
    
    def _format_amount(self, amount: Any) -> str:
        """Format amount display"""
        try:
            amount_int = int(amount)
            # Assume 18 decimal places for tokens
            if amount_int > 10**15:  # Greater than 0.001 tokens
                eth_amount = amount_int / 10**18
                return f"{eth_amount:.6f} tokens"
            else:
                return f"{amount_int} units"
        except:
            return str(amount)
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """Format timestamp"""
        try:
            ts = int(timestamp)
            if ts > 1000000000:  # Unix timestamp
                dt = datetime.datetime.fromtimestamp(ts)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
        return str(timestamp)
    
    def _format_field_value(self, field_name: str, value: Any, field_type: str) -> str:
        """Format field value"""
        if "address" in field_type.lower() or field_name.lower().endswith(("er", "to", "from")):
            return self._format_address(str(value))
        elif field_name.lower() in ["deadline", "timestamp", "starttime", "endtime"]:
            return self._format_timestamp(value)
        elif field_name.lower() in ["value", "amount", "price"] and isinstance(value, (int, str)):
            return self._format_amount(value)
        elif isinstance(value, list):
            return f"Array containing {len(value)} items"
        elif isinstance(value, dict):
            return f"Object containing {len(value)} fields"
        else:
            return str(value)
    
    def _describe_items(self, items: List[Dict], action: str) -> str:
        """Describe item list"""
        if not items:
            return f"{action}: None"
        
        descriptions = []
        for i, item in enumerate(items):
            item_type = item.get("itemType", 0)
            token = item.get("token", "")
            amount = item.get("startAmount", item.get("amount", "1"))
            
            if item_type == 0:  # ETH
                eth_amount = int(amount) / 10**18 if amount else 0
                descriptions.append(f"  {i+1}. {eth_amount:.6f} ETH")
            elif item_type == 1:  # ERC20
                token_addr = self._format_address(token)
                formatted_amount = self._format_amount(amount)
                descriptions.append(f"  {i+1}. {formatted_amount} (Token: {token_addr})")
            elif item_type == 2:  # ERC721
                token_id = item.get("identifierOrCriteria", "")
                token_addr = self._format_address(token)
                descriptions.append(f"  {i+1}. NFT #{token_id} (Contract: {token_addr})")
            else:
                descriptions.append(f"  {i+1}. Other type item")
        
        return f"{action}:\n" + "\n".join(descriptions)
    
    def _get_chain_name(self, chain_id: Any) -> str:
        """Get chain name"""
        chain_names = {
            1: "Ethereum Mainnet",
            5: "Goerli Testnet", 
            11155111: "Sepolia Testnet",
            137: "Polygon Mainnet",
            56: "BSC Mainnet"
        }
        try:
            return chain_names.get(int(chain_id), f"Chain ID {chain_id}")
        except:
            return "Unknown Network"


def create_nlp_generator() -> StructuredDataToNLConverter:
    """
    Create NLP natural language generator instance
    
    Returns:
        StructuredDataToNLConverter: Generator instance
    """
    return StructuredDataToNLConverter() 