import { describe, expect, it } from "vitest";
import {
  AnalyzeRequestV2Schema,
  MaliciousAddressesKnowledgeSchema,
  MaliciousDomainsKnowledgeSchema,
} from "@sd/core-schema";

describe("AnalyzeRequestV2Schema", () => {
  it("accepts valid signature request", () => {
    const input = {
      kind: "signature",
      method: "personal_sign",
      payload: { message: "hello" },
      context: {},
    };

    const parsed = AnalyzeRequestV2Schema.parse(input);
    expect(parsed.kind).toBe("signature");
  });

  it("rejects invalid kind/method pairing", () => {
    const input = {
      kind: "transaction",
      method: "personal_sign",
      payload: {},
      context: {},
    };

    expect(() => AnalyzeRequestV2Schema.parse(input)).toThrowError();
  });
});

describe("Threat intel knowledge schemas", () => {
  it("rejects invalid malicious address keys", () => {
    expect(() =>
      MaliciousAddressesKnowledgeSchema.parse({
        version: "v2",
        addresses: {
          "0x1234": {
            category: "phishing",
            severity: "high",
            reason: "too short",
          },
        },
      })
    ).toThrowError();
  });

  it("rejects invalid malicious domain keys", () => {
    expect(() =>
      MaliciousDomainsKnowledgeSchema.parse({
        version: "v2",
        domains: {
          "NOT_A_DOMAIN": {
            category: "phishing",
            severity: "high",
            reason: "bad hostname format",
          },
        },
      })
    ).toThrowError();
  });
});
