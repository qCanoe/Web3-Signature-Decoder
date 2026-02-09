import { describe, expect, it } from "vitest";
import { parseStrictJson } from "@sd/core-llm";
import { LlmReasoningResponseSchema } from "@sd/core-schema";

describe("LLM adapter", () => {
  it("extracts strict json from mixed text", () => {
    const parsed = parseStrictJson(
      'Sure. {"action":"approve","description":"desc","confidence":0.8,"riskSignals":[]}'
    );

    const validated = LlmReasoningResponseSchema.parse(parsed);
    expect(validated.action).toBe("approve");
  });

  it("accepts two-stage detect+explain shape", () => {
    const parsed = parseStrictJson(
      '{"detect":{"action":"token_approval","protocol":"Uniswap","confidence":0.72,"riskSignals":[{"key":"suspicious_calldata","reason":"Calldata looks obfuscated","severity":"medium"}]},"explain":{"description":"This request may approve token spending."}}'
    );

    const validated = LlmReasoningResponseSchema.parse(parsed);
    expect(validated.action).toBe("token_approval");
    expect(validated.description).toContain("approve token spending");
    expect(validated.detect?.action).toBe("token_approval");
    expect(validated.explain?.description).toBeDefined();
  });
});
