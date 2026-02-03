# Signature Decoder Snap

MetaMask Snap，为签名和交易提供语义化的安全洞察。

## 功能

- **签名分析** - 解析 `personal_sign`、`eth_signTypedData_v4` 等签名请求
- **交易分析** - 分析 `eth_sendTransaction` 交易内容
- **风险评估** - 识别无限授权、危险操作等风险
- **协议识别** - 识别 Permit2、Seaport、Uniswap 等常见协议

## 权限

此 Snap 请求以下权限：

| 权限 | 用途 |
|------|------|
| `endowment:signature-insight` | 拦截并分析签名请求 |
| `endowment:transaction-insight` | 拦截并分析交易请求 |
| `endowment:network-access` | 调用后端 API 进行深度分析 |

## 安装

### 开发环境

1. 安装依赖：

```bash
yarn install
```

2. 启动开发服务器：

```bash
yarn start
```

3. 在 MetaMask Flask 中安装 Snap（连接到 `http://localhost:8080`）

### 生产环境

通过 npm 安装：

```bash
npm:@signature-decoder/snap
```

## 项目结构

```
signature-decoder-snap/
├── snap.manifest.json       # Snap 配置和权限声明
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts             # 入口点 (onSignature, onTransaction)
│   ├── types.ts             # 类型定义
│   ├── handlers/
│   │   ├── signature.ts     # 签名处理逻辑
│   │   └── transaction.ts   # 交易处理逻辑
│   ├── analyzers/
│   │   ├── local.ts         # 本地轻量分析
│   │   ├── eip712.ts        # EIP-712 解析
│   │   └── classifier.ts    # 基础分类器
│   ├── api/
│   │   └── client.ts        # 后端 API 客户端
│   ├── ui/
│   │   └── components.tsx   # UI 组件
│   └── data/
│       ├── signatures.json  # 常用函数签名缓存
│       └── eip712Types.json # EIP-712 类型定义
└── test/
    └── index.test.ts        # 测试文件
```

## 开发

### 构建

```bash
yarn build
```

### 测试

```bash
yarn test
```

### 代码检查

```bash
yarn lint
yarn lint:fix
```

## 后端 API

Snap 会尝试调用后端 API 进行深度分析。如果后端不可用，将回退到本地轻量分析。

后端 API 端点：`POST /snap/analyze`

请求格式：
```json
{
  "type": "signature" | "transaction",
  "data": { ... },
  "origin": "https://example.com",
  "chainId": "eip155:1",
  "signatureMethod": "eth_signTypedData_v4"
}
```

## 风险等级

| 等级 | 描述 | MetaMask 行为 |
|------|------|---------------|
| `critical` | 极度危险 | 显示阻断式警告弹窗 |
| `high` | 高风险 | 显示阻断式警告弹窗 |
| `medium` | 中等风险 | 正常显示洞察 |
| `low` | 低风险 | 正常显示洞察 |
| `safe` | 安全 | 正常显示洞察 |

## 许可证

MIT
