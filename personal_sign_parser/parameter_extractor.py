"""
PersonalSign 参数提取器
用于从 personal_sign 消息中提取结构化参数
"""

import re
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import parse_qs, urlparse

from .models import ExtractedParameters, RegexPatterns


class ParameterExtractor:
    """参数提取器"""
    
    def __init__(self):
        self.patterns = RegexPatterns()
        
    def extract(self, message: str) -> ExtractedParameters:
        """
        从消息中提取参数
        
        Args:
            message: 要解析的消息
            
        Returns:
            提取的参数对象
        """
        params = ExtractedParameters()
        
        # 清理消息（去除多余空白）
        cleaned_message = self._clean_message(message)
        
        # 尝试解析为 JSON
        json_data = self._try_parse_json(cleaned_message)
        if json_data:
            self._extract_from_json(json_data, params)
        
        # 尝试解析为 URL 查询参数
        query_params = self._try_parse_query_string(cleaned_message)
        if query_params:
            self._extract_from_query_params(query_params, params)
        
        # 使用正则表达式提取
        self._extract_with_regex(cleaned_message, params)
        
        # 提取结构化文本参数
        self._extract_structured_text(cleaned_message, params)
        
        return params
    
    def _clean_message(self, message: str) -> str:
        """清理消息"""
        # 如果是 hex 编码的消息，尝试解码
        if message.startswith('0x'):
            try:
                hex_bytes = bytes.fromhex(message[2:])
                decoded = hex_bytes.decode('utf-8', errors='ignore')
                if decoded.strip():
                    message = decoded
            except (ValueError, UnicodeDecodeError):
                pass
        
        return message.strip()
    
    def _try_parse_json(self, message: str) -> Optional[Dict[str, Any]]:
        """尝试解析为 JSON"""
        try:
            return json.loads(message)
        except (json.JSONDecodeError, ValueError):
            # 尝试查找 JSON 片段
            json_pattern = re.compile(r'\{[^{}]*\}')
            matches = json_pattern.findall(message)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
            return None
    
    def _try_parse_query_string(self, message: str) -> Optional[Dict[str, List[str]]]:
        """尝试解析为 URL 查询字符串"""
        try:
            # 如果包含 URL
            if 'http' in message:
                parsed_url = urlparse(message)
                if parsed_url.query:
                    return parse_qs(parsed_url.query)
            
            # 如果直接是查询字符串格式
            if '=' in message and '&' in message:
                return parse_qs(message)
            
            return None
        except:
            return None
    
    def _extract_from_json(self, data: Dict[str, Any], params: ExtractedParameters):
        """从 JSON 数据中提取参数"""
        # 通用参数
        params.domain = data.get('domain') or data.get('uri') or data.get('url')
        params.nonce = str(data.get('nonce', '')) if data.get('nonce') else None
        params.timestamp = str(data.get('timestamp', '')) if data.get('timestamp') else None
        params.expires_at = str(data.get('expires_at', '')) if data.get('expires_at') else None
        params.address = data.get('address') or data.get('wallet_address')
        
        # 登录相关
        params.session_id = data.get('session_id') or data.get('sessionId')
        params.user_id = data.get('user_id') or data.get('userId')
        
        # 绑定相关
        params.binding_target = data.get('email') or data.get('phone') or data.get('username')
        params.binding_type = data.get('binding_type') or data.get('type')
        
        # 授权相关
        if 'permissions' in data:
            params.permissions = data['permissions'] if isinstance(data['permissions'], list) else [data['permissions']]
        params.resource = data.get('resource')
        params.action = data.get('action')
        
        # 验证相关
        params.challenge = data.get('challenge')
        params.verification_code = data.get('code') or data.get('verification_code')
        
        # 自定义字段
        excluded_keys = {
            'domain', 'uri', 'url', 'nonce', 'timestamp', 'expires_at', 'address', 
            'wallet_address', 'session_id', 'sessionId', 'user_id', 'userId',
            'email', 'phone', 'username', 'binding_type', 'type', 'permissions',
            'resource', 'action', 'challenge', 'code', 'verification_code'
        }
        
        for key, value in data.items():
            if key not in excluded_keys and isinstance(value, (str, int, float)):
                params.custom_fields[key] = str(value)
    
    def _extract_from_query_params(self, query_params: Dict[str, List[str]], params: ExtractedParameters):
        """从 URL 查询参数中提取"""
        def get_first_value(key: str) -> Optional[str]:
            return query_params.get(key, [None])[0]
        
        params.domain = get_first_value('domain') or get_first_value('site')
        params.nonce = get_first_value('nonce')
        params.timestamp = get_first_value('timestamp') or get_first_value('t')
        params.address = get_first_value('address') or get_first_value('wallet')
        params.session_id = get_first_value('session_id') or get_first_value('sid')
        params.challenge = get_first_value('challenge')
    
    def _extract_with_regex(self, message: str, params: ExtractedParameters):
        """使用正则表达式提取参数"""
        # 提取以太坊地址
        if not params.address:
            eth_addresses = self.patterns.ETH_ADDRESS.findall(message)
            if eth_addresses:
                params.address = eth_addresses[0]
        
        # 提取域名
        if not params.domain:
            domains = self.patterns.DOMAIN.findall(message)
            if domains:
                params.domain = domains[0] if isinstance(domains[0], str) else domains[0][0]
        
        # 提取时间戳
        if not params.timestamp:
            timestamps = self.patterns.TIMESTAMP.findall(message)
            if timestamps:
                params.timestamp = timestamps[0]
        
        # 提取 UUID（可能是 session_id 或 nonce）
        uuids = self.patterns.UUID.findall(message)
        if uuids:
            if not params.session_id:
                params.session_id = uuids[0]
            elif not params.nonce:
                params.nonce = uuids[0]
        
        # 提取 Token
        tokens = self.patterns.TOKEN.findall(message)
        if tokens:
            for token in tokens:
                if not params.nonce and len(token) > 20:
                    params.nonce = token
                    break
    
    def _extract_structured_text(self, message: str, params: ExtractedParameters):
        """从结构化文本中提取参数"""
        lines = message.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            # 简单的 key:value 格式
            if line.count(':') == 1:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if not value:
                    continue
                
                # 映射常见的键名
                if key in ['domain', 'site', 'website']:
                    params.domain = params.domain or value
                elif key in ['nonce', 'random', 'token']:
                    params.nonce = params.nonce or value
                elif key in ['timestamp', 'time', 'date']:
                    params.timestamp = params.timestamp or value
                elif key in ['address', 'wallet', 'account']:
                    params.address = params.address or value
                elif key in ['session', 'session_id', 'sessionid']:
                    params.session_id = params.session_id or value
                elif key in ['user', 'user_id', 'userid']:
                    params.user_id = params.user_id or value
                elif key in ['email', 'mail']:
                    params.binding_target = params.binding_target or value
                    params.binding_type = params.binding_type or 'email'
                elif key in ['phone', 'mobile', 'tel']:
                    params.binding_target = params.binding_target or value 
                    params.binding_type = params.binding_type or 'phone'
                elif key in ['challenge', 'code']:
                    params.challenge = params.challenge or value
                else:
                    # 其他自定义字段
                    params.custom_fields[key] = value
    
    def extract_security_info(self, message: str) -> Dict[str, Any]:
        """提取安全相关信息"""
        security_info = {
            'contains_sensitive_keywords': False,
            'sensitive_keywords': [],
            'contains_urls': bool(self.patterns.URL.search(message)),
            'contains_addresses': bool(self.patterns.ETH_ADDRESS.search(message)),
            'contains_emails': bool(self.patterns.EMAIL.search(message)),
            'contains_phone_numbers': bool(self.patterns.PHONE.search(message)),
            'message_length': len(message),
            'is_hex_encoded': message.startswith('0x')
        }
        
        # 检查敏感关键词
        from .models import TemplateKeywords
        all_security_keywords = TemplateKeywords.SECURITY_KEY
        message_lower = message.lower()
        
        for keyword in all_security_keywords:
            if keyword in message_lower:
                security_info['contains_sensitive_keywords'] = True
                security_info['sensitive_keywords'].append(keyword)
        
        return security_info 