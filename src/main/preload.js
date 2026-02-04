const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Folder selection
    selectFolder: () => ipcRenderer.invoke('select-folder'),

    // Scan folder for files
    scanFolder: (folderPath) => ipcRenderer.invoke('scan-folder', folderPath),

    // Simulate categorization (dry run)
    simulate: (options) => ipcRenderer.invoke('simulate', options),

    // Execute categorization
    categorize: (options) => ipcRenderer.invoke('categorize', options),

    // Undo last operation
    undo: () => ipcRenderer.invoke('undo'),

    // Get last operation info
    getLastOperation: () => ipcRenderer.invoke('get-last-operation'),

    // Cancel current operation
    cancelOperation: () => ipcRenderer.invoke('cancel-operation'),

    // Progress update listener
    onProgressUpdate: (callback) => {
        ipcRenderer.on('progress-update', (event, data) => callback(data));
    },

    // Log message listener
    onLogMessage: (callback) => {
        ipcRenderer.on('log-message', (event, data) => callback(data));
    },

    // Remove listeners
    removeProgressListener: () => {
        ipcRenderer.removeAllListeners('progress-update');
    },

    removeLogListener: () => {
        ipcRenderer.removeAllListeners('log-message');
    }
});
