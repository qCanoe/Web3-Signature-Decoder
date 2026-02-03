/**
 * EIP-712 类型化数据解析器
 */

import type { Signature } from "@metamask/snaps-sdk";
import type { EIP712TypedData, EIP712Domain } from "../types";

/**
 * 从签名对象解析 EIP-712 类型化数据
 */
export function parseEIP712Data(signature: Signature): EIP712TypedData | null {
  try {
    // 检查签名对象结构
    if (!("data" in signature)) {
      return null;
    }

    const data = signature.data;

    // 如果是字符串，尝试解析 JSON
    if (typeof data === "string") {
      return JSON.parse(data) as EIP712TypedData;
    }

    // 如果已经是对象
    if (typeof data === "object" && data !== null) {
      return data as unknown as EIP712TypedData;
    }

    return null;
  } catch (error) {
    console.error("Failed to parse EIP-712 data:", error);
    return null;
  }
}

/**
 * 扁平化 EIP-712 类型化数据，提取关键字段
 */
export function flattenTypedData(
  typedData: EIP712TypedData
): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  // 提取 domain 信息
  if (typedData.domain) {
    result["domain.name"] = typedData.domain.name;
    result["domain.version"] = typedData.domain.version;
    result["domain.chainId"] = typedData.domain.chainId;
    result["domain.verifyingContract"] = typedData.domain.verifyingContract;
  }

  // 提取 primaryType
  result["primaryType"] = typedData.primaryType;

  // 递归扁平化 message
  flattenObject(typedData.message, result, "");

  return result;
}

/**
 * 递归扁平化对象
 */
function flattenObject(
  obj: Record<string, unknown>,
  result: Record<string, unknown>,
  prefix: string
): void {
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key;

    if (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value)
    ) {
      flattenObject(value as Record<string, unknown>, result, newKey);
    } else {
      result[newKey] = value;
    }
  }
}

/**
 * 提取 EIP-712 关键字段用于显示
 */
export function extractDisplayFields(
  typedData: EIP712TypedData
): Array<{ label: string; value: string }> {
  const fields: Array<{ label: string; value: string }> = [];
  const message = typedData.message;

  // 常见字段映射
  const fieldLabels: Record<string, string> = {
    owner: "Owner",
    spender: "Spender",
    value: "Amount",
    amount: "Amount",
    nonce: "Nonce",
    deadline: "Deadline",
    expiry: "Expiry",
    token: "Token",
    permitted: "Permitted",
    details: "Details",
    witness: "Witness",
    from: "From",
    to: "To",
    receiver: "Receiver",
  };

  // 提取已知字段
  for (const [key, label] of Object.entries(fieldLabels)) {
    const value = message[key];
    if (value !== undefined) {
      fields.push({
        label,
        value: formatFieldValue(value),
      });
    }
  }

  return fields;
}

/**
 * 格式化字段值用于显示
 */
function formatFieldValue(value: unknown): string {
  if (typeof value === "string") {
    // 地址格式化
    if (value.match(/^0x[a-fA-F0-9]{40}$/)) {
      return shortenAddress(value);
    }
    // 大数字格式化
    if (value.match(/^0x[a-fA-F0-9]+$/) && value.length > 20) {
      return formatBigNumber(value);
    }
    return value;
  }

  if (typeof value === "number" || typeof value === "bigint") {
    return formatBigNumber(value);
  }

  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }

  return String(value);
}

/**
 * 缩短地址显示
 */
function shortenAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

/**
 * 格式化大数字
 */
function formatBigNumber(value: unknown): string {
  try {
    const bigValue = BigInt(String(value));

    // 检查是否为无限授权
    const maxUint256 = BigInt(
      "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    );
    if (bigValue === maxUint256) {
      return "Unlimited (MAX)";
    }

    // 尝试转换为可读格式
    const absValue = bigValue < 0n ? -bigValue : bigValue;

    if (absValue >= BigInt(10) ** BigInt(18)) {
      // 可能是 18 位小数的代币
      const wholePart = absValue / BigInt(10) ** BigInt(18);
      return `${wholePart.toString()} (18 decimals)`;
    }

    return bigValue.toString();
  } catch {
    return String(value);
  }
}

/**
 * 获取 domain 信息摘要
 */
export function getDomainSummary(domain: EIP712Domain): string {
  const parts: string[] = [];

  if (domain.name) {
    parts.push(domain.name);
  }

  if (domain.version) {
    parts.push(`v${domain.version}`);
  }

  if (domain.chainId) {
    parts.push(`Chain: ${domain.chainId}`);
  }

  return parts.join(" | ") || "Unknown Domain";
}
