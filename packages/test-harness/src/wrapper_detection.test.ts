import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";

class FailingProvider {
  model = "fail";
  promptVersion = "fail-v1";

  async reason(): Promise<never> {
    throw new Error("simulated llm failure");
  }
}

const neutralMock = new MockReasoningProvider({
  action: "mock_action",
  description: "mock description",
  confidence: 0.5,
  riskSignals: [],
});

describe("Wrapper request detection", () => {
  it("extracts malicious spender addresses from embedded SafeTx calldata", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "eth_signTypedData_v4",
      payload: {
        primaryType: "SafeTx",
        domain: {
          chainId: 1,
          verifyingContract: "0x29fcb43b46531bca003ddc8fcb67ffe91900c762",
        },
        message: {
          to: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
          value: "0",
          data: "0x095ea7b3000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeefffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          operation: "0",
          safeTxGas: "0",
          baseGas: "0",
          gasPrice: "0",
          gasToken: "0x0000000000000000000000000000000000000000",
          refundReceiver: "0x0000000000000000000000000000000000000000",
          nonce: "42",
        },
      },
      context: {
        origin: "https://app.safe.global",
        chainId: "eip155:1",
      },
    });

    expect(result.decision.value).toBe("block");
    expect(result.risk.signals.some((s) => s.key === "malicious_address_hit")).toBe(true);
    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(true);
  });

  it("detects setApprovalForAll embedded in wrapper signatures", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });

    const result = await engine.analyze({
      kind: "signature",
      method: "eth_signTypedData_v4",
      payload: {
        primaryType: "SafeTx",
        domain: {
          chainId: 1,
          verifyingContract: "0x29fcb43b46531bca003ddc8fcb67ffe91900c762",
        },
        message: {
          to: "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
          value: "0",
          data: "0xa22cb465000000000000000000000000beefbeefbeefbeefbeefbeefbeefbeefbeefbeef0000000000000000000000000000000000000000000000000000000000000001",
          operation: "0",
          safeTxGas: "0",
          baseGas: "0",
          gasPrice: "0",
          gasToken: "0x0000000000000000000000000000000000000000",
          refundReceiver: "0x0000000000000000000000000000000000000000",
          nonce: "7",
        },
      },
      context: {
        origin: "https://app.safe.global",
        chainId: "eip155:1",
      },
    });

    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(true);
  });
});
