from typing import Dict, Any, Optional, List
import re
import json
import os
from pathlib import Path
from functools import lru_cache
from ..config import Config

# Get the directory where this file is located
_DATA_DIR = Path(__file__).parent / "data"

def _load_json(filename: str) -> Dict[str, Any]:
    """Load JSON data from data directory."""
    filepath = _DATA_DIR / filename
    if not filepath.exists():
        # Fallback to empty dict if file doesn't exist
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


class KnowledgeBase:
    """
    Static knowledge base for contract ABIs, function signatures, and known protocols.
    Data is loaded from JSON files in the data/ directory for better maintainability.
    """
    
    # Load data from JSON files
    FUNCTION_SIGNATURES: Dict[str, Dict[str, Any]] = _load_json("function_signatures.json")
    EIP712_TYPES: Dict[str, str] = _load_json("eip712_types.json")
    TOKEN_METADATA: Dict[str, Dict[str, Any]] = _load_json("token_metadata.json")
    PERSONAL_SIGN_PATTERNS: Dict[str, Dict[str, Any]] = _load_json("personal_sign_patterns.json")
    ACTOR_FIELD_PATTERNS: Dict[str, List[str]] = _load_json("actor_field_patterns.json")
    PROTOCOL_NAME_PATTERNS: Dict[str, List[str]] = _load_json("protocol_name_patterns.json")
    
    # Load known contracts (chain_id as string -> address -> name)
    _KNOWN_CONTRACTS_RAW: Dict[str, Dict[str, str]] = _load_json("known_contracts.json")
    # Convert string keys to integers for backward compatibility
    KNOWN_CONTRACTS: Dict[int, Dict[str, str]] = {
        int(chain_id): contracts 
        for chain_id, contracts in _KNOWN_CONTRACTS_RAW.items()
    }
    
    # Load chain names (chain_id as string -> name)
    _CHAIN_NAMES_RAW: Dict[str, str] = _load_json("chain_names.json")
    # Convert string keys to integers for backward compatibility
    _CHAIN_NAMES: Dict[int, str] = {
        int(chain_id): name 
        for chain_id, name in _CHAIN_NAMES_RAW.items()
    }

    @staticmethod
    @lru_cache(maxsize=1000 if Config.PERFORMANCE["enable_caching"] else None)
    def get_function_name(selector: str) -> Optional[str]:
        definition = KnowledgeBase.get_function_definition(selector)
        return definition.get("name") if definition else None

    @staticmethod
    @lru_cache(maxsize=1000 if Config.PERFORMANCE["enable_caching"] else None)
    def get_function_definition(selector: Optional[str]) -> Optional[Dict[str, Any]]:
        if not selector:
            return None
        return KnowledgeBase.FUNCTION_SIGNATURES.get(selector.lower())

    @staticmethod
    @lru_cache(maxsize=500 if Config.PERFORMANCE["enable_caching"] else None)
    def get_eip712_category(primary_type: str) -> str:
        return KnowledgeBase.EIP712_TYPES.get(primary_type, "unknown")

    @staticmethod
    @lru_cache(maxsize=2000 if Config.PERFORMANCE["enable_caching"] else None)
    def get_contract_name(chain_id: int, address: str) -> Optional[str]:
        if not chain_id or not address:
            return None
        return KnowledgeBase.KNOWN_CONTRACTS.get(chain_id, {}).get(address.lower())

    @staticmethod
    @lru_cache(maxsize=2000 if Config.PERFORMANCE["enable_caching"] else None)
    def get_token_metadata(address: Optional[str]) -> Dict[str, Any]:
        if not address:
            return {}
        return KnowledgeBase.TOKEN_METADATA.get(address.lower(), {})

    @staticmethod
    def is_infinite_allowance(value: Any) -> bool:
        """Check if a value represents infinite allowance."""
        if isinstance(value, int):
            return value > (1 << 255) # Roughly check for uint256 max
        if isinstance(value, str):
            # Check for max uint256 hex or decimal
            if value.startswith("0x"):
                return len(value) >= 66 and value.lower().replace("0x", "").startswith("f" * 10)
            elif value.isdigit():
                return len(value) > 75 # 2^256 is 78 digits
        return False
    
    @staticmethod
    def identify_actor_role(field_name: str, value: Any = None) -> Optional[str]:
        """
        Identify the role of an actor based on field name and context.
        
        Args:
            field_name: Name of the field
            value: Optional value to check against known contracts
            
        Returns:
            Actor role string or None
        """
        field_lower = field_name.lower()
        
        # Check field name patterns
        for role, patterns in KnowledgeBase.ACTOR_FIELD_PATTERNS.items():
            if any(pattern in field_lower for pattern in patterns):
                return role
        
        return None
    
    @staticmethod
    @lru_cache(maxsize=500 if Config.PERFORMANCE["enable_caching"] else None)
    def identify_protocol_type(domain_name: str, contract_address: Optional[str] = None, chain_id: Optional[int] = None) -> Optional[str]:
        """
        Identify the protocol type based on domain name and contract address.
        
        Args:
            domain_name: Domain name from EIP712 domain
            contract_address: Contract address (optional)
            chain_id: Chain ID (optional)
            
        Returns:
            Protocol type string or None
        """
        if not domain_name:
            return None
        
        domain_lower = domain_name.lower()
        
        # Check protocol name patterns
        for protocol_type, patterns in KnowledgeBase.PROTOCOL_NAME_PATTERNS.items():
            if any(pattern in domain_lower for pattern in patterns):
                return protocol_type
        
        # Check contract address if provided
        if contract_address and chain_id:
            contract_name = KnowledgeBase.get_contract_name(chain_id, contract_address)
            if contract_name:
                contract_lower = contract_name.lower()
                for protocol_type, patterns in KnowledgeBase.PROTOCOL_NAME_PATTERNS.items():
                    if any(pattern in contract_lower for pattern in patterns):
                        return protocol_type
        
        return None
    
    @staticmethod
    @lru_cache(maxsize=100 if CACHE_ENABLED else None)
    def get_chain_name(chain_id: int) -> str:
        """Get human-readable chain name from chain ID."""
        return KnowledgeBase._CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")
    
    @staticmethod
    def get_actor_type(actor_value: Any, ir: Optional[Any] = None) -> str:
        """
        Identify the type of actor (User, Protocol, Contract, etc.)
        
        Args:
            actor_value: The actor's address or identifier
            ir: Optional IntermediateRepresentation for context
            
        Returns:
            Actor type string
        """
        if isinstance(actor_value, str) and actor_value.startswith("0x"):
            # Check if it's a known contract
            if ir and ir.chain_id and ir.contract:
                contract_name = KnowledgeBase.get_contract_name(ir.chain_id, actor_value)
                if contract_name:
                    return "Protocol"
            return "User"
        return "Unknown"
    
    @staticmethod
    def get_actor_name(actor_value: Any, ir: Optional[Any] = None) -> str:
        """
        Get a human-readable name for an actor.
        
        Args:
            actor_value: The actor's address or identifier
            ir: Optional IntermediateRepresentation for context
            
        Returns:
            Actor name string
        """
        if isinstance(actor_value, str) and actor_value.startswith("0x"):
            # Check if it's a known contract
            if ir and ir.chain_id:
                contract_name = KnowledgeBase.get_contract_name(ir.chain_id, actor_value)
                if contract_name:
                    return contract_name
            # Return shortened address
            return f"{actor_value[:6]}...{actor_value[-4:]}"
        return str(actor_value)
