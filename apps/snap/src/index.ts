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
    token: SNAP_GATEWAY_TOKEN || undefined,
    timeoutMs: SNAP_GATEWAY_TIMEOUT_MS,
    model: "gateway",
    promptVersion: "gateway-v2",
  }),
});

export const onSignature: OnSignatureHandler = async ({
  signature,
  signatureOrigin,
}) => {
  try {
    const method = mapSignatureMethod(signature.signatureMethod);
    if (!method) {
      return toSnapSignatureResponse(makeUnsupportedResult(signature.signatureMethod));
    }

    const request: AnalyzeRequestV2 = {
      kind: "signature",
      method,
      payload: signature,
      context: {
        origin: normalizeOrigin(signatureOrigin),
        timestamp: Date.now(),
      },
    };

    const result = await engine.analyze(request);
    return toSnapSignatureResponse(result);
  } catch (error) {
    return toSnapSignatureResponse(makeRuntimeFailureResult("signature", error));
  }
};

export const onTransaction: OnTransactionHandler = async ({
  transaction,
  chainId,
  transactionOrigin,
}) => {
  try {
    const request: AnalyzeRequestV2 = {
      kind: "transaction",
      method: "eth_sendTransaction",
      payload: transaction,
      context: {
        origin: normalizeOrigin(transactionOrigin),
        chainId,
        walletAddress: pickWalletAddress(transaction),
        timestamp: Date.now(),
      },
    };

    const result = await engine.analyze(request);
    return toSnapTransactionResponse(result);
  } catch (error) {
    return toSnapTransactionResponse(makeRuntimeFailureResult("transaction", error));
  }
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

function normalizeOrigin(origin?: string): string | undefined {
  if (!origin) {
    return undefined;
  }

  try {
    return new URL(origin).toString();
  } catch {
    return undefined;
  }
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

function makeRuntimeFailureResult(
  operation: "signature" | "transaction",
  error: unknown
): AnalysisResultV2 {
  const reason = error instanceof Error ? error.message : "unknown_error";

  return {
    summary: {
      action: `${operation}_analysis_failed`,
      description: `Snap failed to analyze this ${operation}.`,
      confidence: 0,
    },
    risk: {
      level: "critical",
      score: 100,
      reasons: ["Snap analysis runtime failure", reason],
      signals: [
        {
          key: "analysis_runtime_failure",
          weight: 100,
          source: "policy",
          reason,
        },
      ],
    },
    decision: {
      value: "block",
      policyReason: "analysis_runtime_failure",
    },
    entities: {
      actors: [],
      assets: [],
      contracts: [],
    },
    highlights: [
      {
        label: "operation",
        value: operation,
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


