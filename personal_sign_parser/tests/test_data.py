"""
PersonalSign 解析器测试数据
包含各种类型的 PersonalSign 消息示例
"""

from typing import Dict, List, Any

# 登录类型消息示例
LOGIN_MESSAGES = [
    {
        "message": "Sign in to example.com\nNonce: abc123\nTimestamp: 1640995200",
        "expected_template": "login",
        "expected_params": {
            "domain": "example.com",
            "nonce": "abc123",
            "timestamp": "1640995200"
        }
    },
    {
        "message": '{"domain":"app.example.com","nonce":"xyz789","action":"login","session_id":"sess_123"}',
        "expected_template": "login",
        "expected_params": {
            "domain": "app.example.com",
            "nonce": "xyz789",
            "session_id": "sess_123"
        }
    },
    {
        "message": "欢迎登录 MyApp\n域名: myapp.com\n随机数: random123\n用户ID: user456",
        "expected_template": "login",
        "expected_params": {
            "domain": "myapp.com",
            "nonce": "random123",
            "user_id": "user456"
        }
    },
    {
        "message": "Welcome to DeFi Protocol\nPlease sign in to continue\nWallet: 0x1234567890123456789012345678901234567890\nNonce: auth_token_xyz",
        "expected_template": "login",
        "expected_params": {
            "address": "0x1234567890123456789012345678901234567890",
            "nonce": "auth_token_xyz"
        }
    }
]

# 绑定类型消息示例
BINDING_MESSAGES = [
    {
        "message": "Bind email: user@example.com\nCode: 123456",
        "expected_template": "binding",
        "expected_params": {
            "binding_target": "user@example.com",
            "binding_type": "email",
            "verification_code": "123456"
        }
    },
    {
        "message": "绑定手机号码: +1234567890\n验证码: 456789\n过期时间: 1640995800",
        "expected_template": "binding",
        "expected_params": {
            "binding_target": "+1234567890",
            "binding_type": "phone",
            "verification_code": "456789",
            "expires_at": "1640995800"
        }
    },
    {
        "message": '{"type":"bind","email":"test@domain.com","nonce":"bind_123","timestamp":"1640995200"}',
        "expected_template": "binding",
        "expected_params": {
            "binding_target": "test@domain.com",
            "binding_type": "email", 
            "nonce": "bind_123",
            "timestamp": "1640995200"
        }
    },
    {
        "message": "Link your account\nConnect to: social_platform\nUser: @username123",
        "expected_template": "binding",
        "expected_params": {
            "binding_target": "@username123",
            "binding_type": None
        }
    }
]

# 授权类型消息示例
AUTHORIZATION_MESSAGES = [
    {
        "message": "Authorize access to: user profile\nPermissions: read, write\nResource: /api/user",
        "expected_template": "authorization",
        "expected_params": {
            "resource": "/api/user",
            "permissions": ["read", "write"]
        }
    },
    {
        "message": "授权访问资源: 用户数据\n权限: 读取\n操作: get_profile\n时间戳: 1640995200",
        "expected_template": "authorization",
        "expected_params": {
            "resource": "用户数据",
            "permissions": ["读取"],
            "action": "get_profile",
            "timestamp": "1640995200"
        }
    },
    {
        "message": '{"action":"authorize","permissions":["transfer","approve"],"resource":"0x1234567890123456789012345678901234567890","nonce":"auth_456"}',
        "expected_template": "authorization",
        "expected_params": {
            "permissions": ["transfer", "approve"],
            "resource": "0x1234567890123456789012345678901234567890",
            "action": "authorize",
            "nonce": "auth_456"
        }
    }
]

# 验证类型消息示例
VERIFICATION_MESSAGES = [
    {
        "message": "Verify ownership of this wallet\nChallenge: random_challenge_123\nAddress: 0x1234567890123456789012345678901234567890",
        "expected_template": "verification",
        "expected_params": {
            "challenge": "random_challenge_123",
            "address": "0x1234567890123456789012345678901234567890"
        }
    },
    {
        "message": "验证钱包所有权\n挑战码: challenge_xyz_789\n时间戳: 1640995200",
        "expected_template": "verification",
        "expected_params": {
            "challenge": "challenge_xyz_789",
            "timestamp": "1640995200"
        }
    },
    {
        "message": '{"action":"verify","challenge":"proof_123","nonce":"verify_456","domain":"verify.example.com"}',
        "expected_template": "verification",
        "expected_params": {
            "challenge": "proof_123",
            "nonce": "verify_456",
            "domain": "verify.example.com"
        }
    }
]

# 自定义消息示例
CUSTOM_MESSAGES = [
    {
        "message": "Hello World!\nThis is a custom message.",
        "expected_template": "custom_message",
        "expected_params": {}
    },
    {
        "message": "Random text with some data\nKey: value\nAnother: field",
        "expected_template": "custom_message",
        "expected_params": {
            "custom_fields": {"key": "value", "another": "field"}
        }
    }
]

# 高风险消息示例（包含敏感关键词）
HIGH_RISK_MESSAGES = [
    {
        "message": "Transfer 100 ETH to address 0x1234567890123456789012345678901234567890\nApprove this transaction",
        "expected_template": "unknown",
        "risk_level": "high",
        "should_have_warnings": True
    },
    {
        "message": "Authorize spending of your tokens\nAmount: unlimited\nSpender: 0x1234567890123456789012345678901234567890",
        "expected_template": "authorization",
        "risk_level": "high",
        "should_have_warnings": True
    },
    {
        "message": "Withdraw all funds from your wallet\nDestination: 0x1234567890123456789012345678901234567890",
        "expected_template": "unknown",
        "risk_level": "high",
        "should_have_warnings": True
    }
]

# Hex 编码消息示例
HEX_MESSAGES = [
    {
        "message": "0x48656c6c6f20576f726c6421",  # "Hello World!" 的 hex 编码
        "expected_decoded": "Hello World!",
        "expected_template": "custom_message"
    },
    {
        "message": "0x7b22646f6d61696e223a226578616d706c652e636f6d222c226e6f6e6365223a22616263313233227d",  # JSON 的 hex 编码
        "expected_decoded": '{"domain":"example.com","nonce":"abc123"}',
        "expected_template": "login"
    }
]

# 结构化消息示例
STRUCTURED_MESSAGES = [
    {
        "message": "domain: example.com\nnonce: abc123\ntimestamp: 1640995200\naction: login",
        "format_type": "key_value",
        "expected_template": "login"
    },
    {
        "message": "domain=example.com&nonce=abc123&action=login&session_id=sess_123",
        "format_type": "query_string",
        "expected_template": "login"
    }
]

# 多语言消息示例
MULTILINGUAL_MESSAGES = [
    {
        "message": "登录到 example.com\n随机数: abc123\n时间戳: 1640995200",
        "language": "chinese",
        "expected_template": "login"
    },
    {
        "message": "example.comにログイン\nノンス: abc123\nタイムスタンプ: 1640995200",
        "language": "japanese",
        "expected_template": "login"
    },
    {
        "message": "example.com에 로그인\n논스: abc123\n타임스탬프: 1640995200",
        "language": "korean",
        "expected_template": "login"
    }
]

# 所有测试数据
ALL_TEST_DATA = {
    "login": LOGIN_MESSAGES,
    "binding": BINDING_MESSAGES,
    "authorization": AUTHORIZATION_MESSAGES,
    "verification": VERIFICATION_MESSAGES,
    "custom": CUSTOM_MESSAGES,
    "high_risk": HIGH_RISK_MESSAGES,
    "hex_encoded": HEX_MESSAGES,
    "structured": STRUCTURED_MESSAGES,
    "multilingual": MULTILINGUAL_MESSAGES
}


def get_test_data(category: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    获取测试数据
    
    Args:
        category: 数据类别，如果不指定则返回所有数据
        
    Returns:
        测试数据字典
    """
    if category:
        return {category: ALL_TEST_DATA.get(category, [])}
    return ALL_TEST_DATA


def get_sample_messages() -> List[str]:
    """获取所有示例消息文本"""
    messages = []
    for category_data in ALL_TEST_DATA.values():
        for item in category_data:
            messages.append(item["message"])
    return messages 