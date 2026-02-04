// File Categorizer - Renderer Script
// Simple event handling for UI

// State
const state = {
    folder: null,
    modes: [],
    options: {
        language: 'en',
        dateFormat: 'YYYY',
        conflictResolution: 'number',
        similarityThreshold: 80,
        multiCriteria: { criteria1: 'extension', criteria2: 'year', operator: 'AND' }
    },
    hasUndo: false
};

// DOM elements
const dom = {
    folderPath: document.getElementById('folderPath'),
    selectFolderBtn: document.getElementById('selectFolderBtn'),
    folderInfo: document.getElementById('folderInfo'),
    fileCount: document.getElementById('fileCount'),
    totalSize: document.getElementById('totalSize'),
    modeCheckboxes: document.querySelectorAll('input[name="mode"]'),
    folderLanguage: document.getElementById('folderLanguage'),
    dateFormat: document.getElementById('dateFormat'),
    conflictResolution: document.getElementById('conflictResolution'),
    similarityThreshold: document.getElementById('similarityThreshold'),
    similarityValue: document.getElementById('similarityValue'),
    multiCriteriaSection: document.getElementById('multiCriteriaSection'),
    criteria1: document.getElementById('criteria1'),
    criteria2: document.getElementById('criteria2'),
    logicOperator: document.getElementById('logicOperator'),
    categorizeBtn: document.getElementById('categorizeBtn'),
    undoBtn: document.getElementById('undoBtn'),
    simulateBtn: document.getElementById('simulateBtn'),
    resultPlaceholder: document.getElementById('resultPlaceholder'),
    resultContent: document.getElementById('resultContent'),
    resultTotal: document.getElementById('resultTotal'),
    resultMoved: document.getElementById('resultMoved'),
    resultFolders: document.getElementById('resultFolders'),
    resultErrors: document.getElementById('resultErrors'),
    resultDuration: document.getElementById('resultDuration'),
    folderList: document.getElementById('folderList'),
    errorSection: document.getElementById('errorSection'),
    errorList: document.getElementById('errorList'),
    tabs: document.querySelectorAll('.tab'),
    resultTab: document.getElementById('resultTab'),
    logTab: document.getElementById('logTab'),
    logContent: document.getElementById('logContent'),
    progressBar: document.getElementById('progressBar'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    cancelBtn: document.getElementById('cancelBtn'),
    simulationModal: document.getElementById('simulationModal'),
    simFiles: document.getElementById('simFiles'),
    simFolders: document.getElementById('simFolders'),
    simPreview: document.getElementById('simPreview'),
    closeSimModal: document.getElementById('closeSimModal'),
    cancelSim: document.getElementById('cancelSim'),
    confirmSim: document.getElementById('confirmSim')
};

// Initialize
function init() {
    setupEventListeners();
    setupProgressListeners();
    checkUndo();
    log('Application ready.', 'info');
}

// Event listeners
function setupEventListeners() {
    // Folder selection
    dom.selectFolderBtn.addEventListener('click', selectFolder);

    // Mode checkboxes
    dom.modeCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateModes);
    });

    // Options
    dom.folderLanguage.addEventListener('change', e => state.options.language = e.target.value);
    dom.dateFormat.addEventListener('change', e => state.options.dateFormat = e.target.value);
    dom.conflictResolution.addEventListener('change', e => state.options.conflictResolution = e.target.value);
    dom.similarityThreshold.addEventListener('input', e => {
        state.options.similarityThreshold = parseInt(e.target.value);
        dom.similarityValue.textContent = e.target.value + '%';
    });
    dom.criteria1.addEventListener('change', e => state.options.multiCriteria.criteria1 = e.target.value);
    dom.criteria2.addEventListener('change', e => state.options.multiCriteria.criteria2 = e.target.value);
    dom.logicOperator.addEventListener('change', e => state.options.multiCriteria.operator = e.target.value);

    // Main buttons
    dom.categorizeBtn.addEventListener('click', categorize);
    dom.undoBtn.addEventListener('click', undo);
    dom.simulateBtn.addEventListener('click', simulate);
    dom.cancelBtn.addEventListener('click', cancel);

    // Tabs
    dom.tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Modal
    dom.closeSimModal.addEventListener('click', closeModal);
    dom.cancelSim.addEventListener('click', closeModal);
    dom.confirmSim.addEventListener('click', confirmSimulation);
}

// Progress listeners
function setupProgressListeners() {
    window.electronAPI.onProgressUpdate(data => {
        if (data.percent !== undefined) {
            dom.progressFill.style.width = data.percent + '%';
        }
        if (data.message) {
            dom.progressText.textContent = data.message;
        }
    });

    window.electronAPI.onLogMessage(data => {
        log(data.message, data.type);
    });
}

// Select folder
async function selectFolder() {
    const folder = await window.electronAPI.selectFolder();
    if (!folder) return;

    state.folder = folder;
    dom.folderPath.value = folder;

    log('Folder selected: ' + folder, 'info');
    showProgress('Scanning folder...');

    const result = await window.electronAPI.scanFolder(folder);
    hideProgress();

    if (result.success) {
        dom.fileCount.textContent = result.total_files + ' files';
        dom.totalSize.textContent = formatSize(result.total_size);
        dom.folderInfo.classList.remove('hidden');
        log(result.total_files + ' files found.', 'success');
    } else {
        log('Scan error: ' + result.error, 'error');
    }

    updateButtons();
}

// Update modes
function updateModes() {
    state.modes = [];
    dom.modeCheckboxes.forEach(cb => {
        if (cb.checked) state.modes.push(cb.value);
    });

    // Show/hide multi criteria section
    dom.multiCriteriaSection.style.display = state.modes.includes('multi_criteria') ? 'block' : 'none';

    updateButtons();
}

// Update button states
function updateButtons() {
    const canRun = state.folder && state.modes.length > 0;
    dom.categorizeBtn.disabled = !canRun;
    dom.simulateBtn.disabled = !canRun;
    dom.undoBtn.disabled = !state.hasUndo;
}

// Check for undo
async function checkUndo() {
    const lastOp = await window.electronAPI.getLastOperation();
    state.hasUndo = !!lastOp;
    updateButtons();
}

// Simulate
async function simulate() {
    if (!state.folder || state.modes.length === 0) return;

    log('Starting simulation...', 'info');
    showProgress('Running simulation...');

    const result = await window.electronAPI.simulate({
        folderPath: state.folder,
        modes: state.modes,
        advancedOptions: state.options
    });

    hideProgress();

    if (result.success) {
        showSimulationModal(result);
        log('Simulation completed.', 'success');
    } else {
        log('Simulation error: ' + result.error, 'error');
    }
}

// Categorize
async function categorize() {
    if (!state.folder || state.modes.length === 0) return;

    log('Starting categorization...', 'info');
    showProgress('Moving files...');

    const result = await window.electronAPI.categorize({
        folderPath: state.folder,
        modes: state.modes,
        advancedOptions: state.options
    });

    hideProgress();

    if (result.success) {
        showResult(result);
        log('Categorization completed: ' + result.moved_files + ' files moved.', 'success');
        await checkUndo();
    } else {
        log('Categorization error: ' + result.error, 'error');
    }
}

// Undo
async function undo() {
    log('Starting undo...', 'info');
    showProgress('Restoring files...');

    const result = await window.electronAPI.undo();
    hideProgress();

    if (result.success) {
        log('Undo completed: ' + (result.restored_files || 0) + ' files restored.', 'success');
        showResultPlaceholder();
    } else {
        log('Undo error: ' + result.error, 'error');
    }

    await checkUndo();
}

// Cancel
async function cancel() {
    await window.electronAPI.cancelOperation();
    hideProgress();
    log('Operation cancelled.', 'warning');
}

// Show result
function showResult(result) {
    dom.resultPlaceholder.classList.add('hidden');
    dom.resultContent.classList.remove('hidden');

    dom.resultTotal.textContent = result.total_files || 0;
    dom.resultMoved.textContent = result.moved_files || 0;
    dom.resultFolders.textContent = result.folders_created || 0;
    dom.resultErrors.textContent = (result.errors || []).length;
    dom.resultDuration.textContent = (result.duration || 0).toFixed(2);

    // Folder list
    dom.folderList.innerHTML = '';
    if (result.folder_breakdown) {
        for (const [name, count] of Object.entries(result.folder_breakdown)) {
            const div = document.createElement('div');
            div.className = 'folder-item';
            div.innerHTML = `<span class="folder-item-name">${name}</span><span class="folder-item-count">${count} files</span>`;
            dom.folderList.appendChild(div);
        }
    }

    // Errors
    if (result.errors && result.errors.length > 0) {
        dom.errorSection.classList.remove('hidden');
        dom.errorList.innerHTML = '';
        result.errors.forEach(err => {
            const li = document.createElement('li');
            li.textContent = err;
            dom.errorList.appendChild(li);
        });
    } else {
        dom.errorSection.classList.add('hidden');
    }
}

function showResultPlaceholder() {
    dom.resultPlaceholder.classList.remove('hidden');
    dom.resultContent.classList.add('hidden');
}

// Simulation modal
function showSimulationModal(result) {
    dom.simFiles.textContent = result.total_files || 0;
    dom.simFolders.textContent = Object.keys(result.plan || {}).length;

    dom.simPreview.innerHTML = '';
    if (result.plan) {
        for (const [folder, files] of Object.entries(result.plan)) {
            const folderDiv = document.createElement('div');
            folderDiv.className = 'sim-folder';
            folderDiv.innerHTML = `<div class="sim-folder-name">📁 ${folder}/</div>`;

            const toShow = files.slice(0, 5);
            toShow.forEach(file => {
                const fileDiv = document.createElement('div');
                fileDiv.className = 'sim-file';
                fileDiv.textContent = '└ ' + (typeof file === 'string' ? file : file.name);
                folderDiv.appendChild(fileDiv);
            });

            if (files.length > 5) {
                const more = document.createElement('div');
                more.className = 'sim-file';
                more.textContent = '└ ... and ' + (files.length - 5) + ' more files';
                folderDiv.appendChild(more);
            }

            dom.simPreview.appendChild(folderDiv);
        }
    }

    dom.simulationModal.classList.remove('hidden');
}

function closeModal() {
    dom.simulationModal.classList.add('hidden');
}

async function confirmSimulation() {
    closeModal();
    await categorize();
}

// Tabs
function switchTab(tabName) {
    dom.tabs.forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    dom.resultTab.classList.add('hidden');
    dom.logTab.classList.add('hidden');

    if (tabName === 'result') dom.resultTab.classList.remove('hidden');
    if (tabName === 'log') dom.logTab.classList.remove('hidden');
}

// Progress
function showProgress(text) {
    dom.progressText.textContent = text;
    dom.progressFill.style.width = '0%';
    dom.progressBar.classList.remove('hidden');
}

function hideProgress() {
    dom.progressBar.classList.add('hidden');
}

// Log
function log(message, type = 'info') {
    const time = new Date().toLocaleTimeString('en-US');
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + type;
    entry.textContent = `[${time}] ${message}`;
    dom.logContent.insertBefore(entry, dom.logContent.firstChild);

    // Keep max 100 entries
    while (dom.logContent.children.length > 100) {
        dom.logContent.removeChild(dom.logContent.lastChild);
    }
}

// Format size
function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Start
document.addEventListener('DOMContentLoaded', init);
