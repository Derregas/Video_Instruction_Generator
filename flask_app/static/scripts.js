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
                // Разница в секундах
                const secondsPassed = (now - parseUTCDate(TASK_START_TIME)) / 1000;
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
    
    if (!instructionData) {
        infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description text-danger">Ошибка: нет данных для отображения</div></div>`;
        return;
    }
    
    try {
        let instructions = instructionData;
        
        // Если это строка, пытаемся парсить как JSON
        if (typeof instructionData === 'string') {
            try {
                instructions = JSON.parse(instructionData);
            } catch (e) {
                console.log('Не получилось парсить как JSON, выводим как текст');
                infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description">${escapeHtml(instructionData)}</div></div>`;
                return;
            }
        }
        
        // Ищем массив: либо это прямо массив, либо массив внутри объекта
        let dataArray = null;
        
        if (Array.isArray(instructions)) {
            dataArray = instructions;
            console.log('Найден прямой массив');
        } else if (typeof instructions === 'object' && instructions !== null) {
            // Ищем первый массив в объекте (может быть instructions, steps, data, items и т.д.)
            dataArray = Object.values(instructions).find(v => Array.isArray(v));
            if (dataArray) {
                console.log('Найден массив внутри объекта');
            }
        }
        
        let html = '';
        
        if (dataArray && Array.isArray(dataArray)) {
            if (dataArray.length === 0) {
                html = `<div class="instruction-item"><div class="instruction-description">Инструкции не найдены</div></div>`;
            } else {
                dataArray.forEach((item, index) => {
                    const title = item.title || item.name || item.step || 'Без названия';
                    const description = item.description || item.text || item.content || '';
                    
                    // Получаем время в секундах и конвертируем в mm:ss или hh:mm:ss
                    const startTimeSeconds = parseFloat(item.start_time || item.startTime || item.time_start || 0);
                    const endTimeSeconds = parseFloat(item.end_time || item.endTime || item.time_end || 0);
                    
                    const startTimeFormatted = formatTime(startTimeSeconds);
                    const endTimeFormatted = formatTime(endTimeSeconds);
                    
                    html += `
                        <div class="instruction-item">
                            <div class="instruction-title">Шаг ${index + 1}: ${escapeHtml(String(title))}</div>
                            <div class="instruction-description">${escapeHtml(String(description))}</div>
                            <div class="instruction-time" style="cursor: pointer;">
                                <i class="fas fa-clock"></i>
                                <span class="time-link" onclick="seekVideo(${startTimeSeconds})" title="Нажмите, чтобы перейти к этому времени">
                                    ${startTimeFormatted}
                                </span>
                                <span> - </span>
                                <span class="time-link" onclick="seekVideo(${endTimeSeconds})" title="Нажмите, чтобы перейти к этому времени">
                                    ${endTimeFormatted}
                                </span>
                            </div>
                        </div>
                    `;
                });
            }
        } else if (typeof instructions === 'object' && instructions !== null) {
            // Если это объект без массива, отображаем его как текст
            html = `<div class="instruction-item"><div class="instruction-description"><pre>${escapeHtml(JSON.stringify(instructions, null, 2))}</pre></div></div>`;
        } else if (typeof instructions === 'string') {
            // Если это простая строка
            html = `<div class="instruction-item"><div class="instruction-description">${escapeHtml(instructions)}</div></div>`;
        } else {
            html = `<div class="instruction-item"><div class="instruction-description">${escapeHtml(String(instructions))}</div></div>`;
        }
        
        infoPanel.innerHTML = html;
    } catch (e) {
        console.error('Ошибка при обработке инструкций:', e);
        infoPanel.innerHTML = `<div class="instruction-item"><div class="instruction-description text-danger">Ошибка при обработке: ${escapeHtml(e.message)}</div></div>`;
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
    let start = parseUTCDate(TASK_START_TIME);
    let end = parseUTCDate(TASK_END_TIME);

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