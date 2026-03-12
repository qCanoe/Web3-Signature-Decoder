import { z } from "zod";

export const AnalyzeKindSchema = z.enum(["signature", "transaction"]);
export const AnalyzeMethodSchema = z.enum([
  "eth_sign",
  "personal_sign",
  "eth_signTypedData_v4",
  "eth_sendTransaction",
]);

export const AnalyzeContextSchema = z.object({
  origin: z.string().url().optional(),
  chainId: z.string().optional(),
  walletAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/).optional(),
  timestamp: z.number().int().positive().optional(),
});

export const AnalyzeRequestV2Schema = z
  .object({
    kind: AnalyzeKindSchema,
    method: AnalyzeMethodSchema,
    payload: z.unknown(),
    context: AnalyzeContextSchema.optional().default({}),
  })
  .superRefine((value, ctx) => {
    if (value.kind === "transaction" && value.method !== "eth_sendTransaction") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "transaction kind must use eth_sendTransaction",
      });
    }

    if (value.kind === "signature" && value.method === "eth_sendTransaction") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "signature kind cannot use eth_sendTransaction",
      });
    }
  });

export const RiskLevelSchema = z.enum(["low", "medium", "high", "critical"]);
export const DecisionSchema = z.enum(["allow", "block", "error"]);

export const RiskSignalSchema = z.object({
  key: z.string().min(1),
  weight: z.number().int(),
  source: z.enum(["knowledge", "llm", "policy"]),
  reason: z.string().min(1),
});

export const SummarySchema = z.object({
  action: z.string().min(1),
  description: z.string().min(1),
  protocol: z.string().optional(),
  confidence: z.number().min(0).max(1),
});

export const EntityActorSchema = z.object({
  role: z.string().min(1),
  address: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
});

export const EntityAssetSchema = z.object({
  symbol: z.string().min(1),
  amount: z.string().min(1),
  standard: z.enum(["native", "erc20", "erc721", "unknown"]),
});

export const EntityContractSchema = z.object({
  role: z.string().min(1),
  address: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
  label: z.string().optional(),
});

export const HighlightSchema = z.object({
  label: z.string().min(1),
  value: z.string().min(1),
  type: z.enum(["text", "address", "amount", "token"]).default("text"),
});

export const LlmMetaSchema = z.object({
  model: z.string().min(1),
  latencyMs: z.number().int().nonnegative(),
  promptVersion: z.string().min(1),
  status: z.enum(["ok", "error"]),
});

export const AnalysisResultV2Schema = z.object({
  summary: SummarySchema,
  risk: z.object({
    level: RiskLevelSchema,
    score: z.number().int().min(0).max(100),
    reasons: z.array(z.string().min(1)).max(20),
    signals: z.array(RiskSignalSchema),
  }),
  decision: z.object({
    value: DecisionSchema,
    policyReason: z.string().min(1),
  }),
  entities: z.object({
    actors: z.array(EntityActorSchema),
    assets: z.array(EntityAssetSchema),
    contracts: z.array(EntityContractSchema),
  }),
  highlights: z.array(HighlightSchema),
  llm: LlmMetaSchema,
});

const LlmRiskSignalSchema = z.object({
  key: z.string().min(1),
  reason: z.string().min(1),
  severity: z.enum(["low", "medium", "high", "critical"]),
});

const LlmDetectSchema = z.object({
  action: z.string().min(1),
  protocol: z.string().optional(),
  riskSignals: z.array(LlmRiskSignalSchema).default([]),
  confidence: z.number().min(0).max(1).optional(),
});

const LlmExplainSchema = z.object({
  description: z.string().min(1).max(160),
});

export const LlmReasoningResponseSchema = z
  .object({
    // Backward-compatible fields used by existing callers.
    action: z.string().min(1).optional(),
    description: z.string().min(1).max(160).optional(),
    confidence: z.number().min(0).max(1).optional(),
    protocol: z.string().optional(),
    riskSignals: z.array(LlmRiskSignalSchema).optional(),
    // New two-stage output fields.
    detect: LlmDetectSchema.optional(),
    explain: LlmExplainSchema.optional(),
    // AI-driven judgment fields — primary decision outputs.
    riskLevel: z.enum(["low", "medium", "high", "critical"]).optional(),
    decision: z.enum(["allow", "block"]).optional(),
    reasoning: z.string().min(1).optional(),
  })
  .superRefine((value, ctx) => {
    const hasAction = Boolean(value.action ?? value.detect?.action);
    const hasDescription = Boolean(value.description ?? value.explain?.description);
    const hasSignals = Array.isArray(value.riskSignals) || Array.isArray(value.detect?.riskSignals);

    if (!hasAction) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "LLM response must include action or detect.action",
      });
    }
    if (!hasDescription) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "LLM response must include description or explain.description",
      });
    }
    if (!hasSignals) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "LLM response must include riskSignals or detect.riskSignals",
      });
    }
  })
  .transform((value) => {
    const detect = value.detect
      ? {
          action: value.detect.action,
          riskSignals: value.detect.riskSignals,
          ...(value.detect.protocol ? { protocol: value.detect.protocol } : {}),
          ...(value.detect.confidence !== undefined
            ? { confidence: value.detect.confidence }
            : {}),
        }
      : undefined;
    const explain = value.explain
      ? {
          description: value.explain.description,
        }
      : undefined;

    return {
      action: value.action ?? detect?.action ?? "unknown_operation",
      description: value.description ?? explain?.description ?? "LLM description unavailable",
      confidence: value.confidence ?? detect?.confidence ?? 0.5,
      riskSignals: value.riskSignals ?? detect?.riskSignals ?? [],
      ...(value.protocol ?? detect?.protocol
        ? { protocol: value.protocol ?? detect?.protocol }
        : {}),
      ...(detect ? { detect } : {}),
      ...(explain ? { explain } : {}),
      ...(value.riskLevel !== undefined ? { riskLevel: value.riskLevel } : {}),
      ...(value.decision !== undefined ? { decision: value.decision } : {}),
      ...(value.reasoning !== undefined ? { reasoning: value.reasoning } : {}),
    };
  });

const VersionSchema = z.literal("v2");

export const SelectorsKnowledgeSchema = z.object({
  version: VersionSchema,
  selectors: z.record(
    z.object({
      signature: z.string().min(1),
      action: z.string().min(1),
      tags: z.array(z.string()),
    })
  ),
});

export const Eip712TypesKnowledgeSchema = z.object({
  version: VersionSchema,
  types: z.record(
    z.object({
      action: z.string().min(1),
      tags: z.array(z.string()),
    })
  ),
});

export const ProtocolsKnowledgeSchema = z.object({
  version: VersionSchema,
  protocols: z.array(
    z.object({
      name: z.string().min(1),
      domainPatterns: z.array(z.string().min(1)),
      contractPatterns: z.array(z.string().min(1)).optional().default([]),
    })
  ),
});

export const RiskRulesKnowledgeSchema = z.object({
  version: VersionSchema,
  baseScoreByMethod: z.record(z.number().int().min(0).max(100)),
  // Deprecated: weight-based scoring fields are no longer used for decision-making.
  signalWeights: z.record(z.number().int().min(-100).max(100)).optional(),
  llmSourceWeightCap: z.number().int().min(0).max(100).optional(),
  thresholds: z
    .object({
      medium: z.number().int().min(0).max(100),
      high: z.number().int().min(0).max(100),
      critical: z.number().int().min(0).max(100),
    })
    .optional(),
});

export const MessagePatternsKnowledgeSchema = z.object({
  version: VersionSchema,
  patterns: z.array(
    z.object({
      key: z.string().min(1),
      regex: z.string().min(1),
      signal: z.string().min(1),
      reason: z.string().min(1),
    })
  ),
});

const ThreatIntelEntrySchema = z.object({
  category: z.string().min(1),
  severity: RiskLevelSchema,
  reason: z.string().min(1),
});

const ThreatIntelAddressKeySchema = z.string().regex(/^0x[a-fA-F0-9]{40}$/);
const ThreatIntelDomainKeySchema = z
  .string()
  .regex(/^(?=.{1,253}$)(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}$/);

export const MaliciousAddressesKnowledgeSchema = z.object({
  version: VersionSchema,
  addresses: z.record(ThreatIntelAddressKeySchema, ThreatIntelEntrySchema),
});

export const MaliciousDomainsKnowledgeSchema = z.object({
  version: VersionSchema,
  domains: z.record(ThreatIntelDomainKeySchema, ThreatIntelEntrySchema),
});

const ChainRiskFeatureKnowledgeSchema = z.object({
  key: z.string().min(1),
  signal: z.string().min(1),
  reason: z.string().min(1),
  selectors: z.array(z.string().regex(/^0x[a-fA-F0-9]{8}$/)).default([]),
  primaryTypes: z.array(z.string().min(1)).default([]),
  actionKeywords: z.array(z.string().min(1)).default([]),
});

export const ChainsKnowledgeSchema = z.object({
  version: VersionSchema,
  chains: z.record(
    z.object({
      name: z.string().min(1),
      features: z.array(ChainRiskFeatureKnowledgeSchema).default([]),
    })
  ),
});

export type AnalyzeRequestV2 = z.infer<typeof AnalyzeRequestV2Schema>;
export type AnalysisResultV2 = z.infer<typeof AnalysisResultV2Schema>;
export type RiskSignal = z.infer<typeof RiskSignalSchema>;
export type LlmReasoningResponse = z.infer<typeof LlmReasoningResponseSchema>;
export type SelectorsKnowledge = z.infer<typeof SelectorsKnowledgeSchema>;
export type Eip712TypesKnowledge = z.infer<typeof Eip712TypesKnowledgeSchema>;
export type ProtocolsKnowledge = z.infer<typeof ProtocolsKnowledgeSchema>;
export type RiskRulesKnowledge = z.infer<typeof RiskRulesKnowledgeSchema>;
export type MessagePatternsKnowledge = z.infer<typeof MessagePatternsKnowledgeSchema>;
export type MaliciousAddressesKnowledge = z.infer<typeof MaliciousAddressesKnowledgeSchema>;
export type MaliciousDomainsKnowledge = z.infer<typeof MaliciousDomainsKnowledgeSchema>;
export type ChainsKnowledge = z.infer<typeof ChainsKnowledgeSchema>;

export function validateAnalyzeRequest(input: unknown): AnalyzeRequestV2 {
  return AnalyzeRequestV2Schema.parse(input);
}

export function validateAnalysisResult(input: unknown): AnalysisResultV2 {
  return AnalysisResultV2Schema.parse(input);
}
