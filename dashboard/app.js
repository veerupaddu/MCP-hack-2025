// ===== Configuration =====
const CONFIG = {
    wsUrl: 'ws://localhost:8000/ws',
    apiUrl: 'http://localhost:8000/api'
};

// ===== Workflow Steps Definition =====
const WORKFLOW_STEPS = [
    { id: 1, name: 'Requirement Analysis', icon: '📝' },
    { id: 2, name: 'RAG & Fine-tuning Query', icon: '🧠' },
    { id: 3, name: 'Git Branch Created', icon: '🌿' },
    { id: 4, name: 'Code Generation', icon: '⚡' },
    { id: 5, name: 'Code Review', icon: '🔍' },
    { id: 6, name: 'Git Commit', icon: '💾' },
    { id: 7, name: 'Unit Testing', icon: '🧪' },
    { id: 8, name: 'Manual Approval', icon: '✋' },
    { id: 9, name: 'PR Submission', icon: '🚀' },
    { id: 10, name: 'PR Merge & Notification', icon: '🎉' }
];

// ===== State Management =====
let state = {
    ws: null,
    connected: false,
    currentStep: 0,
    steps: WORKFLOW_STEPS.map(step => ({
        ...step,
        status: 'pending',
        details: ''
    })),
    activityLog: [],
    modifiedFiles: []
};

// ===== DOM Elements =====
const elements = {
    form: document.getElementById('requirementForm'),
    textarea: document.getElementById('requirement'),
    charCount: document.getElementById('charCount'),
    submitBtn: document.getElementById('submitBtn'),
    connectionStatus: document.getElementById('connectionStatus'),
    progressFill: document.getElementById('progressFill'),
    progressPercentage: document.getElementById('progressPercentage'),
    workflowSteps: document.getElementById('workflowSteps'),
    activityLog: document.getElementById('activityLog'),
    fileList: document.getElementById('fileList'),
    // Modal Elements
    detailsModal: document.getElementById('detailsModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
    modalClose: document.getElementById('modalClose'),
    // Error Modal Elements
    errorModal: document.getElementById('errorModal'),
    errorModalBody: document.getElementById('errorModalBody'),
    errorModalClose: document.getElementById('errorModalClose'),
    errorModalOk: document.getElementById('errorModalOk')
};

// ... (Utility functions remain same) ...

function renderWorkflowSteps() {
    elements.workflowSteps.innerHTML = state.steps.map(step => {
        let statusIcon = '⏳';
        let statusText = 'Pending';
        let statusClass = 'pending';

        if (step.status === 'complete') {
            statusIcon = '✅';
            statusText = 'Complete';
            statusClass = 'complete';
        } else if (step.status === 'in-progress') {
            statusIcon = '🔄';
            statusText = 'In Progress';
            statusClass = 'in-progress';
        } else if (step.status === 'error') {
            statusIcon = '❌';
            statusText = 'Error';
            statusClass = 'error';
        }

        const hasData = step.data && Object.keys(step.data).length > 0;
        const detailsBtn = hasData
            ? `<button class="btn-details" onclick="showStepDetails(${step.id})">View Details</button>`
            : '';

        return `
                <div class="step ${statusClass}">
                    <div class="step-number">${step.id}</div>
                    <div class="step-icon">${step.icon}</div>
                    <div class="step-content">
                        <div class="step-name">${step.name}</div>
                        <div class="step-status">${statusIcon} ${statusText}${step.details ? ` - ${step.details}` : ''}</div>
                    </div>
                    ${detailsBtn}
                </div>
            `;
    }).join('');
}

// ... (Activity Log and File List functions remain same) ...

function updateStepStatus(stepId, status, details = '', data = null) {
    const step = state.steps.find(s => s.id === stepId);
    if (step) {
        step.status = status;
        step.details = details;
        if (data) {
            step.data = data;
        }
        renderWorkflowSteps();
        updateProgress();
    }
}

// ===== Modal Logic =====
window.showStepDetails = function (stepId) {
    const step = state.steps.find(s => s.id === stepId);
    if (!step || !step.data) return;

    elements.modalTitle.textContent = `${step.icon} ${step.name} - Details`;

    // Format data for display
    const dataHtml = Object.entries(step.data).map(([key, value]) => {
        // Format key (snake_case to Title Case)
        const label = key.replace(/_/g, ' ');

        // Format value
        let displayValue = value;
        if (Array.isArray(value)) {
            displayValue = value.map(v => `• ${v}`).join('\n');
        } else if (typeof value === 'object' && value !== null) {
            displayValue = JSON.stringify(value, null, 2);
        }

        return `
                <div class="data-item">
                    <div class="data-label">${label}</div>
                    <div class="data-value ${key.includes('status') ? 'highlight' : ''}">${displayValue}</div>
                </div>
            `;
    }).join('');

    elements.modalBody.innerHTML = `<div class="data-grid">${dataHtml}</div>`;
    elements.detailsModal.classList.add('active');
};

function closeModal() {
    elements.detailsModal.classList.remove('active');
}

function showErrorModal(title, message, details) {
    const errorHtml = `
        <div class="data-grid">
            <div class="data-item">
                <div class="data-label">Error Message</div>
                <div class="data-value" style="color: #f5576c;">${message}</div>
            </div>
            ${details ? `
            <div class="data-item">
                <div class="data-label">Details</div>
                <div class="data-value">${details}</div>
            </div>
            ` : ''}
        </div>
    `;
    elements.errorModalBody.innerHTML = errorHtml;
    elements.errorModal.classList.add('active');

    // Re-enable form
    elements.submitBtn.disabled = false;
    elements.textarea.disabled = false;
}

function closeErrorModal() {
    elements.errorModal.classList.remove('active');
}

if (elements.modalClose) {
    elements.modalClose.addEventListener('click', closeModal);
}

if (elements.errorModalClose) {
    elements.errorModalClose.addEventListener('click', closeErrorModal);
}

if (elements.errorModalOk) {
    elements.errorModalOk.addEventListener('click', closeErrorModal);
}

// Close on click outside
if (elements.detailsModal) {
    elements.detailsModal.addEventListener('click', (e) => {
        if (e.target === elements.detailsModal) {
            closeModal();
        }
    });
}

if (elements.errorModal) {
    elements.errorModal.addEventListener('click', (e) => {
        if (e.target === elements.errorModal) {
            closeErrorModal();
        }
    });
}

// ===== WebSocket Connection =====
function connectWebSocket() {
    try {
        state.ws = new WebSocket(CONFIG.wsUrl);

        state.ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus(true);
            addActivityLog('Connected to server', 'success');
        };

        state.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        state.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            addActivityLog('Connection error occurred', 'error');
        };

        state.ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            addActivityLog('Disconnected from server', 'warning');

            // Attempt to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        updateConnectionStatus(false);
        setTimeout(connectWebSocket, 5000);
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'step_update':
            updateStepStatus(data.stepId, data.status, data.details, data.data);
            addActivityLog(data.message, 'info');
            break;

        case 'log':
            addActivityLog(data.message, data.level || 'info');
            break;

        case 'file_modified':
            addModifiedFile(data.path, data.status, data.stats);
            addActivityLog(`File ${data.status}: ${data.path}`, 'info');
            break;

        case 'workflow_complete':
            addActivityLog('Workflow completed successfully!', 'success');
            break;

        case 'workflow_error':
            addActivityLog(`Error: ${data.message}`, 'error');
            showErrorModal(data.title || 'Workflow Error', data.message, data.details);
            break;

        case 'error':
            addActivityLog(`Error: ${data.message}`, 'error');
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

// ... (Rest of the file remains same) ...

// ===== Form Submission =====
async function handleSubmit(event) {
    event.preventDefault();

    const requirement = elements.textarea.value.trim();

    if (requirement.length < 50) {
        addActivityLog('Requirement too short. Please provide at least 50 characters.', 'warning');
        return;
    }

    // Disable form
    elements.submitBtn.disabled = true;
    elements.textarea.disabled = true;

    addActivityLog('Submitting requirement...', 'info');

    try {
        const response = await fetch(`${CONFIG.apiUrl}/submit-requirement`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ requirement })
        });

        if (response.ok) {
            const result = await response.json();
            addActivityLog('Requirement submitted successfully!', 'success');
            addActivityLog('Starting workflow...', 'info');

            // Start first step
            updateStepStatus(1, 'in-progress');
        } else {
            throw new Error('Failed to submit requirement');
        }
    } catch (error) {
        console.error('Submission error:', error);
        addActivityLog('Failed to submit requirement. Please try again.', 'error');

        // Re-enable form
        elements.submitBtn.disabled = false;
        elements.textarea.disabled = false;
    }
}

// ===== Event Listeners =====
elements.textarea.addEventListener('input', updateCharCount);
elements.form.addEventListener('submit', handleSubmit);

// ===== Initialization =====
function init() {
    console.log('Initializing AI Development Agent Dashboard...');

    // Render initial state
    renderWorkflowSteps();
    renderActivityLog();
    renderFileList();

    // Connect WebSocket
    connectWebSocket();

    // Add welcome message
    addActivityLog('System ready. Waiting for input...', 'info');
}

// Start the application
init();
