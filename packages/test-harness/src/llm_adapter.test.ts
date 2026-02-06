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
});
