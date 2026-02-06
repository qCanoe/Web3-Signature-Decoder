/**
 * 签名处理器
 *
 * 处理所有签名请求的分析逻辑
 */

import type { OnSignatureResponse, Signature } from "@metamask/snaps-sdk";

import { localAnalyzeSignature } from "../analyzers/local";
import { fetchBackendAnalysis, isBackendConfigured } from "../api/client";
import type { AnalysisResult, LocalAnalysisResult } from "../types";
import { mapRiskToSeverity } from "../types";
import { renderInsights, renderLocalInsights, renderError } from "../ui/components";

/**
 * 处理签名请求
 *
 * @param signature - 签名对象
 * @param signatureOrigin - 签名来源 (dApp URL)
 * @returns Snap UI 响应
 */
export async function handleSignature(
  signature: Signature,
  signatureOrigin?: string
): Promise<OnSignatureResponse> {
  try {
    // 1. 本地预分析（快速）
    const localInsights = await localAnalyzeSignature(signature);

    // 2. 尝试调用后端深度分析
    let deepInsights: AnalysisResult | null = null;
    if (isBackendConfigured()) {
      try {
        deepInsights = await fetchBackendAnalysis({
          type: "signature",
          data: signature,
          origin: signatureOrigin,
          signatureMethod: signature.signatureMethod,
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
        content: renderInsights(deepInsights),
        severity,
      };
    }

    // 回退到本地分析结果
    return renderLocalInsights(localInsights);
  } catch (error) {
    console.error("Signature analysis error:", error);
    return {
      content: renderError("分析签名时发生错误"),
    };
  }
}

/**
 * 获取签名方法的友好名称
 */
export function getSignatureMethodName(method: string): string {
  const methodNames: Record<string, string> = {
    eth_sign: "Raw Signature (Dangerous)",
    personal_sign: "Personal Message",
    eth_signTypedData: "Typed Data v1",
    eth_signTypedData_v1: "Typed Data v1",
    eth_signTypedData_v3: "Typed Data v3",
    eth_signTypedData_v4: "Typed Data v4",
  };
  return methodNames[method] || method;
}
