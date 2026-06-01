const dropzone = document.getElementById('dropzone');               // Для загрузки видео
const infoPanel = document.getElementById('infoPanel');
const videoInput = document.getElementById('videoInput');
const videoPlayer = document.getElementById('videoPlayer');
const videoFileName = document.getElementById('videoFileName');
const videoContainer = document.getElementById('videoContainer');
const loadingSpinner = document.getElementById('loadingSpinner');
        
const documentsUpload = document.getElementById('documentsUpload');
const documentsInput = document.getElementById('documentsInput');
const documentsInfo = document.getElementById('documentsInfo');
const documentsList = document.getElementById('documentsList');
const startButton = document.getElementById('startButton');

const exportButton = document.getElementById('exportButton');
const exportMenu = document.getElementById('exportMenu');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const exportDocxBtn = document.getElementById('exportDocxBtn');

let uploadedDocuments = [];

let uploadedVideo = null;

let pollInterval = null;

let timerInterval = null;
let estimatedWaitTime = null;


// ==================== ЕСЛИ МЫ НА СТРАНИЦЕ ЗАДАЧИ ====================
if (TASK_ID != "None") {
    // Мы на странице задачи /<task_id>
    // Восстанавливаем UI: показываем видео и документы с сервера
    // Если есть документы в БД — показываем их в списке
    documentsUpload.style.display = 'none'
    if (TASK_DOCUMENT_NAMES.length > 0) {
        restoreDocumentsList(TASK_DOCUMENT_NAMES);
    }

    if (TASK_STATUS === 'completed') {
        restoreVideoAndShowResult(TASK_RESULT, TASK_VIDEO_FILENAME);
    } else if (TASK_STATUS === 'failed') {
        restoreVideoAndShowError(TASK_ERROR, TASK_VIDEO_FILENAME);
    } else if (TASK_STATUS === 'processing' || TASK_STATUS === 'pending') {
        restoreVideoForProcessing(TASK_VIDEO_FILENAME);
        pollTaskStatus(TASK_ID);
    }
}
// Если TASK_ID === null — обычная форма загрузки (работает как раньше)

// ==================== POLLING ====================
function pollTaskStatus(taskId) {
    pollInterval = setInterval(() => {
        fetch('/api/task/' + taskId)
            .then(r => r.json())
            .then(data => {
                switch (data.status) {
                    case 'completed':
                        clearInterval(pollInterval);
                        loadingSpinner.classList.remove('active');
                        displayInstructions(data.result);
                        showExportButton();
                        const videoInfo = document.querySelector('.video-info small');
                        if (videoInfo) videoInfo.textContent = '✓ Обработка завершена';
                        break;
                    case 'failed':
                        clearInterval(pollInterval);
                        loadingSpinner.classList.remove('active');
                        infoPanel.innerHTML = `
                            <div class="instruction-item" style="border-left-color: #dc3545;">
                                <div class="instruction-title" style="color: #dc3545;">
                                    <i class="fas fa-exclamation-triangle"></i> Ошибка обработки
                                </div>
                                <div class="instruction-description">${escapeHtml(data.error)}</div>
                            </div>
                        `;
                        const videoInfo2 = document.querySelector('.video-info small');
                        if (videoInfo2) videoInfo2.textContent = '✗ Ошибка обработки';
                        break;
                }
            })
            .catch(() => {});
    }, 2000);
}

// ==================== UI ФУНКЦИИ ====================

// Востановление списка документов
function restoreDocumentsList(names) {
    uploadedDocuments = []
    // Восстанавливаем список документов только визуально
    names.forEach((name, index) => {
        const item = document.createElement('div');
        item.className = 'document-item';
        item.innerHTML = `
            <span class="document-item-name" title="${escapeHtml(name)}">
                <i class="fas fa-file"></i> ${escapeHtml(name)}
            </span>
            <span class="document-item-size" style="color: #6c757d; font-style: italic;">
                (на сервере)
            </span>
            <span style="color: #6c757d; font-size: 11px;">
                <i class="fas fa-check"></i>
            </span>
        `;
        documentsInfo.style.display = 'none'
        documentsList.appendChild(item);
        uploadedDocuments.push(name);
    });
}

// Востановление видео с сервера
// Используем в других функциях
function restoreVideoPlayer(filename) {
    // Скрываем dropzone
    dropzone.style.display = 'none';
    // Показываем контейнер видео
    videoContainer.classList.add('active');
    // Устанавливаем src видео — теперь с сервера по API
    videoPlayer.src = `/api/task/${TASK_ID}/video`;
    videoFileName.textContent = filename;
    // Загружаем метаданные
    videoPlayer.onloadedmetadata = () => {
        const videoDuration = videoPlayer.duration;
        const estimatedSeconds = videoDuration + 30 + uploadedDocuments.length * 180;
        estimatedWaitTime = estimatedSeconds;
        // Если мы в процессе обработки, запускаем таймер
        if (TASK_STATUS === 'processing' || TASK_STATUS === 'pending') {
            let remainingSeconds = 0
            if(TASK_START_TIME){
                const now = new Date();
                const start = new Date(TASK_START_TIME)
                // Разница в секундах
                const secondsPassed = (now - start) / 1000;
                // 3. Вычисляем остаток
                remainingSeconds = estimatedSeconds - secondsPassed;
            }

            startWaitTimer(remainingSeconds);
        }
        if (TASK_STATUS === 'completed') {
            showProcessingCompletionInfo();
        }
    };
    videoPlayer.load();
}

// Если задача в обработке
function restoreVideoForProcessing(video) {
    // Видео + документы видны, показываем спиннер и начинаем polling
    restoreVideoPlayer(video);
    
    infoPanel.innerHTML = `
        <div class="info-panel-empty">
            <div>
                <div class="info-panel-empty-icon">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <p style="margin: 0;">Обработка видео...</p>
            </div>
        </div>
    `;
    
    loadingSpinner.classList.add('active');
}

// Если видео уже обработано
function restoreVideoAndShowResult(result, video) {
    // Видео + документы видны, показываем готовый результат
    restoreVideoPlayer(video);
    displayInstructions(result);
    showExportButton();
}

// На случай ошибки, не проверялось
function restoreVideoAndShowError(errorMsg, video) {
    // Видео + документы видны, показываем ошибку
    restoreVideoPlayer(video);
    
    infoPanel.innerHTML = `
        <div class="instruction-item" style="border-left-color: #dc3545;">
            <div class="instruction-title" style="color: #dc3545;">
                <i class="fas fa-exclamation-triangle"></i> Ошибка обработки
            </div>
            <div class="instruction-description">${escapeHtml(errorMsg)}</div>
        </div>
    `;
    
    const videoInfo = document.querySelector('.video-info small');
    if (videoInfo) videoInfo.textContent = '✗ Ошибка обработки';
}

// Отображение готовой инструкции
function displayInstructions(instructionData) {
    console.log('Displaying instructions:', instructionData);
    
    if (!instructionData && !INSTRUCTION_DATA) {
        infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description text-danger">Ошибка: нет данных для отображения</div></div>`;
        return;
    }
    
    try {
        // Приоритет: используем INSTRUCTION_DATA из шаблона, если он есть, иначе парсим переданные данные
        let data = INSTRUCTION_DATA || instructionData;
        
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description">${escapeHtml(data)}</div></div>`;
                return;
            }
        }
        
        // Ожидаем структуру: { instruction: {title, description, ...}, steps: [], keywords: {keywords_list: []} }
        let instruction = null;
        let steps = [];
        let keywords = [];

        if (data.instruction) {
            instruction = data.instruction;
            steps = data.steps || [];
            keywords = (data.keywords && data.keywords.keywords_list) ? data.keywords.keywords_list : [];
        } else if (data.steps) {
            // Старый формат или упрощенный
            steps = data.steps;
            instruction = { title: data.name || 'Инструкция', description: data.description || '' };
            keywords = data.key_words || [];
        } else if (Array.isArray(data)) {
            steps = data;
        }

        let html = '';
        
        // 1. Заголовок и описание инструкции
        if (instruction) {
            html += `
                <div class="instruction-item" style="border-left-color: #764ba2; background: #fcfaff;">
                    <div class="instruction-title" style="font-size: 16px; color: #764ba2;">
                        <i class="fas fa-book-open"></i> ${escapeHtml(instruction.title || 'Инструкция')}
                    </div>
                    <div class="instruction-description" style="font-weight: 500;">${escapeHtml(instruction.description || '')}</div>
                    ${keywords.length > 0 ? `
                        <div class="instruction-time" style="margin-top: 10px; font-style: italic;">
                            <i class="fas fa-tags"></i> ${keywords.map(k => `#${escapeHtml(k)}`).join(' ')}
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        // 2. Шаги инструкции
        if (steps && Array.isArray(steps)) {
            if (steps.length === 0) {
                html += `<div class="instruction-item"><div class="instruction-description">Шаги не найдены</div></div>`;
            } else {
                steps.forEach((item, index) => {
                    const title = item.title || item.name || 'Без названия';
                    const description = item.text || item.description || item.content || '';
                    
                    const startTimeSeconds = parseFloat(item.time_start || item.startTime || item.start_start || 0);
                    const endTimeSeconds = parseFloat(item.time_end || item.endTime || item.end_time || 0);
                    
                    const startTimeFormatted = formatTime(startTimeSeconds);
                    const endTimeFormatted = formatTime(endTimeSeconds);
                    
                    html += `
                        <div class="instruction-item">
                            <div class="instruction-title">Шаг ${index + 1}: ${escapeHtml(String(title))}</div>
                            <div class="instruction-description">${escapeHtml(String(description))}</div>
                            <div class="instruction-time" style="cursor: pointer;">
                                <i class="fas fa-clock"></i>
                                <span class="time-link" onclick="seekVideo(${startTimeSeconds})" title="Перейти к началу шага">
                                    ${startTimeFormatted}
                                </span>
                                <span> - </span>
                                <span class="time-link" onclick="seekVideo(${endTimeSeconds})" title="Перейти к концу шага">
                                    ${endTimeFormatted}
                                </span>
                            </div>
                        </div>
                    `;
                });
            }
        } else if (!instruction) {
            html = `<div class="instruction-item"><div class="instruction-description text-danger">Данные инструкции отсутствуют или имеют неверный формат</div></div>`;
        }
        
        infoPanel.innerHTML = html;
    } catch (e) {
        console.error('Ошибка при отображении инструкции:', e);
        infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description text-danger">Ошибка отображения: ${escapeHtml(e.message)}</div></div>`;
    }
}

// Работа таймера
function startWaitTimer(estimatedSeconds) {
    let remainingSeconds = Math.ceil(estimatedSeconds);
    estimatedWaitTime = estimatedSeconds;
    
    const timerHtml = `
        <div class="wait-timer" id="waitTimer">
            <div>⏱️ Ожидаемое время обработки:</div>
            <span class="timer-value" id="timerValue">${formatTime(remainingSeconds)}</span>
        </div>
    `;
    
    infoPanel.innerHTML = timerHtml;
    
    // Запускаем таймер отсчета
    timerInterval = setInterval(() => {
        remainingSeconds--;
        const timerValueElement = document.getElementById('timerValue');
        const waitTimer = document.getElementById('waitTimer');
        
        if (timerValueElement && waitTimer) {
            // Если время превышено, окрашиваем в красный
            if (remainingSeconds < 0) {
                waitTimer.classList.add('exceeded');
                waitTimer.querySelector('div').textContent = '⏱️ Превышено на:';
                // Показываем превышение в позитивном формате (abs)
                timerValueElement.textContent = formatTime(Math.abs(remainingSeconds));
            } else {
                timerValueElement.textContent = formatTime(remainingSeconds);
            }
        }
    }, 1000);
}

// ==================== Утилиты ====================

// Функция удаления опасных символов
// Используется при всавке элементов на стрницу
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Преобразование времени
function formatTime(seconds) {
    // Преобразует секунды в формат mm:ss или hh:mm:ss
    if (isNaN(seconds) || seconds < 0) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    // Если видео длиннее часа, показываем hh:mm:ss
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    // Иначе показываем mm:ss
    return `${minutes}:${String(secs).padStart(2, '0')}`;
}

// Функция загрузки видео, вызывается в videoInput.addEventListener или 
function handleVideoUpload(file) {
    if (!file.type.startsWith('video/')) {
        alert('Пожалуйста, выберите видео файл');
        return;
    }

    uploadedVideo = file;
    
    // Показываем видео плеер
    const reader = new FileReader();
    reader.onload = (e) => {
        dropzone.style.display = 'none';
        videoPlayer.src = e.target.result;
        videoFileName.textContent = file.name;
        videoContainer.classList.add('active');
        
        // Получаем длительность видео и обновляем состояние кнопки
        videoPlayer.onloadedmetadata = () => {
            startButton.disabled = false;
            startButton.classList.remove('start-button-hidden');
        };
    };
    reader.readAsDataURL(file);
}

// Функция загрузки документов, вызывается в documentsInput.addEventListener или 
function handleDocumentsUpload(files) {
    const MAX_FILES = 5;
    const MAX_SIZE_MB = 30;
    const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;
    
    // Проверяем общее количество файлов
    if (uploadedDocuments.length + files.length > MAX_FILES) {
        alert(`Максимум ${MAX_FILES} файлов. Вы можете загрузить еще ${MAX_FILES - uploadedDocuments.length}`);
        return;
    }
    
    let totalSize = uploadedDocuments.reduce((sum, doc) => sum + doc.size, 0);
    
    // Добавляем новые файлы с валидацией
    for (let file of files) {
        if (uploadedDocuments.some(doc => doc.name === file.name)){
            alert(`Файл с таким названием уже присутвует в списке ${file.name}`);
            continue;
        }
        if (totalSize + file.size > MAX_SIZE_BYTES) {
            alert(`Общий размер файлов превышает ${MAX_SIZE_MB}МБ`);
            break;
        }
        uploadedDocuments.push(file);
        totalSize += file.size;
    }
    updateDocumentsList();
    //updateStartButtonState();
}

// Загрузка документов на форму
function updateDocumentsList() {
    documentsList.innerHTML = '';
    
    if (uploadedDocuments.length === 0) {
        documentsList.innerHTML = '';
        documentsInfo.innerHTML = `
        <strong>Ограничения</strong>
        <br> • Макс. 5 файлов
        <br> • Макс. 30 МБ всего
        `
        return;
    }
    
    let totalSize = 0;
    uploadedDocuments.forEach((doc, index) => {
        totalSize += doc.size;
        const sizeKB = (doc.size / 1024).toFixed(1);
        const sizeDisplay = doc.size > 1024 * 1024 ? 
            `${(doc.size / (1024 * 1024)).toFixed(1)}MB` : 
            `${sizeKB}KB`;
        
        const item = document.createElement('div');
        item.className = 'document-item';
        item.innerHTML = `
            <span class="document-item-name" title="${doc.name}">
                <i class="fas fa-file"></i> ${doc.name}
            </span>
            <span class="document-item-size">${sizeDisplay}</span>
            <button class="document-remove" onclick="removeDocument(${index})" title="Удалить">
                <i class="fas fa-times"></i>
            </button>
        `;
        documentsList.appendChild(item);
    });
    
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
    if (documentsInfo) {
        documentsInfo.innerHTML = `
            <strong>Загружено:</strong> ${uploadedDocuments.length}/5 файлов<br>
            <strong>Размер:</strong> ${totalSizeMB}/30 МБ
        `;
    }
}

// Удаление документа из списка для обработки
function removeDocument(index) {
    uploadedDocuments.splice(index, 1);
    updateDocumentsList();
    //updateStartButtonState();
}

// Пеермотка на указаный отрезок
function seekVideo(timeInSeconds) {
    // Переходит к нужному времени в видео
    const video = document.getElementById('videoPlayer');
    if (video) {
        video.currentTime = timeInSeconds;
        // Если видео на паузе, начинаем проигрывание
        if (video.paused) {
            video.play().catch(err => console.log('Не удалось начать проигрывание:', err));
        }
    }
}

// Отображение времени обработки
function showProcessingCompletionInfo() {
    let start = new Date(TASK_START_TIME);
    let end = new Date(TASK_END_TIME);

    let message = `Начало обработки ${formatDateTime(start)}<br>Окончание - ${formatDateTime(end)}<br>`;
    
    // Разница в секундах
    const secondsPassed = (end - start) / 1000;
    const isExceeded = secondsPassed > estimatedWaitTime;

    if (isExceeded) {
        const excessSeconds = secondsPassed - estimatedWaitTime;
        message += `⏱️ Обработано за ${formatTime(secondsPassed)} (превышено на ${formatTime(excessSeconds)})`;
    } else {
        message += `✓ Обработано за ${formatTime(secondsPassed)}`;
    }
    
    updateVideoInfo(message);
}

// Обновление сообщения о видео
function updateVideoInfo(message) {
    const videoInfo = document.querySelector('.video-info small');
    if (videoInfo) {
        videoInfo.innerHTML = message;
    }
}

// Подготовка к обработке
function startProcessing() {
    startButton.disabled = true;
    startButton.classList.add('start-button-hidden');
    uploadVideoToServer(uploadedVideo);
}

// Загрузка файлов на сервер
function uploadVideoToServer(file) {
    const formData = new FormData();
    formData.append('video', file);
    uploadedDocuments.forEach(doc => formData.append('documents', doc));

    fetch('/api/process', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // 303 redirect — браузер переходит сам, ничего делать не нужно
        // Но если AJAX не следует редиректу автоматически:
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => {
        loadingSpinner.classList.remove('active');
        alert('Ошибка: ' + error.message);
        resetUpload();
    });
}

// Форматирование даты
function formatDateTime(date) {
    if (!date || !(date instanceof Date) || isNaN(date)) return '';
    // Форматируем как "DD.MM.YYYY HH:MM:SS" в локальном времени
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Месяцы с 0
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
}

// На случай ошибок - не тестилось
function resetUpload() {
    uploadedVideo = null;
    videoInput.value = '';
    dropzone.style.display = 'block';
    videoContainer.classList.remove('active');
    loadingSpinner.classList.remove('active');
    startButton.classList.add('start-button-hidden');
    videoPlayer.src = '';
    
    // Возвращаем зону загрузки документов
    const documentsUploadZone = document.getElementById('documentsUpload');
    if (documentsUploadZone) {
        documentsUploadZone.style.display = 'block';
    }
    
    isVideoLoaded = false;
    isProcessing = false;
    
    // Очищаем таймер и переменные
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    processingStartTime = null;
    estimatedWaitTime = null;
    
    infoPanel.innerHTML = `
        <div class="info-panel-empty">
            <div>
                <div class="info-panel-empty-icon">
                    <i class="fas fa-video"></i>
                </div>
                <p style="margin: 0;">Загрузите видео для обработки</p>
            </div>
        </div>
    `;
}

// ==================== Обработчики ====================
dropzone.addEventListener('click', () => videoInput.click());

videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleVideoUpload(e.target.files[0]);
    }
});

documentsUpload.addEventListener('click', () => documentsInput.click());

documentsInput.addEventListener('change', (e) => {
    handleDocumentsUpload(e.target.files);
    // Очищаем input для возможности повторной загрузки
    e.target.value = '';
});

// Drag&Drop для видео
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleVideoUpload(files[0]);
    }
});

// Drag&Drop для файлов
documentsUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    documentsUpload.classList.add('dragover');
});

documentsUpload.addEventListener('dragleave', () => {
    documentsUpload.classList.remove('dragover');
});

documentsUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    documentsUpload.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleDocumentsUpload(files);
    }
});

// Кнопка "Начать обработку"
startButton.addEventListener('click', () => {
    startProcessing();
});

// ==================== ЭКСПОРТ И РЕДАКТИРОВАНИЕ ИНСТРУКЦИИ ====================

// Показать кнопку экспорта
function showExportButton() {
    const exportBtn = document.getElementById('exportButton');
    if (exportBtn) {
        exportBtn.disabled = false;
    }
}

// Скрыть кнопку экспорта
function hideExportButton() {
    const exportBtn = document.getElementById('exportButton');
    const exportMenu = document.getElementById('exportMenu');
    if (exportBtn) {
        exportBtn.disabled = true;
    }
    if (exportMenu) {
        exportMenu.classList.remove('active');
    }
}

// Открыть/закрыть меню экспорта
function toggleExportMenu() {
    const exportMenu = document.getElementById('exportMenu');
    if (exportMenu) {
        exportMenu.classList.toggle('active');
    }
}

// Закрыть меню экспорта
function closeExportMenu() {
    const exportMenu = document.getElementById('exportMenu');
    if (exportMenu) {
        exportMenu.classList.remove('active');
    }
}

// Экспортировать в указанном формате
function exportInstruction(format) {
    if (TASK_ID && TASK_ID !== 'None') {
        window.location.href = `/api/task/${TASK_ID}/instruction?format=${format}`;
        closeExportMenu();
    }
}

// --- РЕДАКТОР ИНСТРУКЦИИ ---

function openEditor() {
    if (!INSTRUCTION_DATA) {
        alert('Данные инструкции еще не готовы');
        return;
    }

    const modal = document.getElementById('editorModal');
    const titleInput = document.getElementById('editTitle');
    const descInput = document.getElementById('editDescription');
    const keysInput = document.getElementById('editKeywords');
    const stepsList = document.getElementById('stepsEditorList');

    // Заполняем основные поля
    const data = INSTRUCTION_DATA.instruction;
    titleInput.value = data.title;
    descInput.value = data.description;
    keysInput.value = (INSTRUCTION_DATA.keywords.keywords_list);
    
    // Заполняем шаги
    stepsList.innerHTML = '';
    const steps = INSTRUCTION_DATA.steps || [];
    steps.forEach((step, index) => {
        addStepToEditor(step, index);
    });

    modal.style.display = 'flex';
}

function closeEditor() {
    document.getElementById('editorModal').style.display = 'none';
}

function addStepToEditor(stepData = null, index = null) {
    const stepsList = document.getElementById('stepsEditorList');
    const stepId = stepData ? stepData.id : strUuid();
    
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-editor-item';
    stepDiv.dataset.id = stepId;
    // Сохраняем image_id в data-атрибуте, чтобы не потерять при сохранении
    if (stepData && stepData.image_id) {
        stepDiv.dataset.imageId = stepData.image_id;
    }
    
    stepDiv.innerHTML = `
        <div class="step-editor-controls">
            <button class="btn btn-outline-secondary btn-small" onclick="moveStep(this, -1)"><i class="fas fa-arrow-up"></i></button>
            <button class="btn btn-outline-secondary btn-small" onclick="moveStep(this, 1)"><i class="fas fa-arrow-down"></i></button>
            <button class="btn btn-outline-danger btn-small" onclick="removeStep(this)"><i class="fas fa-trash"></i></button>
        </div>
        <div class="mb-2">
            <input type="text" class="form-control form-control-sm step-title" placeholder="Заголовок шага" value="${stepData ? escapeHtml(stepData.title) : ''}">
        </div>
        <div class="mb-2">
            <textarea class="form-control form-control-sm step-text" rows="2" placeholder="Описание шага">${stepData ? escapeHtml(stepData.text) : ''}</textarea>
        </div>
        <div class="d-flex gap-2">
            <div class="flex-fill">
                <small class="text-muted">Начало (сек)</small>
                <input type="number" step="0.1" class="form-control form-control-sm step-start" value="${stepData ? stepData.time_start : '0'}">
            </div>
            <div class="flex-fill">
                <small class="text-muted">Конец (сек)</small>
                <input type="number" step="0.1" class="form-control form-control-sm step-end" value="${stepData ? stepData.time_end : '0'}">
            </div>
        </div>
    `;
    
    stepsList.appendChild(stepDiv);
}

function moveStep(btn, direction) {
    const item = btn.closest('.step-editor-item');
    if (direction === -1 && item.previousElementSibling) {
        item.parentNode.insertBefore(item, item.previousElementSibling);
    } else if (direction === 1 && item.nextElementSibling) {
        item.parentNode.insertBefore(item.nextElementSibling, item);
    }
}

function removeStep(btn) {
    if (confirm('Удалить этот шаг?')) {
        btn.closest('.step-editor-item').remove();
    }
}

function addNewStep() {
    addStepToEditor();
}

async function saveInstruction() {
    const title = document.getElementById('editTitle').value;
    const description = document.getElementById('editDescription').value;
    const keywords = document.getElementById('editKeywords').value.split(',').map(k => k.trim()).filter(k => k);
    
    const steps = [];
    document.querySelectorAll('.step-editor-item').forEach(item => {
        steps.push({
            id: item.dataset.id,
            title: item.querySelector('.step-title').value,
            text: item.querySelector('.step-text').value,
            time_start: parseFloat(item.querySelector('.step-start').value) || 0,
            time_end: parseFloat(item.querySelector('.step-end').value) || 0,
            image_id: item.dataset.imageId || "null"
        });
    });

    const payload = {
        title,
        description,
        keywords,
        steps
    };

    try {
        const response = await fetch(`/api/instruction/${INSTRUCTION_DATA.instruction.id}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            alert('Инструкция успешно сохранена!');
            closeEditor();
            // Перезагружаем страницу, чтобы обновить данные в INSTRUCTION_DATA
            window.location.reload();
        } else {
            const err = await response.json();
            alert('Ошибка сохранения: ' + (err.error || 'Неизвестная ошибка'));
        }
    } catch (e) {
        alert('Ошибка сети: ' + e.message);
    }
}

function strUuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Обработчики для кнопок экспорта
if (exportButton) {
    exportButton.addEventListener('click', () => {
        toggleExportMenu();
    });
}

if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', () => {
        exportInstruction('pdf');
    });
}

if (exportDocxBtn) {
    exportDocxBtn.addEventListener('click', () => {
        exportInstruction('docx');
    });
}

// Обработчик кнопки редактирования
if (document.getElementById('editButton')) {
    document.getElementById('editButton').addEventListener('click', openEditor);
}

// Закрыть меню при клике вне его
document.addEventListener('click', (e) => {
    const exportSection = document.getElementById('exportButton')?.parentElement;
    if (exportSection && !exportSection.contains(e.target)) {
        closeExportMenu();
    }
});