"""
统一签名解析器
支持自动识别和解析多种签名类型：EIP712、Personal Sign、Transaction
"""

import json
from typing import Dict, Any, Optional, Union
from enum import Enum


class SignatureType(str, Enum):
    """签名类型"""
    EIP712 = "eip712"
    PERSONAL_SIGN = "personal_sign"
    TRANSACTION = "transaction"
    UNKNOWN = "unknown"


class UnifiedSignatureParser:
    """统一签名解析器"""
    
    def __init__(self, enable_nlp: bool = False, openai_api_key: Optional[str] = None):
        """
        初始化统一解析器
        
        Args:
            enable_nlp: 是否启用NLP自然语言生成
            openai_api_key: OpenAI API密钥（用于AI分析）
        """
        self.enable_nlp = enable_nlp
        self.openai_api_key = openai_api_key
        
        # 延迟加载解析器，避免循环导入
        self._eip712_parser = None
        self._personal_sign_parser = None
        self._transaction_parser = None
    
    def _get_eip712_parser(self):
        """获取EIP712解析器实例"""
        if self._eip712_parser is None:
            from dynamic_parser.core import DynamicEIP712Parser
            self._eip712_parser = DynamicEIP712Parser(
                enable_nlp=self.enable_nlp
            )
        return self._eip712_parser
    
    def _get_personal_sign_parser(self):
        """获取Personal Sign解析器实例"""
        if self._personal_sign_parser is None:
            from personal_sign_parser.parser import PersonalSignParser
            self._personal_sign_parser = PersonalSignParser()
        return self._personal_sign_parser
    
    def _get_transaction_parser(self):
        """获取Transaction解析器实例"""
        if self._transaction_parser is None:
            from eth_transaction_parser.parser import EthTransactionParser
            self._transaction_parser = EthTransactionParser()
        return self._transaction_parser
    
    def detect_signature_type(self, data: Union[str, Dict[str, Any]]) -> SignatureType:
        """
        自动检测签名类型
        
        Args:
            data: 签名数据（字符串或字典）
            
        Returns:
            SignatureType: 检测到的签名类型
        """
        try:
            # 如果是字符串，尝试解析为JSON
            if isinstance(data, str):
                # 如果是纯文本（不是JSON），可能是Personal Sign
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError:
                    return SignatureType.PERSONAL_SIGN
            else:
                parsed_data = data
            
            # 检测EIP712签名
            if isinstance(parsed_data, dict):
                # EIP712 必须包含 types, domain, primaryType, message
                if all(key in parsed_data for key in ['types', 'domain', 'primaryType', 'message']):
                    return SignatureType.EIP712
                
                # 检测Transaction
                if any(key in parsed_data for key in ['to', 'from', 'value', 'data', 'gas', 'gasPrice']):
                    return SignatureType.TRANSACTION
            
            # 默认为Personal Sign（文本消息）
            return SignatureType.PERSONAL_SIGN
            
        except Exception:
            return SignatureType.UNKNOWN
    
    def parse(self, data: Union[str, Dict[str, Any]], signature_type: Optional[SignatureType] = None) -> Dict[str, Any]:
        """
        解析签名数据
        
        Args:
            data: 签名数据
            signature_type: 指定签名类型（如果为None则自动检测）
            
        Returns:
            Dict: 解析结果
        """
        # 自动检测类型
        if signature_type is None:
            signature_type = self.detect_signature_type(data)
        
        try:
            # 根据类型调用相应的解析器
            if signature_type == SignatureType.EIP712:
                return self._parse_eip712(data)
            elif signature_type == SignatureType.PERSONAL_SIGN:
                return self._parse_personal_sign(data)
            elif signature_type == SignatureType.TRANSACTION:
                return self._parse_transaction(data)
            else:
                return {
                    'success': False,
                    'error': f'不支持的签名类型: {signature_type}',
                    'signature_type': signature_type.value
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'signature_type': signature_type.value if signature_type else 'unknown'
            }
    
    def _parse_eip712(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """解析EIP712签名"""
        parser = self._get_eip712_parser()
        
        # 转换为字典格式
        if isinstance(data, str):
            data = json.loads(data)
        
        # 解析
        result = parser.parse(data)
        formatted_result = parser.format_result(result)
        
        # 生成AI分析（如果启用）
        ai_analysis = None
        if self.enable_nlp and self.openai_api_key:
            try:
                from dynamic_parser.openai_nlp_generator import generate_english_with_openai
                ai_analysis = generate_english_with_openai(data, self.openai_api_key)
            except Exception as e:
                ai_analysis = {'error': f'AI分析失败: {str(e)}'}
        
        return {
            'success': True,
            'signature_type': SignatureType.EIP712.value,
            'formatted_result': formatted_result,
            'raw_result': result,
            'ai_analysis': ai_analysis
        }
    
    def _parse_personal_sign(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """解析Personal Sign消息"""
        parser = self._get_personal_sign_parser()
        
        # 如果是字典格式，尝试提取message字段
        if isinstance(data, dict):
            message = data.get('message', json.dumps(data))
        else:
            message = data
        
        # 解析
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
        """解析以太坊交易"""
        parser = self._get_transaction_parser()
        
        # 转换为字典格式
        if isinstance(data, str):
            data = json.loads(data)
        
        # 解析
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

