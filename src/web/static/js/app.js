/**
 * Signature Confirmation Interface JavaScript
 * Left-right layout + Advanced risk display UI
 */

// Global variables
let testData = {};
let currentSignatureData = null;

// Initialize after page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSignatureInterface();
});

/**
 * Initialize signature interface
 */
function initializeSignatureInterface() {
    console.log('Initializing signature confirmation interface');
    loadTestDataFromServer();
    bindEventListeners();
    showWelcomeState();
}

/**
 * Bind event listeners
 */
function bindEventListeners() {
    // Test data selector
    const testDataSelect = document.getElementById('testDataSelect');
    if (testDataSelect) {
        testDataSelect.addEventListener('change', function() {
            const selectedKey = this.value;
            if (selectedKey && testData[selectedKey]) {
                loadSelectedTestData(selectedKey);
            }
        });
    }
    
    // Input change listener
    const signatureInput = document.getElementById('signatureInput');
    if (signatureInput) {
        signatureInput.addEventListener('input', function() {
            updateInputStatus();
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl+Enter confirm signature
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            if (currentSignatureData) {
                confirmSignature();
            }
        }
        
        // Escape reject signature
        if (event.key === 'Escape') {
            event.preventDefault();
            if (currentSignatureData) {
                rejectSignature();
            }
        }
    });
}

/**
 * Load test data from server
 */
async function loadTestDataFromServer() {
    try {
        const response = await fetch('/api/test_data');
        const data = await response.json();
        
        if (data.success) {
            testData = data.test_data;
            populateTestDataSelect();
        } else {
            console.error('Failed to load test data:', data.error);
        }
    } catch (error) {
        console.error('Error loading test data:', error);
    }
}

/**
 * Populate test data selector
 */
function populateTestDataSelect() {
    const select = document.getElementById('testDataSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select test data...</option>';
    
    // Add all test data as flat list
    Object.keys(testData).forEach(key => {
        const item = testData[key];
        const option = document.createElement('option');
        option.value = key;
        option.textContent = item.description || key;
        select.appendChild(option);
    });
}

/**
 * Show/hide test data selector
 */
function loadTestData() {
    const testDataSelect = document.getElementById('testDataSelect');
    
    if (testDataSelect) {
        if (testDataSelect.style.display === 'none') {
            testDataSelect.style.display = 'block';
            if (Object.keys(testData).length === 0) {
                loadTestDataFromServer();
            }
            testDataSelect.focus();
        } else {
            testDataSelect.style.display = 'none';
        }
    }
}

/**
 * Load selected test data
 */
function loadSelectedTestData(key) {
    if (!testData[key]) return;
    
        const input = document.getElementById('signatureInput');
    if (input) {
        input.value = JSON.stringify(testData[key].data, null, 2);
        
        const testDataSelect = document.getElementById('testDataSelect');
        if (testDataSelect) {
            testDataSelect.style.display = 'none';
        }
        
        updateInputStatus();
        showToast('Test data loaded', 'success');
        
        // Auto parse
        setTimeout(() => {
            parseSignature();
        }, 500);
    }
}

/**
 * Clear input
 */
function clearInput() {
        const input = document.getElementById('signatureInput');
    if (input) {
        input.value = '';
        
        const select = document.getElementById('testDataSelect');
        if (select) {
            select.value = '';
            select.style.display = 'none';
        }
        
        updateInputStatus();
        showWelcomeState();
    }
}
        
/**
 * Update input status
 */
function updateInputStatus() {
        const input = document.getElementById('signatureInput');
    const statusElement = document.getElementById('inputStatus');
    
    if (!input || !statusElement) return;
    
    const hasInput = input.value.trim().length > 0;
    const statusIcon = statusElement.querySelector('i');
    const statusText = statusElement.querySelector('span');
    
    if (hasInput) {
        statusIcon.className = 'fas fa-check-circle';
        statusText.textContent = 'Data entered, click parse button to analyze';
        statusElement.style.background = '#f0fdf4';
        statusElement.style.borderColor = '#bbf7d0';
        statusElement.style.color = '#166534';
    } else {
        statusIcon.className = 'fas fa-info-circle';
        statusText.textContent = 'Please input EIP712 data to sign';
        statusElement.style.background = '#f0f9ff';
        statusElement.style.borderColor = '#bae6fd';
        statusElement.style.color = '#0369a1';
    }
}

/**
 * Parse signature data
 */
async function parseSignature() {
        const input = document.getElementById('signatureInput');
    
    if (!input || !input.value.trim()) {
        showToast('Please input data to sign', 'error');
        return;
    }
    
    showLoadingState();
    
    try {
        let signatureData;
        try {
            signatureData = JSON.parse(input.value);
        } catch (e) {
            throw new Error('Invalid data format, please input valid JSON');
        }
        
        const response = await fetch('/api/parse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: signatureData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentSignatureData = result;
            showSignatureState(result);
            showToast('Signature data loaded', 'success');
        } else {
            showErrorState(result.error);
            showToast('Loading failed', 'error');
        }
        
    } catch (error) {
        showErrorState(error.message);
        showToast('Loading failed', 'error');
    }
}

/**
 * Show signature confirmation state
 */
function showSignatureState(result) {
    hideAllStates();
    
    const signatureState = document.getElementById('signatureState');
    if (signatureState) {
        signatureState.style.display = 'block';
    }
    
    // Update request origin info
    updateRequestOrigin(result.raw_result.domain_info);
    
    // Update simplified risk assessment
    updateSimpleRiskAssessment(result.raw_result.english_description);
    
    // Update AI explanation
    updateAIExplanation(result.raw_result.english_description);
}

/**
 * Update request origin info
 */
function updateRequestOrigin(domainInfo) {
    const requestOrigin = document.getElementById('requestOrigin');
    const originName = document.getElementById('originName');
    const originDomain = document.getElementById('originDomain');
    
    if (domainInfo && domainInfo.name) {
        if (requestOrigin) requestOrigin.style.display = 'block';
        if (originName) originName.textContent = domainInfo.name;
        if (originDomain) {
            const contract = domainInfo.verifyingContract;
            if (contract) {
                originDomain.textContent = `${contract.substring(0, 6)}...${contract.slice(-4)}`;
            } else {
                originDomain.textContent = 'Unknown Contract';
            }
        }
    } else {
        if (requestOrigin) requestOrigin.style.display = 'none';
    }
}

/**
 * Update simplified risk assessment
 */
function updateSimpleRiskAssessment(englishData) {
    const riskAssessment = document.getElementById('riskAssessment');
    if (!riskAssessment) return;
    
    const riskLevel = englishData && englishData.risk_level ? englishData.risk_level.toLowerCase() : 'low';
    const riskExplanation = englishData && englishData.risk_explanation ? englishData.risk_explanation : '';
    
    // Get risk info (with custom explanation if available)
    const riskInfo = getSimpleRiskInfo(riskLevel, riskExplanation);
    
    // Create simplified risk assessment HTML
    const riskHTML = `
        <div class="risk-circle-simple ${riskLevel}">
            <img src="${riskInfo.icon}" alt="${riskLevel} risk" class="risk-circle-icon">
        </div>
        <div class="risk-info-simple">
            <div class="risk-title-simple ${riskLevel}">
                ${riskInfo.title}
            </div>
            <div class="risk-desc-simple">
                ${riskInfo.description}
            </div>
        </div>
    `;
    
    riskAssessment.innerHTML = riskHTML;
}

/**
 * Get simplified risk info
 */
function getSimpleRiskInfo(riskLevel, customExplanation) {
    // Use custom explanation from backend if available, otherwise use default
    const riskData = {
        'low': {
            title: 'Low Risk Operation',
            description: customExplanation || 'This is a relatively safe operation',
            icon: '/static/low.png'
        },
        'medium': {
            title: 'Medium Risk Operation', 
            description: customExplanation || 'Please carefully review signature content',
            icon: '/static/medium.png'
        },
        'high': {
            title: 'High Risk Operation',
            description: customExplanation || 'Warning: May involve important permissions or assets',
            icon: '/static/high.png'
        }
    };
    
    return riskData[riskLevel] || riskData.low;
}

/**
 * Update AI explanation
 */
function updateAIExplanation(englishData) {
    const aiExplanation = document.getElementById('aiExplanation');
    
    if (!englishData || englishData.error) {
        if (aiExplanation) {
            aiExplanation.style.display = 'none';
        }
        return;
    }
    
    if (aiExplanation) {
        aiExplanation.style.display = 'block';
    }
    
    const aiTitle = document.getElementById('aiTitle');
    const aiSummary = document.getElementById('aiSummary');
    
    if (aiTitle) {
        aiTitle.textContent = englishData.title || 'Smart Analysis';
    }
    
    if (aiSummary) {
        // Backend already provides highlighted HTML, so we can use it directly
        const summary = englishData.summary || 'AI is analyzing the meaning of this signature for you...';
        aiSummary.innerHTML = summary;
    }
}








/**
 * Confirm signature
 */
function confirmSignature() {
    if (!currentSignatureData) {
        showToast('No data to sign', 'error');
        return;
    }
    
    // Here you can integrate real signature logic
    showToast('Signature confirmed!', 'success');
    
    // Simulate post-signature completion state
    setTimeout(() => {
        showCompleteState();
    }, 1000);
}

/**
 * Reject signature
 */
function rejectSignature() {
    showToast('Signature rejected', 'info');
    
    setTimeout(() => {
        showWelcomeState();
        currentSignatureData = null;
    }, 1000);
}
    
/**
 * Show complete state
 */
function showCompleteState() {
    hideAllStates();
    
    const completeState = document.getElementById('completeState');
    if (completeState) {
        completeState.style.display = 'block';
    }
}

/**
 * Reset interface
 */
function resetInterface() {
    currentSignatureData = null;
    clearInput();
    showWelcomeState();
}

/**
 * Show welcome state
 */
function showWelcomeState() {
    hideAllStates();
    
    const welcomeState = document.getElementById('welcomeState');
    if (welcomeState) {
        welcomeState.style.display = 'block';
    }
    
    // Hide request origin
    const requestOrigin = document.getElementById('requestOrigin');
    if (requestOrigin) {
        requestOrigin.style.display = 'none';
    }
}

/**
 * Show loading state
 */
function showLoadingState() {
    hideAllStates();
    
    const loadingState = document.getElementById('loadingState');
    if (loadingState) {
        loadingState.style.display = 'block';
    }
    
    // Simulate loading steps
    setTimeout(() => {
        const steps = document.querySelectorAll('.step');
        if (steps.length >= 3) {
            steps[2].classList.add('active');
            steps[2].querySelector('i').className = 'fas fa-check';
        }
    }, 1500);
}

/**
 * Show error state
 */
function showErrorState(error) {
    hideAllStates();
    
    const errorState = document.getElementById('errorState');
    if (errorState) {
        errorState.style.display = 'block';
        
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = error || 'Please check data format';
        }
    }
}

/**
 * Hide all states
 */
function hideAllStates() {
    const states = [
        'welcomeState',
        'loadingState',
        'errorState',
        'signatureState',
        'completeState'
    ];
    
    states.forEach(stateId => {
        const state = document.getElementById(stateId);
        if (state) {
            state.style.display = 'none';
        }
    });
}

/**
 * Show Toast message
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Show animation
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Global function exports
window.loadTestData = loadTestData;
window.clearInput = clearInput;
window.parseSignature = parseSignature;
window.confirmSignature = confirmSignature;
window.rejectSignature = rejectSignature;
window.resetInterface = resetInterface;
window.showWelcomeState = showWelcomeState; 