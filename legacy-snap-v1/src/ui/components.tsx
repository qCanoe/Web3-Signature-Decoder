/**
 * UI 组件
 *
 * 使用 MetaMask Snaps JSX 组件渲染分析结果
 */

import type { OnSignatureResponse, OnTransactionResponse } from "@metamask/snaps-sdk";
import {
  Box,
  Heading,
  Text,
  Divider,
  Bold,
  Row,
  Address,
  Copyable,
} from "@metamask/snaps-sdk/jsx";

import type { AnalysisResult, LocalAnalysisResult, RiskLevel } from "../types";
import { mapRiskToSeverity } from "../types";
import { getChainName } from "../handlers/transaction";

/**
 * 渲染完整分析结果
 */
export function renderInsights(insights: AnalysisResult) {
  const riskIcon = getRiskIcon(insights.risk.level);
  const riskColor = getRiskColor(insights.risk.level);

  return (
    <Box>
      {/* 风险等级标题 */}
      <Heading>
        {riskIcon} {insights.action}
      </Heading>

      <Divider />

      {/* 语义描述 */}
      <Text>{insights.description}</Text>

      <Divider />

      {/* 风险评估 */}
      <Row label="Risk Level">
        <Text>
          <Bold>{insights.risk.level.toUpperCase()}</Bold> (Score:{" "}
          {insights.risk.score}/100)
        </Text>
      </Row>

      {/* 风险原因 */}
      {insights.risk.reasons.length > 0 && (
        <Box>
          <Heading>Risk Factors</Heading>
          {insights.risk.reasons.map((reason, i) => (
            <Text key={`reason-${i}`}>• {reason}</Text>
          ))}
        </Box>
      )}

      <Divider />

      {/* 关键参数高亮 */}
      {insights.highlights.length > 0 && (
        <Box>
          <Heading>Key Parameters</Heading>
          {insights.highlights.map((h, i) => (
            <Row key={`highlight-${i}`} label={h.label}>
              {h.type === "address"
                ? renderAddressOrText(h.value)
                : <Text>{h.value}</Text>}
            </Row>
          ))}
        </Box>
      )}

      {/* 参与者信息 */}
      {insights.actors.length > 0 && (
        <Box>
          <Divider />
          <Heading>Participants</Heading>
          {insights.actors.map((actor, i) => (
            <Row key={`actor-${i}`} label={actor.role}>
              {renderAddressOrText(actor.address)}
            </Row>
          ))}
        </Box>
      )}
    </Box>
  );
}

/**
 * 渲染交易分析结果
 */
export function renderTransactionInsights(
  insights: AnalysisResult,
  chainId: string
) {
  const chainName = getChainName(chainId);
  const riskIcon = getRiskIcon(insights.risk.level);

  return (
    <Box>
      {/* 链和操作类型 */}
      <Heading>
        {riskIcon} {insights.action}
      </Heading>

      <Row label="Network">
        <Text>{chainName}</Text>
      </Row>

      <Divider />

      {/* 语义描述 */}
      <Text>{insights.description}</Text>

      <Divider />

      {/* 风险评估 */}
      <Row label="Risk Level">
        <Text>
          <Bold>{insights.risk.level.toUpperCase()}</Bold> (Score:{" "}
          {insights.risk.score}/100)
        </Text>
      </Row>

      {/* 风险原因 */}
      {insights.risk.reasons.length > 0 && (
        <Box>
          <Heading>Risk Factors</Heading>
          {insights.risk.reasons.map((reason, i) => (
            <Text key={`reason-${i}`}>• {reason}</Text>
          ))}
        </Box>
      )}

      <Divider />

      {/* 关键参数 */}
      {insights.highlights.length > 0 && (
        <Box>
          <Heading>Key Parameters</Heading>
          {insights.highlights.map((h, i) => (
            <Row key={`highlight-${i}`} label={h.label}>
              {h.type === "address"
                ? renderAddressOrText(h.value)
                : h.type === "amount"
                ? <Copyable value={h.value} />
                : <Text>{h.value}</Text>}
            </Row>
          ))}
        </Box>
      )}

      {/* 参与者 */}
      {insights.actors.length > 0 && (
        <Box>
          <Divider />
          <Heading>Participants</Heading>
          {insights.actors.map((actor, i) => (
            <Row key={`actor-${i}`} label={actor.role}>
              {renderAddressOrText(actor.address)}
            </Row>
          ))}
        </Box>
      )}
    </Box>
  );
}

/**
 * 渲染本地分析结果 (后端不可用时的回退)
 */
export function renderLocalInsights(
  insights: LocalAnalysisResult
): OnSignatureResponse {
  const riskIcon = getRiskIcon(insights.basicRisk);

  const content = (
    <Box>
      <Heading>
        {riskIcon} Signature Analysis
      </Heading>

      <Divider />

      {/* 签名类型 */}
      <Row label="Type">
        <Text>{formatSignatureType(insights.signatureType)}</Text>
      </Row>

      {/* 协议 */}
      {insights.protocol && (
        <Row label="Protocol">
          <Text>{insights.protocol}</Text>
        </Row>
      )}

      {/* 风险等级 */}
      <Row label="Risk Level">
        <Text>
          <Bold>{insights.basicRisk.toUpperCase()}</Bold>
        </Text>
      </Row>

      {/* 警告 */}
      {insights.warnings.length > 0 && (
        <Box>
          <Divider />
          <Heading>Warnings</Heading>
          {insights.warnings.map((warning, i) => (
            <Text key={`warning-${i}`}>⚠️ {warning}</Text>
          ))}
        </Box>
      )}

      {/* 关键字段 */}
      {Object.keys(insights.fields).length > 0 && (
        <Box>
          <Divider />
          <Heading>Details</Heading>
          {Object.entries(insights.fields)
            .slice(0, 5) // 限制显示数量
            .map(([key, value], i) => (
              <Row key={`field-${i}`} label={formatFieldLabel(key)}>
                <Text>{formatFieldValue(value)}</Text>
              </Row>
            ))}
        </Box>
      )}

      <Divider />
      <Text>
        Note: Advanced analysis unavailable. Results are based on local analysis
        only.
      </Text>
    </Box>
  );

  return {
    content,
    severity: mapRiskToSeverity(insights.basicRisk),
  };
}

/**
 * 渲染本地交易分析结果
 */
export function renderLocalTransactionInsights(
  insights: LocalAnalysisResult
): OnTransactionResponse {
  const riskIcon = getRiskIcon(insights.basicRisk);

  const content = (
    <Box>
      <Heading>
        {riskIcon} Transaction Analysis
      </Heading>

      <Divider />

      {/* 风险等级 */}
      <Row label="Risk Level">
        <Text>
          <Bold>{insights.basicRisk.toUpperCase()}</Bold>
        </Text>
      </Row>

      {/* 警告 */}
      {insights.warnings.length > 0 && (
        <Box>
          <Divider />
          <Heading>Warnings</Heading>
          {insights.warnings.map((warning, i) => (
            <Text key={`warning-${i}`}>⚠️ {warning}</Text>
          ))}
        </Box>
      )}

      {/* 关键字段 */}
      {Object.keys(insights.fields).length > 0 && (
        <Box>
          <Divider />
          <Heading>Details</Heading>
          {Object.entries(insights.fields)
            .slice(0, 5)
            .map(([key, value], i) => (
              <Row key={`field-${i}`} label={formatFieldLabel(key)}>
                <Text>{formatFieldValue(value)}</Text>
              </Row>
            ))}
        </Box>
      )}

      <Divider />
      <Text>
        Note: Advanced analysis unavailable. Results are based on local analysis
        only.
      </Text>
    </Box>
  );

  return {
    content,
    severity: mapRiskToSeverity(insights.basicRisk),
  };
}

/**
 * 渲染错误信息
 */
export function renderError(message: string) {
  return (
    <Box>
      <Heading>⚠️ Analysis Error</Heading>
      <Divider />
      <Text>{message}</Text>
      <Text>Please review the transaction details carefully before signing.</Text>
    </Box>
  );
}

/**
 * 获取风险等级对应的图标
 */
function getRiskIcon(level: RiskLevel): string {
  switch (level) {
    case "critical":
      return "🚨";
    case "high":
      return "⛔";
    case "medium":
      return "⚠️";
    case "low":
      return "ℹ️";
    case "safe":
      return "✅";
    default:
      return "❓";
  }
}

/**
 * 获取风险等级对应的颜色 (用于将来的样式扩展)
 */
function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case "critical":
      return "#FF0000";
    case "high":
      return "#FF4444";
    case "medium":
      return "#FFA500";
    case "low":
      return "#4CAF50";
    case "safe":
      return "#00FF00";
    default:
      return "#888888";
  }
}

/**
 * 格式化签名类型
 */
function formatSignatureType(type: string): string {
  const typeNames: Record<string, string> = {
    eth_sign: "Raw Signature (Dangerous)",
    personal_sign: "Personal Message",
    eth_signTypedData: "Typed Data v1",
    eth_signTypedData_v1: "Typed Data v1",
    eth_signTypedData_v3: "Typed Data v3",
    eth_signTypedData_v4: "Typed Data v4",
    unknown: "Unknown",
  };
  return typeNames[type] || type;
}

/**
 * 格式化字段标签
 */
function formatFieldLabel(key: string): string {
  // 移除前缀并转换为可读格式
  const cleanKey = key.replace(/^(domain\.|message\.)/, "");
  return cleanKey
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
}

/**
 * 格式化字段值
 */
function formatFieldValue(value: unknown): string {
  // 处理 null 和 undefined
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "string") {
    // 地址缩短
    if (value.match(/^0x[a-fA-F0-9]{40}$/)) {
      return `${value.slice(0, 6)}...${value.slice(-4)}`;
    }
    // 大数字缩短
    if (value.length > 30) {
      return `${value.slice(0, 20)}...`;
    }
    return value;
  }

  if (typeof value === "number") {
    return value.toString();
  }

  if (typeof value === "bigint") {
    return value.toString();
  }

  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }

  if (Array.isArray(value)) {
    return `[${value.length} items]`;
  }

  if (typeof value === "object") {
    try {
      const str = JSON.stringify(value);
      if (str.length > 50) {
        return str.slice(0, 47) + "...";
      }
      return str;
    } catch {
      return "[Object]";
    }
  }

  return String(value);
}

/**
 * 渲染地址，非法时回退为文本
 */
function renderAddressOrText(value: string) {
  if (isHexAddress(value)) {
    return <Address address={value as `0x${string}`} />;
  }
  return <Text>{value}</Text>;
}

/**
 * 检查是否为有效的 0x 地址
 */
function isHexAddress(value: string): boolean {
  return /^0x[a-fA-F0-9]{40}$/.test(value);
}
