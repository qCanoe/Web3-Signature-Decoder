"""
PersonalSign 解析器的类型定义
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import re


class PersonalSignTemplateType(str, Enum):
    """PersonalSign 模板类型枚举"""
    LOGIN = "login"
    BINDING = "binding" 
    AUTHORIZATION = "authorization"
    VERIFICATION = "verification"
    CUSTOM_MESSAGE = "custom_message"
    UNKNOWN = "unknown"


@dataclass
class ExtractedParameters:
    """提取的参数"""
    # 通用参数
    domain: Optional[str] = None
    nonce: Optional[str] = None
    timestamp: Optional[str] = None
    expires_at: Optional[str] = None
    address: Optional[str] = None
    
    # 登录相关参数
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # 绑定相关参数
    binding_target: Optional[str] = None  # 绑定目标（如邮箱、手机号等）
    binding_type: Optional[str] = None    # 绑定类型
    
    # 授权相关参数
    permissions: List[str] = None         # 权限列表
    resource: Optional[str] = None        # 资源
    action: Optional[str] = None          # 操作
    
    # 验证相关参数
    challenge: Optional[str] = None       # 挑战码
    verification_code: Optional[str] = None  # 验证码
    
    # 自定义参数
    custom_fields: Dict[str, str] = None  # 其他自定义字段
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.custom_fields is None:
            self.custom_fields = {}


@dataclass 
class TemplateInfo:
    """模板信息"""
    template_type: PersonalSignTemplateType
    confidence: float  # 置信度 0-1
    matched_patterns: List[str]  # 匹配的模式
    description: str  # 模板描述
    
    # 模板特征
    required_fields: List[str] = None      # 必需字段
    optional_fields: List[str] = None      # 可选字段
    security_level: str = "medium"         # 安全级别: low, medium, high
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.optional_fields is None:
            self.optional_fields = []


@dataclass
class PersonalSignMessage:
    """PersonalSign 消息"""
    # 原始消息
    raw_message: str
    
    # 解析结果
    template_info: TemplateInfo
    extracted_parameters: ExtractedParameters
    
    # 消息属性
    message_length: int
    is_hex: bool
    language: str
    
    # 安全分析
    security_warnings: List[str] = None
    risk_level: str = "low"  # low, medium, high
    
    # 结构化信息
    contains_urls: bool = False
    contains_addresses: bool = False
    contains_emails: bool = False
    contains_phone_numbers: bool = False
    
    def __post_init__(self):
        if self.security_warnings is None:
            self.security_warnings = []


# 常用的正则表达式模式
class RegexPatterns:
    """常用的正则表达式模式"""
    
    # 以太坊地址
    ETH_ADDRESS = re.compile(r'0x[a-fA-F0-9]{40}')
    
    # 域名
    DOMAIN = re.compile(r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}')
    
    # URL
    URL = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    
    # 邮箱
    EMAIL = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # 手机号（简单匹配）
    PHONE = re.compile(r'(\+?1?[- ]?)?\(?([0-9]{3})\)?[- ]?([0-9]{3})[- ]?([0-9]{4})')
    
    # 时间戳
    TIMESTAMP = re.compile(r'\b\d{10,13}\b')
    
    # UUID
    UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
    
    # 随机字符串/Token
    TOKEN = re.compile(r'[a-zA-Z0-9+/=]{20,}')


# 模板关键词定义
class TemplateKeywords:
    """模板关键词定义"""
    
    LOGIN = [
        "sign in", "login", "log in", "登录", "登入", "sign into",
        "authenticate", "认证", "身份验证", "welcome", "欢迎"
    ]
    
    BINDING = [
        "bind", "绑定", "link", "connect", "关联", "连接",
        "verify account", "验证账户", "confirm", "确认"
    ]
    
    AUTHORIZATION = [
        "authorize", "授权", "permission", "权限", "grant", "允许",
        "approve", "批准", "access", "访问", "delegate", "委托"
    ]
    
    VERIFICATION = [
        "verify", "验证", "confirm", "确认", "validate", "校验",
        "check", "检查", "prove", "证明", "challenge", "挑战"
    ]
    
    # 安全相关关键词
    SECURITY_KEY = [
        "transfer", "转账", "send", "发送", "approve", "批准",
        "spend", "花费", "withdraw", "提取", "deposit", "存入"
    ] 