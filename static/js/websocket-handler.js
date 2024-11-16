
// WebSocket 處理
class WebSocketHandler {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.isConnecting = false;
        this.messageQueue = [];
        
        this.connect();
    }

    connect() {
        if (this.isConnecting) return;
        
        this.isConnecting = true;
        connectionManager.updateStatus('connecting');
        
        try {
            this.ws = new WebSocket('ws://localhost:8888');
            this.setupEventListeners();
            debugLogger.log('正在建立 WebSocket 連接...');
        } catch (error) {
            debugLogger.error(`WebSocket 連接失敗: ${error.message}`);
            this.handleReconnect();
        }
    }

    setupEventListeners() {
        this.ws.onopen = this.handleOpen.bind(this);
        this.ws.onclose = this.handleClose.bind(this);
        this.ws.onerror = this.handleError.bind(this);
        this.ws.onmessage = this.handleMessage.bind(this);
    }

    handleOpen() {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        connectionManager.updateStatus('connected');
        generateBtn.disabled = false;
        debugLogger.success('WebSocket 連接已建立');

        // 處理排隊的消息
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }

    handleClose() {
        this.isConnecting = false;
        connectionManager.updateStatus('disconnected');
        generateBtn.disabled = true;
        debugLogger.warn('WebSocket 連接已關閉');
        this.handleReconnect();
    }

    handleError(error) {
        debugLogger.error(`WebSocket 錯誤: ${error}`);
        generateBtn.disabled = true;
    }

    async handleMessage(event) {
        try {
            const response = JSON.parse(event.data);
            debugLogger.log('收到消息:', response);

            if (response.error) {
                this.handleError(response.error);
                return;
            }

            switch (response.status) {
                case 'section_ready':
                    await this.handleSectionReady(response);
                    break;
                case 'complete':
                    this.handleComplete();
                    break;
                case 'file_processed':
                    this.handleFileProcessed(response);
                    break;
                case 'processing_status':
                    this.handleProcessingStatus(response);
                    break;
                default:
                    debugLogger.warn(`未知的消息狀態: ${response.status}`);
            }
        } catch (error) {
            debugLogger.error(`處理消息失敗: ${error.message}`);
        }
    }

    async handleSectionReady(response) {
        try {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message p-4 rounded-lg ${
                response.user === 'M' ? 'bg-blue-50' : 'bg-pink-50'
            }`;
            
            const userSpan = document.createElement('span');
            userSpan.className = `font-bold ${
                response.user === 'M' ? 'text-blue-600' : 'text-pink-600'
            }`;
            userSpan.textContent = response.user === 'M' ? '男生：' : '女生：';
            
            const textSpan = document.createElement('span');
            textSpan.className = 'ml-2 text-gray-700';
            textSpan.textContent = response.text;

            messageDiv.appendChild(userSpan);
            messageDiv.appendChild(textSpan);
            dialogueContainer.appendChild(messageDiv);
            dialogueContainer.scrollTop = dialogueContainer.scrollHeight;

            // 添加到音頻管理器
            const audioUrl = `http://localhost:8000${response.audio_file}`;
            audioManager.addAudio(audioUrl, messageDiv);

            debugLogger.log(`添加對話段落: ${response.text}`);
        } catch (error) {
            debugLogger.error(`處理對話段落失敗: ${error.message}`);
        }
    }

    handleComplete() {
        generationStatus.classList.add('hidden');
        generateBtn.disabled = false;
        topicInput.disabled = false;
        debugLogger.success('對話生成完成');
    }

    handleFileProcessed(response) {
        debugLogger.success(`文件處理完成: ${response.file_id}`);
        if (fileUploadManager) {
            fileUploadManager.updateFileStatus(response.file_id, 'processed');
        }
    }

    handleProcessingStatus(response) {
        const statusText = document.createElement('div');
        statusText.className = 'text-sm text-gray-600 mt-2';
        statusText.textContent = response.message;
        generationStatus.appendChild(statusText);
        setTimeout(() => statusText.remove(), 3000);
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            debugLogger.error('重連次數超過上限，請刷新頁面重試');
            alert('連接失敗，請刷新頁面重試');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
        debugLogger.log(`嘗試重新連接 (${this.reconnectAttempts}/${this.maxReconnectAttempts}) ${delay}ms 後重試...`);
        
        setTimeout(() => {
            if (!this.isConnecting) {
                this.connect();
            }
        }, delay);
    }

    sendMessage(message) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            debugLogger.warn('WebSocket 未連接，消息已加入隊列');
            this.messageQueue.push(message);
            return;
        }

        try {
            const messageString = typeof message === 'string' ? 
                message : JSON.stringify(message);
            this.ws.send(messageString);
            debugLogger.log('發送消息:', message);
        } catch (error) {
            debugLogger.error(`發送消息失敗: ${error.message}`);
            this.messageQueue.push(message);
        }
    }

    getConnectionStatus() {
        if (!this.ws) return 'disconnected';
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            default:
                return 'disconnected';
        }
    }
}

// 生成按鈕事件處理
document.getElementById('generateBtn').addEventListener('click', function() {
    const topic = topicInput.value.trim();
    if (!topic) {
        alert('請輸入對話主題');
        return;
    }

    // 重置音頻管理器
    audioManager.reset();
    
    // 清空對話容器
    dialogueContainer.innerHTML = '';
    
    // 顯示狀態
    generationStatus.classList.remove('hidden');
    generateBtn.disabled = true;
    topicInput.disabled = true;

    // 獲取活動文件上下文
    const activeFileContext = fileUploadManager ? 
        fileUploadManager.getActiveFileContext() : null;

    // 發送請求
    wsHandler.sendMessage({
        type: 'dialogue',
        topic: topic,
        use_context: true,
        file_context: activeFileContext
    });
});

// 初始化 WebSocket 處理器
const wsHandler = new WebSocketHandler();