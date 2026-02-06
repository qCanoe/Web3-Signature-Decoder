/**
 * 交易处理器
 *
 * 处理所有交易请求的分析逻辑
 */

import type { OnTransactionResponse } from "@metamask/snaps-sdk";

import { localAnalyzeTransaction } from "../analyzers/local";
import { fetchBackendAnalysis, isBackendConfigured } from "../api/client";
import type { AnalysisResult } from "../types";
import { mapRiskToSeverity } from "../types";
import {
  renderTransactionInsights,
  renderLocalTransactionInsights,
  renderError,
} from "../ui/components";

/**
 * 交易对象类型
 */
interface Transaction {
  from: string;
  to?: string;
  value?: string;
  data?: string;
  gas?: string;
  gasPrice?: string;
  maxFeePerGas?: string;
  maxPriorityFeePerGas?: string;
  nonce?: string;
}

/**
 * 处理交易请求
 *
 * @param transaction - 交易对象
 * @param chainId - 链 ID (CAIP-2 格式)
 * @param transactionOrigin - 交易来源 (dApp URL)
 * @returns Snap UI 响应
 */
export async function handleTransaction(
  transaction: Transaction,
  chainId: string,
  transactionOrigin?: string
): Promise<OnTransactionResponse> {
  try {
    // 1. 本地预分析（快速）
    const localInsights = await localAnalyzeTransaction(transaction, chainId);

    // 2. 尝试调用后端深度分析
    let deepInsights: AnalysisResult | null = null;
    if (isBackendConfigured()) {
      try {
        deepInsights = await fetchBackendAnalysis({
          type: "transaction",
          data: transaction,
          chainId,
          origin: transactionOrigin,
        });
      } catch (error) {
        // 后端不可用时，使用本地分析结果
        console.error("Backend analysis failed:", error);
      }
    }

    // 3. 合并结果，渲染 UI
    if (deepInsights) {
      const severity = mapRiskToSeverity(deepInsights.risk.level);
      return {
        content: renderTransactionInsights(deepInsights, chainId),
        severity,
      };
    }

    // 回退到本地分析结果
    return renderLocalTransactionInsights(localInsights);
  } catch (error) {
    console.error("Transaction analysis error:", error);
    return {
      content: renderError("分析交易时发生错误"),
    };
  }
}

/**
 * 解析链 ID
 * @param chainId - CAIP-2 格式的链 ID (如 "eip155:1")
 * @returns 数字格式的链 ID
 */
export function parseChainId(chainId: string): number {
  const match = chainId.match(/^eip155:(\d+)$/);
  if (match) {
    return parseInt(match[1], 10);
  }
  return 1; // 默认以太坊主网
}

/**
 * 获取链名称
 */
export function getChainName(chainId: string): string {
  const chainNames: Record<string, string> = {
    "eip155:1": "Ethereum",
    "eip155:10": "Optimism",
    "eip155:56": "BNB Chain",
    "eip155:137": "Polygon",
    "eip155:42161": "Arbitrum One",
    "eip155:43114": "Avalanche",
    "eip155:8453": "Base",
    "eip155:324": "zkSync Era",
    "eip155:59144": "Linea",
    "eip155:534352": "Scroll",
    "eip155:5": "Goerli",
    "eip155:11155111": "Sepolia",
  };
  return chainNames[chainId] || `Chain ${chainId}`;
}
