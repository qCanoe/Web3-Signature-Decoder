import type {
  OnSignatureHandler,
  OnTransactionHandler,
  Signature,
  OnSignatureResponse,
  OnTransactionResponse,
} from "@metamask/snaps-sdk";
import { CoreEngine } from "@sd/core-engine";
import { GatewayReasoningProvider } from "@sd/core-llm";
import {
  toSnapSignatureResponse,
  toSnapTransactionResponse,
} from "@sd/core-renderers";
import type { AnalysisResultV2, AnalyzeRequestV2 } from "@sd/core-schema";
import {
  SNAP_GATEWAY_TIMEOUT_MS,
  SNAP_GATEWAY_TOKEN,
  SNAP_GATEWAY_URL,
} from "./config";

const engine = new CoreEngine({
  llmProvider: new GatewayReasoningProvider({
    endpoint: SNAP_GATEWAY_URL,
    token: SNAP_GATEWAY_TOKEN,
    timeoutMs: SNAP_GATEWAY_TIMEOUT_MS,
    model: "gateway",
    promptVersion: "gateway-v2",
  }),
});

export const onSignature: OnSignatureHandler = async ({
  signature,
  signatureOrigin,
}) => {
  const method = mapSignatureMethod(signature.signatureMethod);
  if (!method) {
    return toSnapSignatureResponse(makeUnsupportedResult(signature.signatureMethod));
  }

  const request: AnalyzeRequestV2 = {
    kind: "signature",
    method,
    payload: signature,
    context: {
      origin: signatureOrigin,
      timestamp: Date.now(),
    },
  };

  const result = await engine.analyze(request);
  return toSnapSignatureResponse(result);
};

export const onTransaction: OnTransactionHandler = async ({
  transaction,
  chainId,
  transactionOrigin,
}) => {
  const request: AnalyzeRequestV2 = {
    kind: "transaction",
    method: "eth_sendTransaction",
    payload: transaction,
    context: {
      origin: transactionOrigin,
      chainId,
      walletAddress: pickWalletAddress(transaction),
      timestamp: Date.now(),
    },
  };

  const result = await engine.analyze(request);
  return toSnapTransactionResponse(result);
};

function mapSignatureMethod(method: string): AnalyzeRequestV2["method"] | null {
  if (method === "eth_sign") return "eth_sign";
  if (method === "personal_sign") return "personal_sign";
  if (method === "eth_signTypedData_v4") return "eth_signTypedData_v4";
  return null;
}

function pickWalletAddress(transaction: Record<string, unknown>): string | undefined {
  const from = transaction.from;
  if (typeof from === "string") {
    return from;
  }
  return undefined;
}

function makeUnsupportedResult(method: string): AnalysisResultV2 {
  return {
    summary: {
      action: "unsupported_method",
      description: `Signature method is not supported in v2 core: ${method}`,
      confidence: 1,
    },
    risk: {
      level: "critical",
      score: 100,
      reasons: ["Unsupported signature method"],
      signals: [
        {
          key: "unsupported_method",
          weight: 100,
          source: "policy",
          reason: "Method is outside allowed v2 signature methods",
        },
      ],
    },
    decision: {
      value: "block",
      policyReason: "unsupported_method",
    },
    entities: {
      actors: [],
      assets: [],
      contracts: [],
    },
    highlights: [
      {
        label: "method",
        value: method,
        type: "text",
      },
    ],
    llm: {
      model: "gateway",
      latencyMs: 0,
      promptVersion: "gateway-v2",
      status: "error",
    },
  };
}
