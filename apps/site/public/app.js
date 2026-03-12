/* ─── MINIMALIST CONTROLLER ─── */

const EL = (id) => document.getElementById(id);
const STATE = {
  snapId: "local:http://localhost:8080",
  hasWallet: false,
  busy: false,           // lock to prevent concurrent MetaMask requests
  connectedAddr: null,   // currently connected wallet address
  chainId: null,         // current chain ID (hex)
};

// ─── UI Helpers ───
const log = (msg, type = 'info') => {
  const el = EL('log');
  const div = document.createElement('div');
  const ts = new Date().toISOString().split('T')[1].slice(0,8);
  
  div.className = `log-entry new ${type}`;
  div.innerHTML = `<span class="ts">${ts}</span> ${msg}`;
  
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;

  // Fade out old logs logic removed for brutalist permanence
};

const setStatus = (msg, active = false, err = false) => {
  EL('statusText').innerText = msg;
  EL('statusDot').className = `dot ${active ? 'active' : ''} ${err ? 'error' : ''}`;
  EL('statusDot').style.opacity = active || err ? 1 : 0.3;
};

// ─── Core Logic ───
async function init() {
  // Config Injection
  if (window.__SD_SITE__?.snapOrigin) {
    STATE.snapId = window.__SD_SITE__.snapOrigin;
  }
  EL('snapIdDisplay').innerText = STATE.snapId;

  log('System sequence started.');
  
  // Wallet Check
  if (typeof window.ethereum === 'undefined') {
    log('CRITICAL: MetaMask provider not found.', 'err');
    EL('envDisplay').innerText = 'MISSING_PROVIDER';
    setStatus('NO PROVIDER', false, true);
    return;
  }

  STATE.hasWallet = true;
  EL('envDisplay').innerText = 'METAMASK_DETECTED';
  
  // Auto-check
  await checkStatus(true);
}

async function checkStatus(silent = false) {
  if (!STATE.hasWallet) return;
  
  if (!silent) log('Verifying snap integrity...');
  
  try {
    const snaps = await window.ethereum.request({ method: 'wallet_getSnaps' });
    // snaps is { [snapId]: { version, ... } } — check key directly
    const entry = snaps && snaps[STATE.snapId];
    
    if (entry) {
      const v = entry.version ? ` v${entry.version}` : '';
      if (!silent) log(`Snap verified: INSTALLED${v}`);
      setStatus('OPERATIONAL', true);
      EL('installBtn').innerText = "RE-INSTALL SNAP";
    } else {
      if (!silent) log('Snap verified: NOT FOUND');
      setStatus('STANDBY', false);
      EL('installBtn').innerText = "INITIALIZE SNAP";
    }
  } catch (e) {
    log(`Check failed: ${e.message}`, 'err');
    setStatus('ERROR', false, true);
  }
}

async function install() {
  if (!STATE.hasWallet) return;
  if (STATE.busy) {
    log('Request already in progress — wait for MetaMask to respond.', 'err');
    return;
  }
  
  STATE.busy = true;
  EL('installBtn').disabled = true;
  EL('checkBtn').disabled = true;
  log(`Initiating install sequence for ${STATE.snapId}...`);
  
  try {
    await window.ethereum.request({
      method: 'wallet_requestSnaps',
      params: { [STATE.snapId]: {} },
    });
    log('Installation sequence complete.');
    await checkStatus();
  } catch (e) {
    log(`Install aborted: ${e.message}`, 'err');
  } finally {
    STATE.busy = false;
    EL('installBtn').disabled = false;
    EL('checkBtn').disabled = false;
  }
}

// ─── Signature Samples ───
const SAMPLES = {
  loginMessage: {
    method: 'personal_sign',
    label: 'Login Message',
    build: (addr) => ({
      method: 'personal_sign',
      params: [
        '0x' + Array.from(new TextEncoder().encode('Sign in to ExampleDApp\nNonce: 8a3b1f\nTimestamp: 2025-01-01T00:00:00Z'))
          .map(b => b.toString(16).padStart(2, '0')).join(''),
        addr,
      ],
    }),
  },
  hexMessage: {
    method: 'personal_sign',
    label: 'Hex Message',
    build: (addr) => ({
      method: 'personal_sign',
      params: ['0xdeadbeefcafebabe0000000000000000000000000000000000000000feedface', addr],
    }),
  },
  permit2Unlimited: {
    method: 'eth_signTypedData_v4',
    label: 'Permit2 Unlimited',
    build: (addr) => ({
      method: 'eth_signTypedData_v4',
      params: [addr, JSON.stringify({
        types: {
          EIP712Domain: [
            { name: 'name', type: 'string' },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' },
          ],
          PermitSingle: [
            { name: 'details', type: 'PermitDetails' },
            { name: 'spender', type: 'address' },
            { name: 'sigDeadline', type: 'uint256' },
          ],
          PermitDetails: [
            { name: 'token', type: 'address' },
            { name: 'amount', type: 'uint160' },
            { name: 'expiration', type: 'uint48' },
            { name: 'nonce', type: 'uint48' },
          ],
        },
        primaryType: 'PermitSingle',
        domain: { name: 'Permit2', chainId: 1, verifyingContract: '0x000000000022D473030F116dDEE9F6B43aC78BA3' },
        message: {
          details: {
            token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            amount: '0xffffffffffffffffffffffffffffffffffffffff',
            expiration: '281474976710655',
            nonce: '0',
          },
          spender: '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
          sigDeadline: '1999999999',
        },
      })],
    }),
  },
  seaportOrder: {
    method: 'eth_signTypedData_v4',
    label: 'Seaport Order',
    build: (addr) => ({
      method: 'eth_signTypedData_v4',
      params: [addr, JSON.stringify({
        types: {
          EIP712Domain: [
            { name: 'name', type: 'string' },
            { name: 'version', type: 'string' },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' },
          ],
          OrderComponents: [
            { name: 'offerer', type: 'address' },
            { name: 'zone', type: 'address' },
            { name: 'offer', type: 'OfferItem[]' },
            { name: 'consideration', type: 'ConsiderationItem[]' },
            { name: 'orderType', type: 'uint8' },
            { name: 'startTime', type: 'uint256' },
            { name: 'endTime', type: 'uint256' },
            { name: 'salt', type: 'uint256' },
            { name: 'conduitKey', type: 'bytes32' },
            { name: 'counter', type: 'uint256' },
          ],
          OfferItem: [
            { name: 'itemType', type: 'uint8' },
            { name: 'token', type: 'address' },
            { name: 'identifierOrCriteria', type: 'uint256' },
            { name: 'startAmount', type: 'uint256' },
            { name: 'endAmount', type: 'uint256' },
          ],
          ConsiderationItem: [
            { name: 'itemType', type: 'uint8' },
            { name: 'token', type: 'address' },
            { name: 'identifierOrCriteria', type: 'uint256' },
            { name: 'startAmount', type: 'uint256' },
            { name: 'endAmount', type: 'uint256' },
            { name: 'recipient', type: 'address' },
          ],
        },
        primaryType: 'OrderComponents',
        domain: { name: 'Seaport', version: '1.5', chainId: 1, verifyingContract: '0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC' },
        message: {
          offerer: addr,
          zone: '0x0000000000000000000000000000000000000000',
          offer: [{ itemType: 2, token: '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D', identifierOrCriteria: '1234', startAmount: '1', endAmount: '1' }],
          consideration: [{ itemType: 0, token: '0x0000000000000000000000000000000000000000', identifierOrCriteria: '0', startAmount: '500000000000000000', endAmount: '500000000000000000', recipient: addr }],
          orderType: 0,
          startTime: '0',
          endTime: '1999999999',
          salt: '12345',
          conduitKey: '0x0000000000000000000000000000000000000000000000000000000000000000',
          counter: '0',
        },
      })],
    }),
  },
  daiPermit: {
    method: 'eth_signTypedData_v4',
    label: 'DAI Permit',
    build: (addr) => ({
      method: 'eth_signTypedData_v4',
      params: [addr, JSON.stringify({
        types: {
          EIP712Domain: [
            { name: 'name', type: 'string' },
            { name: 'version', type: 'string' },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' },
          ],
          Permit: [
            { name: 'holder', type: 'address' },
            { name: 'spender', type: 'address' },
            { name: 'nonce', type: 'uint256' },
            { name: 'expiry', type: 'uint256' },
            { name: 'allowed', type: 'bool' },
          ],
        },
        primaryType: 'Permit',
        domain: { name: 'Dai Stablecoin', version: '1', chainId: 1, verifyingContract: '0x6B175474E89094C44Da98b954EedeAC495271d0F' },
        message: { holder: addr, spender: '0xDef1C0ded9bec7F1a1670819833240f027b25EfF', nonce: '0', expiry: '1999999999', allowed: true },
      })],
    }),
  },
  blindEthSign: {
    method: 'personal_sign',
    label: 'Blind Hex Sign',
    // personal_sign is supported by MetaMask, unlike eth_sign in many dapp contexts.
    // Using an opaque hex payload still reproduces the same "blind signature" phishing UX.
    build: (addr) => ({
      method: 'personal_sign',
      params: [
        '0x4a5c5d454721bbbb25540c3317521e71c373ae36fef33a82cb1c4f2bf2d79dc3',
        addr,
      ],
    }),
  },
  phishingPermit: {
    method: 'eth_signTypedData_v4',
    label: 'Phishing Permit',
    // Uses the same Permit2 shape that MetaMask already accepts in the working sample,
    // but swaps in an attacker-controlled spender and keeps the unlimited amount.
    build: (addr) => ({
      method: 'eth_signTypedData_v4',
      params: [addr, JSON.stringify({
        types: {
          EIP712Domain: [
            { name: 'name', type: 'string' },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' },
          ],
          PermitSingle: [
            { name: 'details', type: 'PermitDetails' },
            { name: 'spender', type: 'address' },
            { name: 'sigDeadline', type: 'uint256' },
          ],
          PermitDetails: [
            { name: 'token', type: 'address' },
            { name: 'amount', type: 'uint160' },
            { name: 'expiration', type: 'uint48' },
            { name: 'nonce', type: 'uint48' },
          ],
        },
        primaryType: 'PermitSingle',
        domain: {
          name: 'Permit2',
          chainId: 1,
          verifyingContract: '0x000000000022D473030F116dDEE9F6B43aC78BA3',
        },
        message: {
          details: {
            token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            // MAX_UINT160 = unlimited Permit2 allowance
            amount: '1461501637330902918203684832716283019655932542975',
            expiration: '281474976710655',
            nonce: '0',
          },
          // Attacker-controlled spender instead of a known router
          spender: '0xbaDc0FFee0000000000000000000000000000001',
          sigDeadline: '1999999999',
        },
      })],
    }),
  },
  nftDrainer: {
    method: 'eth_signTypedData_v4',
    label: 'NFT Drainer',
    // Seaport order: user offers a Bored Ape NFT, consideration is 0 ETH.
    // Attacker receives the NFT for free. Classic NFT drainer via fake "claim" site.
    build: (addr) => ({
      method: 'eth_signTypedData_v4',
      params: [addr, JSON.stringify({
        types: {
          EIP712Domain: [
            { name: 'name',    type: 'string'  },
            { name: 'version', type: 'string'  },
            { name: 'chainId', type: 'uint256' },
            { name: 'verifyingContract', type: 'address' },
          ],
          OrderComponents: [
            { name: 'offerer',   type: 'address' },
            { name: 'zone',      type: 'address' },
            { name: 'offer',          type: 'OfferItem[]'         },
            { name: 'consideration',  type: 'ConsiderationItem[]' },
            { name: 'orderType',  type: 'uint8'   },
            { name: 'startTime',  type: 'uint256' },
            { name: 'endTime',    type: 'uint256' },
            { name: 'salt',       type: 'uint256' },
            { name: 'conduitKey', type: 'bytes32' },
            { name: 'counter',    type: 'uint256' },
          ],
          OfferItem: [
            { name: 'itemType', type: 'uint8'   },
            { name: 'token',    type: 'address' },
            { name: 'identifierOrCriteria', type: 'uint256' },
            { name: 'startAmount', type: 'uint256' },
            { name: 'endAmount',   type: 'uint256' },
          ],
          ConsiderationItem: [
            { name: 'itemType', type: 'uint8'   },
            { name: 'token',    type: 'address' },
            { name: 'identifierOrCriteria', type: 'uint256' },
            { name: 'startAmount', type: 'uint256' },
            { name: 'endAmount',   type: 'uint256' },
            { name: 'recipient',   type: 'address' },
          ],
        },
        primaryType: 'OrderComponents',
        domain: {
          name: 'Seaport',
          version: '1.5',
          chainId: 1,
          verifyingContract: '0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC',
        },
        message: {
          offerer: addr,
          zone: '0x0000000000000000000000000000000000000000',
          offer: [{
            itemType: 2, // ERC-721
            token: '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D', // BAYC
            identifierOrCriteria: '3681',
            startAmount: '1',
            endAmount: '1',
          }],
          // Zero-value consideration — user gets nothing in return
          consideration: [{
            itemType: 0, // ETH
            token: '0x0000000000000000000000000000000000000000',
            identifierOrCriteria: '0',
            startAmount: '0',
            endAmount: '0',
            // Attacker's wallet receives the NFT
            recipient: '0xbaDc0FFee0000000000000000000000000000001',
          }],
          orderType: 0,
          startTime: '0',
          endTime: '1999999999',
          salt: '99999',
          conduitKey: '0x0000000000000000000000000000000000000000000000000000000000000000',
          counter: '0',
        },
      })],
    }),
  },
};

async function triggerSample(key) {
  const sample = SAMPLES[key];
  if (!sample) { log(`Unknown sample: ${key}`, 'err'); return; }
  if (!STATE.hasWallet) { log('No wallet detected — cannot trigger sample.', 'err'); return; }
  if (STATE.busy) { log('Request already in progress — wait for MetaMask to respond.', 'err'); return; }

  STATE.busy = true;
  // Disable all sample buttons while busy
  document.querySelectorAll('.sample-row').forEach(b => b.disabled = true);

  try {
    log(`[${sample.label}] Requesting account...`);
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    const addr = accounts[0];
    log(`[${sample.label}] Account: ${addr.slice(0,6)}...${addr.slice(-4)}`);

    const rpc = sample.build(addr);
    log(`[${sample.label}] Sending ${rpc.method}...`);
    const result = await window.ethereum.request(rpc);
    log(`[${sample.label}] Result: ${typeof result === 'string' ? result.slice(0, 42) + '...' : JSON.stringify(result)}`);
  } catch (e) {
    const reason = e?.code === 4001 ? 'User rejected' : e.message;
    log(`[${sample.label}] ${reason}`, 'err');
  } finally {
    STATE.busy = false;
    document.querySelectorAll('.sample-row').forEach(b => b.disabled = false);
  }
}

// ─── Wallet Connect ───
const CHAINS = {
  '0x1': 'Ethereum Mainnet',
  '0x5': 'Goerli',
  '0xaa36a7': 'Sepolia',
  '0x89': 'Polygon',
  '0xa4b1': 'Arbitrum One',
  '0xa': 'Optimism',
  '0x38': 'BNB Chain',
  '0xe708': 'Linea',
  '0x2105': 'Base',
  '0x539': 'Localhost',
};

function updateWalletUI() {
  const dot = EL('walletDot');
  const chain = EL('walletChain');
  const addr = EL('walletAddr');
  const actions = EL('walletActions');

  if (STATE.connectedAddr) {
    const short = STATE.connectedAddr.slice(0, 6) + '...' + STATE.connectedAddr.slice(-4);
    const chainHex = STATE.chainId;
    const chainName = CHAINS[chainHex] || `Chain ${parseInt(chainHex, 16)}`;

    dot.className = 'wallet-dot connected';
    chain.textContent = chainName;
    addr.style.display = 'none'; // Hide text address
    
    // Green connected button with address
    actions.innerHTML = `<button class="wallet-btn connected-btn" id="walletDisconnectBtn" title="Disconnect">${short}</button>`;
    EL('walletDisconnectBtn').onclick = disconnectWallet;
  } else {
    dot.className = 'wallet-dot';
    chain.textContent = 'NOT CONNECTED';
    addr.style.display = 'inline'; // Show placeholder if needed, or keep hidden
    addr.textContent = '';
    
    // Gray connect button
    actions.innerHTML = '<button class="wallet-btn connect-btn" id="walletConnectBtn">Connect Wallet</button>';
    EL('walletConnectBtn').onclick = connectWallet;
  }
}

async function connectWallet() {
  if (!STATE.hasWallet) {
    log('No MetaMask provider found — install MetaMask first.', 'err');
    return;
  }
  if (STATE.busy) {
    log('Request in progress — wait for MetaMask.', 'err');
    return;
  }

  STATE.busy = true;
  try {
    log('Wallet connect requested...');
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    if (accounts.length > 0) {
      STATE.connectedAddr = accounts[0];
      const chainId = await window.ethereum.request({ method: 'eth_chainId' });
      STATE.chainId = chainId;
      log(`Wallet connected: ${STATE.connectedAddr.slice(0,6)}...${STATE.connectedAddr.slice(-4)}`);
      updateWalletUI();
    }
  } catch (e) {
    const reason = e?.code === 4001 ? 'User rejected connection' : e.message;
    log(`Wallet connect failed: ${reason}`, 'err');
  } finally {
    STATE.busy = false;
  }
}

function disconnectWallet() {
  STATE.connectedAddr = null;
  STATE.chainId = null;
  log('Wallet disconnected (local).');
  updateWalletUI();
}

function setupWalletListeners() {
  if (!window.ethereum) return;

  window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
      STATE.connectedAddr = null;
      STATE.chainId = null;
      log('Wallet account disconnected by user.', 'err');
    } else {
      STATE.connectedAddr = accounts[0];
      log(`Wallet account changed: ${accounts[0].slice(0,6)}...${accounts[0].slice(-4)}`);
    }
    updateWalletUI();
  });

  window.ethereum.on('chainChanged', (chainId) => {
    STATE.chainId = chainId;
    const name = CHAINS[chainId] || `Chain ${parseInt(chainId, 16)}`;
    log(`Network switched: ${name}`);
    updateWalletUI();
  });
}

// ─── Bindings ───
EL('installBtn').onclick = install;
EL('checkBtn').onclick = () => checkStatus();

// Sample panel bindings
document.querySelectorAll('.sample-row').forEach(btn => {
  btn.addEventListener('click', () => triggerSample(btn.dataset.sample));
});

// Wallet connect binding
EL('walletConnectBtn').onclick = connectWallet;

// ─── Boot ───
init();
setupWalletListeners();

// Auto-detect already-connected accounts (silent)
(async () => {
  if (!window.ethereum) return;
  try {
    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
    if (accounts.length > 0) {
      STATE.connectedAddr = accounts[0];
      STATE.chainId = await window.ethereum.request({ method: 'eth_chainId' });
      updateWalletUI();
      log(`Wallet auto-detected: ${accounts[0].slice(0,6)}...${accounts[0].slice(-4)}`);
    }
  } catch (_) { /* silent */ }
})();
