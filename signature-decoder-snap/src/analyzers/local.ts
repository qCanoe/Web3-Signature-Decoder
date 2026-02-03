/**
 * 本地轻量分析器
 *
 * 在 Snap 端执行快速的基础分析，无需后端调用
 */

import type { Signature } from "@metamask/snaps-sdk";

import type {
  LocalAnalysisResult,
  SignatureType,
  RiskLevel,
  TransactionType,
} from "../types";
import { classifyEIP712Type, detectProtocol } from "./classifier";
import { parseEIP712Data, flattenTypedData } from "./eip712";

/**
 * 交易对象接口
 */
interface Transaction {
  from: string;
  to?: string;
  value?: string;
  data?: string;
}

/**
 * 本地分析签名
 */
export async function localAnalyzeSignature(
  signature: Signature
): Promise<LocalAnalysisResult> {
  const signatureType = signature.signatureMethod as SignatureType;
  const warnings: string[] = [];
  let basicRisk: RiskLevel = "low";
  let protocol: string | undefined;
  let fields: Record<string, unknown> = {};

  // eth_sign 是最危险的签名方法
  if (signatureType === "eth_sign") {
    warnings.push("eth_sign 可以签署任意数据，极度危险");
    basicRisk = "critical";
  }

  // 处理 EIP-712 类型化数据
  if (
    signatureType === "eth_signTypedData_v4" ||
    signatureType === "eth_signTypedData_v3" ||
    signatureType === "eth_signTypedData"
  ) {
    try {
      const typedData = parseEIP712Data(signature);
      if (typedData) {
        // 检测协议
        protocol = detectProtocol(typedData);

        // 分类并提取关键字段
        const classification = classifyEIP712Type(typedData);
        fields = flattenTypedData(typedData);

        // 基于分类评估风险
        if (classification.type === "permit" || classification.type === "permit2") {
          // 检查是否为无限授权
          const amount = fields["value"] || fields["amount"];
          if (isUnlimitedAmount(amount)) {
            warnings.push("无限授权 - 允许花费全部代币");
            basicRisk = "high";
          } else {
            basicRisk = "medium";
          }
        }

        // 检查授权期限
        const deadline = fields["deadline"] || fields["expiry"];
        if (deadline && isLongDeadline(deadline)) {
          warnings.push("授权期限较长");
        }
      }
    } catch (error) {
      console.error("EIP-712 parsing error:", error);
    }
  }

  // 处理 personal_sign
  if (signatureType === "personal_sign") {
    const message = extractPersonalMessage(signature);
    if (message) {
      fields["message"] = message;

      // 检测登录签名
      if (isLoginMessage(message)) {
        basicRisk = "safe";
      }
    }
  }

  return {
    signatureType,
    protocol,
    basicRisk,
    warnings,
    fields,
  };
}

/**
 * 本地分析交易
 */
export async function localAnalyzeTransaction(
  transaction: Transaction,
  chainId: string
): Promise<LocalAnalysisResult> {
  const warnings: string[] = [];
  let basicRisk: RiskLevel = "low";
  let protocol: string | undefined;
  const fields: Record<string, unknown> = {};
  let signatureType: SignatureType = "unknown";

  // 提取基本字段
  fields["from"] = transaction.from;
  fields["to"] = transaction.to;
  fields["value"] = transaction.value || "0x0";
  fields["chainId"] = chainId;

  // 检查是否为合约部署
  if (!transaction.to) {
    warnings.push("合约部署交易");
    basicRisk = "medium";
    return {
      signatureType,
      protocol,
      basicRisk,
      warnings,
      fields,
    };
  }

  // 检查交易数据
  const data = transaction.data || "0x";

  // 纯 ETH 转账
  if (data === "0x" || data === "") {
    basicRisk = "low";
    return {
      signatureType,
      protocol,
      basicRisk,
      warnings,
      fields,
    };
  }

  // 解析函数选择器
  const selector = data.slice(0, 10).toLowerCase();
  const txType = identifyTransactionType(selector);
  fields["transactionType"] = txType;

  // 基于交易类型评估风险
  switch (txType) {
    case "erc20_approve":
      basicRisk = "medium";
      // 检查是否为无限授权
      if (data.length >= 74) {
        const amountHex = "0x" + data.slice(74, 138);
        if (isUnlimitedAmount(amountHex)) {
          warnings.push("无限授权 - 允许花费全部代币");
          basicRisk = "high";
        }
      }
      break;

    case "erc20_transfer":
    case "erc721_transfer":
      basicRisk = "low";
      break;

    case "multicall":
      warnings.push("批量调用 - 包含多个操作");
      basicRisk = "medium";
      break;

    default:
      basicRisk = "low";
  }

  return {
    signatureType,
    protocol,
    basicRisk,
    warnings,
    fields,
  };
}

/**
 * 识别交易类型
 */
function identifyTransactionType(selector: string): TransactionType {
  const selectors: Record<string, TransactionType> = {
    // ERC20
    "0xa9059cbb": "erc20_transfer", // transfer(address,uint256)
    "0x23b872dd": "erc20_transfer", // transferFrom(address,address,uint256)
    "0x095ea7b3": "erc20_approve", // approve(address,uint256)

    // ERC721
    "0x42842e0e": "erc721_transfer", // safeTransferFrom(address,address,uint256)
    "0xb88d4fde": "erc721_transfer", // safeTransferFrom(address,address,uint256,bytes)

    // Multicall
    "0xac9650d8": "multicall", // multicall(bytes[])
    "0x5ae401dc": "multicall", // multicall(uint256,bytes[])
    "0x1f0464d1": "multicall", // multicall(bytes32,bytes[])
  };

  return selectors[selector] || "contract_interaction";
}

/**
 * 检查是否为无限授权金额
 */
function isUnlimitedAmount(amount: unknown): boolean {
  if (typeof amount !== "string") return false;

  // uint256 最大值或接近最大值
  const maxUint256 =
    "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
  const threshold =
    "0x8000000000000000000000000000000000000000000000000000000000000000";

  const normalizedAmount = amount.toLowerCase();

  // 检查是否为最大值
  if (normalizedAmount === maxUint256) return true;

  // 检查是否超过阈值
  try {
    if (BigInt(normalizedAmount) >= BigInt(threshold)) {
      return true;
    }
  } catch {
    // 解析失败，保守返回 false
  }

  return false;
}

/**
 * 检查是否为长期授权
 */
function isLongDeadline(deadline: unknown): boolean {
  if (typeof deadline !== "string" && typeof deadline !== "number") {
    return false;
  }

  const deadlineNum =
    typeof deadline === "string" ? parseInt(deadline, 10) : deadline;
  const now = Math.floor(Date.now() / 1000);
  const oneYear = 365 * 24 * 60 * 60;

  return deadlineNum > now + oneYear;
}

/**
 * 提取 personal_sign 消息内容
 */
function extractPersonalMessage(signature: Signature): string | null {
  try {
    // signature.data 包含消息内容
    if ("data" in signature && typeof signature.data === "string") {
      // 尝试将 hex 转换为字符串
      if (signature.data.startsWith("0x")) {
        const hex = signature.data.slice(2);
        const bytes = new Uint8Array(
          hex.match(/.{1,2}/g)?.map((byte) => parseInt(byte, 16)) || []
        );
        return new TextDecoder().decode(bytes);
      }
      return signature.data;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * 检测是否为登录签名消息
 */
function isLoginMessage(message: string): boolean {
  const loginPatterns = [
    /sign.*(in|up|login)/i,
    /authenticate/i,
    /verify.*address/i,
    /welcome.*to/i,
    /nonce[:=\s]/i,
    /login.*nonce/i,
    /Sign this message to/i,
  ];

  return loginPatterns.some((pattern) => pattern.test(message));
}
