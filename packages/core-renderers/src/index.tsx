import {
  type OnSignatureResponse,
  type OnTransactionResponse,
  SeverityLevel,
} from "@metamask/snaps-sdk";
import { Box, Bold, Divider, Heading, Row, Text } from "@metamask/snaps-sdk/jsx";
import type { AnalysisResultV2 } from "@sd/core-schema";

export function riskToSeverity(result: AnalysisResultV2): SeverityLevel | undefined {
  if (result.decision.value === "block") {
    return SeverityLevel.Critical;
  }

  if (result.risk.level === "critical" || result.risk.level === "high") {
    return SeverityLevel.Critical;
  }

  return undefined;
}

export function renderSnapAnalysis(result: AnalysisResultV2) {
  const blockLabel = result.decision.value === "block" ? "Blocked" : "Allowed";

  return (
    <Box>
      <Heading>{blockLabel}: {result.summary.action}</Heading>
      <Text>{result.summary.description}</Text>

      <Divider />

      <Row label="Risk">
        <Text>
          <Bold>{result.risk.level.toUpperCase()}</Bold> ({result.risk.score}/100)
        </Text>
      </Row>

      <Row label="Decision">
        <Text>{result.decision.value.toUpperCase()}</Text>
      </Row>

      {result.summary.protocol && (
        <Row label="Protocol">
          <Text>{result.summary.protocol}</Text>
        </Row>
      )}

      {result.risk.reasons.length > 0 && (
        <Box>
          <Divider />
          <Heading>Risk Factors</Heading>
          {result.risk.reasons.slice(0, 6).map((reason, index) => (
            <Text key={`reason-${index}`}>- {reason}</Text>
          ))}
        </Box>
      )}

      {result.highlights.length > 0 && (
        <Box>
          <Divider />
          <Heading>Highlights</Heading>
          {result.highlights.slice(0, 6).map((highlight, index) => (
            <Row key={`highlight-${index}`} label={highlight.label}>
              <Text>{highlight.value}</Text>
            </Row>
          ))}
        </Box>
      )}

      <Divider />
      <Row label="LLM">
        <Text>{result.llm.status} ({result.llm.model})</Text>
      </Row>
    </Box>
  );
}

export function toSnapSignatureResponse(result: AnalysisResultV2): OnSignatureResponse {
  return {
    content: renderSnapAnalysis(result),
    severity: riskToSeverity(result),
  };
}

export function toSnapTransactionResponse(result: AnalysisResultV2): OnTransactionResponse {
  return {
    content: renderSnapAnalysis(result),
    severity: riskToSeverity(result),
  };
}
