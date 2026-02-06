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
  if (llm.status === "error") {
    return {
      summary: {
        action: "analysis_unavailable",
        description: "Unable to complete mandatory safety analysis. Please retry.",
        protocol: enriched.inferredProtocol,
        confidence: 0,
      },
      risk: {
        level: "critical",
        score: 100,
        reasons: [
          "LLM reasoning failed",
          llm.failureReason ?? "analysis_unavailable",
        ],
        signals: [
          {
            key: "analysis_unavailable",
            weight: 100,
            source: "policy",
            reason: "Fail-closed policy: block when analysis cannot complete",
          },
        ],
      },
      decision: {
        value: "block",
        policyReason: "analysis_unavailable",
      },
      entities: {
        actors: enriched.actors,
        assets: enriched.assets,
        contracts: enriched.contracts,
      },
      highlights: enriched.highlights,
      llm: {
        model: "unavailable",
        latencyMs: llm.latencyMs,
        promptVersion: "reasoning-v2",
        status: "error",
      },
    };
  }

  const knowledge = getKnowledge();
  const rule = knowledge.riskRules;

  const base = rule.baseScoreByMethod[enriched.request.method] ?? 30;
  const signals = mergeSignals(enriched.inferredSignals, llm.output.riskSignals);

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

  return {
    summary: {
      action: llm.output.action || enriched.inferredAction,
      description: llm.output.description,
      protocol: llm.output.protocol ?? enriched.inferredProtocol,
      confidence: llm.output.confidence,
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
      model: "provider",
      latencyMs: llm.latencyMs,
      promptVersion: "reasoning-v2",
      status: "ok",
    },
  };
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
