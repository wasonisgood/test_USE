// 音頻管理器
class AudioManager {
    constructor() {
        this.audioQueue = [];
        this.currentAudioIndex = -1;
        this.isPlaying = false;
        this.currentAudio = null;
        
        // UI 元素
        this.playAllBtn = document.getElementById('playAllBtn');
        this.pauseBtn = document.getElementById('pauseBtn');
        this.progressBar = document.querySelector('.progress');
        this.currentTimeDisplay = document.getElementById('currentTime');
        this.totalTimeDisplay = document.getElementById('totalTime');
        
        this.setupEventListeners();
        debugLogger.log('音頻管理器初始化完成');
    }

    setupEventListeners() {
        this.playAllBtn.addEventListener('click', () => this.togglePlayAll());
        this.pauseBtn.addEventListener('click', () => this.togglePause());

        // 添加鍵盤控制
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                this.togglePlayAll();
            }
        });
    }

    addAudio(audioUrl, messageElement) {
        try {
            const audio = new Audio(audioUrl);
            audio.messageElement = messageElement;
            
            audio.addEventListener('timeupdate', () => {
                if (audio === this.currentAudio) {
                    this.updateProgress();
                }
            });

            audio.addEventListener('ended', () => {
                if (audio === this.currentAudio) {
                    this.playNext();
                }
            });

            audio.addEventListener('loadedmetadata', () => {
                if (audio === this.currentAudio) {
                    this.updateTotalTime();
                }
            });

            audio.addEventListener('error', (e) => {
                debugLogger.error(`音頻加載失敗 (${audioUrl}): ${e.target.error.message}`);
            });

            this.audioQueue.push(audio);
            debugLogger.log(`添加音頻到隊列: ${audioUrl}`);
            return audio;
        } catch (error) {
            debugLogger.error(`添加音頻失敗: ${error.message}`);
            return null;
        }
    }

    togglePlayAll() {
        if (!this.isPlaying) {
            if (this.currentAudioIndex === -1 || this.currentAudioIndex >= this.audioQueue.length - 1) {
                this.currentAudioIndex = -1;
                this.playNext();
            } else {
                this.resumeCurrent();
            }
        } else {
            this.pauseCurrent();
        }
    }

    togglePause() {
        if (this.isPlaying) {
            this.pauseCurrent();
        } else {
            this.resumeCurrent();
        }
    }

    async playNext() {
        try {
            if (this.currentAudio) {
                this.currentAudio.messageElement.classList.remove('active-message');
            }

            this.currentAudioIndex++;
            if (this.currentAudioIndex < this.audioQueue.length) {
                const audio = this.audioQueue[this.currentAudioIndex];
                this.currentAudio = audio;
                audio.messageElement.classList.add('active-message');
                
                await audio.play();
                this.isPlaying = true;
                this.updateControls();
                this.updateTotalTime();
                audio.messageElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                debugLogger.log(`開始播放音頻 ${this.currentAudioIndex + 1}/${this.audioQueue.length}`);
            } else {
                this.currentAudioIndex = -1;
                this.isPlaying = false;
                this.currentAudio = null;
                this.updateControls();
                debugLogger.log('播放隊列結束');
            }
        } catch (error) {
            debugLogger.error(`播放失敗: ${error.message}`);
            this.playNext(); // 嘗試播放下一個
        }
    }

    pauseCurrent() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.isPlaying = false;
            this.updateControls();
            debugLogger.log('暫停播放');
        }
    }

    async resumeCurrent() {
        if (this.currentAudio) {
            try {
                await this.currentAudio.play();
                this.isPlaying = true;
                this.updateControls();
                debugLogger.log('恢復播放');
            } catch (error) {
                debugLogger.error(`恢復播放失敗: ${error.message}`);
            }
        }
    }

    updateControls() {
        this.playAllBtn.textContent = this.isPlaying ? '暫停' : '播放全部';
        this.pauseBtn.disabled = !this.currentAudio;
        this.pauseBtn.textContent = this.isPlaying ? '暫停' : '繼續';
    }

    updateProgress() {
        if (this.currentAudio) {
            const progress = (this.currentAudio.currentTime / this.currentAudio.duration) * 100;
            this.progressBar.style.width = `${progress}%`;
            this.currentTimeDisplay.textContent = formatTime(this.currentAudio.currentTime);
        }
    }

    updateTotalTime() {
        if (this.currentAudio) {
            this.totalTimeDisplay.textContent = formatTime(this.currentAudio.duration);
        }
    }

    reset() {
        this.audioQueue.forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });
        
        this.audioQueue = [];
        this.currentAudioIndex = -1;
        this.isPlaying = false;
        this.currentAudio = null;
        this.progressBar.style.width = '0%';
        this.currentTimeDisplay.textContent = '0:00';
        this.totalTimeDisplay.textContent = '0:00';
        this.updateControls();
        debugLogger.log('音頻管理器已重置');
    }
}

// 初始化音頻管理器
const audioManager = new AudioManager();