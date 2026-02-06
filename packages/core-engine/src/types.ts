import type {
  AnalyzeRequestV2,
  RiskSignal,
  LlmReasoningResponse,
} from "@sd/core-schema";

export type Actor = {
  role: string;
  address: string;
};

export type Asset = {
  symbol: string;
  amount: string;
  standard: "native" | "erc20" | "erc721" | "unknown";
};

export type ContractEntity = {
  role: string;
  address: string;
  label?: string;
};

export type Highlight = {
  label: string;
  value: string;
  type: "text" | "address" | "amount" | "token";
};

export interface ParsedRequest {
  request: AnalyzeRequestV2;
  normalizedPayload: Record<string, unknown>;
  primaryType?: string;
  domainName?: string;
  verifyingContract?: string;
  selector?: string;
  message?: string;
  value?: string;
  actors: Actor[];
  assets: Asset[];
  contracts: ContractEntity[];
  highlights: Highlight[];
}

export interface EnrichedRequest extends ParsedRequest {
  inferredAction: string;
  inferredProtocol?: string;
  inferredSignals: RiskSignal[];
}

export interface LlmStageResult {
  output: LlmReasoningResponse;
  latencyMs: number;
  status: "ok" | "error";
  model: string;
  promptVersion: string;
  failureReason?: string;
}
