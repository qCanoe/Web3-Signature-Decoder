import type {
  AnalysisResultV2,
  RiskSignal,
  LlmReasoningResponse,
} from "@sd/core-schema";
import type { EnrichedRequest, LlmStageResult } from "./types";

export interface RiskDecisionInput {
  enriched: EnrichedRequest;
  llm: LlmStageResult;
}

export function buildAnalysisResult({ enriched, llm }: RiskDecisionInput): AnalysisResultV2 {
  const llmFailed = llm.status === "error";

  if (llmFailed) {
    return buildErrorResult(enriched, llm);
  }

  const llmOutput = llm.output;

  // AI is the primary decision-maker, but hard knowledge signals (e.g. infinite_allowance,
  // malicious address/domain) enforce a minimum "high" floor that the LLM cannot override.
  const llmLevel = llmOutput.riskLevel ?? deriveRiskLevelFromSignals(enriched, llmOutput);
  const level = applyPolicyFloor(llmLevel, enriched);
  const decision = level === "high" || level === "critical"
    ? "block"
    : (llmOutput.decision ?? "allow");
  const score = riskLevelToScore(level);

  const signals = buildSignals(enriched, llmOutput);
  const reasons = buildReasons(llmOutput, signals);

  const action = llmOutput.action || enriched.inferredAction;
  const description = llmOutput.description;
  const protocol = llmOutput.protocol ?? enriched.inferredProtocol;
  const confidence = llmOutput.confidence;

  return {
    summary: {
      action,
      description,
      protocol,
      confidence,
    },
    risk: {
      level,
      score,
      reasons,
      signals,
    },
    decision: {
      value: decision,
      policyReason: decision === "block" ? "high_risk" : "policy_allow",
    },
    entities: {
      actors: enriched.actors,
      assets: enriched.assets,
      contracts: enriched.contracts,
    },
    highlights: enriched.highlights,
    llm: {
      model: llm.model,
      latencyMs: llm.latencyMs,
      promptVersion: llm.promptVersion,
      status: llm.status,
    },
  };
}

// Knowledge signals that are severe enough to force a block even without LLM.
const CRITICAL_KNOWLEDGE_KEYS = new Set([
  "infinite_allowance",
  "malicious_address_hit",
  "malicious_domain_hit",
  "phishing_domain",
]);

// Knowledge signals that must floor the risk level at "high" even when LLM succeeds.
// The LLM can raise the level further (e.g. to "critical") but cannot lower it below "high".
const FLOOR_HIGH_RISK_KEYS = new Set([
  "infinite_allowance",
  "malicious_address_hit",
  "malicious_domain_hit",
  "phishing_domain",
]);

const RISK_LEVEL_ORDER: Record<string, number> = {
  low: 0, medium: 1, high: 2, critical: 3,
};

function applyPolicyFloor(
  level: "low" | "medium" | "high" | "critical",
  enriched: EnrichedRequest
): "low" | "medium" | "high" | "critical" {
  const hasFloorSignal = enriched.inferredSignals.some((s) =>
    FLOOR_HIGH_RISK_KEYS.has(s.key)
  );
  if (!hasFloorSignal) return level;
  return RISK_LEVEL_ORDER[level] >= RISK_LEVEL_ORDER["high"] ? level : "high";
}

function buildErrorResult(enriched: EnrichedRequest, llm: LlmStageResult): AnalysisResultV2 {
  const hasCriticalKnowledge = enriched.inferredSignals.some((s) =>
    CRITICAL_KNOWLEDGE_KEYS.has(s.key)
  );

  // Even without LLM, deterministic threat signals (e.g. infinite_allowance,
  // malicious address/domain hit) are sufficient to block.
  const decision = hasCriticalKnowledge ? "block" : "error";
  const level = hasCriticalKnowledge ? "high" : "medium";
  const score = hasCriticalKnowledge ? 75 : 50;
  const policyReason = hasCriticalKnowledge ? "high_risk" : "analysis_unavailable";

  const reasons = hasCriticalKnowledge
    ? [
        "AI analysis unavailable — decision based on knowledge signals only",
        ...enriched.inferredSignals
          .filter((s) => CRITICAL_KNOWLEDGE_KEYS.has(s.key))
          .map((s) => s.reason),
      ]
    : ["AI analysis unavailable — risk level could not be determined"];

  return {
    summary: {
      action: enriched.inferredAction,
      description: buildFallbackDescription(enriched),
      protocol: enriched.inferredProtocol,
      confidence: 0,
    },
    risk: {
      level,
      score,
      reasons,
      signals: [
        {
          key: "llm_unavailable",
          weight: 0,
          source: "policy",
          reason: "LLM reasoning unavailable — cannot assess risk",
        },
        ...enriched.inferredSignals,
      ],
    },
    decision: {
      value: decision,
      policyReason,
    },
    entities: {
      actors: enriched.actors,
      assets: enriched.assets,
      contracts: enriched.contracts,
    },
    highlights: enriched.highlights,
    llm: {
      model: llm.model,
      latencyMs: llm.latencyMs,
      promptVersion: llm.promptVersion,
      status: llm.status,
    },
  };
}

/**
 * Fallback risk level derivation when LLM did not return a riskLevel.
 * Used only as a safety net — the LLM should always return riskLevel with the new prompt.
 */
function deriveRiskLevelFromSignals(
  enriched: EnrichedRequest,
  llmOutput: LlmReasoningResponse
): "low" | "medium" | "high" | "critical" {
  const hasThreatIntel =
    enriched.maliciousAddressHits.length > 0 || enriched.maliciousDomainHits.length > 0;

  if (hasThreatIntel) {
    return "critical";
  }

  const allSignals = [
    ...llmOutput.riskSignals,
    ...(llmOutput.detect?.riskSignals ?? []),
  ];

  const hasCritical = allSignals.some((s) => s.severity === "critical");
  const hasHigh = allSignals.some((s) => s.severity === "high");

  if (hasCritical) return "critical";
  if (hasHigh) return "high";
  if (allSignals.length > 0) return "medium";
  return "low";
}

function riskLevelToScore(level: "low" | "medium" | "high" | "critical"): number {
  switch (level) {
    case "critical": return 95;
    case "high": return 75;
    case "medium": return 50;
    case "low": return 15;
  }
}

function buildSignals(enriched: EnrichedRequest, llmOutput: LlmReasoningResponse): RiskSignal[] {
  const knowledgeSignals: RiskSignal[] = enriched.inferredSignals.map((s) => ({
    ...s,
    source: "knowledge" as const,
  }));

  // Keys already covered by knowledge — skip LLM signals with the same key to avoid duplication.
  const knowledgeKeys = new Set(knowledgeSignals.map((s) => s.key));

  const llmSignals: RiskSignal[] = llmOutput.riskSignals
    .filter((s) => !knowledgeKeys.has(s.key))
    .map((s) => ({
      key: s.key,
      weight: 0,
      source: "llm" as const,
      reason: s.reason,
    }));

  return [...knowledgeSignals, ...llmSignals];
}

function buildReasons(llmOutput: LlmReasoningResponse, signals: RiskSignal[]): string[] {
  const reasons: string[] = [];

  if (llmOutput.reasoning) {
    reasons.push(llmOutput.reasoning);
  }

  for (const signal of signals) {
    if (signal.reason && !reasons.includes(signal.reason)) {
      reasons.push(signal.reason);
    }
  }

  if (reasons.length === 0) {
    reasons.push("No explicit risk signals were identified");
  }

  return reasons.slice(0, 20);
}

function buildFallbackDescription(enriched: EnrichedRequest): string {
  const method = enriched.request.method;
  const protocol = enriched.inferredProtocol;
  const action = enriched.inferredAction;

  const parts: string[] = [];

  if (action !== "unknown_operation") {
    parts.push(`Detected: ${action}`);
  } else {
    parts.push(`Method: ${method}`);
  }

  if (protocol) {
    parts.push(`Protocol: ${protocol}`);
  }

  parts.push("(AI analysis unavailable)");

  return parts.join(". ");
}
