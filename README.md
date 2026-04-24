# Video Instruction Generator

> Приложение для автоматической обработки видео-инструкций и генерации текстовых инструкций с помощью AI.

![Status](https://img.shields.io/badge/status-development-yellow)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Содержание

- [Обзор](#-обзор)
- [Возможности](#-возможности)
- [Установка](#-установка)
- [Быстрый старт](#-быстрый-старт)
- [Конфигурация](#-конфигурация)
- [Архитектура](#-архитектура)
- [API](#-api)
- [Примеры](#-примеры)
- [Тестирование](#-тестирование)
- [Troubleshooting](#-troubleshooting)

## 🎯 Обзор

Video Instruction Generator преобразует видео-инструкции в структурированный текст с помощью:
- **Whisper AI** для распознавания речи (многоязычная поддержка)
- **GPU ускорение** (CUDA 12.1) для быстрой обработки
- **Модульной архитектуры** для легкого расширения

### Текущий функционал

✅ Извлечение аудио из видео  
✅ Транскрипция речи с временными метками  
✅ Многоязычная поддержка  
✅ GPU / CPU обработка  

🔲 Обработка видео (нарезка, извлечение кадров)  
🔲 Генерация инструкций через LLM  
🔲 Web UI (Django/Flask)  
🔲 REST API  

## ✨ Возможности

| Функция | Статус | Описание |
|---------|--------|---------|
| **Аудио экстракция** | ✅ | Извлечение аудиодорожки из видео |
| **Транскрипция** | ✅ | Автоматическое распознавание речи |
| **Многоязычность** | ✅ | Поддержка 99 языков |
| **GPU ускорение** | ✅ | CUDA 12.1 поддержка |
| **Валидация** | ✅ | Проверка входных данных |
| **Логирование** | ✅ | Подробное логирование в файл и консоль |
| **Конфигурация** | ✅ | .env файлы + Pydantic валидация |
| **Временные файлы** | ✅ | Безопасная работа с временными директориями |

## 🚀 Установка

### Требования
- Python 3.9+
- NVIDIA GPU с CUDA 12.1 (для GPU обработки)
- Windows / Linux / macOS

### Пошаговая установка

#### 1. Клонировать репозиторий
```bash
git clone <repository_url>
cd Video_Instruction_Generator
```

#### 2. Создать виртуальное окружение
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

#### 3. Установить PyTorch с CUDA 12.1
```bash
# Windows / Linux с GPU
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Для CPU (если нет GPU)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

#### 4. Установить остальные зависимости
```bash
pip install -r requirements.txt
```

#### 5. Создать конфигурацию
```bash
cp .env.example .env
# Отредактируйте .env под ваши нужды
```

#### 6. Проверить установку
```bash
python run.py --help
```

## ⚡ Быстрый старт

### Базовая обработка видео

```bash
# Обработать видео и вывести результат в консоль
python run.py video.mp4

# Обработать и сохранить результат в JSON
python run.py video.mp4 --output results.json

# Обработать на CPU (медленнее, но не требует GPU)
python run.py video.mp4 --device cpu

# Использовать более точную модель (медленнее)
python run.py video.mp4 --model large-v3
```

### Programmatic использование

```python
from src import InstructionProcessingService, get_config, setup_logging

# Загрузить конфиг и инициализировать логирование
config = get_config()
setup_logging(config)

# Создать сервис
service = InstructionProcessingService(use_config=True)

# Обработать видео
result = service.process_video("video.mp4")

# Использовать результат
print(f"Язык: {result['language']}")
print(f"Сегментов: {len(result['transcript'])}")

for segment in result['transcript']:
    print(f"[{segment['start']:.1f}s - {segment['end']:.1f}s] {segment['text']}")
```

## 🔧 Конфигурация

Конфигурация загружается из `.env` файла. Скопируйте `.env.example` и отредактируйте:

```bash
cp .env.example .env
```

### Основные параметры

#### Whisper (распознавание речи)
```env
# Размер модели (компромисс между скоростью и точностью)
WHISPER_MODEL_SIZE=base              # tiny, base, small, medium, large-v3

# Устройство обработки
WHISPER_DEVICE=cuda                  # cuda для GPU, cpu для процессора

# Тип вычислений
WHISPER_COMPUTE_TYPE=float16         # float16, float32, int8

# Параметры транскрипции
WHISPER_BEAM_SIZE=5                  # больше = точнее но медленнее
WHISPER_LANGUAGE=                    # auto-detect по умолчанию
```

#### Processing (обработка)
```env
# Директория для временных файлов
PROCESSING_TEMP_DIR=./temp

# Удалять ли temps после обработки
PROCESSING_CLEANUP_TEMP=true

# Количество параллельных обработчиков
PROCESSING_MAX_WORKERS=2

# Timeout для одной задачи (секунды)
PROCESSING_TIMEOUT_SECONDS=3600
```

#### Logging (логирование)
```env
# Уровень логирования
LOGGING_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Путь к файлу логов
LOGGING_FILE_PATH=./generator.log

# Логировать ли в файл и консоль
LOGGING_ENABLE_FILE_LOGGING=true
LOGGING_ENABLE_CONSOLE_LOGGING=true
```

### Рекомендованные конфигурации

#### Для быстрой обработки (средний ПК)
```env
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cuda
WHISPER_BEAM_SIZE=3
PROCESSING_MAX_WORKERS=2
```

#### Для максимальной точности (мощный GPU)
```env
WHISPER_MODEL_SIZE=large-v3
WHISPER_DEVICE=cuda
WHISPER_BEAM_SIZE=10
PROCESSING_MAX_WORKERS=1
```

#### Для CPU обработки
```env
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
PROCESSING_MAX_WORKERS=1
PROCESSING_TIMEOUT_SECONDS=7200      # 2 часа
```

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│           CLI / Web API                 │
│        (run.py / FastAPI)               │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│   InstructionProcessingService          │
│  (Главный сервис обработки)             │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────────────────┐
    │                             │
┌───▼────────────┐  ┌──────────────────────┐
│ AudioProcessor │  │  VideoProcessor      │
│ (✅ готов)     │  │  (🔲 планируется)    │
└───┬────────────┘  └──────────────────────┘
    │
    ├─ extract_audio()   (MoviePy)
    └─ transcribe()      (Whisper)

┌─────────────────────────────────────────┐
│        Конфигурация (AppConfig)         │
│  ├─ WhisperConfig                       │
│  ├─ VideoConfig                         │
│  ├─ AudioConfig                         │
│  ├─ ProcessingConfig                    │
│  └─ LoggingConfig                       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          Обработка ошибок               │
│  ProcessingError (базовый)              │
│  ├─ ValidationError                     │
│  ├─ AudioProcessingError                │
│  ├─ ConfigurationError                  │
│  └─ ModelLoadError                      │
└─────────────────────────────────────────┘
```

### Структура проекта

```
Video_Instruction_Generator/
├── src/
│   ├── __init__.py              # Экспорт публичного API
│   ├── config.py                # Конфигурационная система (Pydantic)
│   ├── exceptions.py            # Кастомные исключения
│   ├── main.py                  # CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── processor.py         # InstructionProcessingService
│   └── modules/
│       ├── __init__.py
│       ├── audio_processor.py   # AudioProcessor (Whisper + MoviePy)
│       ├── video_processor.py   # VideoProcessor (планируется)
│       └── llm_processor.py     # LLMProcessor (планируется)
├── run.py                       # Entry point
├── requirements.txt             # Python зависимости
├── .env.example                 # Пример конфигурации
├── .env                         # Конфигурация (не коммитить!)
├── examples.py                  # Примеры использования
├── tests.py                     # Unit-тесты
└── README.md                    # Этот файл
```

## 📚 API

### InstructionProcessingService

```python
from src import InstructionProcessingService, get_config, setup_logging

# Инициализация
service = InstructionProcessingService(
    model_size="base",      # tiny, base, small, medium, large-v3
    device="cuda",          # cuda или cpu
    use_config=True         # использовать .env конфиг
)

# Обработка видео
result = service.process_video(
    video_path="video.mp4",
    validate=True,          # проверить видеофайл
    cleanup=True            # удалить temps
)

# Результат
{
    'transcript': [
        {
            'start': 0.0,
            'end': 2.5,
            'text': 'Привет, это инструкция'
        },
        ...
    ],
    'language': 'ru',
    'confidence': 0.95,
    'video_file': 'video.mp4'
}
```

### AudioProcessor

```python
from src import AudioProcessor

processor = AudioProcessor(
    model_size="base",
    device="cuda",
    temp_dir="./temp",
    cleanup_temp=True,
    beam_size=5
)

# Валидация видео
processor.validate_video(
    "video.mp4",
    max_size_gb=10.0
)

# Извлечение аудио
audio_path = processor.extract_audio(
    video_path="video.mp4",
    output_path=None,       # используется temp dir если None
    validate=True
)

# Транскрипция
result = processor.transcribe(
    audio_path=audio_path,
    language=None,          # auto-detect если None
    return_language_info=True
)

# Очистка
processor.cleanup(audio_path)
```

### Конфигурация

```python
from src import get_config, setup_logging

# Получить конфиг
config = get_config()

# Доступ к параметрам
config.whisper.model_size
config.whisper.device
config.video.max_file_size_gb
config.processing.temp_dir
config.logging.level

# Инициализировать логирование
setup_logging(config)
```

## 🔍 Примеры

Смотрите файл `examples.py` для полных примеров:

```bash
python examples.py
```

### Пример 1: Базовая обработка

```python
from src import InstructionProcessingService, get_config, setup_logging

config = get_config()
setup_logging(config)

service = InstructionProcessingService(use_config=True)
result = service.process_video("video.mp4")

print(f"Язык: {result['language']}")
for segment in result['transcript']:
    print(f"[{segment['start']}s - {segment['end']}s] {segment['text']}")
```

### Пример 2: Обработка с кастомными параметрами

```python
service = InstructionProcessingService(
    model_size="large-v3",
    device="cuda"
)
result = service.process_video("video.mp4")
```

### Пример 3: Обработка с обработкой ошибок

```python
from src.exceptions import ValidationError, AudioProcessingError

try:
    result = service.process_video("video.mp4")
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
except AudioProcessingError as e:
    print(f"Ошибка обработки: {e}")
```

## ✅ Тестирование

### Установка pytest

```bash
pip install pytest pytest-cov
```

### Запуск тестов

```bash
# Все тесты
pytest tests.py -v

# Конкретный тест
pytest tests.py::TestAudioProcessorValidation -v

# С coverage
pytest tests.py --cov=src
```

## 🛠️ Troubleshooting

### ❌ "CUDA не доступна"
```
Решение: Переключитесь на CPU обработку
python run.py video.mp4 --device cpu

Или переустановите PyTorch с CUDA:
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### ❌ "Out of Memory" (GPU)
```
Решение: Используйте меньшую модель
python run.py video.mp4 --model base

Или используйте CPU:
python run.py video.mp4 --device cpu
```

### ❌ "Видеофайл не содержит аудиодорожку"
```
Решение: Проверьте что видео имеет аудиодорожку
ffmpeg -i video.mp4 -c:a aac -c:v copy video_with_audio.mp4
```

### ❌ "ModuleNotFoundError: No module named 'src'"
```
Решение: Убедитесь что запускаете из корневой директории проекта
cd Video_Instruction_Generator
python run.py video.mp4
```

### ❌ Медленная обработка
```
Решение: 
1. Используйте GPU: --device cuda
2. Уменьшите качество: --model base
3. Уменьшите beam_size в .env: WHISPER_BEAM_SIZE=3
```

## 📝 Развитие проекта

### PHASE 2: Реализация модулей (3-4 недели)
- [ ] VideoProcessor (извлечение кадров, нарезка)
- [ ] LLMProcessor (интеграция с LLM)
- [ ] Unit-тесты (pytest)
- [ ] Документация API

### PHASE 3: Backend (2-3 недели)
- [ ] FastAPI REST API
- [ ] Celery Job Queue
- [ ] WebSocket для progress tracking
- [ ] PostgreSQL для хранения

### PHASE 4: UI и Deployment (2-3 недели)
- [ ] Django/Flask + React/Vue (веб)
- [ ] Или PyQt (десктоп)
- [ ] Docker контейнеризация
- [ ] GitHub Actions CI/CD

## 📄 Лицензия

MIT License - смотрите LICENSE файл

## 👥 Контрибуция

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📞 Поддержка

Для вопросов и issues используйте GitHub Issues.

---

**Последнее обновление:** 24 апреля 2026 г.
