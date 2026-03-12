const fixtures = {

  // ── 1. 普通登录签名 ──────────────────────────────────────────────────────────
  "login_siwe": {
    kind: "signature",
    method: "personal_sign",
    payload: {
      message: "app.uniswap.org wants you to sign in with your Ethereum account:\n0x1111111111111111111111111111111111111111\n\nSign in with Ethereum to the app.\n\nURI: https://app.uniswap.org\nVersion: 1\nChain ID: 1\nNonce: abc123xyz\nIssued At: 2024-11-01T10:00:00Z\nExpiration Time: 2024-11-02T10:00:00Z"
    },
    context: {
      origin: "https://app.uniswap.org",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 2. Permit2 无限额度授权（已知协议 Uniswap）──────────────────────────────
  "permit2_unlimited_uniswap": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "PermitSingle",
      domain: {
        name: "Permit2",
        chainId: 1,
        verifyingContract: "0x000000000022d473030f116ddee9f6b43ac78ba3"
      },
      message: {
        details: {
          token: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
          amount: "1461501637330902918203684832716283019655932542975",
          expiration: "1924992000",
          nonce: "0"
        },
        spender: "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
        sigDeadline: "1924992000"
      }
    },
    context: {
      origin: "https://app.uniswap.org",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 3. OpenSea Seaport — NFT 挂单出售 ───────────────────────────────────────
  // 用户将 BAYC #7537 以 10 ETH 挂单，2.5% 给平台版税
  "opensea_seaport_nft_listing": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "OrderComponents",
      domain: {
        name: "Seaport",
        version: "1.5",
        chainId: 1,
        verifyingContract: "0x00000000000000adc04c56bf30ac9d3c0aaf14dc"
      },
      message: {
        offerer: "0x1111111111111111111111111111111111111111",
        zone: "0x004C00500000aD104D7DBd00e3ae0A5C00560C00",
        offer: [
          {
            itemType: "2",
            token: "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
            identifierOrCriteria: "7537",
            startAmount: "1",
            endAmount: "1"
          }
        ],
        consideration: [
          {
            itemType: "0",
            token: "0x0000000000000000000000000000000000000000",
            identifierOrCriteria: "0",
            startAmount: "9750000000000000000",
            endAmount: "9750000000000000000",
            recipient: "0x1111111111111111111111111111111111111111"
          },
          {
            itemType: "0",
            token: "0x0000000000000000000000000000000000000000",
            identifierOrCriteria: "0",
            startAmount: "250000000000000000",
            endAmount: "250000000000000000",
            recipient: "0x0000a26b00c1f0df003000390027140000faa719"
          }
        ],
        orderType: "2",
        startTime: "1700000000",
        endTime: "1924992000",
        zoneHash: "0x0000000000000000000000000000000000000000000000000000000000000000",
        salt: "0x360c6ebe0000000000000000000000000000000000000000f3cfe1fb67a5e7b3",
        conduitKey: "0x0000007b02230091a7ed01230072f7006a004d60a8d4e71d599b8104250f0000",
        counter: "0"
      }
    },
    context: {
      origin: "https://opensea.io",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 4. Gnosis Safe — 多签交易审批 ────────────────────────────────────────────
  // 多签钱包批准一笔向外部地址转账 10,000 USDC 的交易
  "gnosis_safe_multisig_approve": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "SafeTx",
      domain: {
        chainId: 1,
        verifyingContract: "0x29fcb43b46531bca003ddc8fcb67ffe91900c762"
      },
      message: {
        to: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        value: "0",
        data: "0xa9059cbb000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa9604500000000000000000000000000000000000000000000000000000002540be400",
        operation: "0",
        safeTxGas: "0",
        baseGas: "0",
        gasPrice: "0",
        gasToken: "0x0000000000000000000000000000000000000000",
        refundReceiver: "0x0000000000000000000000000000000000000000",
        nonce: "42"
      }
    },
    context: {
      origin: "https://app.safe.global",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 5. ERC-2612 Permit — 可疑来源的 USDC 授权 ───────────────────────────────
  // 合法的 USDC 授权结构，但来自可疑域名 swap-airdrop.finance
  "usdc_permit_suspicious_origin": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "Permit",
      domain: {
        name: "USD Coin",
        version: "2",
        chainId: 1,
        verifyingContract: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
      },
      message: {
        owner: "0x1111111111111111111111111111111111111111",
        spender: "0x4444444444444444444444444444444444444444",
        value: "115792089237316195423570985008687907853269984665640564039457584007913129639935",
        nonce: "0",
        deadline: "1924992000"
      }
    },
    context: {
      origin: "https://swap-airdrop.finance",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 6. Compound 治理投票委托 ──────────────────────────────────────────────────
  // 用户通过链下签名委托投票权给另一地址
  "compound_governance_delegation": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "Delegation",
      domain: {
        name: "Compound",
        chainId: 1,
        verifyingContract: "0xc00e94cb662c3520282e6f5717214004a7f26888"
      },
      message: {
        delegatee: "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        nonce: "0",
        expiry: "1924992000"
      }
    },
    context: {
      origin: "https://app.compound.finance",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 7. Blur — NFT 批量挂单授权 ────────────────────────────────────────────────
  // Blur 要求签名授权其合约批量操作用户的 NFT（来源合法，但权限较大）
  "blur_bulk_listing_auth": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "Root",
      domain: {
        name: "Blur Exchange",
        version: "1.0",
        chainId: 1,
        verifyingContract: "0x000000000000ad05ccc4f10045630fb830b95127"
      },
      message: {
        root: "0xabc123def456abc123def456abc123def456abc123def456abc123def456abc123"
      }
    },
    context: {
      origin: "https://blur.io",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },

  // ── 8. 高风险：仿冒 Uniswap 的钓鱼 Permit ────────────────────────────────────
  // 结构完全模仿合法 Permit2，但来自拼写接近的钓鱼域名
  "phishing_fake_uniswap_permit": {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "PermitSingle",
      domain: {
        name: "Permit2",
        chainId: 1,
        verifyingContract: "0x000000000022d473030f116ddee9f6b43ac78ba3"
      },
      message: {
        details: {
          token: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
          amount: "1461501637330902918203684832716283019655932542975",
          expiration: "1924992000",
          nonce: "0"
        },
        spender: "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        sigDeadline: "1924992000"
      }
    },
    context: {
      origin: "https://uniswap-airdrop.xyz",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  }
};

// ── UI 逻辑 ──────────────────────────────────────────────────────────────────

const LABELS = {
  login_siwe:                   "① Login — SIWE 登录签名",
  permit2_unlimited_uniswap:    "② Permit2 — 无限额度（Uniswap）",
  opensea_seaport_nft_listing:  "③ Seaport — NFT 挂单出售",
  gnosis_safe_multisig_approve: "④ Safe — 多签交易审批",
  usdc_permit_suspicious_origin:"⑤ Permit — 可疑来源 USDC 授权",
  compound_governance_delegation:"⑥ Compound — 治理投票委托",
  blur_bulk_listing_auth:       "⑦ Blur — NFT 批量挂单授权",
  phishing_fake_uniswap_permit: "⑧ 钓鱼 — 仿冒 Uniswap Permit"
};

const apiBaseInput = document.getElementById("apiBase");
const fixtureSelect = document.getElementById("fixtureSelect");
const payloadEditor = document.getElementById("payloadEditor");
const output = document.getElementById("output");
const decisionBadge = document.getElementById("decisionBadge");

function init() {
  const apiBase = window.__SD_CONFIG__?.apiBase || "http://localhost:4000";
  apiBaseInput.value = apiBase;

  fixtureSelect.innerHTML = Object.keys(fixtures)
    .map((name) => `<option value="${name}">${LABELS[name] ?? name}</option>`)
    .join("");

  loadFixture();
}

function loadFixture() {
  const name = fixtureSelect.value;
  payloadEditor.value = JSON.stringify(fixtures[name], null, 2);
}

async function analyze() {
  try {
    const payload = JSON.parse(payloadEditor.value);
    const response = await fetch(`${apiBaseInput.value}/v2/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    output.textContent = JSON.stringify(result, null, 2);

    const decision = result?.decision?.value;
    if (decision === "block") {
      decisionBadge.textContent = "BLOCK";
      decisionBadge.className = "badge block";
    } else if (decision === "allow") {
      decisionBadge.textContent = "ALLOW";
      decisionBadge.className = "badge allow";
    } else if (decision === "error") {
      decisionBadge.textContent = "ERROR";
      decisionBadge.className = "badge block";
    } else {
      decisionBadge.textContent = "N/A";
      decisionBadge.className = "badge allow";
    }
  } catch (error) {
    output.textContent = String(error);
    decisionBadge.textContent = "ERROR";
    decisionBadge.className = "badge block";
  }
}

async function validateFixtures() {
  const response = await fetch(`${apiBaseInput.value}/v2/fixtures/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });

  const result = await response.json();
  output.textContent = JSON.stringify(result, null, 2);
}

document.getElementById("loadFixtureBtn").addEventListener("click", loadFixture);
document.getElementById("analyzeBtn").addEventListener("click", analyze);
document.getElementById("validateBtn").addEventListener("click", validateFixtures);
fixtureSelect.addEventListener("change", loadFixture);

init();
