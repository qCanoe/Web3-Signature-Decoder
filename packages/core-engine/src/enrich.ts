import { getKnowledge } from "@sd/core-knowledge";
import type { RiskSignal } from "@sd/core-schema";
import type { EnrichedRequest, ParsedRequest } from "./types";

const MAX_UINT256 = BigInt(
  "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
);

export function enrichParsedRequest(parsed: ParsedRequest): EnrichedRequest {
  const knowledge = getKnowledge();
  const inferredSignals: RiskSignal[] = [];
  let inferredAction = "unknown_operation";
  let inferredProtocol: string | undefined;

  if (parsed.selector) {
    const selectorInfo = knowledge.selectors.selectors[parsed.selector.toLowerCase()];
    if (selectorInfo) {
      inferredAction = selectorInfo.action;
      inferredSignals.push({
        key: selectorInfo.action,
        weight: 0,
        source: "knowledge",
        reason: `Selector matched ${selectorInfo.signature}`,
      });
    }
  }

  if (parsed.primaryType) {
    const typeInfo = knowledge.eip712Types.types[parsed.primaryType];
    if (typeInfo) {
      inferredAction = typeInfo.action;
      inferredSignals.push({
        key: typeInfo.action,
        weight: 0,
        source: "knowledge",
        reason: `Primary type matched ${parsed.primaryType}`,
      });
    }
  }

  const protocol = detectProtocol(parsed.domainName, parsed.verifyingContract);
  if (protocol) {
    inferredProtocol = protocol;
  } else if (parsed.request.method === "eth_signTypedData_v4" || parsed.request.method === "eth_sendTransaction") {
    inferredSignals.push({
      key: "unknown_protocol",
      weight: 0,
      source: "knowledge",
      reason: "Protocol could not be identified",
    });
  }

  if (parsed.message) {
    for (const pattern of knowledge.messagePatterns.patterns) {
      const regex = new RegExp(pattern.regex, "i");
      if (regex.test(parsed.message)) {
        inferredSignals.push({
          key: pattern.signal,
          weight: 0,
          source: "knowledge",
          reason: pattern.reason,
        });
      }
    }
  }

  if (isUnlimitedApproval(parsed)) {
    inferredSignals.push({
      key: "infinite_allowance",
      weight: 0,
      source: "knowledge",
      reason: "Detected potentially unlimited token approval",
    });
  }

  if (parsed.selector?.toLowerCase() === "0xac9650d8") {
    inferredSignals.push({
      key: "batch_operation",
      weight: 0,
      source: "knowledge",
      reason: "Transaction is a multicall batch",
    });
  }

  return {
    ...parsed,
    inferredAction,
    inferredProtocol,
    inferredSignals: dedupeSignals(inferredSignals),
  };

  function detectProtocol(domainName?: string, verifyingContract?: string): string | undefined {
    const domainLower = domainName?.toLowerCase() ?? "";
    const contractLower = verifyingContract?.toLowerCase() ?? "";

    for (const protocolEntry of knowledge.protocols.protocols) {
      if (protocolEntry.domainPatterns.some((pattern) => domainLower.includes(pattern.toLowerCase()))) {
        return protocolEntry.name;
      }

      if (
        contractLower &&
        protocolEntry.contractPatterns.some(
          (pattern) => pattern.toLowerCase() === contractLower
        )
      ) {
        return protocolEntry.name;
      }
    }

    return undefined;
  }
}

function dedupeSignals(signals: RiskSignal[]): RiskSignal[] {
  const seen = new Set<string>();
  return signals.filter((signal) => {
    const key = `${signal.key}:${signal.reason}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function isUnlimitedApproval(parsed: ParsedRequest): boolean {
  if (parsed.request.method === "eth_sendTransaction") {
    const data = parsed.normalizedPayload.data;
    if (typeof data === "string" && data.startsWith("0x") && data.length >= 138) {
      const amountHex = `0x${data.slice(74, 138)}`;
      try {
        return BigInt(amountHex) >= MAX_UINT256 / 2n;
      } catch {
        return false;
      }
    }
  }

  if (parsed.request.method === "eth_signTypedData_v4") {
    const msg = parsed.normalizedPayload.message;
    if (msg && typeof msg === "object" && !Array.isArray(msg)) {
      const value = (msg as Record<string, unknown>).value ?? (msg as Record<string, unknown>).amount;
      if (value !== undefined) {
        try {
          return BigInt(String(value)) >= MAX_UINT256 / 2n;
        } catch {
          return false;
        }
      }
    }
  }

  return false;
}
