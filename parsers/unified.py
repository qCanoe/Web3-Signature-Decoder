"""
Unified Signature Parser
Supports automatic detection and parsing of multiple signature types: EIP712, Personal Sign, Transaction
"""

import json
from typing import Dict, Any, Optional, Union
from enum import Enum


class SignatureType(str, Enum):
    """Signature type"""
    EIP712 = "eip712"
    PERSONAL_SIGN = "personal_sign"
    TRANSACTION = "transaction"
    UNKNOWN = "unknown"


class UnifiedSignatureParser:
    """Unified signature parser"""
    
    def __init__(self, enable_nlp: bool = False, openai_api_key: Optional[str] = None):
        """
        Initialize unified parser
        
        Args:
            enable_nlp: Whether to enable NLP natural language generation
            openai_api_key: OpenAI API key (for AI analysis)
        """
        self.enable_nlp = enable_nlp
        self.openai_api_key = openai_api_key
        
        # Lazy load parsers to avoid circular imports
        self._eip712_parser = None
        self._personal_sign_parser = None
        self._transaction_parser = None
    
    def _get_eip712_parser(self):
        """Get EIP712 parser instance"""
        if self._eip712_parser is None:
            from dynamic_parser.core import DynamicEIP712Parser
            self._eip712_parser = DynamicEIP712Parser(
                enable_nlp=self.enable_nlp
            )
        return self._eip712_parser
    
    def _get_personal_sign_parser(self):
        """Get Personal Sign parser instance"""
        if self._personal_sign_parser is None:
            from personal_sign_parser.parser import PersonalSignParser
            self._personal_sign_parser = PersonalSignParser()
        return self._personal_sign_parser
    
    def _get_transaction_parser(self):
        """Get Transaction parser instance"""
        if self._transaction_parser is None:
            from eth_transaction_parser.parser import EthTransactionParser
            self._transaction_parser = EthTransactionParser()
        return self._transaction_parser
    
    def detect_signature_type(self, data: Union[str, Dict[str, Any]]) -> SignatureType:
        """
        Automatically detect signature type
        
        Args:
            data: Signature data (string or dictionary)
            
        Returns:
            SignatureType: Detected signature type
        """
        try:
            # If string, try to parse as JSON
            if isinstance(data, str):
                # If plain text (not JSON), might be Personal Sign
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError:
                    return SignatureType.PERSONAL_SIGN
            else:
                parsed_data = data
            
            # Detect EIP712 signature
            if isinstance(parsed_data, dict):
                # EIP712 must contain types, domain, primaryType, message
                if all(key in parsed_data for key in ['types', 'domain', 'primaryType', 'message']):
                    return SignatureType.EIP712
                
                # Detect Transaction
                if any(key in parsed_data for key in ['to', 'from', 'value', 'data', 'gas', 'gasPrice']):
                    return SignatureType.TRANSACTION
            
            # Default to Personal Sign (text message)
            return SignatureType.PERSONAL_SIGN
            
        except Exception:
            return SignatureType.UNKNOWN
    
    def parse(self, data: Union[str, Dict[str, Any]], signature_type: Optional[SignatureType] = None) -> Dict[str, Any]:
        """
        Parse signature data
        
        Args:
            data: Signature data
            signature_type: Specify signature type (auto-detect if None)
            
        Returns:
            Dict: Parsing result
        """
        # Auto-detect type
        if signature_type is None:
            signature_type = self.detect_signature_type(data)
        
        try:
            # Call appropriate parser based on type
            if signature_type == SignatureType.EIP712:
                return self._parse_eip712(data)
            elif signature_type == SignatureType.PERSONAL_SIGN:
                return self._parse_personal_sign(data)
            elif signature_type == SignatureType.TRANSACTION:
                return self._parse_transaction(data)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported signature type: {signature_type}',
                    'signature_type': signature_type.value
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'signature_type': signature_type.value if signature_type else 'unknown'
            }
    
    def _parse_eip712(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse EIP712 signature"""
        parser = self._get_eip712_parser()
        
        # Convert to dictionary format
        if isinstance(data, str):
            data = json.loads(data)
        
        # Parse
        result = parser.parse(data)
        formatted_result = parser.format_result(result)
        
        # Generate AI analysis (if enabled)
        ai_analysis = None
        if self.enable_nlp and self.openai_api_key:
            try:
                from dynamic_parser.openai_nlp_generator import generate_english_with_openai
                ai_analysis = generate_english_with_openai(data, self.openai_api_key)
            except Exception as e:
                ai_analysis = {'error': f'AI analysis failed: {str(e)}'}
        
        return {
            'success': True,
            'signature_type': SignatureType.EIP712.value,
            'formatted_result': formatted_result,
            'raw_result': result,
            'ai_analysis': ai_analysis
        }
    
    def _parse_personal_sign(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Personal Sign message"""
        parser = self._get_personal_sign_parser()
        
        # If dictionary format, try to extract message field
        if isinstance(data, dict):
            message = data.get('message', json.dumps(data))
        else:
            message = data
        
        # Parse
        result = parser.parse(message)
        
        return {
            'success': True,
            'signature_type': SignatureType.PERSONAL_SIGN.value,
            'result': {
                'template_type': result.template_info.template_type.value if result.template_info else 'unknown',
                'confidence': result.template_info.confidence if result.template_info else 0,
                'description': result.template_info.description if result.template_info else '',
                'security_level': result.template_info.security_level if result.template_info else 'unknown',
                'language': result.language,
                'risk_level': result.risk_level,
                'security_warnings': result.security_warnings,
                'parameters': {
                    'domain': result.extracted_parameters.domain,
                    'nonce': result.extracted_parameters.nonce,
                    'timestamp': result.extracted_parameters.timestamp,
                    'address': result.extracted_parameters.address,
                } if result.extracted_parameters else None
            },
            'raw_message': message
        }
    
    def _parse_transaction(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Ethereum transaction"""
        parser = self._get_transaction_parser()
        
        # Convert to dictionary format
        if isinstance(data, str):
            data = json.loads(data)
        
        # Parse
        result = parser.parse(data)
        
        return {
            'success': True,
            'signature_type': SignatureType.TRANSACTION.value,
            'result': {
                'transaction_type': result.transaction.transaction_type.value if result.transaction else 'unknown',
                'from': result.transaction.from_address if result.transaction else None,
                'to': result.transaction.to_address if result.transaction else None,
                'value': result.transaction.value if result.transaction else None,
                'gas': result.transaction.gas if result.transaction else None,
                'gas_price': result.transaction.gas_price if result.transaction else None,
                'risk_level': result.risk_level.value if result.risk_level else 'unknown',
                'risk_factors': result.risk_factors,
                'warnings': result.warnings,
            },
            'raw_transaction': data
        }

