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
    chainId?: string;
    walletAddress?: string;
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

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    const prompt = buildPrompt(input);

    try {
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
              content:
                "You are a blockchain security analyst. Return JSON only. No markdown.",
            },
            {
              role: "user",
              content: prompt,
            },
          ],
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new LlmUnavailableError(
          `OpenAI request failed (${response.status})`,
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
    } catch (error) {
      if (error instanceof LlmUnavailableError) {
        throw error;
      }

      if (error instanceof Error && error.name === "AbortError") {
        throw new LlmUnavailableError("LLM timeout");
      }

      throw new LlmUnavailableError(
        error instanceof Error ? error.message : "Unknown LLM failure"
      );
    } finally {
      clearTimeout(timeout);
    }
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

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
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
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new LlmUnavailableError(`Gateway request failed (${response.status})`);
      }

      const data = (await response.json()) as unknown;
      return LlmReasoningResponseSchema.parse(data);
    } catch (error) {
      if (error instanceof LlmUnavailableError) {
        throw error;
      }

      if (error instanceof Error && error.name === "AbortError") {
        throw new LlmUnavailableError("Gateway timeout");
      }

      throw new LlmUnavailableError(
        error instanceof Error ? error.message : "Unknown gateway failure"
      );
    } finally {
      clearTimeout(timeout);
    }
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

function buildPrompt(input: LlmReasoningInput): string {
  return [
    "Analyze this wallet request and return strict JSON with shape:",
    '{"action":"...","description":"...","confidence":0.0,"protocol":"...","riskSignals":[{"key":"...","reason":"...","severity":"low|medium|high|critical"}]}',
    "Request:",
    JSON.stringify(input),
  ].join("\n");
}
