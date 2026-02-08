import { getKnowledge } from "@sd/core-knowledge";
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
  const knowledge = getKnowledge();
  const rule = knowledge.riskRules;
  const llmFailed = llm.status === "error";

  // Always run knowledge-based scoring, even when LLM is unavailable.
  const base = rule.baseScoreByMethod[enriched.request.method] ?? 30;
  const signals = llmFailed
    ? [...enriched.inferredSignals]
    : mergeSignals(enriched.inferredSignals, llm.output.riskSignals);

  // When LLM failed, add a policy signal so the user knows analysis was degraded.
  if (llmFailed) {
    signals.push({
      key: "llm_unavailable",
      weight: 0,
      source: "policy",
      reason: "LLM reasoning unavailable — analysis based on knowledge base only",
    });
  }

  let score = base;
  const reasons: string[] = [];

  for (const signal of signals) {
    const weight = rule.signalWeights[signal.key] ?? 0;
    signal.weight = weight;
    score += weight;
    reasons.push(signal.reason);
  }

  const normalizedScore = clamp(score, 0, 100);
  const level = determineLevel(normalizedScore, rule.thresholds);

  let decision: "allow" | "block" = "allow";
  let policyReason = "policy_allow";

  if (level === "high" || level === "critical") {
    decision = "block";
    policyReason = "high_risk";
  }

  // Use LLM output when available, fall back to enriched (knowledge-base) data.
  const action = llmFailed
    ? enriched.inferredAction
    : llm.output.action || enriched.inferredAction;

  const description = llmFailed
    ? buildFallbackDescription(enriched)
    : llm.output.description;

  const protocol = llmFailed
    ? enriched.inferredProtocol
    : llm.output.protocol ?? enriched.inferredProtocol;

  const confidence = llmFailed ? 0 : llm.output.confidence;

  return {
    summary: {
      action,
      description,
      protocol,
      confidence,
    },
    risk: {
      level,
      score: normalizedScore,
      reasons: dedupeReasons(reasons),
      signals,
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
      model: llmFailed ? "unavailable" : llm.model,
      latencyMs: llm.latencyMs,
      promptVersion: llm.promptVersion,
      status: llm.status,
    },
  };
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

  parts.push("(LLM unavailable, knowledge-base analysis only)");

  return parts.join(". ");
}

function mergeSignals(
  knowledgeSignals: RiskSignal[],
  llmSignals: LlmReasoningResponse["riskSignals"]
): RiskSignal[] {
  const fromKnowledge: RiskSignal[] = knowledgeSignals.map((signal) => ({
    ...signal,
    source: "knowledge",
  }));

  const fromLlm: RiskSignal[] = llmSignals.map((signal) => ({
    key:
      signal.severity === "critical"
        ? "llm_critical_risk"
        : signal.severity === "high"
          ? "llm_high_risk"
          : signal.key,
    weight: 0,
    source: "llm",
    reason: signal.reason,
  }));

  return dedupeSignals([...fromKnowledge, ...fromLlm]);
}

function determineLevel(
  score: number,
  thresholds: { medium: number; high: number; critical: number }
): "low" | "medium" | "high" | "critical" {
  if (score >= thresholds.critical) {
    return "critical";
  }
  if (score >= thresholds.high) {
    return "high";
  }
  if (score >= thresholds.medium) {
    return "medium";
  }
  return "low";
}

function dedupeSignals(signals: RiskSignal[]): RiskSignal[] {
  const seen = new Set<string>();
  return signals.filter((signal) => {
    const key = `${signal.source}:${signal.key}:${signal.reason}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function dedupeReasons(reasons: string[]): string[] {
  const seen = new Set<string>();
  const output: string[] = [];
  for (const reason of reasons) {
    if (!reason || seen.has(reason)) {
      continue;
    }
    seen.add(reason);
    output.push(reason);
  }

  if (output.length === 0) {
    output.push("No explicit risk signals were triggered");
  }

  return output.slice(0, 20);
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
