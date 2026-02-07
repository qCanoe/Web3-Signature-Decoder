/* ─── MINIMALIST CONTROLLER ─── */

const EL = (id) => document.getElementById(id);
const STATE = {
  snapId: "local:http://localhost:8080",
  hasWallet: false,
  busy: false            // lock to prevent concurrent MetaMask requests
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

// ─── Bindings ───
EL('installBtn').onclick = install;
EL('checkBtn').onclick = () => checkStatus();

// ─── Boot ───
init();
