import { AnalyzeRequestV2Schema } from "@sd/core-schema";
import permit2SingleUnlimited from "./fixtures/permit2_single_unlimited.json";
import permitUnlimitedHigh from "./fixtures/permit_unlimited_high.json";
import personalSignLogin from "./fixtures/personal_sign_login.json";
import txMulticall from "./fixtures/tx_multicall.json";

export interface FixtureCase {
  name: string;
  request: unknown;
  expected: {
    decision: "allow" | "block";
  };
}

const FIXTURES: FixtureCase[] = [
  permit2SingleUnlimited as FixtureCase,
  permitUnlimitedHigh as FixtureCase,
  personalSignLogin as FixtureCase,
  txMulticall as FixtureCase,
];

export function loadFixtures(): FixtureCase[] {
  for (const fixture of FIXTURES) {
    AnalyzeRequestV2Schema.parse(fixture.request);
  }
  return FIXTURES;
}
