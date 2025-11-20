"""
PersonalSign Parser Type Definitions
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import re


class PersonalSignTemplateType(str, Enum):
    """PersonalSign template type enumeration"""
    LOGIN = "login"
    BINDING = "binding" 
    AUTHORIZATION = "authorization"
    VERIFICATION = "verification"
    CUSTOM_MESSAGE = "custom_message"
    UNKNOWN = "unknown"


@dataclass
class ExtractedParameters:
    """Extracted parameters"""
    # Common parameters
    domain: Optional[str] = None
    nonce: Optional[str] = None
    timestamp: Optional[str] = None
    expires_at: Optional[str] = None
    address: Optional[str] = None
    
    # Login related parameters
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Binding related parameters
    binding_target: Optional[str] = None  # Binding target (e.g., email, phone number, etc.)
    binding_type: Optional[str] = None    # Binding type
    
    # Authorization related parameters
    permissions: List[str] = None         # Permission list
    resource: Optional[str] = None        # Resource
    action: Optional[str] = None          # Action
    
    # Verification related parameters
    challenge: Optional[str] = None       # Challenge code
    verification_code: Optional[str] = None  # Verification code
    
    # Custom parameters
    custom_fields: Dict[str, str] = None  # Other custom fields
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.custom_fields is None:
            self.custom_fields = {}


@dataclass 
class TemplateInfo:
    """Template information"""
    template_type: PersonalSignTemplateType
    confidence: float  # Confidence 0-1
    matched_patterns: List[str]  # Matched patterns
    description: str  # Template description
    
    # Template features
    required_fields: List[str] = None      # Required fields
    optional_fields: List[str] = None      # Optional fields
    security_level: str = "medium"         # Security level: low, medium, high
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.optional_fields is None:
            self.optional_fields = []


@dataclass
class PersonalSignMessage:
    """PersonalSign message"""
    # Original message
    raw_message: str
    
    # Parsing results
    template_info: TemplateInfo
    extracted_parameters: ExtractedParameters
    
    # Message properties
    message_length: int
    is_hex: bool
    language: str
    
    # Security analysis
    security_warnings: List[str] = None
    risk_level: str = "low"  # low, medium, high
    
    # Structured information
    contains_urls: bool = False
    contains_addresses: bool = False
    contains_emails: bool = False
    contains_phone_numbers: bool = False
    
    def __post_init__(self):
        if self.security_warnings is None:
            self.security_warnings = []


# Common regular expression patterns
class RegexPatterns:
    """Common regular expression patterns"""
    
    # Ethereum address
    ETH_ADDRESS = re.compile(r'0x[a-fA-F0-9]{40}')
    
    # Domain name
    DOMAIN = re.compile(r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}')
    
    # URL
    URL = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    
    # Email
    EMAIL = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # Phone number (simple matching)
    PHONE = re.compile(r'(\+?1?[- ]?)?\(?([0-9]{3})\)?[- ]?([0-9]{3})[- ]?([0-9]{4})')
    
    # Timestamp
    TIMESTAMP = re.compile(r'\b\d{10,13}\b')
    
    # UUID
    UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
    
    # Random string/Token
    TOKEN = re.compile(r'[a-zA-Z0-9+/=]{20,}')


# Template keyword definitions
class TemplateKeywords:
    """Template keyword definitions"""
    
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
    
    # Security-related keywords
    SECURITY_KEY = [
        "transfer", "转账", "send", "发送", "approve", "批准",
        "spend", "花费", "withdraw", "提取", "deposit", "存入"
    ] 