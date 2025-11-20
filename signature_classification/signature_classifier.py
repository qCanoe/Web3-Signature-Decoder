"""
Signature Classifier - Core signature recognition engine
"""

import json
import re
from typing import Dict, Any, Union, Optional, List, Tuple
from dataclasses import dataclass

from .signature_types import SignatureType, SignatureCategory, SecurityLevel, get_signature_metadata


@dataclass
class ClassificationResult:
    """Classification result"""
    signature_type: SignatureType
    category: SignatureCategory
    security_level: SecurityLevel
    confidence: float  # Confidence 0-1
    metadata: Dict[str, Any]
    warnings: List[str]
    detected_patterns: List[str]


class SignatureClassifier:
    """Signature classifier - identifies and classifies Ethereum signature types"""
    
    def __init__(self):
        """Initialize classifier"""
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize detection patterns"""
        
        # EIP-712 detection patterns
        self.eip712_required_fields = {"types", "domain", "primaryType", "message"}
        self.eip712_domain_fields = {"name", "version", "chainId", "verifyingContract"}
        
        # Transaction data detection patterns
        self.transaction_fields = {
            "required": {"to"},
            "optional": {"from", "value", "data", "gas", "gasPrice", "gasLimit", "nonce", "maxFeePerGas", "maxPriorityFeePerGas"}
        }
        
        # Hexadecimal patterns
        self.hex_patterns = {
            "address": re.compile(r'^0x[a-fA-F0-9]{40}$'),
            "hash": re.compile(r'^0x[a-fA-F0-9]{64}$'),
            "signature": re.compile(r'^0x[a-fA-F0-9]{130}$'),
            "hex_data": re.compile(r'^0x[a-fA-F0-9]+$')
        }
        
        # Risk keyword detection
        self.risk_keywords = {
            "high": ["transfer", "approve", "withdraw", "claim", "execute"],
            "medium": ["sign", "auth", "verify", "permit", "delegate"],
            "phishing": ["urgent", "limited time", "expires", "act now", "verify immediately"]
        }
    
    def classify(self, data: Union[str, Dict[str, Any]]) -> ClassificationResult:
        """
        Classify signature data
        
        Args:
            data: Input signature data
            
        Returns:
            Classification result
        """
        # Data preprocessing
        processed_data, data_format = self._preprocess_data(data)
        
        # Perform classification
        signature_type = self._detect_signature_type(processed_data, data_format)
        
        # Get metadata
        metadata = get_signature_metadata(signature_type)
        
        # Calculate confidence
        confidence = self._calculate_confidence(processed_data, signature_type, data_format)
        
        # Detect warnings and patterns
        warnings = self._detect_warnings(processed_data, signature_type)
        patterns = self._detect_patterns(processed_data, signature_type)
        
        # Build result
        return ClassificationResult(
            signature_type=signature_type,
            category=metadata.category,
            security_level=metadata.security_level,
            confidence=confidence,
            metadata={
                "data_format": data_format,
                "description": metadata.description,
                "common_use_cases": metadata.common_use_cases,
                "risk_factors": metadata.risk_factors,
                "wallet_support": metadata.wallet_support,
                "raw_data_type": type(data).__name__
            },
            warnings=warnings,
            detected_patterns=patterns
        )
    
    def _preprocess_data(self, data: Union[str, Dict[str, Any]]) -> Tuple[Union[str, Dict[str, Any]], str]:
        """Preprocess input data"""
        
        if isinstance(data, dict):
            return data, "dict"
        
        if isinstance(data, str):
            # Remove whitespace
            data = data.strip()
            
            # Try to parse JSON
            if data.startswith('{'):
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        return parsed, "json_string"
                except (json.JSONDecodeError, ValueError):
                    pass
            
            return data, "string"
        
        return str(data), "other"
    
    def _detect_signature_type(self, data: Union[str, Dict[str, Any]], data_format: str) -> SignatureType:
        """Detect signature type"""
        
        if data_format in ["dict", "json_string"]:
            return self._classify_dict_data(data)
        else:
            return self._classify_string_data(data)
    
    def _classify_dict_data(self, data: Dict[str, Any]) -> SignatureType:
        """Classify dictionary format data"""
        
        # Check EIP-712 structure
        if self._is_eip712_structure(data):
            return SignatureType.ETH_SIGN_TYPED_DATA_V4
        
        # Check transaction structure
        if self._is_transaction_structure(data):
            return SignatureType.ETH_SEND_TRANSACTION
        
        # Check personal message structure
        if self._is_personal_message_structure(data):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _classify_string_data(self, data: str) -> SignatureType:
        """Classify string format data"""
        
        if not data:
            return SignatureType.UNKNOWN
        
        # Check hexadecimal data
        if data.startswith("0x"):
            return self._classify_hex_data(data)
        
        # Check plain text message
        if self._is_readable_text(data):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _is_eip712_structure(self, data: Dict[str, Any]) -> bool:
        """Check if it's an EIP-712 structure"""
        
        # Check required fields
        if not self.eip712_required_fields.issubset(data.keys()):
            return False
        
        # Validate types field
        types = data.get("types")
        if not isinstance(types, dict) or "EIP712Domain" not in types:
            return False
        
        # Validate domain field
        domain = data.get("domain")
        if not isinstance(domain, dict):
            return False
        
        # Validate primary type
        primary_type = data.get("primaryType")
        if not isinstance(primary_type, str) or primary_type not in types:
            return False
        
        # Validate message
        message = data.get("message")
        if not isinstance(message, dict):
            return False
        
        return True
    
    def _is_transaction_structure(self, data: Dict[str, Any]) -> bool:
        """Check if it's a transaction structure"""
        
        # Must include 'to' field, which is a basic requirement for transactions
        if "to" not in data:
            return False
        
        # Check number of transaction-related fields
        transaction_field_count = 0
        all_transaction_fields = self.transaction_fields["required"] | self.transaction_fields["optional"]
        
        for field in all_transaction_fields:
            if field in data:
                transaction_field_count += 1
        
        # If contains enough transaction fields, consider it a transaction
        return transaction_field_count >= 2
    
    def _is_personal_message_structure(self, data: Dict[str, Any]) -> bool:
        """Check if it's a personal message structure"""
        
        # Check message field
        if "message" in data and isinstance(data["message"], str):
            return True
        
        # Check other possible message fields
        message_fields = ["text", "content", "msg", "data"]
        for field in message_fields:
            if field in data and isinstance(data[field], str):
                return True
        
        return False
    
    def _classify_hex_data(self, data: str) -> SignatureType:
        """Classify hexadecimal data"""
        
        # Check address format
        if self.hex_patterns["address"].match(data):
            return SignatureType.PERSONAL_SIGN
        
        # Check hash format
        if self.hex_patterns["hash"].match(data):
            return SignatureType.ETH_SIGN
        
        # Check signature format
        if self.hex_patterns["signature"].match(data):
            return SignatureType.ETH_SIGN
        
        # Other hexadecimal data
        if self.hex_patterns["hex_data"].match(data):
            hex_length = len(data) - 2  # Subtract '0x'
            if hex_length > 128:  # Long data might be raw signature
                return SignatureType.ETH_SIGN
            else:
                return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _is_readable_text(self, text: str) -> bool:
        """Check if it's readable text"""
        
        try:
            # Check UTF-8 encoding
            text.encode('utf-8')
            
            # Check if contains too many control characters
            control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r')
            control_ratio = control_chars / len(text) if text else 0
            
            # If control character ratio is too high, consider it not readable text
            return control_ratio < 0.1
            
        except UnicodeEncodeError:
            return False
    
    def _calculate_confidence(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType, data_format: str) -> float:
        """Calculate classification confidence"""
        
        confidence = 0.5  # Base confidence
        
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            if isinstance(data, dict) and self._is_eip712_structure(data):
                confidence = 0.95
        
        elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
            if isinstance(data, dict) and self._is_transaction_structure(data):
                field_count = len(set(data.keys()) & (self.transaction_fields["required"] | self.transaction_fields["optional"]))
                confidence = min(0.9, 0.6 + field_count * 0.1)
        
        elif signature_type == SignatureType.PERSONAL_SIGN:
            if isinstance(data, str):
                if self._is_readable_text(data):
                    confidence = 0.8
                elif data.startswith("0x") and self.hex_patterns["address"].match(data):
                    confidence = 0.7
        
        elif signature_type == SignatureType.ETH_SIGN:
            if isinstance(data, str) and data.startswith("0x"):
                if self.hex_patterns["signature"].match(data) or self.hex_patterns["hash"].match(data):
                    confidence = 0.9
        
        return confidence
    
    def _detect_warnings(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> List[str]:
        """Detect warning messages"""
        
        warnings = []
        
        # High-risk signature type warnings
        if signature_type == SignatureType.ETH_SIGN:
            warnings.append("⚠️ eth_sign method has extremely high security risks and has been disabled by most wallets")
        
        # Check risk keywords in data
        data_text = str(data).lower()
        
        for keyword in self.risk_keywords["phishing"]:
            if keyword in data_text:
                warnings.append(f"⚠️ Detected phishing-related keyword: '{keyword}'")
        
        # EIP-712 specific warnings
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4 and isinstance(data, dict):
            # Check expiration time
            message = data.get("message", {})
            if isinstance(message, dict):
                # Check common time fields
                time_fields = ["endTime", "deadline", "expiry", "validUntil"]
                for field in time_fields:
                    if field in message:
                        warnings.append(f"⚠️ Signature contains time limit, please note {field} field")
        
        return warnings
    
    def _detect_patterns(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> List[str]:
        """Detect data patterns"""
        
        patterns = []
        
        if isinstance(data, dict):
            patterns.append(f"Structured data, contains {len(data)} fields")
            
            if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
                primary_type = data.get("primaryType")
                if primary_type:
                    patterns.append(f"EIP-712 primary type: {primary_type}")
                
                domain = data.get("domain", {})
                if isinstance(domain, dict) and "name" in domain:
                    patterns.append(f"Protocol name: {domain['name']}")
        
        elif isinstance(data, str):
            if data.startswith("0x"):
                hex_length = len(data) - 2
                patterns.append(f"Hexadecimal data, length: {hex_length} characters")
            else:
                patterns.append(f"Text message, length: {len(data)} characters")
        
        return patterns
    
    def get_supported_types(self) -> List[SignatureType]:
        """Get list of supported signature types"""
        return [
            SignatureType.ETH_SEND_TRANSACTION,
            SignatureType.PERSONAL_SIGN,
            SignatureType.ETH_SIGN_TYPED_DATA_V4,
            SignatureType.ETH_SIGN
        ]
    
    def batch_classify(self, data_list: List[Union[str, Dict[str, Any]]]) -> List[ClassificationResult]:
        """Batch classify signature data"""
        return [self.classify(data) for data in data_list] 