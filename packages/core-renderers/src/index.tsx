import {
  type OnSignatureResponse,
  type OnTransactionResponse,
  SeverityLevel,
} from "@metamask/snaps-sdk";
import {
  Banner,
  Box,
  Divider,
  Heading,
  Row,
  Text,
} from "@metamask/snaps-sdk/jsx";
import type { AnalysisResultV2 } from "@sd/core-schema";

// ─── Helpers ────────────────────────────────────────────────────────────────

/**
 * Converts an action string to a human-readable heading.
 * AI-generated phrases (contain spaces) are title-cased on the first letter only.
 * snake_case fallbacks are converted to Title Case.
 */
function formatHeading(action: string): string {
  if (action.includes(" ")) {
    return action.charAt(0).toUpperCase() + action.slice(1);
  }
  return action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const THREAT_INTEL_KEYS = new Set([
  "malicious_address_hit",
  "malicious_domain_hit",
  "phishing_domain",
]);

// Knowledge signals that are always worth surfacing to the user, regardless of AI riskLevel.
const ALWAYS_NOTABLE_KEYS = new Set([
  "infinite_allowance",
]);

const ALWAYS_NOTABLE_REASONS: Record<string, string> = {
  infinite_allowance: "Unlimited token approval — spender can transfer all your tokens at any time",
};

/**
 * Returns up to 4 risk factor strings to show in the Banner, in priority order:
 * 1. Always-notable knowledge signals (e.g. infinite_allowance) — deterministic, never filtered
 * 2. AI reasoning paragraph (first reason, if it reads like a sentence)
 * 3. LLM-sourced signal reasons
 * 4. Threat-intel signal reasons
 * Each entry is truncated to 80/120 characters.
 */
function getDisplayedRiskFactors(result: AnalysisResultV2): string[] {
  const items: string[] = [];

  // Always-notable knowledge signals come first — surface them even if AI downplayed them.
  for (const signal of result.risk.signals) {
    if (ALWAYS_NOTABLE_KEYS.has(signal.key)) {
      const text = signal.reason
        ? truncate(signal.reason, 80)
        : (ALWAYS_NOTABLE_REASONS[signal.key] ?? signal.key);
      if (!items.includes(text)) {
        items.push(text);
      }
    }
  }

  const firstReason = result.risk.reasons[0] ?? "";
  const isAiReasoning =
    firstReason.length > 20 &&
    firstReason !== "No explicit risk signals were identified" &&
    firstReason !== "AI analysis unavailable — risk level could not be determined";

  if (isAiReasoning) {
    const text = truncate(firstReason, 120);
    if (!items.includes(text)) {
      items.push(text);
    }
  }

  for (const signal of result.risk.signals) {
    if (signal.source === "llm" && signal.reason) {
      const entry = truncate(signal.reason, 80);
      if (!items.includes(entry)) {
        items.push(entry);
      }
    }
  }

  for (const signal of result.risk.signals) {
    if (THREAT_INTEL_KEYS.has(signal.key) && signal.reason) {
      const entry = truncate(signal.reason, 80);
      if (!items.includes(entry)) {
        items.push(entry);
      }
    }
  }

  return items.slice(0, 4);
}

/**
 * Returns true when a risk section should be shown to the user.
 * Applies when: risk level is non-low, LLM flagged signals, threat intel hit,
 * or an always-notable knowledge signal is present (e.g. infinite_allowance).
 */
function shouldShowRiskSection(result: AnalysisResultV2): boolean {
  if (result.risk.level !== "low") return true;
  if (result.risk.signals.some((s) => s.source === "llm")) return true;
  if (result.risk.signals.some((s) => THREAT_INTEL_KEYS.has(s.key))) return true;
  if (result.risk.signals.some((s) => ALWAYS_NOTABLE_KEYS.has(s.key))) return true;
  return false;
}

/**
 * Maps risk level to the Banner severity.
 * critical/high → danger (red)
 * medium/low    → warning (yellow)
 */
function getBannerSeverity(
  level: "low" | "medium" | "high" | "critical"
): "danger" | "warning" {
  return level === "critical" || level === "high" ? "danger" : "warning";
}

function truncate(value: string, max: number): string {
  return value.length <= max ? value : `${value.slice(0, max - 1)}…`;
}

// ─── Severity (MetaMask native indicator) ───────────────────────────────────

export function riskToSeverity(result: AnalysisResultV2): SeverityLevel | undefined {
  if (result.risk.level === "critical" || result.risk.level === "high") {
    return SeverityLevel.Critical;
  }
  return undefined;
}

// ─── Render ─────────────────────────────────────────────────────────────────

export function renderSnapAnalysis(result: AnalysisResultV2) {
  const heading = formatHeading(result.summary.action);
  const isError = result.decision.value === "error";
  const isBlock = result.decision.value === "block";
  const showRisk = shouldShowRiskSection(result);
  const riskFactors = getDisplayedRiskFactors(result);
  const bannerSeverity = getBannerSeverity(result.risk.level);

  return (
    <Box>
      <Heading>{heading}</Heading>
      <Text>{result.summary.description}</Text>

      {result.summary.protocol ? (
        <Box>
          <Divider />
          <Row label="Protocol">
            <Text>{result.summary.protocol}</Text>
          </Row>
        </Box>
      ) : null}

      {isError ? (
        <Box>
          <Divider />
          <Banner title="Analysis Unavailable" severity="warning">
            <Text>
              Risk analysis could not be completed. Review carefully before
              signing.
            </Text>
          </Banner>
        </Box>
      ) : isBlock ? (
        <Box>
          <Divider />
          <Banner title="This request should be blocked" severity="danger">
            {riskFactors.length > 0
              ? riskFactors.map((factor, index) => (
                  <Text key={`rf-${index}`}>{`• ${factor}`}</Text>
                ))
              : <Text>This request has been flagged as high risk.</Text>}
          </Banner>
        </Box>
      ) : showRisk && riskFactors.length > 0 ? (
        <Box>
          <Divider />
          <Banner title="Risk Factors" severity={bannerSeverity}>
            {riskFactors.map((factor, index) => (
              <Text key={`rf-${index}`}>{`• ${factor}`}</Text>
            ))}
          </Banner>
        </Box>
      ) : null}
    </Box>
  );
}

// ─── Response builders ───────────────────────────────────────────────────────

export function toSnapSignatureResponse(result: AnalysisResultV2): OnSignatureResponse {
  return {
    content: renderSnapAnalysis(result),
    // MetaMask Snaps currently only supports `critical` severity for signature
    // and transaction insights. Keep signatures explicit here so future changes
    // do not assume lower severities are available.
    severity: SeverityLevel.Critical,
  };
}

export function toSnapTransactionResponse(result: AnalysisResultV2): OnTransactionResponse {
  return {
    content: renderSnapAnalysis(result),
    severity: riskToSeverity(result),
  };
}
