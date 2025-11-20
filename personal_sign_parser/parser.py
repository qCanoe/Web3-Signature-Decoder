"""
PersonalSign Main Parser
Integrates parameter extraction and template recognition functionality
"""

import re
from typing import Union, Dict, Any, Optional, List

from .models import PersonalSignMessage, PersonalSignTemplateType, ExtractedParameters, TemplateInfo
from .parameter_extractor import ParameterExtractor
from .template_detector import TemplateDetector


class PersonalSignParser:
    """PersonalSign parser"""
    
    def __init__(self):
        self.parameter_extractor = ParameterExtractor()
        self.template_detector = TemplateDetector()
    
    def parse(self, message: Union[str, Dict[str, Any]]) -> PersonalSignMessage:
        """
        Parse PersonalSign message
        
        Args:
            message: Message to parse, can be string or dictionary
            
        Returns:
            Parsed PersonalSign message object
        """
        # Normalize message format
        raw_message = self._normalize_message(message)
        
        # Extract parameters
        extracted_params = self.parameter_extractor.extract(raw_message)
        
        # Detect template type
        template_info = self.template_detector.detect(raw_message, extracted_params)
        
        # Analyze message properties
        message_props = self._analyze_message_properties(raw_message)
        
        # Security analysis
        security_analysis = self._perform_security_analysis(raw_message, template_info, extracted_params)
        
        return PersonalSignMessage(
            raw_message=raw_message,
            template_info=template_info,
            extracted_parameters=extracted_params,
            message_length=message_props['length'],
            is_hex=message_props['is_hex'],
            language=message_props['language'],
            security_warnings=security_analysis['warnings'],
            risk_level=security_analysis['risk_level'],
            contains_urls=message_props['contains_urls'],
            contains_addresses=message_props['contains_addresses'],
            contains_emails=message_props['contains_emails'],
            contains_phone_numbers=message_props['contains_phone_numbers']
        )
    
    def _normalize_message(self, message: Union[str, Dict[str, Any]]) -> str:
        """Normalize message format"""
        if isinstance(message, dict):
            # If it's a dictionary, try to extract message content
            if 'message' in message:
                return str(message['message'])
            elif 'data' in message:
                return str(message['data'])
            else:
                # Convert dictionary to JSON string
                import json
                return json.dumps(message, ensure_ascii=False)
        
        return str(message)
    
    def _analyze_message_properties(self, message: str) -> Dict[str, Any]:
        """Analyze message properties"""
        from .models import RegexPatterns
        patterns = RegexPatterns()
        
        return {
            'length': len(message),
            'is_hex': message.startswith('0x'),
            'language': self._detect_language(message),
            'contains_urls': bool(patterns.URL.search(message)),
            'contains_addresses': bool(patterns.ETH_ADDRESS.search(message)),
            'contains_emails': bool(patterns.EMAIL.search(message)),
            'contains_phone_numbers': bool(patterns.PHONE.search(message))
        }
    
    def _detect_language(self, text: str) -> str:
        """Detect text language"""
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
    
    def _perform_security_analysis(self, message: str, template_info: TemplateInfo, params: ExtractedParameters) -> Dict[str, Any]:
        """Perform security analysis"""
        warnings = []
        risk_level = "low"
        
        # Risk assessment based on template type
        if template_info.security_level == "high":
            risk_level = "high"
            warnings.append("This message involves high-risk operations, please verify carefully")
        elif template_info.security_level == "medium":
            risk_level = "medium"
            warnings.append("This message requires extra attention to security")
        
        # Check for sensitive keywords
        security_info = self.parameter_extractor.extract_security_info(message)
        if security_info['contains_sensitive_keywords']:
            risk_level = "high"
            keywords = ', '.join(security_info['sensitive_keywords'][:3])  # Show at most 3
            warnings.append(f"Message contains sensitive keywords: {keywords}")
        
        # Check message length
        if len(message) > 5000:
            warnings.append("Message is too long, may pose risks")
        
        # Check URLs
        if security_info['contains_urls']:
            warnings.append("Message contains URL links, please verify link security")
        
        # Check unknown template type
        if template_info.template_type == PersonalSignTemplateType.UNKNOWN:
            warnings.append("Unable to identify message template type, please handle with caution")
            if risk_level == "low":
                risk_level = "medium"
        
        # Check confidence
        if template_info.confidence < 0.5:
            warnings.append(f"Template recognition confidence is low ({template_info.confidence:.1%})")
        
        # Check for missing required fields
        missing_fields = self._check_missing_required_fields(template_info, params)
        if missing_fields:
            warnings.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        return {
            'warnings': warnings,
            'risk_level': risk_level
        }
    
    def _check_missing_required_fields(self, template_info: TemplateInfo, params: ExtractedParameters) -> List[str]:
        """Check for missing required fields"""
        missing_fields = []
        
        for field in template_info.required_fields:
            if not getattr(params, field, None):
                missing_fields.append(field)
        
        return missing_fields
    
    def get_template_examples(self, template_type: PersonalSignTemplateType) -> Dict[str, Any]:
        """Get template examples"""
        examples = {
            PersonalSignTemplateType.LOGIN: {
                'description': 'Login verification message example',
                'examples': [
                    {
                        'message': 'Sign in to example.com\nNonce: abc123\nTimestamp: 1640995200',
                        'expected_params': ['domain', 'nonce', 'timestamp']
                    },
                    {
                        'message': '{"domain":"app.example.com","nonce":"xyz789","action":"login"}',
                        'expected_params': ['domain', 'nonce']
                    }
                ]
            },
            PersonalSignTemplateType.BINDING: {
                'description': 'Binding verification message example',
                'examples': [
                    {
                        'message': 'Bind email: user@example.com\nCode: 123456',
                        'expected_params': ['binding_target', 'verification_code']
                    },
                    {
                        'message': '绑定手机号码: +1234567890\n验证码: 456789',
                        'expected_params': ['binding_target', 'verification_code']
                    }
                ]
            },
            PersonalSignTemplateType.AUTHORIZATION: {
                'description': 'Authorization confirmation message example',
                'examples': [
                    {
                        'message': 'Authorize access to: user profile\nPermissions: read, write',
                        'expected_params': ['resource', 'permissions']
                    },
                    {
                        'message': '授权访问资源: 用户数据\n权限: 读取',
                        'expected_params': ['resource', 'permissions']
                    }
                ]
            },
            PersonalSignTemplateType.VERIFICATION: {
                'description': 'Identity verification message example',
                'examples': [
                    {
                        'message': 'Verify ownership of this wallet\nChallenge: random_challenge_123',
                        'expected_params': ['challenge']
                    },
                    {
                        'message': '验证钱包所有权\n挑战码: challenge_xyz_789',
                        'expected_params': ['challenge']
                    }
                ]
            }
        }
        
        return examples.get(template_type, {
            'description': 'Unknown template type',
            'examples': []
        })
    
    def validate_message(self, parsed_message: PersonalSignMessage) -> Dict[str, Any]:
        """Validate parsed message"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        template_info = parsed_message.template_info
        params = parsed_message.extracted_parameters
        
        # Check required fields
        missing_fields = self._check_missing_required_fields(template_info, params)
        if missing_fields:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check template confidence
        if template_info.confidence < 0.5:
            validation_result['warnings'].append("Template recognition confidence is low")
            validation_result['suggestions'].append("Suggest manual verification of message type")
        
        # Check security risk
        if parsed_message.risk_level == "high":
            validation_result['warnings'].append("High security risk detected")
            validation_result['suggestions'].append("Suggest careful review of message content")
        
        return validation_result 