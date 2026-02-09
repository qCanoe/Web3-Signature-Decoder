import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";

describe("LLM signal mapping and scoring controls", () => {
  it("maps free-text llm signal to standard taxon key", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "review_message",
        description: "Potentially unsafe request",
        confidence: 0.7,
        riskSignals: [
          {
            key: "strange_payload",
            reason: "Calldata payload appears obfuscated",
            severity: "medium",
          },
        ],
      }),
    });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "Hello wallet" },
      context: {},
    });

    const llmSignal = result.risk.signals.find((signal) => signal.source === "llm");
    expect(llmSignal?.key).toBe("suspicious_calldata");
  });

  it("keeps llm signals incremental when knowledge already covered same key", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "token_approval",
        description: "Token approval request",
        confidence: 0.9,
        riskSignals: [
          {
            key: "token_approval",
            reason: "Token approval found",
            severity: "low",
          },
          {
            key: "calldata_check",
            reason: "Calldata payload looks suspicious",
            severity: "medium",
          },
        ],
      }),
    });

    const result = await engine.analyze({
      kind: "transaction",
      method: "eth_sendTransaction",
      payload: {
        from: "0x1111111111111111111111111111111111111111",
        to: "0x3333333333333333333333333333333333333333",
        data: "0x095ea7b3",
        value: "0x0",
      },
      context: {},
    });

    const llmApproval = result.risk.signals.find(
      (signal) => signal.source === "llm" && signal.key === "token_approval"
    );
    const knowledgeApproval = result.risk.signals.find(
      (signal) => signal.source === "knowledge" && signal.key === "token_approval"
    );

    expect(llmApproval).toBeUndefined();
    expect(knowledgeApproval).toBeDefined();
  });

  it("caps cumulative llm signal weight", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "unknown_operation",
        description: "Multiple high risk indicators",
        confidence: 0.6,
        riskSignals: [
          {
            key: "critical_issue",
            reason: "Critical risk found",
            severity: "critical",
          },
          {
            key: "high_issue",
            reason: "High risk found",
            severity: "high",
          },
          {
            key: "custom_medium",
            reason: "Calldata payload is suspicious",
            severity: "medium",
          },
        ],
      }),
    });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "Hello wallet" },
      context: {},
    });

    const llmWeightTotal = result.risk.signals
      .filter((signal) => signal.source === "llm")
      .reduce((sum, signal) => sum + signal.weight, 0);

    expect(llmWeightTotal).toBeLessThanOrEqual(30);
  });
});
