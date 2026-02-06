import { describe, expect, it } from "vitest";
import { AnalyzeRequestV2Schema } from "@sd/core-schema";

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
