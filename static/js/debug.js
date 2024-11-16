// 調試工具類
class DebugLogger {
    constructor() {
        this.panel = document.getElementById('debugPanel');
        this.logs = [];
        this.maxLogs = 1000;
        this.setupControls();
    }

    setupControls() {
        document.getElementById('toggleDebug').addEventListener('click', () => {
            this.panel.classList.toggle('show');
        });

        document.getElementById('clearDebug').addEventListener('click', () => {
            this.clear();
        });

        document.getElementById('downloadLog').addEventListener('click', () => {
            this.downloadLogs();
        });

        // 添加鍵盤快捷鍵
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                this.panel.classList.toggle('show');
            }
        });
    }

    log(message, type = 'info') {
        try {
            // 確保 message 和 type 都是安全的值
            const safeMessage = this.formatMessage(message);
            const safeType = this.formatType(type);
            
            const timestamp = new Date().toISOString();
            const entry = {
                timestamp,
                message: safeMessage,
                type: safeType
            };

            this.logs.push(entry);
            if (this.logs.length > this.maxLogs) {
                this.logs.shift();
            }

            const logElement = document.createElement('div');
            logElement.className = `debug-entry ${safeType}`;
            logElement.innerHTML = `[${timestamp}] ${safeType.toUpperCase()}: `;

            if (typeof message === 'object' && message !== null) {
                const pre = document.createElement('pre');
                pre.textContent = safeMessage;
                logElement.appendChild(pre);
            } else {
                logElement.innerHTML += safeMessage;
            }

            this.panel.appendChild(logElement);
            this.panel.scrollTop = this.panel.scrollHeight;
        } catch (error) {
            console.error('日誌記錄錯誤:', error);
            // 嘗試基本的錯誤顯示
            try {
                const errorElement = document.createElement('div');
                errorElement.className = 'debug-entry error';
                errorElement.textContent = `[${new Date().toISOString()}] ERROR: ${error.message}`;
                this.panel.appendChild(errorElement);
            } catch (e) {
                // 如果連錯誤顯示都失敗了，至少在控制台輸出
                console.error('嚴重錯誤:', e);
            }
        }
    }

    formatMessage(message) {
        if (message === null) return 'null';
        if (message === undefined) return 'undefined';
        if (typeof message === 'object') {
            try {
                return JSON.stringify(message, null, 2);
            } catch (e) {
                return '[無法序列化的對象]';
            }
        }
        return String(message);
    }

    formatType(type) {
        if (!type || typeof type !== 'string') {
            return 'info';
        }
        // 只允許特定的類型
        const allowedTypes = ['info', 'error', 'warning', 'success'];
        return allowedTypes.includes(type.toLowerCase()) ? type.toLowerCase() : 'info';
    }

    error(message) {
        this.log(message, 'error');
        console.error(message);
    }

    warn(message) {
        this.log(message, 'warning');
        console.warn(message);
    }

    success(message) {
        this.log(message, 'success');
        console.log(message);
    }

    clear() {
        try {
            this.logs = [];
            this.panel.innerHTML = '';
            this.log('日誌已清空', 'info');
        } catch (error) {
            console.error('清除日誌失敗:', error);
        }
    }

    downloadLogs() {
        try {
            const logText = this.logs.map(log => {
                try {
                    return `[${log.timestamp}] ${String(log.type).toUpperCase()}: ${this.formatMessage(log.message)}`;
                } catch (e) {
                    return `[${new Date().toISOString()}] ERROR: 無法格式化日誌條目`;
                }
            }).join('\n');

            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `debug_log_${new Date().toISOString()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.log('日誌已下載', 'success');
        } catch (error) {
            console.error('下載日誌失敗:', error);
            this.error('下載日誌失敗: ' + error.message);
        }
    }
}

// 連接狀態管理
class ConnectionManager {
    constructor() {
        this.statusElement = document.getElementById('connectionStatus');
    }

    updateStatus(status) {
        try {
            this.statusElement.className = `connection-status ${status}`;
            
            const statusText = {
                'connected': '已連接',
                'disconnected': '斷開連接',
                'connecting': '連接中...'
            }[status] || '未知狀態';

            this.statusElement.textContent = statusText;
            // 使用格式化後的狀態文本
            debugLogger.log(`連接狀態更新: ${statusText}`, 'info');
        } catch (error) {
            console.error('更新連接狀態失敗:', error);
        }
    }
}

// 工具函數
function formatTime(seconds) {
    try {
        const minutes = Math.floor(Number(seconds) / 60);
        const remainingSeconds = Math.floor(Number(seconds) % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    } catch (error) {
        console.error('格式化時間失敗:', error);
        return '0:00';
    }
}

function formatFileSize(bytes) {
    try {
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = Number(bytes);
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(2)} ${units[unitIndex]}`;
    } catch (error) {
        console.error('格式化文件大小失敗:', error);
        return '0 B';
    }
}

// 初始化全局變量和實例
let debugLogger, connectionManager;

try {
    debugLogger = new DebugLogger();
    connectionManager = new ConnectionManager();
    
    // 確保其他全局變量存在
    const topicInput = document.getElementById('topicInput');
    const generateBtn = document.getElementById('generateBtn');
    const dialogueContainer = document.getElementById('dialogueContainer');
    const generationStatus = document.getElementById('generationStatus');

    if (!topicInput || !generateBtn || !dialogueContainer || !generationStatus) {
        console.warn('某些 UI 元素未找到，可能會影響功能');
    }
} catch (error) {
    console.error('初始化失敗:', error);
}