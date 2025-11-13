"""
PersonalSign 主解析器
整合参数提取和模板识别功能
"""

import re
from typing import Union, Dict, Any, Optional, List

from .models import PersonalSignMessage, PersonalSignTemplateType, ExtractedParameters, TemplateInfo
from .parameter_extractor import ParameterExtractor
from .template_detector import TemplateDetector


class PersonalSignParser:
    """PersonalSign 解析器"""
    
    def __init__(self):
        self.parameter_extractor = ParameterExtractor()
        self.template_detector = TemplateDetector()
    
    def parse(self, message: Union[str, Dict[str, Any]]) -> PersonalSignMessage:
        """
        解析 PersonalSign 消息
        
        Args:
            message: 要解析的消息，可以是字符串或字典
            
        Returns:
            解析后的 PersonalSign 消息对象
        """
        # 统一处理消息格式
        raw_message = self._normalize_message(message)
        
        # 提取参数
        extracted_params = self.parameter_extractor.extract(raw_message)
        
        # 检测模板类型
        template_info = self.template_detector.detect(raw_message, extracted_params)
        
        # 分析消息属性
        message_props = self._analyze_message_properties(raw_message)
        
        # 安全分析
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
        """标准化消息格式"""
        if isinstance(message, dict):
            # 如果是字典，尝试提取消息内容
            if 'message' in message:
                return str(message['message'])
            elif 'data' in message:
                return str(message['data'])
            else:
                # 将字典转换为 JSON 字符串
                import json
                return json.dumps(message, ensure_ascii=False)
        
        return str(message)
    
    def _analyze_message_properties(self, message: str) -> Dict[str, Any]:
        """分析消息属性"""
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
        """检测文本语言"""
        # 检查是否包含中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "chinese"
        # 检查是否包含日文字符
        elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "japanese"
        # 检查是否包含韩文字符
        elif any('\uac00' <= char <= '\ud7af' for char in text):
            return "korean"
        else:
            return "english"
    
    def _perform_security_analysis(self, message: str, template_info: TemplateInfo, params: ExtractedParameters) -> Dict[str, Any]:
        """执行安全分析"""
        warnings = []
        risk_level = "low"
        
        # 基于模板类型的风险评估
        if template_info.security_level == "high":
            risk_level = "high"
            warnings.append("此消息涉及高风险操作，请仔细验证")
        elif template_info.security_level == "medium":
            risk_level = "medium"
            warnings.append("此消息需要额外注意安全性")
        
        # 检查敏感关键词
        security_info = self.parameter_extractor.extract_security_info(message)
        if security_info['contains_sensitive_keywords']:
            risk_level = "high"
            keywords = ', '.join(security_info['sensitive_keywords'][:3])  # 最多显示3个
            warnings.append(f"消息包含敏感关键词: {keywords}")
        
        # 检查消息长度
        if len(message) > 5000:
            warnings.append("消息长度过长，可能存在风险")
        
        # 检查 URL
        if security_info['contains_urls']:
            warnings.append("消息包含URL链接，请验证链接安全性")
        
        # 检查未知模板类型
        if template_info.template_type == PersonalSignTemplateType.UNKNOWN:
            warnings.append("无法识别消息模板类型，请谨慎处理")
            if risk_level == "low":
                risk_level = "medium"
        
        # 检查置信度
        if template_info.confidence < 0.5:
            warnings.append(f"模板识别置信度较低 ({template_info.confidence:.1%})")
        
        # 检查必需字段缺失
        missing_fields = self._check_missing_required_fields(template_info, params)
        if missing_fields:
            warnings.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        return {
            'warnings': warnings,
            'risk_level': risk_level
        }
    
    def _check_missing_required_fields(self, template_info: TemplateInfo, params: ExtractedParameters) -> List[str]:
        """检查缺失的必需字段"""
        missing_fields = []
        
        for field in template_info.required_fields:
            if not getattr(params, field, None):
                missing_fields.append(field)
        
        return missing_fields
    
    def get_template_examples(self, template_type: PersonalSignTemplateType) -> Dict[str, Any]:
        """获取模板示例"""
        examples = {
            PersonalSignTemplateType.LOGIN: {
                'description': '登录验证消息示例',
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
                'description': '绑定验证消息示例',
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
                'description': '授权确认消息示例',
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
                'description': '身份验证消息示例',
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
            'description': '未知模板类型',
            'examples': []
        })
    
    def validate_message(self, parsed_message: PersonalSignMessage) -> Dict[str, Any]:
        """验证解析后的消息"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        template_info = parsed_message.template_info
        params = parsed_message.extracted_parameters
        
        # 检查必需字段
        missing_fields = self._check_missing_required_fields(template_info, params)
        if missing_fields:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 检查模板置信度
        if template_info.confidence < 0.5:
            validation_result['warnings'].append("模板识别置信度较低")
            validation_result['suggestions'].append("建议人工验证消息类型")
        
        # 检查安全风险
        if parsed_message.risk_level == "high":
            validation_result['warnings'].append("检测到高安全风险")
            validation_result['suggestions'].append("建议仔细审查消息内容")
        
        return validation_result 