const snapInput = document.getElementById("snapId");
const connectButton = document.getElementById("connectButton");
const checkButton = document.getElementById("checkButton");
const statusBox = document.getElementById("status");

function setStatus(message) {
  statusBox.textContent = `Status: ${message}`;
}

async function ensureProvider() {
  if (!window.ethereum) {
    setStatus("MetaMask not found. Please open in MetaMask Flask.");
    return false;
  }
  return true;
}

async function connectSnap() {
  if (!(await ensureProvider())) return;
  const snapId = snapInput.value.trim();
  if (!snapId) {
    setStatus("Snap ID is required.");
    return;
  }

  try {
    setStatus("Requesting snap install...");
    await window.ethereum.request({
      method: "wallet_requestSnaps",
      params: {
        [snapId]: {},
      },
    });
    setStatus("Snap installed or already approved.");
  } catch (error) {
    setStatus(`Install failed: ${error?.message || error}`);
  }
}

async function checkInstalled() {
  if (!(await ensureProvider())) return;
  try {
    const snaps = await window.ethereum.request({
      method: "wallet_getSnaps",
    });
    const snapId = snapInput.value.trim();
    let installed = false;
    if (Array.isArray(snaps)) {
      installed = snaps.some((snap) => snap && snap.id === snapId);
    } else if (snaps && typeof snaps === "object") {
      installed = Object.prototype.hasOwnProperty.call(snaps, snapId);
    }
    setStatus(installed ? "Snap is installed." : "Snap not installed.");
  } catch (error) {
    setStatus(`Check failed: ${error?.message || error}`);
  }
}

connectButton.addEventListener("click", connectSnap);
checkButton.addEventListener("click", checkInstalled);
