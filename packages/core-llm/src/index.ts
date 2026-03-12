import {
  LlmReasoningResponseSchema,
  type LlmReasoningResponse,
} from "@sd/core-schema";

export interface LlmReasoningInput {
  kind: "signature" | "transaction";
  method: "eth_sign" | "personal_sign" | "eth_signTypedData_v4" | "eth_sendTransaction";
  parsed: Record<string, unknown>;
  enriched: Record<string, unknown>;
  context: {
    origin?: string;
    originDomain?: string;
    chainId?: string;
    walletAddress?: string;
    contractAddresses?: string[];
    timestamp?: number;
  };
}

export interface ReasoningProvider {
  readonly model: string;
  readonly promptVersion: string;
  reason(input: LlmReasoningInput): Promise<LlmReasoningResponse>;
}

export class LlmUnavailableError extends Error {
  public readonly code: string;

  constructor(message: string, code = "analysis_unavailable") {
    super(message);
    this.name = "LlmUnavailableError";
    this.code = code;
  }
}

export interface OpenAiProviderOptions {
  apiKey: string;
  model: string;
  timeoutMs?: number;
  endpoint?: string;
  promptVersion?: string;
}

export class OpenAiReasoningProvider implements ReasoningProvider {
  public readonly model: string;
  public readonly promptVersion: string;
  private readonly apiKey: string;
  private readonly timeoutMs: number;
  private readonly endpoint: string;

  constructor(options: OpenAiProviderOptions) {
    this.apiKey = options.apiKey;
    this.model = options.model;
    this.timeoutMs = options.timeoutMs ?? 12_000;
    this.endpoint = options.endpoint ?? "https://api.openai.com/v1/chat/completions";
    this.promptVersion = options.promptVersion ?? "reasoning-v2";
  }

  async reason(input: LlmReasoningInput): Promise<LlmReasoningResponse> {
    if (!this.apiKey) {
      throw new LlmUnavailableError("OPENAI_API_KEY is missing");
    }

    const prompt = buildPrompt(input);

    // Use Promise.race for timeout — avoids relying on AbortController/setTimeout
    // which may not be available in MetaMask Snap SES sandbox.
    const fetchPromise = this.doFetch(prompt);
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new LlmUnavailableError("LLM timeout")), this.timeoutMs);
    });

    try {
      return await Promise.race([fetchPromise, timeoutPromise]);
    } catch (error) {
      if (error instanceof LlmUnavailableError) {
        throw error;
      }
      throw new LlmUnavailableError(
        error instanceof Error ? error.message : "Unknown LLM failure"
      );
    }
  }

  private async doFetch(prompt: string): Promise<LlmReasoningResponse> {
    const response = await fetch(this.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: this.model,
        temperature: 0,
        messages: [
          {
            role: "system",
            content: buildSystemPrompt(),
          },
          {
            role: "user",
            content: prompt,
          },
        ],
      }),
    });

    if (!response.ok) {
      const body = await response.text().catch(() => "");
      throw new LlmUnavailableError(
        `OpenAI request failed (${response.status}): ${body.slice(0, 200)}`,
        "analysis_unavailable"
      );
    }

    const data = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    const content = data.choices?.[0]?.message?.content;
    if (!content) {
      throw new LlmUnavailableError("OpenAI returned empty content");
    }

    const parsed = parseStrictJson(content);
    return LlmReasoningResponseSchema.parse(parsed);
  }
}

export interface GatewayProviderOptions {
  endpoint: string;
  token?: string;
  timeoutMs?: number;
  model?: string;
  promptVersion?: string;
}

export class GatewayReasoningProvider implements ReasoningProvider {
  public readonly model: string;
  public readonly promptVersion: string;
  private readonly endpoint: string;
  private readonly token?: string;
  private readonly timeoutMs: number;

  constructor(options: GatewayProviderOptions) {
    this.endpoint = options.endpoint;
    this.token = options.token;
    this.timeoutMs = options.timeoutMs ?? 12_000;
    this.model = options.model ?? "gateway";
    this.promptVersion = options.promptVersion ?? "gateway-v2";
  }

  async reason(input: LlmReasoningInput): Promise<LlmReasoningResponse> {
    if (!this.endpoint) {
      throw new LlmUnavailableError("Gateway endpoint is missing");
    }

    const fetchPromise = this.doFetch(input);
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new LlmUnavailableError("Gateway timeout")), this.timeoutMs);
    });

    try {
      return await Promise.race([fetchPromise, timeoutPromise]);
    } catch (error) {
      if (error instanceof LlmUnavailableError) {
        throw error;
      }
      throw new LlmUnavailableError(
        error instanceof Error ? error.message : "Unknown gateway failure"
      );
    }
  }

  private async doFetch(input: LlmReasoningInput): Promise<LlmReasoningResponse> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(this.endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ input }),
    });

    if (!response.ok) {
      throw new LlmUnavailableError(`Gateway request failed (${response.status})`);
    }

    const data = (await response.json()) as unknown;
    return LlmReasoningResponseSchema.parse(data);
  }
}

export class MockReasoningProvider implements ReasoningProvider {
  public readonly model = "mock";
  public readonly promptVersion = "mock-v2";

  constructor(private readonly output: LlmReasoningResponse) {}

  async reason(): Promise<LlmReasoningResponse> {
    return this.output;
  }
}

export function parseStrictJson(content: string): unknown {
  const trimmed = content.trim();
  try {
    return JSON.parse(trimmed);
  } catch {
    const match = trimmed.match(/\{[\s\S]*\}/);
    if (!match) {
      throw new LlmUnavailableError("LLM response did not contain JSON");
    }
    return JSON.parse(match[0]);
  }
}

export interface AiContext {
  request: {
    method: string;
    kind: string;
    origin?: string;
    chainId?: string;
    walletAddress?: string;
  };
  payload: {
    selector?: string;
    primaryType?: string;
    domainName?: string;
    message?: unknown;
    /** For eth_signTypedData_v4: the decoded EIP-712 message object (includes token, amount, spender, etc.) */
    typedDataMessage?: unknown;
    value?: unknown;
  };
  intelligence: {
    detectedProtocol?: string;
    detectedAction: string;
    /** True when the protocol/domain could not be matched to any known protocol. */
    isUnknownProtocol: boolean;
    /** All deterministic signal keys from the knowledge base, including unknown_protocol. */
    detectedPatterns: string[];
    /** Full knowledge-base signals with key and human-readable reason. */
    knowledgeSignals: Array<{ key: string; reason: string }>;
    maliciousAddressHits: Array<{
      address: string;
      category: string;
      severity: string;
      reason: string;
    }>;
    maliciousDomainHits: Array<{
      domain: string;
      category: string;
      severity: string;
      reason: string;
    }>;
    chainFeatureHits: Array<{
      key: string;
      signal: string;
      reason: string;
    }>;
    contractAddresses: string[];
  };
}

export function buildAiContext(input: LlmReasoningInput): AiContext {
  const inferredSignals = (
    input.enriched.inferredSignals as Array<{ key: string; reason: string }> | undefined
  ) ?? [];

  // Include unknown_protocol in detectedPatterns so the AI knows the protocol was unrecognized.
  const detectedPatterns = inferredSignals.map((s) => s.key);

  // Provide full signal context (key + reason) so the AI understands what the knowledge base found.
  const knowledgeSignals = inferredSignals
    .filter((s) => s.key !== "unknown_protocol") // exclude noise, protocol status is in isUnknownProtocol
    .map((s) => ({ key: s.key, reason: s.reason }));

  return {
    request: {
      method: input.method,
      kind: input.kind,
      origin: input.context.origin,
      chainId: input.context.chainId,
      walletAddress: input.context.walletAddress,
    },
    payload: {
      selector: input.parsed.selector as string | undefined,
      primaryType: input.parsed.primaryType as string | undefined,
      domainName: input.parsed.domainName as string | undefined,
      message: input.parsed.message,
      typedDataMessage: input.parsed.typedDataMessage,
      value: input.parsed.value,
    },
    intelligence: {
      detectedProtocol: input.enriched.inferredProtocol as string | undefined,
      detectedAction: input.enriched.inferredAction as string,
      isUnknownProtocol: inferredSignals.some((s) => s.key === "unknown_protocol"),
      detectedPatterns,
      knowledgeSignals,
      maliciousAddressHits: (input.enriched.maliciousAddressHits as AiContext["intelligence"]["maliciousAddressHits"]) ?? [],
      maliciousDomainHits: (input.enriched.maliciousDomainHits as AiContext["intelligence"]["maliciousDomainHits"]) ?? [],
      chainFeatureHits: (input.enriched.chainFeatureHits as AiContext["intelligence"]["chainFeatureHits"]) ?? [],
      contractAddresses: input.context.contractAddresses ?? [],
    },
  };
}

function buildSystemPrompt(): string {
  return `You are a blockchain security analyst reviewing a wallet signing request on behalf of the user.

Your task is to determine whether this request is SAFE or RISKY for the user, and provide a clear decision.

CRITICAL GUIDELINES:
1. Common DeFi operations like token approvals, permits, swaps, and staking are NORMAL. Do NOT flag them as high risk solely based on operation type.
2. CONTEXT IS EVERYTHING: The same operation can be safe or dangerous depending on origin, protocol match, and parameters. A Uniswap permit from "app.uniswap.org" is safer than one from an unknown site.
3. Threat intelligence hits (maliciousAddressHits, maliciousDomainHits) are HARD EVIDENCE — treat these as strong indicators of malicious intent and assign high or critical risk.
4. HIGH / CRITICAL risk should only be assigned when there is genuine reason to believe the user may be harmed: unknown origin with drain-like parameters, threat intel hits, phishing indicators, or deeply suspicious calldata with no legitimate explanation.
5. LOW / MEDIUM risk is appropriate for normal DeFi operations from trusted origins, even for large amounts or unfamiliar contract addresses with no threat intel flags.
6. The intelligence.knowledgeSignals array contains what the deterministic analysis engine already detected. Use this as trusted context — it will always be present in the final result regardless of your assessment.

DECISION RULES:
- "allow": low or medium risk — proceed safely
- "block": high or critical risk — user should not sign this

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no explanation outside the JSON:
{
  "riskLevel": "low|medium|high|critical",
  "decision": "allow|block",
  "confidence": <0.0 to 1.0>,
  "action": "<short phrase: what this request does, e.g. 'Approve USDC spending'>",
  "description": "<one sentence: what happens when the user signs this, max 100 chars>",
  "reasoning": "<2-3 sentences explaining your risk assessment, focusing on the key factors>",
  "protocol": "<detected protocol name, or omit if unknown>",
  "riskSignals": [
    { "key": "<snake_case_identifier>", "reason": "<brief reason, max 60 chars>", "severity": "low|medium|high|critical" }
  ],
  "detect": {
    "action": "<same as action above>",
    "protocol": "<same as protocol above, or omit>",
    "confidence": <same as confidence>,
    "riskSignals": <same array as riskSignals>
  },
  "explain": {
    "description": "<same as description above>"
  }
}

RULES:
- riskSignals: include ONLY genuine risk factors, not normal operation characteristics. Max 3 signals.
- If there are no real risk factors, return an empty riskSignals array.
- confidence: how certain you are about your assessment (0.0 = very uncertain, 1.0 = highly certain).
- The "detect" and "explain" fields are required for backward compatibility.`;
}

function buildPrompt(input: LlmReasoningInput): string {
  const ctx = buildAiContext(input);
  return `Analyze the following wallet request and return your assessment as strict JSON.\n\nREQUEST CONTEXT:\n${JSON.stringify(ctx, null, 2)}`;
}
