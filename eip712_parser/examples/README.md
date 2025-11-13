# EIP712 Parser Examples

这是 `eip712_parser` 模块的示例文件夹，包含各种EIP712签名解析和分析的演示程序。

## 文件说明

### `basic_usage.py`
基本使用示例，展示如何解析Seaport NFT列表消息和执行安全检查。

**功能特性：**
- EIP712消息解析
- NFT订单信息提取
- 价格分析
- 安全检查

**使用方法：**
```bash
python basic_usage.py
```

### `advanced_analysis.py`
高级分析示例，提供详细的EIP712签名分析和模块化参数拆解。

**功能特性：**
- 完整的EIP712结构分析
- NFT和Permit消息详细解析
- 安全风险评估
- 余额变化分析

**使用方法：**
```bash
python advanced_analysis.py
```

### `signature_detection_demo.py`
签名识别演示，展示如何使用签名识别器和通用解析器。

**功能特性：**
- 多种签名类型识别
- 批量签名检测
- 通用解析器使用
- 安全警告检测

**测试的签名类型：**
- EIP-712 结构化数据签名
- eth_sendTransaction 交易签名
- personal_sign 个人消息签名
- eth_sign 原始签名（高风险）

**使用方法：**
```bash
python signature_detection_demo.py
```

### `signature_classification_demo.py`
签名分类演示，展示模块化签名识别与分级系统。

**功能特性：**
- 签名类型分类
- 风险级别评估
- 数据格式验证
- 批量处理功能

**使用方法：**
```bash
python signature_classification_demo.py
```

### `quick_start.py`
快速开始示例，简单演示签名分类器的基本功能。

**功能特性：**
- 基础签名分类
- 风险评估
- 安全建议
- 适合初学者

**使用方法：**
```bash
python quick_start.py
```

## 示例覆盖范围

### 支持的协议
- ✅ **Seaport** - NFT市场订单
- ✅ **OpenSea** - NFT交易
- ✅ **Permit/Permit2** - 代币授权
- ✅ **Custom EIP712** - 自定义结构化数据

### 支持的签名类型
- ✅ **eth_signTypedData_v4** - EIP712结构化签名
- ✅ **eth_sendTransaction** - 以太坊交易
- ✅ **personal_sign** - 个人消息签名
- ✅ **eth_sign** - 原始签名（高风险）

### 安全分析功能
- ✅ 价格分析和风险评估
- ✅ 余额变化检测
- ✅ 敏感词检测
- ✅ 钓鱼网站识别
- ✅ 授权风险评估

## 运行要求

确保已安装项目依赖：
```bash
pip install -r ../../../requirements.txt
```

在项目根目录下运行示例：
```bash
cd eip712_parser/examples
python basic_usage.py
python advanced_analysis.py
python signature_detection_demo.py
python signature_classification_demo.py
python quick_start.py
```

## 注意事项

- 所有示例都包含了路径修复代码，可以直接在examples目录下运行
- 示例数据仅用于演示，不包含真实的私钥或敏感信息
- 建议按顺序学习：`quick_start.py` → `basic_usage.py` → `advanced_analysis.py` → 其他示例 