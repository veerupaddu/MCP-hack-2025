// ===== Configuration =====
const CONFIG = {
    wsUrl: 'ws://localhost:8000/ws',
    apiUrl: 'http://localhost:8000/api'
};

// ===== Workflow Steps Definition =====
const WORKFLOW_STEPS = [
    { id: 1, name: 'Requirement Analysis', icon: '📝', desc: 'AI analyzes your requirement' },
    { id: 2, name: 'RAG Product Research', icon: '🔍', desc: 'Query RAG for product specs & best practices' },
    { id: 3, name: 'Fine-tuned Analysis', icon: '🧠', desc: 'Domain-specific insights from fine-tuned model' },
    { id: 4, name: 'Craft User Stories', icon: '📖', desc: 'LLM generates user stories from analysis' },
    { id: 5, name: 'Create JIRA Epic & Stories', icon: '📋', desc: 'Creates epic and stories in JIRA' },
    { id: 6, name: 'Generate Tasks', icon: '✅', desc: 'Break down stories into dev tasks' },
    { id: 7, name: 'Create Git Branch', icon: '🌿', desc: 'Create feature branch' },
    { id: 8, name: 'Code Generation', icon: '⚡', desc: 'AI generates implementation' },
    { id: 9, name: 'Code Review & Testing', icon: '🧪', desc: 'Review and test code' },
    { id: 10, name: 'PR, Merge & Deploy', icon: '🎉', desc: 'Create PR, merge and deploy' }
];

// ===== State Management =====
let state = {
    ws: null,
    connected: false,
    currentStep: 0,
    steps: WORKFLOW_STEPS.map(step => ({
        ...step,
        status: 'pending',
        details: '',
        data: null
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
    stopBtn: document.getElementById('stopBtn'),
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


// ===== Utility Functions =====
function updateCharCount() {
    const count = elements.textarea.value.length;
    elements.charCount.textContent = count;
}

function updateConnectionStatus(connected) {
    state.connected = connected;
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');

    if (connected) {
        statusDot.style.backgroundColor = '#4ade80';
        statusText.textContent = 'Connected';
        elements.connectionStatus.classList.add('connected');
    } else {
        statusDot.style.backgroundColor = '#f87171';
        statusText.textContent = 'Disconnected';
        elements.connectionStatus.classList.remove('connected');
    }
}

function updateProgress() {
    const completedSteps = state.steps.filter(s => s.status === 'complete').length;
    const percentage = Math.round((completedSteps / state.steps.length) * 100);

    elements.progressFill.style.width = `${percentage}%`;
    elements.progressPercentage.textContent = `${percentage}%`;
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ===== Activity Log Functions =====
function addActivityLog(message, level = 'info') {
    const entry = {
        message,
        level,
        timestamp: new Date().toISOString()
    };
    state.activityLog.push(entry);
    renderActivityLog();
}

function renderActivityLog() {
    if (state.activityLog.length === 0) {
        elements.activityLog.innerHTML = `
            <div class="log-entry log-info">
                <span class="log-time">--:--:--</span>
                <span class="log-message">System ready. Waiting for input...</span>
            </div>
        `;
        return;
    }

    elements.activityLog.innerHTML = state.activityLog
        .slice(-50) // Keep last 50 entries
        .reverse()
        .map(entry => `
            <div class="log-entry log-${entry.level}">
                <span class="log-time">${formatTime(entry.timestamp)}</span>
                <span class="log-message">${entry.message}</span>
            </div>
        `).join('');

    // Auto-scroll to top (newest entries)
    elements.activityLog.scrollTop = 0;
}

// ===== File List Functions =====
function addModifiedFile(path, status, stats = '') {
    const file = { path, status, stats };
    state.modifiedFiles.push(file);
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
        let statusIcon = '📄';
        if (file.status === 'added') statusIcon = '➕';
        else if (file.status === 'modified') statusIcon = '✏️';
        else if (file.status === 'deleted') statusIcon = '🗑️';

        return `
            <div class="file-item file-${file.status}">
                <span class="file-icon">${statusIcon}</span>
                <span class="file-path">${file.path}</span>
                ${file.stats ? `<span class="file-stats">${file.stats}</span>` : ''}
            </div>
        `;
    }).join('');
}

// ===== Workflow Steps Rendering =====
function restartFromStep(stepId) {
    // Reset steps after the selected one
    state.steps = state.steps.map(s => {
        if (s.id < stepId) return { ...s, status: 'complete' };
        if (s.id === stepId) return { ...s, status: 'in-progress', details: '', data: null };
        return { ...s, status: 'pending', details: '', data: null };
    });
    renderWorkflowSteps();
    updateProgress();
    addActivityLog(`User restarted workflow from step ${stepId}`, 'info');
    // Notify backend (optional – send a custom WS message)
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'restart_step', stepId }));
    }
}

// Updated renderWorkflowSteps to include a restart button
function renderWorkflowSteps() {
    elements.workflowSteps.innerHTML = state.steps.map(step => {
        let statusIcon = '⏳';
        let statusText = 'Pending';
        let statusClass = 'pending';
        if (step.status === 'complete') { statusIcon = '✅'; statusText = 'Complete'; statusClass = 'complete'; }
        else if (step.status === 'in-progress') { statusIcon = '🔄'; statusText = 'In Progress'; statusClass = 'in-progress'; }
        else if (step.status === 'error') { statusIcon = '❌'; statusText = 'Error'; statusClass = 'error'; }
        const hasData = step.data && Object.keys(step.data).length > 0;
        const detailsBtn = hasData ? `<button class="btn-details" onclick="showStepDetails(${step.id})">View Details</button>` : '';
        const restartBtn = step.status !== 'in-progress' ? `<button class="btn-restart" onclick="restartFromStep(${step.id})">Restart</button>` : '';
        return `
            <div class="step ${statusClass}">
                <div class="step-number">${step.id}</div>
                <div class="step-icon">${step.icon}</div>
                <div class="step-content">
                    <div class="step-name">${step.name}</div>
                    <div class="step-status">${statusIcon} ${statusText}${step.details ? ` - ${step.details}` : ''}</div>
                </div>
                ${detailsBtn}
                ${restartBtn}
            </div>
        `;
    }).join('');
}

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

    // Use appropriate formatter based on step
    let contentHtml = '';
    if (stepId === 1) {
        contentHtml = formatRequirementAnalysis(step.data);
    } else if (stepId === 2) {
        contentHtml = formatJiraData(step.data);
    } else {
        contentHtml = formatGenericData(step.data);
    }

    elements.modalBody.innerHTML = `
        ${contentHtml}
        <div class="modal-footer" style="margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem; display: flex; justify-content: flex-end;">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        </div>
    `;
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

// Modal event listeners
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
            // Re-enable form
            elements.submitBtn.disabled = false;
            elements.textarea.disabled = false;
            elements.stopBtn.style.display = 'none';
            break;

        case 'workflow_error':
            addActivityLog(`Error: ${data.message}`, 'error');
            showErrorModal(data.title || 'Workflow Error', data.message, data.details);
            elements.stopBtn.style.display = 'none';
            elements.submitBtn.disabled = false;
            elements.textarea.disabled = false;
            break;

        case 'error':
            addActivityLog(`Error: ${data.message}`, 'error');
            break;

        // Human-in-the-loop messages
        case 'requirement_analyzed':
        case 'rag_completed':
        case 'finetuned_completed':
        case 'stories_crafted':
        case 'jira_created':
        case 'tasks_generated':
        case 'git_branch_created':
        case 'code_generated':
        case 'review_testing_done':
        case 'deployed':
        case 'step_complete':
            // Show confirmation modal
            showStepConfirmation(data.stepId, data.data);
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

function showStepConfirmation(stepId, data) {
    const step = state.steps.find(s => s.id === stepId);
    if (!step) return;

    elements.modalTitle.textContent = `${step.icon} ${step.name} - Confirmation`;

    // Format data for display
    let contentHtml = '';
    if (data) {
        if (stepId === 1) {
            contentHtml = formatRequirementAnalysis(data);
        } else if (stepId === 2) {
            contentHtml = formatRAGData(data);
        } else if (stepId === 3) {
            contentHtml = formatFinetunedData(data);
        } else if (stepId === 4) {
            contentHtml = formatStoriesData(data);
        } else if (stepId === 5) {
            contentHtml = formatJiraData(data);
        } else {
            contentHtml = formatGenericData(data);
        }
    } else {
        contentHtml = '<p>Step completed. Proceed to next step?</p>';
    }

    elements.modalBody.innerHTML = `
        ${contentHtml}
        <div class="modal-footer" style="margin-top: 2rem; border-top: 1px solid var(--border-color); padding-top: 1rem; display: flex; justify-content: flex-end; gap: 1rem;">
            <button class="btn btn-secondary" onclick="resetWorkflowForEdit()">Modify Requirement</button>
            <button class="btn btn-primary" onclick="confirmStep(${stepId})">Proceed</button>
        </div>
    `;

    elements.detailsModal.classList.add('active');
}

// Format requirement analysis data nicely
function formatRequirementAnalysis(data) {
    const sections = [];
    
    // 1. Actual Question/Requirement
    if (data.user_query) {
        sections.push(`
            <div class="analysis-section question">
                <h4>📝 Requirement</h4>
                <p class="analysis-text">${escapeHtml(data.user_query)}</p>
            </div>
        `);
    }
    
    // 2. Summary (200-500 words)
    if (data.summary) {
        sections.push(`
            <div class="analysis-section summary">
                <h4>📋 Summary</h4>
                <p class="analysis-text">${escapeHtml(data.summary)}</p>
            </div>
        `);
    }
    
    // 3. Complexity to Develop
    if (data.complexity) {
        const complexityClass = getComplexityClass(data.complexity.level);
        sections.push(`
            <div class="analysis-section complexity">
                <h4>⚙️ Development Complexity</h4>
                <div class="complexity-card ${complexityClass}">
                    <div class="complexity-header">
                        <span class="complexity-level">${data.complexity.level}</span>
                        <span class="complexity-estimate">${data.complexity.estimate || ''}</span>
                    </div>
                    ${data.complexity.factors ? `
                        <div class="complexity-factors">
                            ${data.complexity.factors.map(f => `<span class="factor-tag">${escapeHtml(f)}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `);
    }
    
    // Source badge
    if (data.source) {
        sections.push(`<div class="analysis-meta"><span class="meta-badge source">🔗 ${data.source}</span></div>`);
    }
    
    return `<div class="analysis-container">${sections.join('')}</div>`;
}

function getComplexityClass(level) {
    if (!level) return '';
    const l = level.toLowerCase();
    if (l.includes('low') || l.includes('simple')) return 'complexity-low';
    if (l.includes('high') || l.includes('complex')) return 'complexity-high';
    return 'complexity-medium';
}

// Format RAG Product Research data (Step 2)
function formatRAGData(data) {
    const spec = data.spec || {};
    const features = data.features || spec.features || [];
    const techReqs = data.technical_requirements || spec.technical_requirements || [];
    const ragContext = data.rag_context || spec.full_answer || '';
    const source = data.source || 'unknown';
    
    return `
        <div class="rag-container">
            <div class="source-badge ${source.includes('direct') || source.includes('mcp') ? 'real' : 'mock'}">
                ${source.includes('direct') || source.includes('mcp') ? '✅ RAG Retrieved' : '⚠️ Fallback Mode'}
            </div>
            
            ${ragContext ? `
                <div class="rag-section">
                    <h4>📚 Product Research Context</h4>
                    <p class="rag-context">${escapeHtml(ragContext.substring(0, 500))}${ragContext.length > 500 ? '...' : ''}</p>
                </div>
            ` : ''}
            
            ${features.length > 0 ? `
                <div class="rag-section">
                    <h4>✨ Identified Features</h4>
                    <ul class="feature-list">
                        ${features.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${techReqs.length > 0 ? `
                <div class="rag-section">
                    <h4>🔧 Technical Requirements</h4>
                    <ul class="tech-list">
                        ${techReqs.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="rag-meta">
                <span class="meta-badge">Source: ${source}</span>
                ${spec.context_retrieved ? `<span class="meta-badge">${spec.context_retrieved} docs retrieved</span>` : ''}
            </div>
        </div>
    `;
}

// Format Fine-tuned Model data (Step 3)
function formatFinetunedData(data) {
    const recommendations = data.recommendations || [];
    const domain = data.domain || 'general';
    const source = data.source || 'unknown';
    
    return `
        <div class="ft-container">
            <div class="source-badge ${source.includes('real') ? 'real' : 'mock'}">
                ${source.includes('real') ? '✅ Fine-tuned Model' : '⚠️ Default Insights'}
            </div>
            
            <div class="ft-section">
                <h4>🧠 Domain: ${domain.charAt(0).toUpperCase() + domain.slice(1)}</h4>
            </div>
            
            ${recommendations.length > 0 ? `
                <div class="ft-section">
                    <h4>💡 Recommendations</h4>
                    <ul class="recommendation-list">
                        ${recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${data.ft_insights ? `
                <div class="ft-section">
                    <h4>📋 Detailed Insights</h4>
                    <p class="ft-insights">${escapeHtml(data.ft_insights.substring(0, 400))}${data.ft_insights.length > 400 ? '...' : ''}</p>
                </div>
            ` : ''}
        </div>
    `;
}

// Format User Stories data (Step 4)
function formatStoriesData(data) {
    const stories = data.stories || [];
    
    return `
        <div class="stories-container">
            <div class="stories-header">
                <h4>📖 Generated User Stories</h4>
                <span class="story-count">${stories.length} stories</span>
            </div>
            
            ${stories.length > 0 ? `
                <div class="stories-list">
                    ${stories.map((story, i) => `
                        <div class="story-card" data-index="${i}">
                            <div class="story-title">${escapeHtml(story.title || story.summary || 'Story ' + (i+1))}</div>
                            ${story.description ? `<div class="story-desc">${escapeHtml(story.description)}</div>` : ''}
                            ${story.acceptance ? `<div class="story-acceptance"><strong>Acceptance:</strong> ${escapeHtml(story.acceptance)}</div>` : ''}
                            <div class="story-meta">
                                <span class="story-points">${story.points || story.story_points || 3} pts</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : '<p>No stories generated</p>'}
        </div>
    `;
}

// Get icon for actor type
function getActorIcon(actor) {
    const actorLower = actor.toLowerCase();
    if (actorLower.includes('admin')) return '👨‍💼';
    if (actorLower.includes('user') || actorLower.includes('customer')) return '👤';
    if (actorLower.includes('developer') || actorLower.includes('dev')) return '👨‍💻';
    if (actorLower.includes('manager')) return '👔';
    if (actorLower.includes('system') || actorLower.includes('service')) return '🤖';
    if (actorLower.includes('guest') || actorLower.includes('visitor')) return '👁️';
    if (actorLower.includes('moderator')) return '🛡️';
    if (actorLower.includes('support')) return '🎧';
    return '👤';
}

// Helper to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format JIRA data (Step 2)
function formatJiraData(data) {
    const epic = data.epic || {};
    const epicKey = epic.key || data.jira_epic || 'N/A';
    const stories = data.stories || [];
    const tasks = data.tasks || [];
    const jiraSource = data.jira_source || 'unknown';
    
    let html = `
        <div class="jira-container">
            <!-- Source Badge -->
            <div class="source-badge ${jiraSource === 'real_jira' ? 'real' : 'mock'}">
                ${jiraSource === 'real_jira' ? '✅ Created in JIRA' : '⚠️ Mock Mode (JIRA not configured)'}
            </div>
            
            <!-- Epic Card -->
            <div class="jira-epic">
                <div class="jira-header">
                    <span class="jira-type epic">📋 Epic</span>
                    <span class="jira-key">${epicKey}</span>
                </div>
                <div class="jira-summary">${escapeHtml(epic.summary || 'Feature Implementation')}</div>
                <div class="jira-meta">
                    <span>🎯 ${stories.length} stories</span>
                    <span>📊 ${data.total_story_points || 0} points</span>
                    <span>📋 ${tasks.length} tasks</span>
                </div>
                ${epic.url ? `<a href="${epic.url}" target="_blank" class="jira-link">Open in JIRA →</a>` : ''}
            </div>
            
            <!-- RAG Context -->
            ${data.rag_context ? `
                <div class="rag-context">
                    <h4>🧠 RAG Context</h4>
                    <p>${escapeHtml(data.rag_context)}</p>
                </div>
            ` : ''}
            
            <!-- User Stories -->
            <div class="jira-stories">
                <h4>📝 User Stories (${stories.length})</h4>
                ${stories.map(story => `
                    <div class="story-card">
                        <div class="story-header">
                            <span class="jira-key">${story.key || 'NEW'}</span>
                            <span class="story-points">${story.story_points || story.points || 3} pts</span>
                        </div>
                        <div class="story-summary">${escapeHtml(story.summary || story.title || '')}</div>
                        ${story.description ? `<div class="story-desc">${escapeHtml(story.description)}</div>` : ''}
                        ${story.acceptance ? `<div class="story-acceptance">✓ ${escapeHtml(story.acceptance)}</div>` : ''}
                    </div>
                `).join('')}
            </div>
            
            <!-- Development Tasks -->
            ${tasks.length > 0 ? `
                <div class="dev-tasks">
                    <h4>📋 Development Tasks (${tasks.length})</h4>
                    ${tasks.map(task => `
                        <div class="task-item">
                            <span class="task-story">${escapeHtml(task.story || '')}</span>
                            <span class="task-name">${escapeHtml(task.name || '')}</span>
                            <span class="task-hours">${task.hours || '4'}h</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// CRUD Operations
window.showAddStoryModal = function(epicKey) {
    elements.modalTitle.textContent = '📝 Add User Story';
    elements.modalBody.innerHTML = `
        <div class="form-group">
            <label>Summary</label>
            <input type="text" id="storySummary" class="form-input" placeholder="As a user, I want to...">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="storyDescription" class="form-textarea" rows="3" placeholder="Detailed description..."></textarea>
        </div>
        <div class="form-group">
            <label>Story Points</label>
            <select id="storyPoints" class="form-select">
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3" selected>3</option>
                <option value="5">5</option>
                <option value="8">8</option>
            </select>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="createStory('${epicKey}')">Create Story</button>
        </div>
    `;
    elements.detailsModal.classList.add('active');
};

window.createStory = async function(epicKey) {
    const summary = document.getElementById('storySummary').value;
    const description = document.getElementById('storyDescription').value;
    const storyPoints = parseInt(document.getElementById('storyPoints').value);
    
    if (!summary) { alert('Summary is required'); return; }
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary, description, story_points: storyPoints, epic_key: epicKey })
        });
        if (res.ok) {
            addActivityLog('Story created successfully', 'success');
            closeModal();
            refreshJiraData(epicKey);
        }
    } catch (err) { console.error(err); }
};

window.editStory = async function(key) {
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/item/${key}`);
        const story = await res.json();
        
        elements.modalTitle.textContent = `✏️ Edit Story ${key}`;
        elements.modalBody.innerHTML = `
            <div class="form-group">
                <label>Summary</label>
                <input type="text" id="storySummary" class="form-input" value="${escapeHtml(story.summary || '')}">
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="storyDescription" class="form-textarea" rows="3">${escapeHtml(story.description || '')}</textarea>
            </div>
            <div class="form-group">
                <label>Story Points</label>
                <select id="storyPoints" class="form-select">
                    ${[1,2,3,5,8].map(p => `<option value="${p}" ${story.story_points === p ? 'selected' : ''}>${p}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Status</label>
                <select id="storyStatus" class="form-select">
                    ${['To Do', 'In Progress', 'In Review', 'Done'].map(s => `<option value="${s}" ${story.status === s ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="updateStory('${key}')">Save Changes</button>
            </div>
        `;
        elements.detailsModal.classList.add('active');
    } catch (err) { console.error(err); }
};

window.updateStory = async function(key) {
    const data = {
        summary: document.getElementById('storySummary').value,
        description: document.getElementById('storyDescription').value,
        story_points: parseInt(document.getElementById('storyPoints').value),
        status: document.getElementById('storyStatus').value
    };
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/story/${key}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            addActivityLog(`Story ${key} updated`, 'success');
            closeModal();
        }
    } catch (err) { console.error(err); }
};

window.deleteStory = async function(key) {
    if (!confirm(`Delete story ${key} and all its tasks?`)) return;
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/story/${key}`, { method: 'DELETE' });
        if (res.ok) {
            addActivityLog(`Story ${key} deleted`, 'success');
            document.querySelector(`.story-card[data-key="${key}"]`)?.remove();
        }
    } catch (err) { console.error(err); }
};

window.showAddTaskModal = function(storyKey) {
    elements.modalTitle.textContent = '📋 Add Task';
    elements.modalBody.innerHTML = `
        <div class="form-group">
            <label>Task Summary</label>
            <input type="text" id="taskSummary" class="form-input" placeholder="Implement...">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea id="taskDescription" class="form-textarea" rows="2" placeholder="Details..."></textarea>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="createTask('${storyKey}')">Create Task</button>
        </div>
    `;
    elements.detailsModal.classList.add('active');
};

window.createTask = async function(storyKey) {
    const summary = document.getElementById('taskSummary').value;
    const description = document.getElementById('taskDescription').value;
    
    if (!summary) { alert('Summary is required'); return; }
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary, description, story_key: storyKey })
        });
        if (res.ok) {
            addActivityLog('Task created successfully', 'success');
            closeModal();
        }
    } catch (err) { console.error(err); }
};

window.editTask = async function(key) {
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/item/${key}`);
        const task = await res.json();
        
        elements.modalTitle.textContent = `✏️ Edit Task ${key}`;
        elements.modalBody.innerHTML = `
            <div class="form-group">
                <label>Summary</label>
                <input type="text" id="taskSummary" class="form-input" value="${escapeHtml(task.summary || '')}">
            </div>
            <div class="form-group">
                <label>Status</label>
                <select id="taskStatus" class="form-select">
                    ${['To Do', 'In Progress', 'Done'].map(s => `<option value="${s}" ${task.status === s ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="updateTask('${key}')">Save</button>
            </div>
        `;
        elements.detailsModal.classList.add('active');
    } catch (err) { console.error(err); }
};

window.updateTask = async function(key) {
    const data = {
        summary: document.getElementById('taskSummary').value,
        status: document.getElementById('taskStatus').value
    };
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/task/${key}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            addActivityLog(`Task ${key} updated`, 'success');
            closeModal();
        }
    } catch (err) { console.error(err); }
};

window.deleteTask = async function(key) {
    if (!confirm(`Delete task ${key}?`)) return;
    
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/task/${key}`, { method: 'DELETE' });
        if (res.ok) {
            addActivityLog(`Task ${key} deleted`, 'success');
            document.querySelector(`.task-item[data-key="${key}"]`)?.remove();
        }
    } catch (err) { console.error(err); }
};

window.toggleTaskStatus = async function(key, done) {
    const status = done ? 'Done' : 'To Do';
    try {
        await fetch(`${CONFIG.apiUrl}/jira/task/${key}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
    } catch (err) { console.error(err); }
};

async function refreshJiraData(epicKey) {
    // Refresh the step 2 data
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/epic/${epicKey}`);
        if (res.ok) {
            const data = await res.json();
            state.steps[1].data = data;
            // Re-render if modal is open
        }
    } catch (err) { console.error(err); }
}

// Show JIRA item detail modal
window.showJiraDetail = function(key, type) {
    fetch(`${CONFIG.apiUrl}/jira/item/${key}`)
        .then(res => res.json())
        .then(item => {
            const statusOptions = ['To Do', 'In Progress', 'In Review', 'Done'];
            
            elements.modalTitle.textContent = `${type === 'epic' ? '📋' : '📝'} ${item.key} - ${item.summary}`;
            elements.modalBody.innerHTML = `
                <div class="jira-detail">
                    <div class="detail-row">
                        <label>Type</label>
                        <span class="jira-type ${type}">${item.type}</span>
                    </div>
                    <div class="detail-row">
                        <label>Status</label>
                        <select id="statusSelect" class="status-select" onchange="updateJiraStatus('${key}', this.value)">
                            ${statusOptions.map(s => `<option value="${s}" ${item.status === s ? 'selected' : ''}>${s}</option>`).join('')}
                        </select>
                    </div>
                    <div class="detail-row">
                        <label>Priority</label>
                        <span>${item.priority || 'Medium'}</span>
                    </div>
                    ${item.story_points ? `<div class="detail-row"><label>Story Points</label><span>${item.story_points}</span></div>` : ''}
                    <div class="detail-row full">
                        <label>Description</label>
                        <div class="description-text">${escapeHtml(item.description || 'No description')}</div>
                    </div>
                    <div class="detail-row">
                        <label>Reporter</label>
                        <span>${item.reporter || 'AI Agent'}</span>
                    </div>
                    <div class="detail-row">
                        <label>Created</label>
                        <span>${item.created ? new Date(item.created).toLocaleString() : 'N/A'}</span>
                    </div>
                </div>
                <div class="modal-footer" style="margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            `;
            elements.detailsModal.classList.add('active');
        })
        .catch(err => console.error('Error fetching JIRA item:', err));
};

// Update JIRA status
window.updateJiraStatus = async function(key, status) {
    try {
        const res = await fetch(`${CONFIG.apiUrl}/jira/item/${key}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        if (res.ok) {
            addActivityLog(`Updated ${key} status to ${status}`, 'success');
        }
    } catch (err) {
        console.error('Error updating status:', err);
    }
};

function getStatusClass(status) {
    if (!status) return 'todo';
    const s = status.toLowerCase().replace(/\s+/g, '-');
    if (s.includes('done')) return 'done';
    if (s.includes('progress')) return 'in-progress';
    if (s.includes('review')) return 'in-review';
    return 'todo';
}

// Format generic data
function formatGenericData(data) {
    return Object.entries(data).map(([key, value]) => {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        let displayValue = value;
        if (Array.isArray(value)) {
            displayValue = value.map(v => typeof v === 'object' ? JSON.stringify(v) : `• ${v}`).join('\n');
        } else if (typeof value === 'object' && value !== null) {
            displayValue = JSON.stringify(value, null, 2);
        }
        return `<div class="data-item"><div class="data-label">${label}</div><div class="data-value">${displayValue}</div></div>`;
    }).join('');
}

window.confirmStep = function (stepId) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'confirm_step', stepId }));
        closeModal();
        addActivityLog(`User confirmed step ${stepId}`, 'success');
    }
};

window.resetWorkflowForEdit = function () {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'modify_step' }));
    }
    closeModal();

    // Reset UI
    elements.submitBtn.disabled = false;
    elements.textarea.disabled = false;
    elements.stopBtn.style.display = 'none';
    elements.textarea.focus();

    addActivityLog('Workflow reset for modification', 'info');
};

window.stopWorkflow = function () {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'stop_workflow' }));
        addActivityLog('Stopping workflow...', 'warning');
        elements.stopBtn.disabled = true;
        elements.stopBtn.querySelector('.btn-text').textContent = 'Stopping...';
    }
};

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

    // Reset state for new workflow
    state.steps = WORKFLOW_STEPS.map(step => ({
        ...step,
        status: 'pending',
        details: '',
        data: null
    }));
    state.modifiedFiles = [];
    renderWorkflowSteps();
    renderFileList();
    updateProgress();

    addActivityLog('Submitting requirement...', 'info');
    elements.stopBtn.style.display = 'flex';
    elements.stopBtn.disabled = false;
    elements.stopBtn.querySelector('.btn-text').textContent = 'Stop';

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
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit requirement');
        }
    } catch (error) {
        console.error('Submission error:', error);
        addActivityLog(`Failed to submit requirement: ${error.message}`, 'error');

        // Re-enable form
        elements.submitBtn.disabled = false;
        elements.textarea.disabled = false;
    }
}

// ===== Event Listeners =====
elements.textarea.addEventListener('input', updateCharCount);
elements.form.addEventListener('submit', handleSubmit);
elements.stopBtn.addEventListener('click', stopWorkflow);

// ===== Initialization =====
function init() {
    console.log('Initializing AI Development Agent Dashboard...');

    // Render initial state
    renderWorkflowSteps();
    renderActivityLog();
    renderFileList();
    updateCharCount();

    // Connect WebSocket
    connectWebSocket();

    // Add welcome message
    addActivityLog('System ready. Waiting for input...', 'info');
}

// Start the application
init();
