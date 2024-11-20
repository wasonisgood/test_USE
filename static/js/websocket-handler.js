// websocket-handler.js

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
        debugLogger.log('正在建立 WebSocket 連接...');
        
        try {
            this.ws = new WebSocket('ws://localhost:8888');
            this.setupEventListeners();
        } catch (error) {
            debugLogger.error(`WebSocket 連接失敗: ${error.message}`);
            this.handleReconnect();
        }
    }

    setupEventListeners() {
        if (!this.ws) return;

        this.ws.onopen = () => {
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            debugLogger.log('WebSocket 連接已建立');

            // 處理排隊的消息
            while (this.messageQueue.length > 0) {
                const message = this.messageQueue.shift();
                this.sendMessage(message);
            }
        };

        this.ws.onmessage = async (event) => {
            try {
                const response = JSON.parse(event.data);
                debugLogger.log('收到消息:', response);

                // 首先檢查是否有錯誤
                if (response.error) {
                    debugLogger.error(`服務器錯誤: ${response.error}`);
                    return;
                }

                // 根據消息類型處理
                if (response.type) {
                    switch (response.type) {
                        case 'survey_generated':
                            if (surveyManager) {
                                await surveyManager.handleSurveyGenerated(response);
                            }
                            return;
                        case 'survey_analysis':
                            if (surveyManager) {
                                await surveyManager.handleAnalysisReceived(response);
                            }
                            return;
                        case 'program_plan':
                            if (surveyManager) {
                                await surveyManager.handlePlanReceived(response);
                            }
                            return;
                        case 'section_ready':
                            await this.handleSectionReady(response);
                            return;
                        case 'complete':
                            this.handleComplete();
                            return;
                        case 'error':
                            debugLogger.error(`服務器錯誤: ${response.message || '未知錯誤'}`);
                            return;
                    }
                }

                // 處理沒有特定類型但有狀態的消息
                if (response.status) {
                    switch (response.status) {
                        case 'success':
                            debugLogger.log('操作成功:', response.message || '操作完成');
                            if (response.data) {
                                debugLogger.log('返回數據:', response.data);
                            }
                            return;
                        case 'error':
                            debugLogger.error(`操作失敗: ${response.message || '未知錯誤'}`);
                            return;
                        case 'processing':
                            debugLogger.log('處理中:', response.message || '操作進行中');
                            return;
                        default:
                            debugLogger.warn(`未知的消息狀態: ${response.status}`);
                            return;
                    }
                }

                // 如果既沒有 type 也沒有 status
                debugLogger.warn('收到未知格式的消息:', response);

            } catch (error) {
                debugLogger.error(`處理消息失敗: ${error.message}`);
            }
        };

        this.ws.onclose = () => {
            this.isConnecting = false;
            debugLogger.warn('WebSocket 連接已關閉');
            this.handleReconnect();
        };

        this.ws.onerror = (error) => {
            debugLogger.error(`WebSocket 錯誤: ${error}`);
        };
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            debugLogger.error('重連次數超過上限，請刷新頁面重試');
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
            // 標準化消息格式
            const standardMessage = this.standardizeMessage(message);
            const messageString = JSON.stringify(standardMessage);
            
            this.ws.send(messageString);
            debugLogger.log('發送消息:', standardMessage);
        } catch (error) {
            debugLogger.error(`發送消息失敗: ${error.message}`);
            this.messageQueue.push(message);
        }
    }

    standardizeMessage(message) {
        if (typeof message === 'string') {
            return {
                type: 'text',
                content: message
            };
        }

        return {
            type: message.type || 'unknown',
            timestamp: new Date().toISOString(),
            ...message
        };
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

            const dialogueContainer = document.getElementById('dialogueContainer');
            if (dialogueContainer) {
                dialogueContainer.appendChild(messageDiv);
                dialogueContainer.scrollTop = dialogueContainer.scrollHeight;
            }

            if (response.audio_file && window.audioManager) {
                const audioUrl = `http://localhost:8000${response.audio_file}`;
                await window.audioManager.addAudio(audioUrl, messageDiv);
            }

            debugLogger.log(`添加對話段落: ${response.text}`);
        } catch (error) {
            debugLogger.error(`處理對話段落失敗: ${error.message}`);
        }
    }

    handleComplete() {
        const elements = {
            generationStatus: document.getElementById('generationStatus'),
            generateBtn: document.getElementById('generateBtn'),
            topicInput: document.getElementById('topicInput')
        };
        
        if (elements.generationStatus) {
            elements.generationStatus.classList.add('hidden');
        }
        
        if (elements.generateBtn) {
            elements.generateBtn.disabled = false;
        }
        
        if (elements.topicInput) {
            elements.topicInput.disabled = false;
        }
        
        debugLogger.log('對話生成完成');

        if (window.surveyManager) {
            surveyManager.reset();
        }
    }
}

// 創建全局實例
window.wsHandler = new WebSocketHandler();
