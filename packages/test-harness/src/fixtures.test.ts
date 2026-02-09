import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";
import { loadFixtures } from "@sd/test-fixtures";

const mockProvider = new MockReasoningProvider({
  action: "mock_action",
  description: "mock description",
  confidence: 0.7,
  protocol: "mock",
  riskSignals: [],
});

describe("CoreEngine fixtures", () => {
  it("validates golden fixtures decisions", async () => {
    const engine = new CoreEngine({ llmProvider: mockProvider });
    const fixtures = loadFixtures();

    for (const fixture of fixtures) {
      const result = await engine.analyze(fixture.request);
      expect(result.decision.value, fixture.name).toBe(fixture.expected.decision);
      expect(result.risk.score, `${fixture.name}:score`).toBeGreaterThanOrEqual(0);
      expect(result.risk.score, `${fixture.name}:score`).toBeLessThanOrEqual(100);
      expect(result.risk.signals.length, `${fixture.name}:signals`).toBeGreaterThan(0);
      for (const signal of result.risk.signals) {
        expect(["knowledge", "llm", "policy"]).toContain(signal.source);
        expect(signal.key.length).toBeGreaterThan(0);
      }
    }
  });
});
