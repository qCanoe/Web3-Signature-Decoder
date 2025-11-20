"""
PersonalSign Template Detector
Used to identify template types of personal_sign messages (login, binding, signature authorization, etc.)
"""

import re
from typing import Dict, List, Optional, Tuple
from .models import (
    PersonalSignTemplateType, 
    TemplateInfo, 
    TemplateKeywords,
    ExtractedParameters
)


class TemplateDetector:
    """Template detector"""
    
    def __init__(self):
        self.template_rules = self._build_template_rules()
    
    def detect(self, message: str, extracted_params: Optional[ExtractedParameters] = None) -> TemplateInfo:
        """
        Detect message template type
        
        Args:
            message: Message to detect
            extracted_params: Extracted parameters (optional)
            
        Returns:
            Template information
        """
        message_lower = message.lower()
        best_match = None
        best_score = 0.0
        best_patterns = []
        
        # Score each template
        for template_type, rules in self.template_rules.items():
            score, matched_patterns = self._calculate_template_score(message_lower, rules, extracted_params)
            
            if score > best_score:
                best_score = score
                best_match = template_type
                best_patterns = matched_patterns
        
        # If no template matched, set to UNKNOWN
        if best_match is None or best_score < 0.3:
            best_match = PersonalSignTemplateType.UNKNOWN
            best_score = 0.0
            best_patterns = []
        
        # Generate template description
        description = self._generate_template_description(best_match, best_score)
        
        # Determine security level
        security_level = self._determine_security_level(best_match, message_lower)
        
        return TemplateInfo(
            template_type=best_match,
            confidence=best_score,
            matched_patterns=best_patterns,
            description=description,
            required_fields=self._get_required_fields(best_match),
            optional_fields=self._get_optional_fields(best_match),
            security_level=security_level
        )
    
    def _build_template_rules(self) -> Dict[PersonalSignTemplateType, Dict]:
        """Build template recognition rules"""
        return {
            PersonalSignTemplateType.LOGIN: {
                'keywords': TemplateKeywords.LOGIN,
                'weight': 1.0,
                'patterns': [
                    r'sign\s*in',
                    r'log\s*in',
                    r'login',
                    r'登录',
                    r'身份验证',
                    r'authenticate',
                    r'welcome.*to',
                    r'欢迎.*登录'
                ],
                'required_indicators': ['session', 'auth', 'login', 'signin'],
                'boost_fields': ['session_id', 'user_id', 'domain'],
                'penalty_fields': ['transfer', 'approve', 'spend']
            },
            
            PersonalSignTemplateType.BINDING: {
                'keywords': TemplateKeywords.BINDING,
                'weight': 1.0,
                'patterns': [
                    r'bind',
                    r'绑定',
                    r'link.*account',
                    r'connect.*to',
                    r'verify.*account',
                    r'confirm.*email',
                    r'confirm.*phone',
                    r'关联.*账户'
                ],
                'required_indicators': ['bind', 'link', 'connect', 'verify'],
                'boost_fields': ['binding_target', 'binding_type', 'email', 'phone'],
                'penalty_fields': ['transfer', 'spend', 'withdraw']
            },
            
            PersonalSignTemplateType.AUTHORIZATION: {
                'keywords': TemplateKeywords.AUTHORIZATION,
                'weight': 1.2,  # Higher weight due to security sensitivity
                'patterns': [
                    r'authorize',
                    r'授权',
                    r'permission',
                    r'权限',
                    r'grant.*access',
                    r'approve.*to',
                    r'delegate',
                    r'委托',
                    r'允许.*访问'
                ],
                'required_indicators': ['auth', 'permission', 'grant', 'approve', 'delegate'],
                'boost_fields': ['permissions', 'resource', 'action'],
                'penalty_fields': []
            },
            
            PersonalSignTemplateType.VERIFICATION: {
                'keywords': TemplateKeywords.VERIFICATION,
                'weight': 0.9,
                'patterns': [
                    r'verify',
                    r'验证',
                    r'confirm',
                    r'确认',
                    r'validate',
                    r'check.*identity',
                    r'prove.*ownership',
                    r'challenge'
                ],
                'required_indicators': ['verify', 'confirm', 'validate', 'prove'],
                'boost_fields': ['challenge', 'verification_code'],
                'penalty_fields': ['transfer', 'spend']
            }
        }
    
    def _calculate_template_score(self, message: str, rules: Dict, params: Optional[ExtractedParameters]) -> Tuple[float, List[str]]:
        """Calculate template matching score"""
        score = 0.0
        matched_patterns = []
        
        # 1. Keyword matching
        keyword_matches = 0
        for keyword in rules['keywords']:
            if keyword.lower() in message:
                keyword_matches += 1
                matched_patterns.append(f"keyword:{keyword}")
        
        if keyword_matches > 0:
            keyword_score = min(keyword_matches / len(rules['keywords']), 1.0) * 0.4
            score += keyword_score
        
        # 2. Regular expression pattern matching
        pattern_matches = 0
        for pattern in rules['patterns']:
            if re.search(pattern, message, re.IGNORECASE):
                pattern_matches += 1
                matched_patterns.append(f"pattern:{pattern}")
        
        if pattern_matches > 0:
            pattern_score = min(pattern_matches / len(rules['patterns']), 1.0) * 0.4
            score += pattern_score
        
        # 3. Required indicator check
        required_found = 0
        for indicator in rules['required_indicators']:
            if indicator in message:
                required_found += 1
                matched_patterns.append(f"indicator:{indicator}")
        
        if required_found > 0:
            required_score = min(required_found / len(rules['required_indicators']), 1.0) * 0.2
            score += required_score
        
        # 4. Parameter field weighting
        if params:
            boost_score = self._calculate_field_boost(params, rules.get('boost_fields', []))
            penalty_score = self._calculate_field_penalty(params, rules.get('penalty_fields', []))
            
            score += boost_score
            score -= penalty_score
            
            if boost_score > 0:
                matched_patterns.append(f"field_boost:{boost_score:.2f}")
            if penalty_score > 0:
                matched_patterns.append(f"field_penalty:{penalty_score:.2f}")
        
        # Apply weight
        score *= rules.get('weight', 1.0)
        
        # Ensure score is in 0-1 range
        score = max(0.0, min(1.0, score))
        
        return score, matched_patterns
    
    def _calculate_field_boost(self, params: ExtractedParameters, boost_fields: List[str]) -> float:
        """Calculate field boost score"""
        boost = 0.0
        
        for field in boost_fields:
            value = getattr(params, field, None)
            if value:
                boost += 0.1
        
        return min(boost, 0.3)  # Maximum boost 0.3
    
    def _calculate_field_penalty(self, params: ExtractedParameters, penalty_fields: List[str]) -> float:
        """Calculate field penalty score"""
        penalty = 0.0
        
        # Check if custom fields contain penalty keywords
        message_text = " ".join(params.custom_fields.values()).lower()
        
        for field in penalty_fields:
            if field in message_text:
                penalty += 0.2
        
        return min(penalty, 0.5)  # Maximum penalty 0.5
    
    def _generate_template_description(self, template_type: PersonalSignTemplateType, confidence: float) -> str:
        """Generate template description"""
        descriptions = {
            PersonalSignTemplateType.LOGIN: "User login verification message",
            PersonalSignTemplateType.BINDING: "Account binding verification message",
            PersonalSignTemplateType.AUTHORIZATION: "Permission authorization confirmation message",
            PersonalSignTemplateType.VERIFICATION: "Identity verification confirmation message",
            PersonalSignTemplateType.CUSTOM_MESSAGE: "Custom message",
            PersonalSignTemplateType.UNKNOWN: "Unknown type message"
        }
        
        base_desc = descriptions.get(template_type, "Unknown message")
        confidence_desc = f" (Confidence: {confidence:.1%})"
        
        return f"{base_desc}{confidence_desc}"
    
    def _determine_security_level(self, template_type: PersonalSignTemplateType, message: str) -> str:
        """Determine security level"""
        # Check if contains high-risk keywords
        high_risk_keywords = ['transfer', 'send', 'withdraw', 'approve', 'spend', '转账', '发送', '提取', '批准']
        medium_risk_keywords = ['authorize', 'permission', 'grant', '授权', '权限', '允许']
        
        has_high_risk = any(keyword in message for keyword in high_risk_keywords)
        has_medium_risk = any(keyword in message for keyword in medium_risk_keywords)
        
        if has_high_risk:
            return "high"
        elif has_medium_risk or template_type == PersonalSignTemplateType.AUTHORIZATION:
            return "high"
        elif template_type in [PersonalSignTemplateType.LOGIN, PersonalSignTemplateType.BINDING]:
            return "medium"
        else:
            return "low"
    
    def _get_required_fields(self, template_type: PersonalSignTemplateType) -> List[str]:
        """Get template required fields"""
        required_fields_map = {
            PersonalSignTemplateType.LOGIN: ['domain', 'nonce'],
            PersonalSignTemplateType.BINDING: ['binding_target', 'binding_type'],
            PersonalSignTemplateType.AUTHORIZATION: ['permissions', 'resource'],
            PersonalSignTemplateType.VERIFICATION: ['challenge'],
            PersonalSignTemplateType.CUSTOM_MESSAGE: [],
            PersonalSignTemplateType.UNKNOWN: []
        }
        
        return required_fields_map.get(template_type, [])
    
    def _get_optional_fields(self, template_type: PersonalSignTemplateType) -> List[str]:
        """Get template optional fields"""
        optional_fields_map = {
            PersonalSignTemplateType.LOGIN: ['session_id', 'user_id', 'timestamp', 'expires_at'],
            PersonalSignTemplateType.BINDING: ['nonce', 'timestamp', 'expires_at'],
            PersonalSignTemplateType.AUTHORIZATION: ['nonce', 'timestamp', 'expires_at', 'action'],
            PersonalSignTemplateType.VERIFICATION: ['nonce', 'timestamp', 'verification_code'],
            PersonalSignTemplateType.CUSTOM_MESSAGE: ['domain', 'nonce', 'timestamp'],
            PersonalSignTemplateType.UNKNOWN: []
        }
        
        return optional_fields_map.get(template_type, [])
    
    def analyze_message_structure(self, message: str) -> Dict[str, any]:
        """Analyze message structure"""
        return {
            'is_structured': self._is_structured_message(message),
            'format_type': self._detect_format_type(message),
            'has_timestamps': bool(re.search(r'\b\d{10,13}\b', message)),
            'has_urls': bool(re.search(r'https?://', message)),
            'has_json': self._looks_like_json(message),
            'line_count': len(message.split('\n')),
            'has_key_value_pairs': bool(re.search(r'\w+\s*[:=]\s*\w+', message))
        }
    
    def _is_structured_message(self, message: str) -> bool:
        """Determine if message is structured"""
        indicators = [
            ':' in message and '\n' in message,  # Multi-line key-value pairs
            message.strip().startswith('{') and message.strip().endswith('}'),  # JSON
            '=' in message and '&' in message,  # Query string
            re.search(r'\w+\s*:\s*\w+', message)  # Key-value format
        ]
        
        return any(indicators)
    
    def _detect_format_type(self, message: str) -> str:
        """Detect message format type"""
        if self._looks_like_json(message):
            return 'json'
        elif '=' in message and '&' in message:
            return 'query_string'
        elif ':' in message and '\n' in message:
            return 'key_value'
        elif message.startswith('0x'):
            return 'hex'
        else:
            return 'plain_text'
    
    def _looks_like_json(self, message: str) -> bool:
        """Determine if message looks like JSON"""
        message = message.strip()
        return (message.startswith('{') and message.endswith('}')) or \
               (message.startswith('[') and message.endswith(']')) 