import type { AnalyzeRequestV2 } from "@sd/core-schema";
import type { ParsedRequest, Actor, ContractEntity, Asset, Highlight } from "./types";

const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;

export function parseRequest(request: AnalyzeRequestV2): ParsedRequest {
  const normalizedPayload = normalizePayload(request.payload);

  const actors: Actor[] = [];
  const assets: Asset[] = [];
  const contracts: ContractEntity[] = [];
  const highlights: Highlight[] = [];

  let primaryType: string | undefined;
  let domainName: string | undefined;
  let verifyingContract: string | undefined;
  let selector: string | undefined;
  let message: string | undefined;
  let value: string | undefined;

  if (request.method === "eth_signTypedData_v4") {
    const typed = extractTypedData(normalizedPayload);
    primaryType = asString(typed.primaryType);

    const domain = asObject(typed.domain);
    domainName = asString(domain.name);
    verifyingContract = asAddress(domain.verifyingContract);

    const msg = asObject(typed.message);
    collectActorsFromObject(msg, actors);

    if (domainName) {
      highlights.push({ label: "domain", value: domainName, type: "text" });
    }

    if (primaryType) {
      highlights.push({ label: "primaryType", value: primaryType, type: "text" });
    }

    if (verifyingContract) {
      contracts.push({
        role: "verifying_contract",
        address: verifyingContract,
      });
      highlights.push({
        label: "verifyingContract",
        value: verifyingContract,
        type: "address",
      });
    }

    const amount = pickAmount(msg);
    if (amount) {
      assets.push({ symbol: "UNKNOWN", amount, standard: "erc20" });
      highlights.push({ label: "amount", value: amount, type: "amount" });
    }
  }

  if (request.method === "eth_sendTransaction") {
    const tx = asObject(normalizedPayload);
    const from = asAddress(tx.from);
    const to = asAddress(tx.to);
    const data = asHex(tx.data);
    value = normalizeNumeric(tx.value) ?? "0";

    if (from) {
      actors.push({ role: "from", address: from });
    }
    if (to) {
      actors.push({ role: "to", address: to });
      contracts.push({ role: "target_contract", address: to });
      highlights.push({ label: "to", value: to, type: "address" });
    }

    selector = data ? data.slice(0, 10).toLowerCase() : undefined;
    if (selector) {
      highlights.push({ label: "selector", value: selector, type: "text" });
    }

    if (value && value !== "0") {
      assets.push({ symbol: "ETH", amount: value, standard: "native" });
      highlights.push({ label: "value", value, type: "amount" });
    }
  }

  if (request.method === "personal_sign") {
    message = extractMessage(normalizedPayload);
    if (message) {
      highlights.push({ label: "message", value: shorten(message, 140), type: "text" });
    }
  }

  if (request.method === "eth_sign") {
    const raw = asString(normalizedPayload.raw ?? normalizedPayload.data ?? request.payload);
    message = raw;
    if (raw) {
      highlights.push({ label: "raw", value: shorten(raw, 140), type: "text" });
    }
  }

  if (request.context?.walletAddress && ADDRESS_RE.test(request.context.walletAddress)) {
    actors.unshift({ role: "wallet", address: request.context.walletAddress });
  }

  return {
    request,
    normalizedPayload,
    primaryType,
    domainName,
    verifyingContract,
    selector,
    message,
    value,
    actors: uniqueByAddressAndRole(actors),
    assets,
    contracts: uniqueContracts(contracts),
    highlights,
  };
}

function normalizePayload(payload: unknown): Record<string, unknown> {
  if (typeof payload === "string") {
    try {
      const parsed = JSON.parse(payload) as unknown;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
      return { raw: payload };
    } catch {
      return { raw: payload };
    }
  }

  if (payload && typeof payload === "object" && !Array.isArray(payload)) {
    return payload as Record<string, unknown>;
  }

  return { raw: payload };
}

function extractTypedData(payload: Record<string, unknown>): Record<string, unknown> {
  if (payload.data && typeof payload.data === "string") {
    try {
      const parsed = JSON.parse(payload.data) as unknown;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      // fall through
    }
  }

  if (payload.data && typeof payload.data === "object" && !Array.isArray(payload.data)) {
    return payload.data as Record<string, unknown>;
  }

  return payload;
}

function extractMessage(payload: Record<string, unknown>): string | undefined {
  const direct = asString(payload.message);
  if (direct) {
    return decodeHexIfNeeded(direct);
  }

  const data = asString(payload.data);
  if (data) {
    return decodeHexIfNeeded(data);
  }

  const raw = asString(payload.raw);
  if (raw) {
    return decodeHexIfNeeded(raw);
  }

  return undefined;
}

function decodeHexIfNeeded(value: string): string {
  if (!value.startsWith("0x")) {
    return value;
  }

  const hex = value.slice(2);
  if (hex.length % 2 !== 0 || !/^[a-fA-F0-9]+$/.test(hex)) {
    return value;
  }

  try {
    const bytes = new Uint8Array(hex.match(/.{1,2}/g)?.map((part) => parseInt(part, 16)) ?? []);
    return new TextDecoder().decode(bytes);
  } catch {
    return value;
  }
}

function collectActorsFromObject(message: Record<string, unknown>, actors: Actor[]): void {
  for (const [key, value] of Object.entries(message)) {
    if (typeof value === "string" && ADDRESS_RE.test(value)) {
      actors.push({ role: key, address: value });
    }
  }
}

function pickAmount(message: Record<string, unknown>): string | undefined {
  const candidate = message.value ?? message.amount;
  if (candidate === undefined || candidate === null) {
    return undefined;
  }
  return String(candidate);
}

function normalizeNumeric(value: unknown): string | undefined {
  if (value === undefined || value === null) {
    return undefined;
  }

  if (typeof value === "string") {
    if (value.startsWith("0x")) {
      try {
        return BigInt(value).toString();
      } catch {
        return value;
      }
    }
    return value;
  }

  if (typeof value === "number" || typeof value === "bigint") {
    return String(value);
  }

  return undefined;
}

function asObject(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function asAddress(value: unknown): string | undefined {
  if (typeof value === "string" && ADDRESS_RE.test(value)) {
    return value;
  }
  return undefined;
}

function asHex(value: unknown): string | undefined {
  if (typeof value === "string" && /^0x[a-fA-F0-9]*$/.test(value)) {
    return value;
  }
  return undefined;
}

function shorten(value: string, max: number): string {
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 3)}...`;
}

function uniqueByAddressAndRole(input: Actor[]): Actor[] {
  const seen = new Set<string>();
  return input.filter((item) => {
    const key = `${item.role}:${item.address.toLowerCase()}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function uniqueContracts(input: ContractEntity[]): ContractEntity[] {
  const seen = new Set<string>();
  return input.filter((item) => {
    const key = `${item.role}:${item.address.toLowerCase()}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}
