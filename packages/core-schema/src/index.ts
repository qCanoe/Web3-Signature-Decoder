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
export const DecisionSchema = z.enum(["allow", "block"]);

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

export const LlmReasoningResponseSchema = z.object({
  action: z.string().min(1),
  description: z.string().min(1),
  confidence: z.number().min(0).max(1),
  protocol: z.string().optional(),
  riskSignals: z.array(
    z.object({
      key: z.string().min(1),
      reason: z.string().min(1),
      severity: z.enum(["low", "medium", "high", "critical"]),
    })
  ),
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
  signalWeights: z.record(z.number().int().min(-100).max(100)),
  thresholds: z.object({
    medium: z.number().int().min(0).max(100),
    high: z.number().int().min(0).max(100),
    critical: z.number().int().min(0).max(100),
  }),
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

export type AnalyzeRequestV2 = z.infer<typeof AnalyzeRequestV2Schema>;
export type AnalysisResultV2 = z.infer<typeof AnalysisResultV2Schema>;
export type RiskSignal = z.infer<typeof RiskSignalSchema>;
export type LlmReasoningResponse = z.infer<typeof LlmReasoningResponseSchema>;
export type SelectorsKnowledge = z.infer<typeof SelectorsKnowledgeSchema>;
export type Eip712TypesKnowledge = z.infer<typeof Eip712TypesKnowledgeSchema>;
export type ProtocolsKnowledge = z.infer<typeof ProtocolsKnowledgeSchema>;
export type RiskRulesKnowledge = z.infer<typeof RiskRulesKnowledgeSchema>;
export type MessagePatternsKnowledge = z.infer<typeof MessagePatternsKnowledgeSchema>;

export function validateAnalyzeRequest(input: unknown): AnalyzeRequestV2 {
  return AnalyzeRequestV2Schema.parse(input);
}

export function validateAnalysisResult(input: unknown): AnalysisResultV2 {
  return AnalysisResultV2Schema.parse(input);
}
