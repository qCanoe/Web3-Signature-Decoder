/**
 * 类型定义文件
 */

import type { SeverityLevel } from "@metamask/snaps-sdk";

/**
 * 风险等级
 */
export type RiskLevel = "critical" | "high" | "medium" | "low" | "safe";

/**
 * 后端 API 返回的分析结果
 */
export interface AnalysisResult {
  /** 操作类型 (如 Token Approval, Permit2 Signature 等) */
  action: string;
  /** 语义化描述 */
  description: string;
  /** 风险评估 */
  risk: {
    level: RiskLevel;
    score: number;
    reasons: string[];
  };
  /** 关键参数高亮 */
  highlights: Highlight[];
  /** 交易参与者 */
  actors: Actor[];
}

/**
 * 高亮字段
 */
export interface Highlight {
  label: string;
  value: string;
  type?: "address" | "amount" | "token" | "text";
}

/**
 * 参与者信息
 */
export interface Actor {
  role: string;
  address: string;
  label?: string;
}

/**
 * 本地分析结果 (轻量级)
 */
export interface LocalAnalysisResult {
  signatureType: SignatureType;
  protocol?: string;
  basicRisk: RiskLevel;
  warnings: string[];
  fields: Record<string, unknown>;
}

/**
 * 签名类型
 */
export type SignatureType =
  | "eth_sign"
  | "personal_sign"
  | "eth_signTypedData"
  | "eth_signTypedData_v1"
  | "eth_signTypedData_v3"
  | "eth_signTypedData_v4"
  | "unknown";

/**
 * 交易类型
 */
export type TransactionType =
  | "native_transfer"
  | "erc20_transfer"
  | "erc20_approve"
  | "erc721_transfer"
  | "contract_interaction"
  | "contract_deployment"
  | "multicall"
  | "unknown";

/**
 * Snap 后端 API 请求
 */
export interface SnapAnalyzeRequest {
  type: "signature" | "transaction";
  data: unknown;
  origin?: string;
  chainId?: string;
  signatureMethod?: string;
}

/**
 * 风险等级映射到 MetaMask Severity
 */
export function mapRiskToSeverity(level: RiskLevel): SeverityLevel | undefined {
  switch (level) {
    case "critical":
      return "critical";
    case "high":
      return "critical";
    case "medium":
    case "low":
    case "safe":
    default:
      return undefined;
  }
}

/**
 * EIP-712 类型化数据结构
 */
export interface EIP712TypedData {
  types: Record<string, Array<{ name: string; type: string }>>;
  primaryType: string;
  domain: EIP712Domain;
  message: Record<string, unknown>;
}

/**
 * EIP-712 域信息
 */
export interface EIP712Domain {
  name?: string;
  version?: string;
  chainId?: number | string;
  verifyingContract?: string;
  salt?: string;
}
