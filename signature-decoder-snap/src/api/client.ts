/**
 * 后端 API 客户端
 *
 * 与 Python 后端服务通信
 */

import type { AnalysisResult, SnapAnalyzeRequest } from "../types";

/**
 * API 配置
 */
const API_CONFIG = {
  // 默认后端 URL - 可在部署时修改
  baseUrl: "https://signature-decoder-api.example.com",
  timeout: 15000, // 15 秒超时
  endpoints: {
    analyze: "/snap/analyze",
  },
};

/**
 * 调用后端分析 API
 *
 * @param request - 分析请求
 * @returns 分析结果
 * @throws 网络错误或 API 错误
 */
export async function fetchBackendAnalysis(
  request: SnapAnalyzeRequest
): Promise<AnalysisResult> {
  const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.analyze}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new ApiError(
        `API request failed: ${response.status} ${response.statusText}`,
        response.status
      );
    }

    const data = (await response.json()) as AnalysisResult;
    return data;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError("Request timeout", 408);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * API 错误类
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * 检查后端是否可用
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}/health`, {
      method: "GET",
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * 配置 API 基础 URL
 * 用于动态配置后端地址
 */
export function configureApiUrl(baseUrl: string): void {
  API_CONFIG.baseUrl = baseUrl;
}

/**
 * 获取当前 API 配置
 */
export function getApiConfig(): typeof API_CONFIG {
  return { ...API_CONFIG };
}
