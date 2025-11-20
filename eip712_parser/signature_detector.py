"""
Ethereum signature type detector
Used to automatically identify and classify different types of Ethereum signature methods
"""

from typing import Dict, Any, Optional, Union
from enum import Enum
import re
import json


class SignatureType(str, Enum):
    """Signature type enumeration"""
    ETH_SEND_TRANSACTION = "eth_sendTransaction"
    PERSONAL_SIGN = "personal_sign"
    ETH_SIGN_TYPED_DATA_V4 = "eth_signTypedData_v4"
    ETH_SIGN = "eth_sign"
    UNKNOWN = "unknown"


class SignatureDetector:
    """Signature type detector"""
    
    @staticmethod
    def detect_signature_type(data: Union[str, Dict[str, Any]]) -> SignatureType:
        """
        Detect signature type
        
        Args:
            data: Input data, can be string or dictionary
            
        Returns:
            Detected signature type
        """
        if isinstance(data, str):
            return SignatureDetector._detect_string_signature(data)
        elif isinstance(data, dict):
            return SignatureDetector._detect_dict_signature(data)
        else:
            return SignatureType.UNKNOWN
    
    @staticmethod
    def _detect_string_signature(data: str) -> SignatureType:
        """
        Detect string format signature
        
        Args:
            data: Input string
            
        Returns:
            Detected signature type
        """
        # Remove whitespace
        data = data.strip()
        
        # Check empty string
        if not data:
            return SignatureType.UNKNOWN
        
        # Try to parse as JSON
        try:
            parsed_data = json.loads(data)
            if isinstance(parsed_data, dict):
                return SignatureDetector._detect_dict_signature(parsed_data)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Check if it's hexadecimal data
        if data.startswith("0x"):
            hex_data = data[2:]
            # Check if hexadecimal format is valid
            if all(c in "0123456789abcdefABCDEF" for c in hex_data):
                # Might be raw signature data or transaction hash
                if len(data) == 66:  # 32 bytes hash
                    return SignatureType.ETH_SIGN
                elif len(data) == 130:  # 65 bytes signature
                    return SignatureType.ETH_SIGN
                elif len(hex_data) > 40:  # Long hexadecimal data, might be signature
                    return SignatureType.ETH_SIGN
                elif len(hex_data) == 40:  # Address length, but single address treated as personal message
                    return SignatureType.PERSONAL_SIGN
        
        # Check if it's plain text message
        if SignatureDetector._is_plain_text(data):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    @staticmethod
    def _detect_dict_signature(data: Dict[str, Any]) -> SignatureType:
        """
        Detect dictionary format signature
        
        Args:
            data: Input dictionary
            
        Returns:
            Detected signature type
        """
        # Check if it's EIP-712 structured data
        if SignatureDetector._is_eip712_data(data):
            return SignatureType.ETH_SIGN_TYPED_DATA_V4
        
        # Check if it's transaction data
        if SignatureDetector._is_transaction_data(data):
            return SignatureType.ETH_SEND_TRANSACTION
        
        # Check if contains personal_sign related fields
        if "message" in data and isinstance(data["message"], str):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    @staticmethod
    def _is_eip712_data(data: Dict[str, Any]) -> bool:
        """
        Check if it's EIP-712 data format
        
        Args:
            data: Input data
            
        Returns:
            Whether it's EIP-712 format
        """
        required_fields = ["types", "domain", "primaryType", "message"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate types field structure
        types = data["types"]
        if not isinstance(types, dict):
            return False
        
        # Check if contains EIP712Domain
        if "EIP712Domain" not in types:
            return False
        
        # Validate domain field
        domain = data["domain"]
        if not isinstance(domain, dict):
            return False
        
        # Validate primaryType
        primary_type = data["primaryType"]
        if not isinstance(primary_type, str) or primary_type not in types:
            return False
        
        # Validate message field
        if not isinstance(data["message"], dict):
            return False
        
        return True
    
    @staticmethod
    def _is_transaction_data(data: Dict[str, Any]) -> bool:
        """
        Check if it's transaction data
        
        Args:
            data: Input data
            
        Returns:
            Whether it's transaction data
        """
        # Common transaction data fields
        transaction_fields = ["to", "from", "value", "data", "gas", "gasPrice", "nonce"]
        
        # At least contains some transaction fields
        found_fields = sum(1 for field in transaction_fields if field in data)
        
        # If contains multiple transaction fields, consider it transaction data
        if found_fields >= 2:
            return True
        
        # Check specific field combinations
        if "to" in data and ("value" in data or "data" in data):
            return True
        
        return False
    
    @staticmethod
    def _is_plain_text(text: str) -> bool:
        """
        Check if text is plain text
        
        Args:
            text: Input text
            
        Returns:
            Whether it is plain text
        """
        # Check if contains printable characters
        try:
            # Try to encode as UTF-8
            text.encode('utf-8')
            
            # Check if contains control characters (except common whitespace)
            control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r ')
            
            # If too many control characters, might not be plain text
            if control_chars > len(text) * 0.1:
                return False
            
            return True
        except UnicodeEncodeError:
            return False
    
    @staticmethod
    def get_signature_info(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed signature information
        
        Args:
            data: Input data
            
        Returns:
            Signature information dictionary
        """
        signature_type = SignatureDetector.detect_signature_type(data)
        
        info = {
            "type": signature_type,
            "description": SignatureDetector._get_type_description(signature_type),
            "data_format": type(data).__name__,
            "analysis": {}
        }
        
        # Add type-specific analysis
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            info["analysis"] = SignatureDetector._analyze_eip712_data(data)
        elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
            info["analysis"] = SignatureDetector._analyze_transaction_data(data)
        elif signature_type == SignatureType.PERSONAL_SIGN:
            info["analysis"] = SignatureDetector._analyze_personal_sign_data(data)
        elif signature_type == SignatureType.ETH_SIGN:
            info["analysis"] = SignatureDetector._analyze_eth_sign_data(data)
        
        return info
    
    @staticmethod
    def _get_type_description(signature_type: SignatureType) -> str:
        """Get signature type description"""
        descriptions = {
            SignatureType.ETH_SEND_TRANSACTION: "Ethereum transaction signature",
            SignatureType.PERSONAL_SIGN: "Personal message signature",
            SignatureType.ETH_SIGN_TYPED_DATA_V4: "EIP-712 structured data signature",
            SignatureType.ETH_SIGN: "Raw data signature",
            SignatureType.UNKNOWN: "Unknown signature type"
        }
        return descriptions.get(signature_type, "Unknown type")
    
    @staticmethod
    def _analyze_eip712_data(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze EIP-712 data"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return {"error": "Unable to parse JSON data"}
        
        if not isinstance(data, dict):
            return {"error": "Invalid data format"}
        
        analysis = {
            "domain_name": data.get("domain", {}).get("name", "Unknown"),
            "domain_version": data.get("domain", {}).get("version", "Unknown"),
            "chain_id": data.get("domain", {}).get("chainId", "Unknown"),
            "verifying_contract": data.get("domain", {}).get("verifyingContract", "Unknown"),
            "primary_type": data.get("primaryType", "Unknown"),
            "types_count": len(data.get("types", {})),
            "message_fields": list(data.get("message", {}).keys()) if isinstance(data.get("message"), dict) else []
        }
        
        return analysis
    
    @staticmethod
    def _analyze_transaction_data(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction data"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return {"error": "Unable to parse JSON data"}
        
        if not isinstance(data, dict):
            return {"error": "Invalid data format"}
        
        analysis = {
            "to": data.get("to", "Unknown"),
            "from": data.get("from", "Unknown"),
            "value": data.get("value", "0"),
            "has_data": bool(data.get("data")),
            "data_size": len(data.get("data", "")) if data.get("data") else 0,
            "gas": data.get("gas", "Unknown"),
            "gas_price": data.get("gasPrice", "Unknown"),
            "nonce": data.get("nonce", "Unknown")
        }
        
        return analysis
    
    @staticmethod
    def _analyze_personal_sign_data(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze personal signature data"""
        if isinstance(data, dict):
            message = data.get("message", "")
        else:
            message = str(data)
        
        analysis = {
            "message_length": len(message),
            "message_preview": message[:100] + "..." if len(message) > 100 else message,
            "contains_unicode": any(ord(c) > 127 for c in message),
            "is_hex": message.startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in message[2:])
        }
        
        return analysis
    
    @staticmethod
    def _analyze_eth_sign_data(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze raw signature data"""
        if isinstance(data, dict):
            # If it's a dictionary, look for possible signature fields
            signature_data = data.get("signature", data.get("data", str(data)))
        else:
            signature_data = str(data)
        
        analysis = {
            "data_length": len(signature_data),
            "is_hex": signature_data.startswith("0x"),
            "hex_length": len(signature_data[2:]) if signature_data.startswith("0x") else 0,
            "possible_type": "hash" if len(signature_data) == 66 else "signature" if len(signature_data) == 130 else "unknown"
        }
        
        return analysis 