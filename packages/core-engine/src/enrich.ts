import { getKnowledge } from "@sd/core-knowledge";
import type { RiskSignal } from "@sd/core-schema";
import type { EnrichedRequest, ParsedRequest } from "./types";

const MAX_UINT256 = BigInt(
  "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
);
const MAX_UINT160 = BigInt(
  "0xffffffffffffffffffffffffffffffffffffffff"
);

export function enrichParsedRequest(parsed: ParsedRequest): EnrichedRequest {
  const knowledge = getKnowledge();
  const inferredSignals: RiskSignal[] = [];
  const maliciousAddressHits: EnrichedRequest["maliciousAddressHits"] = [];
  const maliciousDomainHits: EnrichedRequest["maliciousDomainHits"] = [];
  const chainFeatureHits: EnrichedRequest["chainFeatureHits"] = [];
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

  const addressesToCheck = new Set<string>();
  for (const actor of parsed.actors) {
    addressesToCheck.add(actor.address.toLowerCase());
  }
  for (const contract of parsed.contracts) {
    addressesToCheck.add(contract.address.toLowerCase());
  }

  for (const address of addressesToCheck) {
    const hit = knowledge.maliciousAddresses.addresses[address];
    if (!hit) {
      continue;
    }

    maliciousAddressHits.push({
      address,
      category: hit.category,
      severity: hit.severity,
      reason: hit.reason,
    });
    inferredSignals.push({
      key: "malicious_address_hit",
      weight: 0,
      source: "knowledge",
      reason: `Threat intel hit (${hit.category}): ${hit.reason}`,
    });
  }

  const domainsToCheck = new Set<string>();
  if (parsed.domainName) {
    domainsToCheck.add(parsed.domainName.toLowerCase());
  }
  const originDomain = extractDomain(parsed.request.context?.origin);
  if (originDomain) {
    domainsToCheck.add(originDomain);
  }

  for (const domain of domainsToCheck) {
    const matched = findDomainIntel(domain, knowledge.maliciousDomains.domains);
    if (!matched) {
      continue;
    }

    maliciousDomainHits.push({
      domain,
      category: matched.category,
      severity: matched.severity,
      reason: matched.reason,
    });
    inferredSignals.push({
      key: "malicious_domain_hit",
      weight: 0,
      source: "knowledge",
      reason: `Threat intel hit (${matched.category}): ${matched.reason}`,
    });

    if (matched.category.toLowerCase().includes("phishing")) {
      inferredSignals.push({
        key: "phishing_domain",
        weight: 0,
        source: "knowledge",
        reason: matched.reason,
      });
    }
  }

  const chainId = parsed.request.context?.chainId;
  if (chainId) {
    const chainConfig = knowledge.chains.chains[chainId];
    if (chainConfig) {
      for (const feature of chainConfig.features) {
        const selectorMatched =
          Boolean(parsed.selector) &&
          feature.selectors.some((selector) => selector.toLowerCase() === parsed.selector?.toLowerCase());
        const typeMatched =
          Boolean(parsed.primaryType) &&
          feature.primaryTypes.some((type) => type.toLowerCase() === parsed.primaryType?.toLowerCase());
        const actionMatched = feature.actionKeywords.some((keyword) =>
          inferredAction.toLowerCase().includes(keyword.toLowerCase())
        );

        if (!selectorMatched && !typeMatched && !actionMatched) {
          continue;
        }

        chainFeatureHits.push({
          key: feature.key,
          signal: feature.signal,
          reason: feature.reason,
        });
        inferredSignals.push({
          key: feature.signal,
          weight: 0,
          source: "knowledge",
          reason: feature.reason,
        });
      }
    }
  }

  return {
    ...parsed,
    inferredAction,
    inferredProtocol,
    inferredSignals: dedupeSignals(inferredSignals),
    maliciousAddressHits: dedupeByKey(maliciousAddressHits, (item) => item.address),
    maliciousDomainHits: dedupeByKey(maliciousDomainHits, (item) => item.domain),
    chainFeatureHits: dedupeByKey(chainFeatureHits, (item) => item.key),
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

function dedupeByKey<T>(items: T[], getKey: (item: T) => string): T[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = getKey(item);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function extractDomain(origin?: string): string | undefined {
  if (!origin) {
    return undefined;
  }
  try {
    return new URL(origin).hostname.toLowerCase();
  } catch {
    return undefined;
  }
}

function findDomainIntel(
  domain: string,
  domains: Record<string, { category: string; severity: "low" | "medium" | "high" | "critical"; reason: string }>
): { category: string; severity: "low" | "medium" | "high" | "critical"; reason: string } | undefined {
  const normalized = domain.toLowerCase();
  for (const [listedDomain, intel] of Object.entries(domains)) {
    const listedLower = listedDomain.toLowerCase();
    if (normalized === listedLower || normalized.endsWith(`.${listedLower}`)) {
      return intel;
    }
  }
  return undefined;
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
      const record = msg as Record<string, unknown>;

      // ERC-2612 Permit: top-level value/amount (uint256)
      const topLevel = record.value ?? record.amount;
      if (topLevel !== undefined) {
        try {
          if (BigInt(String(topLevel)) >= MAX_UINT256 / 2n) return true;
        } catch {
          /* ignore parse errors */
        }
      }

      // Permit2 PermitSingle: details.amount (uint160)
      // Permit2 PermitBatch:  details[].amount (uint160)
      const details = record.details;
      if (details && typeof details === "object") {
        const detailsList = Array.isArray(details) ? details : [details];
        for (const detail of detailsList) {
          if (detail && typeof detail === "object") {
            const amt = (detail as Record<string, unknown>).amount;
            if (amt !== undefined) {
              try {
                if (BigInt(String(amt)) >= MAX_UINT160 / 2n) return true;
              } catch {
                /* ignore parse errors */
              }
            }
          }
        }
      }
    }
  }

  return false;
}
