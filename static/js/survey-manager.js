// survey-manager.js

class SurveyManager {
        constructor() {
            this.currentSurvey = null;
            this.surveyResponses = {};
            this.surveyId = null;
            this.analysis = null;
            this.plan = null;
            this.currentStep = 1;
            
            // 確保DOM完全加載後再初始化
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initialize());
            } else {
                this.initialize();
            }
            
            debugLogger.log('問卷管理器初始化完成');
        }
    
        initialize() {
            // 驗證必要的DOM元素存在
            const requiredElements = [
                'generateBtn',
                'surveyContainer',
                'surveyStatus',
                'analysisResult',
                'programPlan'
            ];
    
            const missingElements = requiredElements.filter(id => !document.getElementById(id));
            if (missingElements.length > 0) {
                debugLogger.error(`缺少必要的DOM元素: ${missingElements.join(', ')}`);
                return;
            }
    
            this.setupEventListeners();
            debugLogger.log('問卷管理器DOM元素初始化完成');
        }
    
        setupEventListeners() {
            const generateBtn = document.getElementById('generateBtn');
            if (!generateBtn) {
                debugLogger.error('找不到生成按鈕元素');
                return;
            }
    
            // 使用箭頭函數保持this綁定
            generateBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                const topicInput = document.getElementById('topicInput');
                if (!topicInput) {
                    debugLogger.error('找不到主題輸入框元素');
                    return;
                }
    
                const topic = topicInput.value.trim();
                if (!topic) {
                    alert('請輸入對話主題');
                    return;
                }
                
                await this.startSurveyProcess(topic);
            });
        }
    

    setupEventListeners() {
        // 改變原有的生成按鈕行為
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const topic = topicInput.value.trim();
            if (!topic) {
                alert('請輸入對話主題');
                return;
            }
            
            // 開始問卷流程
            await this.startSurveyProcess(topic);
        });
    }

    async startSurveyProcess(topic) {
        try {
            // 顯示狀態
            this.updateStatus('生成問卷中...');
            generateBtn.disabled = true;
            topicInput.disabled = true;

            // 請求生成問卷
            wsHandler.sendMessage({
                type: 'survey_generate',
                topic: topic
            });

        } catch (error) {
            debugLogger.error(`開始問卷流程失敗: ${error.message}`);
            this.handleError('開始問卷流程失敗');
        }
    }

    handleSurveyGenerated(data) {
        try {
            this.currentSurvey = data.survey;
            this.surveyId = data.survey_id;
            this.renderSurvey();
            this.updateStatus('請完成問卷');
            this.updateProgressBar(1);
            debugLogger.log('問卷生成完成');
        } catch (error) {
            debugLogger.error(`處理問卷生成結果失敗: ${error.message}`);
            this.handleError('處理問卷失敗');
        }
    }

    renderSurvey() {
        const container = document.getElementById('surveyContainer');
        container.innerHTML = ''; // 清空容器

        // 添加進度指示器
        const progressBar = this.createProgressBar();
        container.appendChild(progressBar);

        // 渲染問卷標題和描述
        const header = document.createElement('div');
        header.className = 'mb-6';
        header.innerHTML = `
            <h3 class="text-xl font-semibold">${this.currentSurvey.title}</h3>
            <p class="text-gray-600 mt-2">${this.currentSurvey.description}</p>
        `;
        container.appendChild(header);

        // 渲染每個部分
        this.currentSurvey.sections.forEach(section => {
            const sectionElement = this.createSection(section);
            container.appendChild(sectionElement);
        });

        // 添加提交按鈕
        const submitButton = document.createElement('button');
        submitButton.className = 'mt-6 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2';
        submitButton.textContent = '提交問卷';
        submitButton.onclick = () => this.submitSurvey();
        container.appendChild(submitButton);
    }

    createProgressBar() {
        const progress = document.createElement('div');
        progress.className = 'survey-progress mb-8';
        progress.innerHTML = `
            <div class="progress-step">
                <div class="step-indicator active">1</div>
                <div class="step-label">問卷填寫</div>
            </div>
            <div class="progress-step">
                <div class="step-indicator">2</div>
                <div class="step-label">分析結果</div>
            </div>
            <div class="progress-step">
                <div class="step-indicator">3</div>
                <div class="step-label">節目規劃</div>
            </div>
        `;
        return progress;
    }
    createSection(section) {
        const sectionElement = document.createElement('div');
        sectionElement.className = 'survey-section mb-8';
        sectionElement.innerHTML = `
            <h4 class="text-lg font-semibold mb-4">${section.title}</h4>
            ${section.description ? `<p class="text-gray-600 mb-4">${section.description}</p>` : ''}
        `;

        // 渲染問題
        section.questions.forEach(question => {
            const questionElement = this.createQuestion(question);
            sectionElement.appendChild(questionElement);
        });

        return sectionElement;
    }

    createQuestion(question) {
        const questionElement = document.createElement('div');
        questionElement.className = 'survey-question mb-6';
        
        // 問題標題
        const titleElement = document.createElement('div');
        titleElement.className = 'question-title flex items-center';
        titleElement.innerHTML = `
            <span class="text-gray-800">${question.title}</span>
            ${question.required ? '<span class="text-red-500 ml-1">*</span>' : ''}
        `;
        questionElement.appendChild(titleElement);

        // 問題描述（如果有）
        if (question.description) {
            const descElement = document.createElement('div');
            descElement.className = 'question-description';
            descElement.textContent = question.description;
            questionElement.appendChild(descElement);
        }

        // 根據問題類型創建不同的輸入元素
        const inputElement = this.createQuestionInput(question);
        questionElement.appendChild(inputElement);

        // 添加驗證錯誤顯示區域
        const errorElement = document.createElement('div');
        errorElement.className = 'validation-error hidden';
        errorElement.id = `error-${question.question_id}`;
        questionElement.appendChild(errorElement);

        return questionElement;
    }

    createQuestionInput(question) {
        const container = document.createElement('div');
        container.className = 'mt-3';

        switch (question.type) {
            case 'single_choice':
                container.className += ' options-container';
                question.options.forEach(option => {
                    const optionElement = document.createElement('label');
                    optionElement.className = 'option-item';
                    optionElement.innerHTML = `
                        <input type="radio" 
                               name="${question.question_id}" 
                               value="${option.value}"
                               class="mr-3">
                        <span>${option.label}</span>
                    `;
                    container.appendChild(optionElement);
                });
                break;

            case 'multiple_choice':
                container.className += ' options-container';
                question.options.forEach(option => {
                    const optionElement = document.createElement('label');
                    optionElement.className = 'option-item';
                    optionElement.innerHTML = `
                        <input type="checkbox" 
                               name="${question.question_id}" 
                               value="${option.value}"
                               class="mr-3">
                        <span>${option.label}</span>
                    `;
                    container.appendChild(optionElement);
                });
                break;

            case 'rating':
                container.className += ' rating-container';
                const max = question.validation?.max || 5;
                for (let i = 1; i <= max; i++) {
                    const starElement = document.createElement('span');
                    starElement.className = 'rating-star text-2xl';
                    starElement.innerHTML = '★';
                    starElement.dataset.value = i;
                    starElement.onclick = () => this.handleRatingClick(question.question_id, i);
                    container.appendChild(starElement);
                }
                break;

            case 'text':
                const textInput = document.createElement('textarea');
                textInput.className = 'text-input';
                textInput.name = question.question_id;
                textInput.rows = 3;
                if (question.validation) {
                    textInput.maxLength = question.validation.max_length;
                }
                container.appendChild(textInput);
                break;
        }

        return container;
    }
    handleRatingClick(questionId, value) {
        // 處理評分點擊
        const container = document.querySelector(`[name="${questionId}"]`).parentElement;
        const stars = container.querySelectorAll('.rating-star');
        stars.forEach((star, index) => {
            star.classList.toggle('active', index < value);
        });
        this.surveyResponses[questionId] = value;
    }

    async submitSurvey() {
        try {
            if (!this.validateResponses()) {
                return;
            }

            this.updateStatus('提交問卷中...');
            
            // 發送問卷回答
            wsHandler.sendMessage({
                type: 'survey_submit',
                survey_id: this.surveyId,
                responses: this.surveyResponses
            });

        } catch (error) {
            debugLogger.error(`提交問卷失敗: ${error.message}`);
            this.handleError('提交問卷失敗');
        }
    }

    validateResponses() {
        let isValid = true;
        const errors = new Set();

        this.currentSurvey.sections.forEach(section => {
            section.questions.forEach(question => {
                const error = this.validateQuestion(question);
                if (error) {
                    errors.add(error);
                    this.showError(question.question_id, error);
                    isValid = false;
                }
            });
        });

        if (!isValid) {
            alert(`請檢查以下問題:\n${Array.from(errors).join('\n')}`);
        }

        return isValid;
    }

    validateQuestion(question) {
        const response = this.surveyResponses[question.question_id];
        
        if (question.required && !response) {
            return `${question.title} 為必填項目`;
        }

        if (!response) return null;

        switch (question.type) {
            case 'multiple_choice':
                const selectedCount = response.length;
                const { min_select, max_select } = question.validation || {};
                if (min_select && selectedCount < min_select) {
                    return `${question.title} 至少選擇 ${min_select} 項`;
                }
                if (max_select && selectedCount > max_select) {
                    return `${question.title} 最多選擇 ${max_select} 項`;
                }
                break;

            case 'text':
                const { min_length, max_length } = question.validation || {};
                if (min_length && response.length < min_length) {
                    return `${question.title} 最少需要 ${min_length} 個字`;
                }
                if (max_length && response.length > max_length) {
                    return `${question.title} 最多允許 ${max_length} 個字`;
                }
                break;

            case 'rating':
                const { min, max } = question.validation || {};
                if (min && response < min) {
                    return `${question.title} 最小評分為 ${min}`;
                }
                if (max && response > max) {
                    return `${question.title} 最大評分為 ${max}`;
                }
                break;
        }

        return null;
    }

    showError(questionId, message) {
        const errorElement = document.getElementById(`error-${questionId}`);
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }

    handleAnalysisReceived(data) {
        try {
            this.analysis = data.analysis;
            this.renderAnalysis();
            this.updateStatus('分析完成');
            this.updateProgressBar(2);
            
            // 自動請求生成節目規劃
            wsHandler.sendMessage({
                type: 'program_plan',
                survey_id: this.surveyId
            });
            
            debugLogger.log('問卷分析完成');
        } catch (error) {
            debugLogger.error(`處理分析結果失敗: ${error.message}`);
            this.handleError('處理分析結果失敗');
        }
    }

    renderAnalysis() {
        const container = document.getElementById('analysisResult');
        container.classList.remove('hidden');
        
        container.innerHTML = `
            <div class="space-y-4">
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-blue-800">認知水平</h4>
                    <p class="text-blue-600">${this.analysis.overview.knowledge_level.description}</p>
                </div>
                
                <div class="bg-green-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-green-800">主要興趣領域</h4>
                    <ul class="list-disc list-inside text-green-600">
                        ${this.analysis.overview.interest_areas
                            .map(area => `<li>${area.area}</li>`)
                            .join('')}
                    </ul>
                </div>
                
                <div class="bg-purple-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-purple-800">學習目標</h4>
                    <p class="text-purple-600">${this.analysis.overview.learning_objectives.depth} 級別理解</p>
                    <p class="text-purple-600">預期投入時間: ${this.analysis.overview.learning_objectives.time_commitment}</p>
                </div>
            </div>
        `;
    }

    handlePlanReceived(data) {
        try {
            this.plan = data.plan;
            this.renderPlan();
            this.updateStatus('規劃完成');
            this.updateProgressBar(3);
            
            // 啟用對話生成按鈕
            generateBtn.disabled = false;
            generateBtn.textContent = '開始生成對話';
            
            debugLogger.log('節目規劃完成');
        } catch (error) {
            debugLogger.error(`處理節目規劃失敗: ${error.message}`);
            this.handleError('處理節目規劃失敗');
        }
    }

    renderPlan() {
        const container = document.getElementById('programPlan');
        container.classList.remove('hidden');
        
        container.innerHTML = `
            <div class="space-y-4">
                <div class="bg-yellow-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-yellow-800">節目信息</h4>
                    <p class="text-yellow-600">時長：${this.plan.program_info.duration} 分鐘</p>
                    <p class="text-yellow-600">目標受眾：${this.plan.program_info.target_audience}</p>
                </div>
                
                <div class="bg-indigo-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-indigo-800">內容結構</h4>
                    ${this.plan.structure.sections.map(section => `
                        <div class="mt-2">
                            <h5 class="font-medium text-indigo-700">${section.title} (${section.duration}分鐘)</h5>
                            <ul class="list-disc list-inside text-indigo-600">
                                ${section.content.topics.map(topic => `<li>${topic}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    updateProgressBar(step) {
        this.currentStep = step;
        const progressSteps = document.querySelectorAll('.progress-step .step-indicator');
        progressSteps.forEach((stepEl, index) => {
            if (index + 1 < step) {
                stepEl.classList.add('completed');
                stepEl.classList.remove('active');
            } else if (index + 1 === step) {
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
            } else {
                stepEl.classList.remove('active', 'completed');
            }
        });
    }

    updateStatus(message) {
        const statusElement = document.getElementById('surveyStatus');
        statusElement.textContent = message;
        debugLogger.log(`問卷狀態更新: ${message}`);
    }

    handleError(message) {
        this.updateStatus(`錯誤: ${message}`);
        alert(message);
        generateBtn.disabled = false;
        topicInput.disabled = false;
    }

    reset() {
        this.currentSurvey = null;
        this.surveyResponses = {};
        this.surveyId = null;
        this.analysis = null;
        this.plan = null;
        this.currentStep = 1;
        
        // 重置 UI
        document.getElementById('surveyContainer').innerHTML = '';
        document.getElementById('analysisResult').classList.add('hidden');
        document.getElementById('programPlan').classList.add('hidden');
        this.updateStatus('');
        debugLogger.log('問卷管理器已重置');
    }
}


