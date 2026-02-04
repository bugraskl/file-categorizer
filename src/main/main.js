const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess = null;

// Python executable path - handles both dev and packaged app
function getPythonPath() {
    if (app.isPackaged) {
        return 'python';
    }
    return 'python';
}

// Get categorizer.py path
function getCategorizerPath() {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, 'python', 'categorizer.py');
    }
    return path.join(__dirname, '..', 'python', 'categorizer.py');
}

// Get logs directory path
function getLogsPath() {
    if (app.isPackaged) {
        return path.join(app.getPath('userData'), 'logs');
    }
    return path.join(__dirname, '..', '..', 'logs');
}

function createWindow() {
    // Hide the menu bar
    Menu.setApplicationMenu(null);

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        backgroundColor: '#f0f0f0',
        titleBarStyle: 'default',
        show: false
    });

    mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Ensure logs directory exists
    const logsPath = getLogsPath();
    if (!fs.existsSync(logsPath)) {
        fs.mkdirSync(logsPath, { recursive: true });
    }
}

// Run Python categorizer
function runPython(args) {
    return new Promise((resolve, reject) => {
        const pythonPath = getPythonPath();
        const categorizerPath = getCategorizerPath();

        const fullArgs = [categorizerPath, ...args];

        pythonProcess = spawn(pythonPath, fullArgs, {
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString('utf-8');
            // Send progress updates to renderer
            try {
                const lines = data.toString('utf-8').split('\n');
                lines.forEach(line => {
                    if (line.startsWith('PROGRESS:')) {
                        const progress = JSON.parse(line.replace('PROGRESS:', ''));
                        mainWindow.webContents.send('progress-update', progress);
                    }
                });
            } catch (e) {
                // Continue processing
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString('utf-8');
            mainWindow.webContents.send('log-message', {
                type: 'error',
                message: data.toString('utf-8')
            });
        });

        pythonProcess.on('close', (code) => {
            pythonProcess = null;
            if (code === 0) {
                try {
                    // Find JSON in stdout
                    const jsonMatch = stdout.match(/RESULT:([\s\S]*?)(?:$|PROGRESS:)/);
                    if (jsonMatch) {
                        resolve(JSON.parse(jsonMatch[1].trim()));
                    } else {
                        // Try parsing entire output as JSON
                        const lastJsonStart = stdout.lastIndexOf('{');
                        if (lastJsonStart !== -1) {
                            const jsonStr = stdout.substring(lastJsonStart);
                            resolve(JSON.parse(jsonStr));
                        } else {
                            resolve({ success: true, message: stdout });
                        }
                    }
                } catch (e) {
                    resolve({ success: true, raw: stdout });
                }
            } else {
                reject(new Error(stderr || `Python process exited with code ${code}`));
            }
        });

        pythonProcess.on('error', (err) => {
            pythonProcess = null;
            reject(err);
        });
    });
}

// IPC Handlers
ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
        title: 'Select folder to categorize'
    });

    if (result.canceled) {
        return null;
    }
    return result.filePaths[0];
});

ipcMain.handle('scan-folder', async (event, folderPath) => {
    try {
        const result = await runPython(['--scan', folderPath]);
        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('simulate', async (event, options) => {
    try {
        const args = [
            '--simulate',
            '--folder', options.folderPath,
            '--modes', JSON.stringify(options.modes),
            '--options', JSON.stringify(options.advancedOptions || {}),
            '--logs-path', getLogsPath()
        ];
        const result = await runPython(args);
        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('categorize', async (event, options) => {
    try {
        const args = [
            '--execute',
            '--folder', options.folderPath,
            '--modes', JSON.stringify(options.modes),
            '--options', JSON.stringify(options.advancedOptions || {}),
            '--logs-path', getLogsPath()
        ];
        const result = await runPython(args);
        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('undo', async () => {
    try {
        const args = ['--undo', '--logs-path', getLogsPath()];
        const result = await runPython(args);
        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('get-last-operation', async () => {
    try {
        const logsPath = getLogsPath();
        const logFiles = fs.readdirSync(logsPath)
            .filter(f => f.startsWith('operation_') && f.endsWith('.json'))
            .sort()
            .reverse();

        if (logFiles.length === 0) {
            return null;
        }

        const lastLog = fs.readFileSync(path.join(logsPath, logFiles[0]), 'utf-8');
        return JSON.parse(lastLog);
    } catch (error) {
        return null;
    }
});

ipcMain.handle('cancel-operation', async () => {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
        return { success: true };
    }
    return { success: false, message: 'No operation running' };
});

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
