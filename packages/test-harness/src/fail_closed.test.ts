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
  it("blocks when llm fails", async () => {
    const engine = new CoreEngine({ llmProvider: new FailingProvider() });

    const result = await engine.analyze({
      kind: "signature",
      method: "personal_sign",
      payload: { message: "sign in" },
      context: {},
    });

    expect(result.decision.value).toBe("block");
    expect(result.decision.policyReason).toBe("analysis_unavailable");
    expect(result.llm.status).toBe("error");
  });
});
