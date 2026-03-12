import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";

describe("LLM signal mapping", () => {
  it("includes LLM signals that are not already covered by knowledge", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "review_message",
        description: "Potentially unsafe request",
        confidence: 0.7,
        riskLevel: "medium",
        decision: "allow",
        riskSignals: [
          {
            key: "suspicious_calldata",
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
    expect(llmSignal).toBeDefined();
    expect(llmSignal?.key).toBe("suspicious_calldata");
  });

  it("skips LLM signals whose key is already covered by knowledge", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "token_approval",
        description: "Token approval request",
        confidence: 0.9,
        riskLevel: "low",
        decision: "allow",
        riskSignals: [
          {
            key: "token_approval",
            reason: "Token approval found",
            severity: "low",
          },
          {
            key: "suspicious_calldata",
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

    // LLM's token_approval signal should be omitted — knowledge already detected it.
    const llmApproval = result.risk.signals.find(
      (signal) => signal.source === "llm" && signal.key === "token_approval"
    );
    const knowledgeApproval = result.risk.signals.find(
      (signal) => signal.source === "knowledge" && signal.key === "token_approval"
    );

    expect(llmApproval).toBeUndefined();
    expect(knowledgeApproval).toBeDefined();
  });

  it("uses AI riskLevel and decision as the primary output", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "unknown_operation",
        description: "Suspicious request from unknown origin",
        confidence: 0.85,
        riskLevel: "high",
        decision: "block",
        reasoning: "Origin does not match any known protocol and parameters are suspicious.",
        riskSignals: [
          {
            key: "unknown_origin",
            reason: "Origin is not a recognized protocol",
            severity: "high",
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

    expect(result.risk.level).toBe("high");
    expect(result.decision.value).toBe("block");
    expect(result.risk.score).toBe(75);
  });

  it("assigns low risk and allow when AI returns no risk signals", async () => {
    const engine = new CoreEngine({
      llmProvider: new MockReasoningProvider({
        action: "login",
        description: "Standard login request",
        confidence: 0.95,
        riskLevel: "low",
        decision: "allow",
        riskSignals: [],
      }),
    });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "Sign in to MyApp. Nonce: abc123" },
      context: {},
    });

    expect(result.risk.level).toBe("low");
    expect(result.decision.value).toBe("allow");
    expect(result.risk.score).toBe(15);
  });
});
