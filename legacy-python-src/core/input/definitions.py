from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum

class SignatureType(str, Enum):
    ETH_SEND_TRANSACTION = "eth_sendTransaction"
    PERSONAL_SIGN = "personal_sign"
    ETH_SIGN_TYPED_DATA_V4 = "eth_signTypedData_v4"
    ETH_SIGN = "eth_sign"
    UNKNOWN = "unknown"

@dataclass
class IntermediateRepresentation:
    """
    Unified Intermediate Representation for all signature types.
    Captures the core components of a signature request before semantic interpretation.
    """
    signature_type: SignatureType
    raw_data: Any
    
    # Context
    chain_id: Optional[int] = None
    dapp_url: Optional[str] = None  # If available from origin
    
    # Key Actors
    sender: Optional[str] = None        # User's address (signer)
    contract: Optional[str] = None      # Target contract address (to / verifyingContract)
    
    # Action Details
    action_type: Optional[str] = None   # e.g., "transfer", "approve", "sign_message"
    value: Optional[str] = "0"          # Native token value involved
    
    # Extracted Parameters (Normalized)
    # For EIP-712: The message content
    # For Transaction: The decoded function args
    # For Personal Sign: The message text
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Rich decoding / inference results
    decoded_call: Dict[str, Any] = field(default_factory=dict)
    assets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata (Original structure preservation if needed for UI)
    metadata: Dict[str, Any] = field(default_factory=dict)

