import { AnalyzeRequestV2Schema } from "@sd/core-schema";
import permit2SingleUnlimited from "./fixtures/permit2_single_unlimited.json";
import permitUnlimitedHigh from "./fixtures/permit_unlimited_high.json";
import personalSignLogin from "./fixtures/personal_sign_login.json";
import txMulticall from "./fixtures/tx_multicall.json";
import phishingFakeUniswapPermit from "./fixtures/phishing_fake_uniswap_permit.json";
import openseaSeaportNftListing from "./fixtures/opensea_seaport_nft_listing.json";
import loginSiwe from "./fixtures/login_siwe.json";
import gnosisSafeMultisigApprove from "./fixtures/gnosis_safe_multisig_approve.json";

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
  phishingFakeUniswapPermit as FixtureCase,
  openseaSeaportNftListing as FixtureCase,
  loginSiwe as FixtureCase,
  gnosisSafeMultisigApprove as FixtureCase,
];

export function loadFixtures(): FixtureCase[] {
  for (const fixture of FIXTURES) {
    AnalyzeRequestV2Schema.parse(fixture.request);
  }
  return FIXTURES;
}
