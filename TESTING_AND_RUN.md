# 测试与运行指导（本地 MVP）

面向 MetaMask Snap 本地可测试流程，按顺序执行即可。

## 1. 环境准备

- Python 3.10+（建议使用已有虚拟环境）
- Node.js 20+ 与 Yarn
- MetaMask Flask

## 2. 启动后端（Flask）

在仓库根目录执行：

```
python src/web/app.py
```

确认服务可用：

```
Invoke-WebRequest -Uri http://127.0.0.1:5001/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

预期返回：

```
{"status":"ok"}
```

## 3. 运行 Snap 测试

```
cd signature-decoder-snap
yarn test
```

预期：所有测试通过。

## 4. 启动 Snap 开发服务

```
cd signature-decoder-snap
yarn start
```

预期：服务监听在 `http://localhost:8080`。

## 5. 配置 Snap 后端地址

默认已配置本地后端地址（`http://localhost:5001`），配置文件：

```
signature-decoder-snap/src/config.ts
```

如后端地址变更，修改 `BACKEND_BASE_URL` 即可。

## 6. MetaMask Flask 端到端验证

1. 在 MetaMask Flask 安装 Snap（`http://localhost:8080`）
   - 也可以使用本地安装页面：`http://127.0.0.1:5001/snap/install`
2. 触发签名：
   - `personal_sign` 或 `eth_signTypedData_v4`
3. 触发交易：
   - `eth_sendTransaction`
4. 验证洞察 UI 是否正常显示
5. 断开后端或修改 `BACKEND_BASE_URL` 为不可用地址，验证回退到本地分析提示

## 常见问题

- `snap.manifest.json` 的 `shasum` 变化：`mm-snap watch` 会自动更新，属于正常现象
- 无图标警告：不影响功能，后续可按需补充

## 关闭服务

- 后端：终端中按 `Ctrl+C`
- Snap 开发服务：终端中按 `Ctrl+C`
