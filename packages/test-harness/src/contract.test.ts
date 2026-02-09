import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";
import { AnalysisResultV2Schema } from "@sd/core-schema";

describe("Result contract", () => {
  it("matches AnalysisResultV2 schema", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "login",
        description: "Mock login reasoning",
        detect: {
          action: "login",
          riskSignals: [],
        },
        explain: {
          description: "Mock login reasoning",
        },
        confidence: 0.6,
        riskSignals: [],
      }),
    });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "Sign in with your wallet nonce: 1" },
      context: { origin: "https://example.test" },
    });

    const parsed = AnalysisResultV2Schema.parse(result);
    expect(parsed.summary.action).toBe("login");
  });
});
