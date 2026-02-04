/**
 * Signature Decoder Snap - 入口点
 *
 * 提供签名和交易的语义分析洞察
 */

import type {
  OnSignatureHandler,
  OnTransactionHandler,
} from "@metamask/snaps-sdk";

import { configureApiUrl } from "./api/client";
import { handleSignature } from "./handlers/signature";
import { handleTransaction } from "./handlers/transaction";
import { BACKEND_BASE_URL } from "./config";

// Configure backend base URL for deep analysis
if (BACKEND_BASE_URL) {
  configureApiUrl(BACKEND_BASE_URL);
}

/**
 * onSignature 处理器 - 处理所有签名请求
 *
 * 拦截以下签名方法:
 * - eth_sign
 * - personal_sign
 * - eth_signTypedData
 * - eth_signTypedData_v1
 * - eth_signTypedData_v3
 * - eth_signTypedData_v4
 */
export const onSignature: OnSignatureHandler = async ({
  signature,
  signatureOrigin,
}) => {
  return handleSignature(signature, signatureOrigin);
};

/**
 * onTransaction 处理器 - 处理所有交易请求
 *
 * 拦截 eth_sendTransaction 调用，分析交易内容
 */
export const onTransaction: OnTransactionHandler = async ({
  transaction,
  chainId,
  transactionOrigin,
}) => {
  return handleTransaction(transaction, chainId, transactionOrigin);
};
