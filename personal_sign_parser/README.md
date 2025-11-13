# PersonalSign 解析器

PersonalSign 解析器是一个用于解析和分析 `personal_sign` 签名消息的 Python 模块，具备参数提取和模板识别功能。

## 功能特性

✨ **模板识别**
- 自动识别消息类型：登录、绑定、授权、验证
- 基于关键词和模式匹配的智能分析
- 支持置信度评估

🔍 **参数提取**
- 智能提取结构化参数（域名、随机数、时间戳等）
- 支持多种消息格式：JSON、键值对、查询字符串
- 自动解码 Hex 编码消息

🛡️ **安全分析**
- 检测高风险操作和敏感关键词
- 提供安全警告和风险级别评估
- 识别可疑消息模式

🌐 **多语言支持**
- 支持中文、英文、日文、韩文
- 自动语言检测

## 快速开始

### 基本使用

```python
from personal_sign_parser import PersonalSignParser

# 创建解析器实例
parser = PersonalSignParser()

# 解析消息
message = """Sign in to example.com
Nonce: abc123
Timestamp: 1640995200"""

result = parser.parse(message)

# 查看结果
print(f"模板类型: {result.template_info.template_type.value}")
print(f"置信度: {result.template_info.confidence:.1%}")
print(f"域名: {result.extracted_parameters.domain}")
print(f"随机数: {result.extracted_parameters.nonce}")
```

### 支持的消息类型

#### 1. 登录消息
```python
# 文本格式
message = """Sign in to example.com
Nonce: abc123
Timestamp: 1640995200"""

# JSON 格式
message = '{"domain":"app.example.com","nonce":"xyz789","action":"login"}'
```

#### 2. 绑定消息
```python
# 邮箱绑定
message = """Bind email: user@example.com
Code: 123456"""

# 手机绑定
message = """绑定手机号码: +1234567890
验证码: 456789"""
```

#### 3. 授权消息
```python
message = """Authorize access to: user profile
Permissions: read, write
Resource: /api/user"""
```

#### 4. 验证消息
```python
message = """Verify ownership of this wallet
Challenge: random_challenge_123
Address: 0x1234567890123456789012345678901234567890"""
```

### 解析结果

解析器返回 `PersonalSignMessage` 对象，包含以下信息：

```python
result = parser.parse(message)

# 基本信息
print(result.raw_message)          # 原始消息
print(result.message_length)       # 消息长度
print(result.language)             # 语言
print(result.is_hex)               # 是否为Hex编码

# 模板信息
print(result.template_info.template_type)    # 模板类型
print(result.template_info.confidence)       # 置信度
print(result.template_info.description)      # 描述
print(result.template_info.security_level)   # 安全级别

# 提取的参数
params = result.extracted_parameters
print(params.domain)               # 域名
print(params.nonce)                # 随机数
print(params.timestamp)            # 时间戳
print(params.address)              # 地址
print(params.session_id)           # 会话ID
# ... 更多参数

# 安全分析
print(result.risk_level)           # 风险级别
print(result.security_warnings)    # 安全警告

# 消息特征
print(result.contains_urls)        # 是否包含URL
print(result.contains_addresses)   # 是否包含地址
print(result.contains_emails)      # 是否包含邮箱
```

## 模板类型

- `LOGIN`: 登录验证消息
- `BINDING`: 账户绑定验证消息  
- `AUTHORIZATION`: 权限授权确认消息
- `VERIFICATION`: 身份验证确认消息
- `CUSTOM_MESSAGE`: 自定义消息
- `UNKNOWN`: 未知类型消息

## 安全级别

- `low`: 低风险
- `medium`: 中等风险
- `high`: 高风险

## 运行演示

运行内置演示查看完整功能：

```bash
cd personal_sign_parser/tests
python demo.py
```

## 测试

运行测试文件：

```bash
cd personal_sign_parser/tests  
python test_parser.py
```

## 项目结构

```
personal_sign_parser/
├── __init__.py                 # 模块初始化
├── types.py                    # 类型定义
├── parser.py                   # 主解析器
├── parameter_extractor.py      # 参数提取器
├── template_detector.py        # 模板识别器
├── tests/                      # 测试文件夹
│   ├── __init__.py
│   ├── test_data.py           # 测试数据
│   ├── test_parser.py         # 解析器测试
│   └── demo.py                # 功能演示
└── README.md                  # 说明文档
```

## 版本信息

- 版本: 0.1.0
- Python 要求: 3.7+

## 许可证

MIT License 