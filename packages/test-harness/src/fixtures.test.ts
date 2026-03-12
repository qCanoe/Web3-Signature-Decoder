import { describe, expect, it } from "vitest";
import { CoreEngine } from "@sd/core-engine";
import { MockReasoningProvider } from "@sd/core-llm";
import { loadFixtures } from "@sd/test-fixtures";

// A neutral mock that does not return riskLevel or decision.
// This forces risk.ts to fall back to deriveRiskLevelFromSignals(),
// which means the final decision depends on what the knowledge base detected.
const neutralMock = new MockReasoningProvider({
  action: "mock_action",
  description: "mock description",
  confidence: 0.5,
  riskSignals: [],
  // No riskLevel, no decision — let the knowledge-based derivation run.
});

describe("CoreEngine fixtures — knowledge-base path", () => {
  it("infinite_allowance signals are always present for unlimited permit fixtures", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();

    const unlimitedFixtures = fixtures.filter((f) =>
      f.name.includes("unlimited") || f.name.includes("permit_unlimited")
    );
    expect(unlimitedFixtures.length).toBeGreaterThan(0);

    for (const fixture of unlimitedFixtures) {
      const result = await engine.analyze(fixture.request);
      const hasInfiniteAllowance = result.risk.signals.some(
        (s) => s.key === "infinite_allowance" && s.source === "knowledge"
      );
      expect(hasInfiniteAllowance, `${fixture.name}: should detect infinite_allowance`).toBe(true);
    }
  });

  it("knowledge signals have valid source and key for every fixture", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();

    for (const fixture of fixtures) {
      const result = await engine.analyze(fixture.request);

      expect(result.risk.score, `${fixture.name}:score`).toBeGreaterThanOrEqual(0);
      expect(result.risk.score, `${fixture.name}:score`).toBeLessThanOrEqual(100);
      expect(result.risk.signals.length, `${fixture.name}:signals`).toBeGreaterThan(0);

      for (const signal of result.risk.signals) {
        expect(["knowledge", "llm", "policy"], `${fixture.name}:${signal.key}:source`).toContain(
          signal.source
        );
        expect(signal.key.length, `${fixture.name}:${signal.key}:key`).toBeGreaterThan(0);
      }
    }
  });

  it("SIWE login fixture is recognized without dangerous approval signals", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();

    const loginFixture = fixtures.find((f) => f.name === "login_siwe");
    expect(loginFixture).toBeDefined();

    const result = await engine.analyze(loginFixture!.request);

    expect(result.risk.signals.some((s) => s.key === "login_siwe")).toBe(true);
    const hasInfiniteAllowance = result.risk.signals.some((s) => s.key === "infinite_allowance");
    const hasMaliciousHit = result.risk.signals.some((s) => s.key.startsWith("malicious_"));
    expect(hasInfiniteAllowance, "login should not trigger infinite_allowance").toBe(false);
    expect(hasMaliciousHit, "login should not trigger malicious intel hits").toBe(false);
  });

  it("phishing permit fixture hits domain, address, and approval knowledge signals", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();
    const fixture = fixtures.find((f) => f.name === "phishing_fake_uniswap_permit");
    expect(fixture).toBeDefined();

    const result = await engine.analyze(fixture!.request);

    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(true);
    expect(result.risk.signals.some((s) => s.key === "phishing_domain")).toBe(true);
    expect(result.risk.signals.some((s) => s.key === "malicious_address_hit")).toBe(true);
  });

  it("known-good OpenSea listing fixture avoids malicious intel hits", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();
    const fixture = fixtures.find((f) => f.name === "opensea_seaport_nft_listing");
    expect(fixture).toBeDefined();

    const result = await engine.analyze(fixture!.request);

    expect(result.risk.signals.some((s) => s.key.startsWith("malicious_"))).toBe(false);
    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(false);
  });

  it("Safe multisig approval fixture avoids malicious intel and infinite approvals", async () => {
    const engine = new CoreEngine({ llmProvider: neutralMock });
    const fixtures = loadFixtures();
    const fixture = fixtures.find((f) => f.name === "gnosis_safe_multisig_approve");
    expect(fixture).toBeDefined();

    const result = await engine.analyze(fixture!.request);

    expect(result.risk.signals.some((s) => s.key.startsWith("malicious_"))).toBe(false);
    expect(result.risk.signals.some((s) => s.key === "infinite_allowance")).toBe(false);
  });
});

describe("CoreEngine fixtures — LLM decision path", () => {
  it("passes AI decision through for every fixture", async () => {
    const fixtures = loadFixtures();

    for (const fixture of fixtures) {
      const expectedDecision = fixture.expected.decision;
      const riskLevel = expectedDecision === "block" ? "high" : "low";

      // Each fixture uses a mock AI that returns the expected risk level and decision,
      // simulating a well-functioning AI judgment for that specific scenario.
      const engine = new CoreEngine({
        llmProvider: new MockReasoningProvider({
          action: "mock_action",
          description: "mock description",
          confidence: 0.7,
          riskSignals: [],
          riskLevel,
          decision: expectedDecision,
        }),
      });

      const result = await engine.analyze(fixture.request);
      expect(result.decision.value, fixture.name).toBe(expectedDecision);
      expect(result.risk.score, `${fixture.name}:score`).toBeGreaterThanOrEqual(0);
      expect(result.risk.score, `${fixture.name}:score`).toBeLessThanOrEqual(100);
    }
  });
});
