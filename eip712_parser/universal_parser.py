"""
Universal signature parser
Integrates signature detector and various types of parsing functionality
"""

from typing import Union, Dict, Any, Optional
from .signature_detector import SignatureDetector, SignatureType
from .parser import parse_request as parse_eip712_request
from .types import ParsedMessage, TransactionLike
import json


class UniversalParser:
    """Universal signature parser"""
    
    def __init__(self):
        self.detector = SignatureDetector()
    
    def parse(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Universal parsing method
        
        Args:
            data: Input data, can be string or dictionary
            
        Returns:
            Parsing result dictionary
        """
        # 1. Detect signature type
        signature_info = self.detector.get_signature_info(data)
        signature_type = signature_info["type"]
        
        result = {
            "signature_info": signature_info,
            "parsed_data": None,
            "success": False,
            "error": None
        }
        
        try:
            # 2. Parse based on type
            if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
                result["parsed_data"] = self._parse_eip712(data)
                result["success"] = result["parsed_data"] is not None
                
            elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
                result["parsed_data"] = self._parse_transaction(data)
                result["success"] = result["parsed_data"] is not None
                
            elif signature_type == SignatureType.PERSONAL_SIGN:
                result["parsed_data"] = self._parse_personal_sign(data)
                result["success"] = True
                
            elif signature_type == SignatureType.ETH_SIGN:
                result["parsed_data"] = self._parse_eth_sign(data)
                result["success"] = True
                
            else:
                result["error"] = f"Unsupported signature type: {signature_type}"
                
        except Exception as e:
            result["error"] = f"Error occurred during parsing: {str(e)}"
            result["success"] = False
        
        return result
    
    def _parse_eip712(self, data: Union[str, Dict[str, Any]]) -> Optional[ParsedMessage]:
        """Parse EIP-712 data"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return None
        
        return parse_eip712_request(data)
    
    def _parse_transaction(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse transaction data"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return {"error": "Unable to parse JSON data"}
        
        # Create TransactionLike object
        transaction = TransactionLike(
            from_address=data.get("from", ""),
            to=data.get("to"),
            data=data.get("data"),
            value=data.get("value")
        )
        
        # Analyze transaction type
        analysis = {
            "transaction": {
                "from": transaction.from_address,
                "to": transaction.to,
                "value": transaction.value,
                "has_data": bool(transaction.data),
                "data_length": len(transaction.data) if transaction.data else 0
            },
            "type_analysis": self._analyze_transaction_type(transaction),
            "security_warnings": self._check_transaction_security(transaction)
        }
        
        return analysis
    
    def _parse_personal_sign(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse personal sign data"""
        if isinstance(data, dict):
            message = data.get("message", str(data))
        else:
            message = str(data)
        
        analysis = {
            "message": message,
            "message_info": {
                "length": len(message),
                "is_hex": message.startswith("0x"),
                "contains_urls": self._contains_urls(message),
                "contains_addresses": self._contains_eth_addresses(message),
                "language": self._detect_language(message)
            },
            "security_warnings": self._check_personal_sign_security(message)
        }
        
        return analysis
    
    def _parse_eth_sign(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse raw signature data"""
        if isinstance(data, dict):
            raw_data = data.get("data", data.get("signature", str(data)))
        else:
            raw_data = str(data)
        
        analysis = {
            "raw_data": raw_data,
            "data_info": {
                "length": len(raw_data),
                "is_hex": raw_data.startswith("0x"),
                "hex_length": len(raw_data[2:]) if raw_data.startswith("0x") else 0,
                "possible_type": self._identify_raw_data_type(raw_data)
            },
            "security_warnings": ["Raw data signature has security risks, please confirm data content"]
        }
        
        return analysis
    
    def _analyze_transaction_type(self, transaction: TransactionLike) -> Dict[str, Any]:
        """Analyze transaction type"""
        analysis = {
            "is_contract_interaction": bool(transaction.data and len(transaction.data) > 2),
            "is_value_transfer": bool(transaction.value and transaction.value != "0"),
            "is_contract_creation": transaction.to is None or transaction.to == "",
        }
        
        # Analyze contract call
        if analysis["is_contract_interaction"] and transaction.data:
            function_selector = transaction.data[:10] if len(transaction.data) >= 10 else ""
            analysis["function_selector"] = function_selector
            analysis["estimated_function"] = self._guess_function_name(function_selector)
        
        return analysis
    
    def _check_transaction_security(self, transaction: TransactionLike) -> list:
        """Check transaction security"""
        warnings = []
        
        # Check high-value transfer
        if transaction.value and transaction.value != "0":
            try:
                value_wei = int(transaction.value, 16) if isinstance(transaction.value, str) and transaction.value.startswith("0x") else int(transaction.value)
                value_eth = value_wei / (10**18)
                if value_eth > 1.0:
                    warnings.append(f"High-value transfer: {value_eth:.4f} ETH")
            except (ValueError, TypeError):
                pass
        
        # Check suspicious contract address
        if transaction.to and len(transaction.to) == 42:
            if self._is_suspicious_address(transaction.to):
                warnings.append("Target address may have risks")
        
        # Check data length
        if transaction.data and len(transaction.data) > 10000:
            warnings.append("Transaction data too long, may have risks")
        
        return warnings
    
    def _check_personal_sign_security(self, message: str) -> list:
        """Check personal signature security"""
        warnings = []
        
        # Check sensitive keywords
        sensitive_keywords = [
            "transfer", "approve", "authorize", "permit", "sign", 
            "wallet", "private", "seed", "password", "mnemonic"
        ]
        
        message_lower = message.lower()
        for keyword in sensitive_keywords:
            if keyword in message_lower:
                warnings.append(f"Message contains sensitive keyword: {keyword}")
        
        # Check URLs
        if self._contains_urls(message):
            warnings.append("Message contains URL links, please verify security")
        
        # Check hexadecimal data
        if message.startswith("0x") and len(message) > 42:
            warnings.append("Message contains hexadecimal data, may be encoded transaction")
        
        return warnings
    
    def _contains_urls(self, text: str) -> bool:
        """Check if text contains URLs"""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return bool(re.search(url_pattern, text))
    
    def _contains_eth_addresses(self, text: str) -> bool:
        """Check if text contains Ethereum addresses"""
        import re
        address_pattern = r'0x[a-fA-F0-9]{40}'
        return bool(re.search(address_pattern, text))
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # Check if contains Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "chinese"
        # Check if contains Japanese characters
        elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "japanese"
        # Check if contains Korean characters
        elif any('\uac00' <= char <= '\ud7af' for char in text):
            return "korean"
        else:
            return "english"
    
    def _identify_raw_data_type(self, data: str) -> str:
        """Identify raw data type"""
        if not data.startswith("0x"):
            return "text"
        
        hex_data = data[2:]
        
        if len(hex_data) == 64:
            return "hash"
        elif len(hex_data) == 128:
            return "signature"
        elif len(hex_data) == 40:
            return "address"
        else:
            return "unknown_hex"
    
    def _guess_function_name(self, selector: str) -> str:
        """Guess function name based on function selector"""
        # Common function selectors
        known_selectors = {
            "0xa9059cbb": "transfer(address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x70a08231": "balanceOf(address)",
            "0x18160ddd": "totalSupply()",
            "0xd505accf": "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)",
            "0x42842e0e": "safeTransferFrom(address,address,uint256)",
            "0xa22cb465": "setApprovalForAll(address,bool)",
        }
        
        return known_selectors.get(selector, f"unknown_function({selector})")
    
    def _is_suspicious_address(self, address: str) -> bool:
        """Check if address is suspicious"""
        # Can add known malicious address list here
        # Or check certain characteristics of the address
        
        # Check if it's zero address
        if address.lower() == "0x0000000000000000000000000000000000000000":
            return True
        
        # Check for repeating patterns (may be fake address)
        hex_part = address[2:].lower()
        for i in range(len(hex_part) - 3):
            if hex_part[i:i+4] * 10 in hex_part:
                return True
        
        return False 