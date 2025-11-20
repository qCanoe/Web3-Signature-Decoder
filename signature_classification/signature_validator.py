"""
Signature Validator - Validates signature data format and validity
"""

import re
from typing import Dict, Any, Union, List, Optional
from dataclasses import dataclass

from .signature_types import SignatureType


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class SignatureValidator:
    """Signature validator"""
    
    def __init__(self):
        """Initialize validator"""
        self._init_validation_rules()
    
    def _init_validation_rules(self):
        """Initialize validation rules"""
        
        # Address validation regex
        self.address_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        
        # Hash validation regex
        self.hash_pattern = re.compile(r'^0x[a-fA-F0-9]{64}$')
        
        # Hexadecimal data validation
        self.hex_pattern = re.compile(r'^0x[a-fA-F0-9]*$')
        
        # EIP-712 required fields
        self.eip712_required_fields = {"types", "domain", "primaryType", "message"}
        
        # Transaction required fields
        self.transaction_required_fields = {"to"}
        self.transaction_optional_fields = {"from", "value", "data", "gas", "gasPrice", "nonce"}
    
    def validate(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> ValidationResult:
        """
        Validate signature data
        
        Args:
            data: Signature data
            signature_type: Signature type
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Basic data validation
        base_errors = self._validate_base_data(data)
        errors.extend(base_errors)
        
        # Type-specific validation based on signature type
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            type_errors, type_warnings, type_metadata = self._validate_eip712(data)
        elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
            type_errors, type_warnings, type_metadata = self._validate_transaction(data)
        elif signature_type == SignatureType.PERSONAL_SIGN:
            type_errors, type_warnings, type_metadata = self._validate_personal_sign(data)
        elif signature_type == SignatureType.ETH_SIGN:
            type_errors, type_warnings, type_metadata = self._validate_eth_sign(data)
        else:
            type_errors, type_warnings, type_metadata = [], [], {}
        
        errors.extend(type_errors)
        warnings.extend(type_warnings)
        metadata.update(type_metadata)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _validate_base_data(self, data: Union[str, Dict[str, Any]]) -> List[str]:
        """Basic data validation"""
        errors = []
        
        if data is None:
            errors.append("Data cannot be empty")
            return errors
        
        if isinstance(data, str):
            if not data.strip():
                errors.append("String data cannot be empty")
        elif isinstance(data, dict):
            if not data:
                errors.append("Dictionary data cannot be empty")
        
        return errors
    
    def _validate_eip712(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """Validate EIP-712 data"""
        errors = []
        warnings = []
        metadata = {}
        
        if not isinstance(data, dict):
            errors.append("EIP-712 data must be in dictionary format")
            return errors, warnings, metadata
        
        # Check required fields
        missing_fields = self.eip712_required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate types field
        if "types" in data:
            types_errors = self._validate_eip712_types(data["types"])
            errors.extend(types_errors)
        
        # Validate domain field
        if "domain" in data:
            domain_errors, domain_metadata = self._validate_eip712_domain(data["domain"])
            errors.extend(domain_errors)
            metadata.update(domain_metadata)
        
        # Validate primaryType field
        if "primaryType" in data and "types" in data:
            primary_type = data["primaryType"]
            if not isinstance(primary_type, str):
                errors.append("primaryType must be a string")
            elif primary_type not in data["types"]:
                errors.append(f"primaryType '{primary_type}' is not in types definition")
        
        # Validate message field
        if "message" in data:
            if not isinstance(data["message"], dict):
                errors.append("message field must be a dictionary")
        
        return errors, warnings, metadata
    
    def _validate_eip712_types(self, types: Any) -> List[str]:
        """Validate EIP-712 types field"""
        errors = []
        
        if not isinstance(types, dict):
            errors.append("types field must be a dictionary")
            return errors
        
        # Check EIP712Domain type
        if "EIP712Domain" not in types:
            errors.append("types must include EIP712Domain definition")
        
        # Validate type definition format
        for type_name, type_def in types.items():
            if not isinstance(type_def, list):
                errors.append(f"Type definition '{type_name}' must be an array")
                continue
            
            for field in type_def:
                if not isinstance(field, dict):
                    errors.append(f"Field definition in type '{type_name}' must be a dictionary")
                    continue
                
                if "name" not in field or "type" not in field:
                    errors.append(f"Fields in type '{type_name}' must include name and type")
        
        return errors
    
    def _validate_eip712_domain(self, domain: Any) -> tuple[List[str], Dict[str, Any]]:
        """Validate EIP-712 domain field"""
        errors = []
        metadata = {}
        
        if not isinstance(domain, dict):
            errors.append("domain field must be a dictionary")
            return errors, metadata
        
        # Validate common domain fields
        if "name" in domain:
            metadata["protocol_name"] = domain["name"]
        
        if "version" in domain:
            metadata["protocol_version"] = domain["version"]
        
        if "chainId" in domain:
            chain_id = domain["chainId"]
            if isinstance(chain_id, str) and chain_id.isdigit():
                metadata["chain_id"] = int(chain_id)
            elif isinstance(chain_id, int):
                metadata["chain_id"] = chain_id
        
        if "verifyingContract" in domain:
            contract = domain["verifyingContract"]
            if isinstance(contract, str):
                if not self.address_pattern.match(contract):
                    errors.append("verifyingContract must be a valid Ethereum address")
                else:
                    metadata["contract_address"] = contract
        
        return errors, metadata
    
    def _validate_transaction(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """Validate transaction data"""
        errors = []
        warnings = []
        metadata = {}
        
        if not isinstance(data, dict):
            errors.append("Transaction data must be in dictionary format")
            return errors, warnings, metadata
        
        # Check required fields
        if "to" not in data:
            errors.append("Transaction must include 'to' field")
        else:
            to_address = data["to"]
            if to_address is not None and not self.address_pattern.match(str(to_address)):
                errors.append("'to' field must be a valid Ethereum address or null")
        
        # Validate optional fields
        if "from" in data:
            from_address = data["from"]
            if not self.address_pattern.match(str(from_address)):
                errors.append("'from' field must be a valid Ethereum address")
        
        if "value" in data:
            value = data["value"]
            if isinstance(value, str):
                if not (value.startswith("0x") and self.hex_pattern.match(value)):
                    if not value.isdigit():
                        errors.append("'value' field must be a hexadecimal string or number")
        
        if "data" in data:
            tx_data = data["data"]
            if isinstance(tx_data, str) and tx_data != "0x":
                if not self.hex_pattern.match(tx_data):
                    errors.append("'data' field must be valid hexadecimal data")
        
        # Validate gas-related fields
        gas_fields = ["gas", "gasLimit", "gasPrice", "maxFeePerGas", "maxPriorityFeePerGas"]
        for field in gas_fields:
            if field in data:
                gas_value = data[field]
                if isinstance(gas_value, str):
                    if not (gas_value.startswith("0x") and self.hex_pattern.match(gas_value)):
                        if not gas_value.isdigit():
                            errors.append(f"'{field}' field must be a hexadecimal string or number")
        
        return errors, warnings, metadata
    
    def _validate_personal_sign(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """Validate personal sign data"""
        errors = []
        warnings = []
        metadata = {}
        
        if isinstance(data, str):
            # Validate string message
            if len(data) > 10000:  # 10KB limit
                warnings.append("Message length is too long, may affect user experience")
            
            # Check if contains hexadecimal data
            if data.startswith("0x"):
                if not self.hex_pattern.match(data):
                    errors.append("Invalid hexadecimal data format")
                else:
                    metadata["data_type"] = "hex"
                    metadata["hex_length"] = len(data) - 2
            else:
                metadata["data_type"] = "text"
                metadata["text_length"] = len(data)
        
        elif isinstance(data, dict):
            # Validate dictionary format personal message
            if "message" not in data:
                warnings.append("Dictionary format personal messages should usually include 'message' field")
        
        return errors, warnings, metadata
    
    def _validate_eth_sign(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """Validate eth_sign data"""
        errors = []
        warnings = ["eth_sign method has security risks, recommend avoiding use"]
        metadata = {}
        
        if isinstance(data, str):
            if not data.startswith("0x"):
                errors.append("eth_sign data must be in hexadecimal format")
            elif not self.hex_pattern.match(data):
                errors.append("Invalid hexadecimal data format")
            else:
                hex_length = len(data) - 2
                metadata["hex_length"] = hex_length
                
                # Determine data type based on length
                if hex_length == 64:  # 32 bytes hash
                    metadata["data_type"] = "hash"
                elif hex_length == 130:  # 65 bytes signature
                    metadata["data_type"] = "signature"
                else:
                    metadata["data_type"] = "raw_data"
        
        return errors, warnings, metadata
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not isinstance(address, str):
            return False
        return bool(self.address_pattern.match(address))
    
    def validate_hash(self, hash_value: str) -> bool:
        """Validate hash format"""
        if not isinstance(hash_value, str):
            return False
        return bool(self.hash_pattern.match(hash_value))
    
    def validate_hex_data(self, hex_data: str) -> bool:
        """Validate hexadecimal data format"""
        if not isinstance(hex_data, str):
            return False
        return bool(self.hex_pattern.match(hex_data)) 