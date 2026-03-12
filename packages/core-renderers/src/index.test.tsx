import { describe, expect, it } from "vitest";
import { SeverityLevel } from "@metamask/snaps-sdk";
import type { AnalysisResultV2 } from "@sd/core-schema";
import {
  renderSnapAnalysis,
  riskToSeverity,
  toSnapSignatureResponse,
  toSnapTransactionResponse,
} from "./index";

function makeResult(
  overrides: Partial<AnalysisResultV2> = {}
): AnalysisResultV2 {
  return {
    summary: {
      action: "token_approval",
      description: "Approve token spending",
      confidence: 0.9,
    },
    risk: {
      level: "low",
      score: 15,
      reasons: ["No explicit risk signals were identified"],
      signals: [],
    },
    decision: {
      value: "allow",
      policyReason: "policy_allow",
    },
    entities: {
      actors: [],
      assets: [],
      contracts: [],
    },
    highlights: [],
    llm: {
      model: "mock",
      latencyMs: 1,
      promptVersion: "mock-v1",
      status: "ok",
    },
    ...overrides,
  };
}

describe("core-renderers", () => {
  it("maps only high and critical transaction risk to MetaMask critical severity", () => {
    expect(riskToSeverity(makeResult({ risk: { level: "low", score: 15, reasons: [], signals: [] } }))).toBeUndefined();
    expect(riskToSeverity(makeResult({ risk: { level: "medium", score: 50, reasons: [], signals: [] } }))).toBeUndefined();
    expect(riskToSeverity(makeResult({ risk: { level: "high", score: 75, reasons: [], signals: [] } }))).toBe(
      SeverityLevel.Critical
    );
  });

  it("keeps signature severity critical because Snap SDK only supports critical insights", () => {
    const response = toSnapSignatureResponse(makeResult());
    expect(response.severity).toBe(SeverityLevel.Critical);
  });

  it("uses computed severity for transactions", () => {
    const lowResponse = toSnapTransactionResponse(makeResult());
    const highResponse = toSnapTransactionResponse(
      makeResult({
        risk: {
          level: "high",
          score: 75,
          reasons: ["Suspicious approval"],
          signals: [],
        },
      })
    );

    expect(lowResponse.severity).toBeUndefined();
    expect(highResponse.severity).toBe(SeverityLevel.Critical);
  });

  it("renders an explicit block banner title for blocked requests", () => {
    const view = renderSnapAnalysis(
      makeResult({
        risk: {
          level: "high",
          score: 75,
          reasons: ["Known phishing domain"],
          signals: [
            {
              key: "phishing_domain",
              weight: 0,
              source: "knowledge",
              reason: "Known phishing domain",
            },
          ],
        },
        decision: {
          value: "block",
          policyReason: "high_risk",
        },
      })
    );

    expect(JSON.stringify(view)).toContain("This request should be blocked");
  });
});
