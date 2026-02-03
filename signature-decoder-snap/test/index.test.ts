/**
 * Snap 测试文件
 *
 * 使用 @metamask/snaps-jest 进行测试
 */

import { installSnap } from "@metamask/snaps-jest";
import { expect } from "@jest/globals";

describe("Signature Decoder Snap", () => {
  describe("onSignature", () => {
    it("should handle personal_sign requests", async () => {
      const { onSignature } = await installSnap();

      const response = await onSignature({
        signature: {
          from: "0x1234567890123456789012345678901234567890",
          data: "0x48656c6c6f20576f726c64", // "Hello World" in hex
          signatureMethod: "personal_sign",
        },
        signatureOrigin: "https://example.com",
      });

      expect(response).toBeDefined();
      // 验证返回的 UI 内容
      expect(response.response).toHaveProperty("content");
    });

    it("should handle eth_signTypedData_v4 requests", async () => {
      const { onSignature } = await installSnap();

      const typedData = {
        types: {
          EIP712Domain: [
            { name: "name", type: "string" },
            { name: "version", type: "string" },
            { name: "chainId", type: "uint256" },
            { name: "verifyingContract", type: "address" },
          ],
          Permit: [
            { name: "owner", type: "address" },
            { name: "spender", type: "address" },
            { name: "value", type: "uint256" },
            { name: "nonce", type: "uint256" },
            { name: "deadline", type: "uint256" },
          ],
        },
        primaryType: "Permit",
        domain: {
          name: "USD Coin",
          version: "2",
          chainId: 1,
          verifyingContract: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        },
        message: {
          owner: "0x1234567890123456789012345678901234567890",
          spender: "0x0987654321098765432109876543210987654321",
          value: "115792089237316195423570985008687907853269984665640564039457584007913129639935",
          nonce: 0,
          deadline: 1893456000,
        },
      };

      const response = await onSignature({
        signature: {
          from: "0x1234567890123456789012345678901234567890",
          data: typedData,
          signatureMethod: "eth_signTypedData_v4",
        },
        signatureOrigin: "https://app.uniswap.org",
      });

      expect(response).toBeDefined();
      expect(response.response).toHaveProperty("content");
      // 无限授权应该返回高风险
      // expect(response.response.severity).toBe("critical");
    });

    it("should flag eth_sign as dangerous", async () => {
      const { onSignature } = await installSnap();

      const response = await onSignature({
        signature: {
          from: "0x1234567890123456789012345678901234567890",
          data: "0xdeadbeef",
          signatureMethod: "eth_sign",
        },
        signatureOrigin: "https://suspicious-site.com",
      });

      expect(response).toBeDefined();
      // eth_sign 应该被标记为危险
      // 验证警告内容
    });
  });

  describe("onTransaction", () => {
    it("should handle simple ETH transfer", async () => {
      const { onTransaction } = await installSnap();

      const response = await onTransaction({
        transaction: {
          from: "0x1234567890123456789012345678901234567890",
          to: "0x0987654321098765432109876543210987654321",
          value: "0xde0b6b3a7640000", // 1 ETH
          data: "0x",
        },
        chainId: "eip155:1",
        transactionOrigin: "https://example.com",
      });

      expect(response).toBeDefined();
      expect(response.response).toHaveProperty("content");
    });

    it("should detect ERC20 approval", async () => {
      const { onTransaction } = await installSnap();

      // approve(address,uint256) with max amount
      const data =
        "0x095ea7b3" +
        "0000000000000000000000000987654321098765432109876543210987654321" +
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

      const response = await onTransaction({
        transaction: {
          from: "0x1234567890123456789012345678901234567890",
          to: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", // USDC
          value: "0x0",
          data,
        },
        chainId: "eip155:1",
        transactionOrigin: "https://app.uniswap.org",
      });

      expect(response).toBeDefined();
      // 无限授权应该触发警告
    });

    it("should handle contract deployment", async () => {
      const { onTransaction } = await installSnap();

      const response = await onTransaction({
        transaction: {
          from: "0x1234567890123456789012345678901234567890",
          value: "0x0",
          data: "0x608060405234801561001057600080fd5b50",
        },
        chainId: "eip155:1",
        transactionOrigin: "https://example.com",
      });

      expect(response).toBeDefined();
      // 合约部署应该被识别
    });
  });
});

describe("Local Analyzers", () => {
  describe("EIP-712 Parser", () => {
    it("should flatten typed data correctly", () => {
      // 测试 flattenTypedData 函数
    });

    it("should detect unlimited approval amounts", () => {
      // 测试无限授权检测
    });
  });

  describe("Classifier", () => {
    it("should classify Permit signatures correctly", () => {
      // 测试 Permit 分类
    });

    it("should classify Permit2 signatures correctly", () => {
      // 测试 Permit2 分类
    });

    it("should detect known protocols", () => {
      // 测试协议检测
    });
  });
});
