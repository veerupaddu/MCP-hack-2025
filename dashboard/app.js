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
    fileList: document.getElementById('fileList')
};

// ===== Utility Functions =====
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour12: false });
}

function updateCharCount() {
    const count = elements.textarea.value.length;
    elements.charCount.textContent = count;
}

function updateConnectionStatus(connected) {
    state.connected = connected;
    const statusBadge = elements.connectionStatus;
    const statusText = statusBadge.querySelector('.status-text');

    if (connected) {
        statusBadge.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        statusBadge.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
}

function updateProgress() {
    const completedSteps = state.steps.filter(s => s.status === 'complete').length;
    const percentage = (completedSteps / state.steps.length) * 100;

    elements.progressFill.style.width = `${percentage}%`;
    elements.progressPercentage.textContent = `${Math.round(percentage)}%`;
}

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
        }

        return `
            <div class="step ${statusClass}">
                <div class="step-number">${step.id}</div>
                <div class="step-icon">${step.icon}</div>
                <div class="step-content">
                    <div class="step-name">${step.name}</div>
                    <div class="step-status">${statusIcon} ${statusText}${step.details ? ` - ${step.details}` : ''}</div>
                </div>
            </div>
        `;
    }).join('');
}

function addActivityLog(message, type = 'info') {
    const time = getCurrentTime();
    const logEntry = { time, message, type };
    state.activityLog.unshift(logEntry);

    // Keep only last 50 entries
    if (state.activityLog.length > 50) {
        state.activityLog = state.activityLog.slice(0, 50);
    }

    renderActivityLog();
}

function renderActivityLog() {
    elements.activityLog.innerHTML = state.activityLog.map(log => `
        <div class="log-entry log-${log.type}">
            <span class="log-time">${log.time}</span>
            <span class="log-message">${log.message}</span>
        </div>
    `).join('');
}

function addModifiedFile(filePath, status, stats = '') {
    const existingIndex = state.modifiedFiles.findIndex(f => f.path === filePath);

    if (existingIndex >= 0) {
        state.modifiedFiles[existingIndex] = { path: filePath, status, stats };
    } else {
        state.modifiedFiles.push({ path: filePath, status, stats });
    }

    renderFileList();
}

function renderFileList() {
    if (state.modifiedFiles.length === 0) {
        elements.fileList.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📄</span>
                <p>No files modified yet</p>
            </div>
        `;
        return;
    }

    elements.fileList.innerHTML = state.modifiedFiles.map(file => {
        const icon = file.status === 'added' ? '➕' :
            file.status === 'modified' ? '📝' : '➖';

        return `
            <div class="file-item">
                <div class="file-icon">${icon}</div>
                <div class="file-info">
                    <div class="file-path">${file.path}</div>
                    ${file.stats ? `<div class="file-stats">${file.stats}</div>` : ''}
                </div>
                <div class="file-badge ${file.status}">${file.status}</div>
            </div>
        `;
    }).join('');
}

function updateStepStatus(stepId, status, details = '') {
    const step = state.steps.find(s => s.id === stepId);
    if (step) {
        step.status = status;
        step.details = details;
        renderWorkflowSteps();
        updateProgress();
    }
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
            updateStepStatus(data.stepId, data.status, data.details);
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

        case 'error':
            addActivityLog(`Error: ${data.message}`, 'error');
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

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
