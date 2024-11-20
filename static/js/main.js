// main.js

// 全局變量聲明（注意：不重複宣告已在其他文件中定義的變量）
let surveyManager = null;
let fileUploadManager = null;

// 等待DOM加載完成
document.addEventListener('DOMContentLoaded', () => {
    debugLogger.log('DOM加載完成，開始初始化組件...');

    try {
        // 1. 初始化各個管理器
        initializeManagers();


        // 2. 設置事件監聽器
        setupEventListeners();

        debugLogger.log('所有組件初始化完成');
    } catch (error) {
        debugLogger.error(`初始化失敗: ${error.message}`);
    }
});

// 初始化所有管理器
function initializeManagers() {
    try {
        // 初始化問卷管理器
        surveyManager = new SurveyManager();
        debugLogger.log('SurveyManager 初始化完成');
        
    } catch (error) {
        debugLogger.error(`管理器初始化失敗: ${error.message}`);
        throw error;
    }
}

// 設置所有事件監聽器
function setupEventListeners() {
    try {
        setupFileUploadListener();
        setupGenerateButtonListener();
        setupDialogueControls();
        debugLogger.log('所有事件監聽器設置完成');
    } catch (error) {
        debugLogger.error(`設置事件監聽器失敗: ${error.message}`);
        throw error;
    }
}

// 設置文件上傳相關的監聽器
function setupFileUploadListener() {
    const toggleFileUpload = document.getElementById('toggleFileUpload');
    if (toggleFileUpload) {
        toggleFileUpload.addEventListener('click', function() {
            const fileUploadSection = document.getElementById('fileUploadSection');
            if (fileUploadSection) {
                if (fileUploadSection.style.display === 'none' || !fileUploadSection.style.display) {
                    fileUploadSection.style.display = 'block';
                    // 懶加載初始化文件上傳管理器
                    if (!fileUploadManager) {
                        fileUploadManager = new FileUploadManager();
                        debugLogger.log('FileUploadManager 初始化完成');
                    }
                } else {
                    fileUploadSection.style.display = 'none';
                }
            }
        });
        debugLogger.log('文件上傳監聽器設置完成');
    } else {
        debugLogger.warn('找不到文件上傳開關按鈕');
    }
}

// 設置生成按鈕監聽器
function setupGenerateButtonListener() {
    const generateBtn = document.getElementById('generateBtn');
    if (!generateBtn) {
        debugLogger.error('找不到生成按鈕');
        return;
    }

    // 移除之前可能存在的事件監聽器
    const newGenerateBtn = document.getElementById('generateBtn');

    newGenerateBtn.addEventListener('click', async function() {
        const topicInput = document.getElementById('topicInput');
        if (!topicInput) {
            debugLogger.error('找不到主題輸入框');
            return;
        }
        
        const topic = topicInput.value.trim();
        if (!topic) {
            alert('請輸入對話主題');
            return;
        }

        debugLogger.log(`用戶輸入主題: ${topic}`);

        // 禁用按鈕和輸入框
        newGenerateBtn.disabled = true;
        topicInput.disabled = true;

        try {
            // 檢查 WebSocket 連接狀態
            if (!wsHandler || wsHandler.getConnectionStatus() !== 'connected') {
                throw new Error('WebSocket 未連接');
            }

            // 重置當前狀態
            resetCurrentState();

            // 開始問卷流程
            debugLogger.log('開始問卷流程...');
            if (surveyManager) {
                await surveyManager.startSurveyProcess(topic);
            } else {
                throw new Error('問卷管理器未初始化');
            }

        } catch (error) {
            debugLogger.error(`處理生成請求失敗: ${error.message}`);
            alert('系統處理失敗，請稍後重試');
            // 重置按鈕狀態
            newGenerateBtn.disabled = false;
            topicInput.disabled = false;
        }
    });

    debugLogger.log('生成按鈕監聽器設置完成');
}

// 設置對話控制相關的監聽器
function setupDialogueControls() {
    setupPlayAllButton();
    setupPauseButton();
    debugLogger.log('對話控制監聽器設置完成');
}

// 設置播放全部按鈕
function setupPlayAllButton() {
    const playAllBtn = document.getElementById('playAllBtn');
    if (playAllBtn) {
        playAllBtn.addEventListener('click', function() {
            if (audioManager) {
                audioManager.playAll();
            }
        });
    } else {
        debugLogger.warn('找不到播放全部按鈕');
    }
}

// 設置暫停按鈕
function setupPauseButton() {
    const pauseBtn = document.getElementById('pauseBtn');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function() {
            if (audioManager) {
                audioManager.pause();
            }
        });
    } else {
        debugLogger.warn('找不到暫停按鈕');
    }
}

// 重置當前狀態
function resetCurrentState() {
    // 重置音頻管理器
    if (audioManager) {
        audioManager.reset();
    }

    // 清空對話容器
    const dialogueContainer = document.getElementById('dialogueContainer');
    if (dialogueContainer) {
        dialogueContainer.innerHTML = '';
    }

    // 重置生成狀態顯示
    const generationStatus = document.getElementById('generationStatus');
    if (generationStatus) {
        generationStatus.innerHTML = '';
        generationStatus.classList.remove('hidden');
    }

    debugLogger.log('當前狀態已重置');
}

// 輔助函數：檢查必要的DOM元素
function checkRequiredElements() {
    const requiredElements = [
        'topicInput',
        'surveyContainer',
        'dialogueContainer',
        'generationStatus'
    ];

    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        debugLogger.error(`缺少必要的DOM元素: ${missingElements.join(', ')}`);
        return false;
    }
    return true;
}

// 輔助函數：格式化時間
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}