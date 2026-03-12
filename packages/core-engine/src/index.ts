import {
  AnalysisResultV2Schema,
  type AnalysisResultV2,
  type AnalyzeRequestV2,
} from "@sd/core-schema";
import {
  type LlmReasoningInput,
  type ReasoningProvider,
} from "@sd/core-llm";
import { normalizeRequest } from "./normalize";
import { parseRequest } from "./parse";
import { enrichParsedRequest } from "./enrich";
import { buildAnalysisResult } from "./risk";
import type { LlmStageResult } from "./types";

export interface CoreEngineOptions {
  llmProvider: ReasoningProvider;
  now?: () => number;
}

export class CoreEngine {
  private readonly llmProvider: ReasoningProvider;
  private readonly now: () => number;

  constructor(options: CoreEngineOptions) {
    this.llmProvider = options.llmProvider;
    this.now = options.now ?? (() => Date.now());
  }

  async analyze(input: unknown): Promise<AnalysisResultV2> {
    const normalized = normalizeRequest(input);
    const parsed = parseRequest(normalized);
    const enriched = enrichParsedRequest(parsed);
    const llm = await this.runLlmStage(enriched.request, enriched);

    const result = buildAnalysisResult({
      enriched,
      llm,
    });

    result.llm.model = llm.model;
    result.llm.promptVersion = llm.promptVersion;

    return AnalysisResultV2Schema.parse(result);
  }

  private async runLlmStage(
    request: AnalyzeRequestV2,
    enriched: ReturnType<typeof enrichParsedRequest>
  ): Promise<LlmStageResult> {
    const start = this.now();
    const reasoningInput: LlmReasoningInput = {
      kind: request.kind,
      method: request.method,
      parsed: {
        selector: enriched.selector,
        primaryType: enriched.primaryType,
        domainName: enriched.domainName,
        message: enriched.message,
        value: enriched.value,
        // For eth_signTypedData_v4: the decoded EIP-712 message object so the AI can
        // inspect actual parameters (e.g. token amount, spender, deadline).
        typedDataMessage: enriched.typedDataMessage,
      },
      enriched: {
        inferredAction: enriched.inferredAction,
        inferredProtocol: enriched.inferredProtocol,
        inferredSignals: enriched.inferredSignals,
        maliciousAddressHits: enriched.maliciousAddressHits,
        maliciousDomainHits: enriched.maliciousDomainHits,
        chainFeatureHits: enriched.chainFeatureHits,
      },
      context: {
        // Omit localhost/loopback origins — they indicate a local dev/test environment
        // and must not be treated as a risk signal by the LLM.
        origin: isLocalOrigin(request.context?.origin) ? undefined : request.context?.origin,
        originDomain: isLocalOrigin(request.context?.origin) ? undefined : extractOriginDomain(request.context?.origin),
        chainId: request.context?.chainId,
        walletAddress: request.context?.walletAddress,
        contractAddresses: enriched.contracts.map((entry) => entry.address),
        timestamp: request.context?.timestamp,
      },
    };

    try {
      const output = await this.llmProvider.reason(reasoningInput);
      return {
        output,
        latencyMs: this.now() - start,
        status: "ok",
        model: this.llmProvider.model,
        promptVersion: this.llmProvider.promptVersion,
      };
    } catch (error: unknown) {
      const reason =
        error instanceof Error ? error.message : "analysis_unavailable";

      return {
        output: {
          action: enriched.inferredAction,
          description: "LLM reasoning unavailable",
          confidence: 0,
          protocol: enriched.inferredProtocol,
          riskSignals: [],
          detect: {
            action: enriched.inferredAction,
            protocol: enriched.inferredProtocol,
            confidence: 0,
            riskSignals: [],
          },
          explain: {
            description: "LLM reasoning unavailable",
          },
        },
        latencyMs: this.now() - start,
        status: "error",
        failureReason: reason,
        model: this.llmProvider.model,
        promptVersion: this.llmProvider.promptVersion,
      };
    }
  }
}

export function createCoreEngine(options: CoreEngineOptions): CoreEngine {
  return new CoreEngine(options);
}

export { normalizeRequest } from "./normalize";
export { parseRequest } from "./parse";
export { enrichParsedRequest } from "./enrich";

function extractOriginDomain(origin?: string): string | undefined {
  if (!origin) {
    return undefined;
  }
  try {
    return new URL(origin).hostname.toLowerCase();
  } catch {
    return undefined;
  }
}

/** Returns true for localhost / loopback origins used during local development/testing. */
function isLocalOrigin(origin?: string): boolean {
  if (!origin) return false;
  try {
    const { hostname } = new URL(origin);
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
  } catch {
    return false;
  }
}
