import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import type { ReasoningProvider } from "@sd/core-llm";

class FailingProvider implements ReasoningProvider {
  model = "fail";
  promptVersion = "fail-v1";

  async reason(): Promise<never> {
    throw new Error("simulated llm failure");
  }
}

describe("Fail-closed policy", () => {
  it("returns error when llm fails on a low-signal request", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "sign in" },
      context: {},
    });

    expect(result.decision.value).toBe("error");
    expect(result.decision.policyReason).toBe("analysis_unavailable");
    expect(result.llm.status).toBe("error");
  });

  it("escalates to block when llm fails but infinite_allowance is detected", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    // MAX_UINT256 value triggers infinite_allowance signal in enrich stage.
    const result = await engine.analyze({
      kind: "signature",
      method: "eth_signTypedData_v4",
      payload: {
        primaryType: "Permit",
        domain: {
          name: "USD Coin",
          verifyingContract: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        },
        message: {
          value: "115792089237316195423570985008687907853269984665640564039457584007913129639935",
        },
      },
      context: {},
    });

    expect(result.decision.value).toBe("block");
    expect(result.decision.policyReason).toBe("high_risk");
    expect(result.risk.level).toBe("high");
    expect(result.llm.status).toBe("error");
    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(true);
  });

  it("escalates to block when llm fails but Permit2 unlimited amount is detected", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "eth_signTypedData_v4",
      payload: {
        primaryType: "PermitSingle",
        domain: {
          name: "Permit2",
          verifyingContract: "0x000000000022d473030f116ddee9f6b43ac78ba3",
        },
        message: {
          details: {
            amount: "1461501637330902918203684832716283019655932542975",
          },
        },
      },
      context: {},
    });

    expect(result.decision.value).toBe("block");
    expect(result.decision.policyReason).toBe("high_risk");
    expect(result.llm.status).toBe("error");
  });

  it("escalates to block when llm fails and a confirmed phishing domain is detected", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "claim your rewards" },
      context: {
        origin: "https://uniswap-airdrop.xyz",
      },
    });

    expect(result.decision.value).toBe("block");
    expect(result.decision.policyReason).toBe("high_risk");
    expect(result.risk.signals.some((s) => s.key === "phishing_domain")).toBe(true);
  });

  it("keeps watchlist-only intel at error when llm fails", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "verify wallet" },
      context: {
        origin: "https://wallet-warning.test",
      },
    });

    expect(result.decision.value).toBe("error");
    expect(result.decision.policyReason).toBe("analysis_unavailable");
    expect(result.risk.signals.some((s) => s.key === "watchlist_domain_hit")).toBe(true);
    expect(result.risk.signals.some((s) => s.key === "malicious_domain_hit")).toBe(false);
  });
});
