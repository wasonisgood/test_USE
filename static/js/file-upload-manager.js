// file-upload-manager.js
// main.js

let fileUploadManager = null;

// 等待 DOM 加載完成
document.addEventListener('DOMContentLoaded', () => {
    debugLogger.log('初始化開始...');
    try {
        initializeFileUploadManager();
        setupFileUploadListener();
        debugLogger.log('初始化完成');
    } catch (error) {
        debugLogger.error(`初始化失敗: ${error.message}`);
    }
});

// 初始化文件上傳管理器
function initializeFileUploadManager() {
    try {
        fileUploadManager = new FileUploadManager();
        debugLogger.log('FileUploadManager 初始化完成');
    } catch (error) {
        debugLogger.error(`FileUploadManager 初始化失敗: ${error.message}`);
        throw error;
    }
}

// 設置文件上傳監聽器
function setupFileUploadListener() {
    const uploadInput = document.getElementById('uploadInput');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');

    if (!uploadInput || !uploadButton) {
        debugLogger.error('找不到文件上傳相關的 DOM 元素');
        return;
    }

    uploadButton.addEventListener('click', async () => {
        const files = uploadInput.files;
        if (!files || files.length === 0) {
            alert('請選擇一個文件');
            return;
        }

        const file = files[0];
        debugLogger.log(`開始上傳文件: ${file.name}`);

        try {
            uploadButton.disabled = true;
            if (!fileUploadManager) {
                throw new Error('FileUploadManager 未初始化');
            }

            const result = await fileUploadManager.uploadFile(file);
            uploadStatus.textContent = `文件上傳成功: ${result.fileName}`;
            debugLogger.log(`文件上傳成功: ${result.fileName}`);
        } catch (error) {
            debugLogger.error(`文件上傳失敗: ${error.message}`);
            uploadStatus.textContent = `文件上傳失敗: ${error.message}`;
        } finally {
            uploadButton.disabled = false;
        }
    });
}

class FileUploadManager {
    constructor() {
        this.files = new Map();
        this.activeFile = null;
        this.maxFileSize = 10 * 1024 * 1024;  // 10MB
        this.supportedTypes = new Set(['.txt', '.csv', '.json', '.pdf', '.docx']);
        
        this.setupListeners();
        this.loadExistingFiles();
        
        debugLogger.log('文件上傳管理器初始化完成');
    }

    setupListeners() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        // 拖放處理
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            debugLogger.log(`收到 ${files.length} 個拖放文件`);
            
            for (const file of files) {
                await this.processFile(file);
            }
        });

        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            debugLogger.log(`選擇了 ${files.length} 個文件`);
            
            for (const file of files) {
                await this.processFile(file);
            }
            fileInput.value = ''; // 重置輸入框
        });
    }

    async loadExistingFiles() {
        try {
            const response = await fetch('http://localhost:8000/files');
            if (response.ok) {
                const files = await response.json();
                files.forEach(file => this.addFileToList(file));
                debugLogger.log(`加載了 ${files.length} 個現有文件`);
            }
        } catch (error) {
            debugLogger.error(`加載現有文件失敗: ${error.message}`);
        }
    }

    async processFile(file) {
        try {
            // 檢查文件大小
            if (file.size > this.maxFileSize) {
                throw new Error(`文件大小超過限制 (最大 ${this.maxFileSize / 1024 / 1024}MB)`);
            }

            // 檢查文件類型
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!this.supportedTypes.has(fileExt)) {
                throw new Error('不支持的文件類型');
            }

            debugLogger.log(`開始處理文件: ${file.name}`);
            
            // 上傳文件
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`上傳失敗: ${response.statusText}`);
            }

            const result = await response.json();
            this.addFileToList(result);
            
            // 觸發文件處理
            wsHandler.sendMessage({
                type: 'file_process',
                file_path: result.file_path
            });

            debugLogger.success(`文件上傳成功: ${file.name}`);

        } catch (error) {
            debugLogger.error(`處理文件失敗: ${error.message}`);
            alert(`處理文件失敗: ${error.message}`);
        }
    }

    addFileToList(fileInfo) {
        this.files.set(fileInfo.file_id, {
            ...fileInfo,
            processed: false,
            context: null
        });
        this.updateFileList();
    }

    updateFileList() {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        this.files.forEach((file, fileId) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg' + 
                                  (this.activeFile === fileId ? ' border-2 border-blue-500' : '');
            
            // 檔案狀態顯示
            const fileStatus = file.processed ? '已處理' : '處理中...';
            const statusClass = file.processed ? 'text-green-600' : 'text-yellow-600';

            fileElement.innerHTML = `
                <div class="flex items-center flex-1">
                    <div class="ml-3 flex-1">
                        <div class="text-sm font-medium text-gray-900">
                            ${file.original_name}
                        </div>
                        <div class="text-xs text-gray-500 flex justify-between">
                            <span>${this.formatFileSize(file.size)}</span>
                            <span class="${statusClass}">${fileStatus}</span>
                        </div>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="text-sm text-blue-500 hover:text-blue-700 px-2 py-1 rounded"
                            onclick="fileUploadManager.toggleFileContext('${fileId}')">
                        ${this.activeFile === fileId ? '停用' : '啟用'}
                    </button>
                    <button class="text-sm text-red-500 hover:text-red-700 px-2 py-1 rounded"
                            onclick="fileUploadManager.deleteFile('${fileId}')">
                        刪除
                    </button>
                </div>
            `;

            fileList.appendChild(fileElement);
        });

        debugLogger.log(`更新文件列表，共 ${this.files.size} 個文件`);
    }

    toggleFileContext(fileId) {
        this.activeFile = this.activeFile === fileId ? null : fileId;
        this.updateFileList();
        debugLogger.log(`${this.activeFile ? '啟用' : '停用'}文件上下文: ${fileId}`);
    }

    async deleteFile(fileId) {
        try {
            const response = await fetch(`http://localhost:8000/file/${fileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('刪除失敗');
            }

            if (this.activeFile === fileId) {
                this.activeFile = null;
            }
            this.files.delete(fileId);
            this.updateFileList();
            debugLogger.success(`文件已刪除: ${fileId}`);

        } catch (error) {
            debugLogger.error(`刪除文件失敗: ${error.message}`);
            alert('刪除文件失敗');
        }
    }

    updateFileStatus(fileId, status, context = null) {
        const file = this.files.get(fileId);
        if (file) {
            file.processed = status === 'processed';
            if (context) {
                file.context = context;
            }
            this.updateFileList();
        }
    }

    getActiveFileContext() {
        if (!this.activeFile) return null;
        const file = this.files.get(this.activeFile);
        return file ? file.context : null;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    isFileSupported(file) {
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        return this.supportedTypes.has(fileExt);
    }

    getProcessedFiles() {
        return Array.from(this.files.values()).filter(file => file.processed);
    }
}

// 初始化文件上傳管理器（延遲加載）
function initializeFileUploadManager() {
    if (!window.fileUploadManager) {
        window.fileUploadManager = new FileUploadManager();
        debugLogger.log('文件上傳管理器已初始化');
    }
}

// 處理開關按鈕點擊
document.getElementById('toggleFileUpload').addEventListener('click', function() {
    const fileUploadSection = document.getElementById('fileUploadSection');
    const isVisible = fileUploadSection.style.display !== 'none';
    
    fileUploadSection.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
        initializeFileUploadManager();
    }
});