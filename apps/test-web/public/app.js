const fixtures = {
  permit_unlimited_high: {
    kind: "signature",
    method: "eth_signTypedData_v4",
    payload: {
      primaryType: "Permit",
      domain: {
        name: "Permit2",
        version: "1",
        chainId: 1,
        verifyingContract: "0x000000000022d473030f116ddee9f6b43ac78ba3"
      },
      message: {
        owner: "0x1111111111111111111111111111111111111111",
        spender: "0x2222222222222222222222222222222222222222",
        value: "115792089237316195423570985008687907853269984665640564039457584007913129639935",
        nonce: "1",
        deadline: "1924992000"
      }
    },
    context: {
      origin: "https://example-dapp.test",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },
  personal_sign_login: {
    kind: "signature",
    method: "personal_sign",
    payload: { message: "Sign in with your wallet. nonce: 123456" },
    context: {
      origin: "https://safe-app.test",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  },
  tx_multicall: {
    kind: "transaction",
    method: "eth_sendTransaction",
    payload: {
      from: "0x1111111111111111111111111111111111111111",
      to: "0x3333333333333333333333333333333333333333",
      data: "0xac9650d80000000000000000000000000000000000000000000000000000000000000020",
      value: "0x0"
    },
    context: {
      origin: "https://dex.test",
      chainId: "eip155:1",
      walletAddress: "0x1111111111111111111111111111111111111111"
    }
  }
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
    .map((name) => `<option value="${name}">${name}</option>`)
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
