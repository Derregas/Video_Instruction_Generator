# Архитектура Video Instruction Generator

## 📐 Обзор архитектуры

### Принципы проектирования

1. **Модульность** - каждый компонент отвечает за одно
2. **Слабая связанность** - компоненты независимы друг от друга
3. **Конфигурируемость** - настройка через .env и код
4. **Обработка ошибок** - явная обработка исключений
5. **Логирование** - все события логируются
6. **Типизация** - использование type hints для самодокументирования

### Слои приложения

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                     │
│  CLI (run.py) | Web API (FastAPI) | UI (React/PyQt)    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Business Logic Layer                        │
│        InstructionProcessingService                      │
│  (Координирование различных модулей)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│            Processing Modules Layer                      │
│  ├─ AudioProcessor (Whisper)                            │
│  ├─ VideoProcessor (MoviePy)                            │
│  └─ LLMProcessor (GPT / Open Source)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│          Configuration & Support Layer                   │
│  ├─ AppConfig (Pydantic)                                │
│  ├─ Logging System                                      │
│  ├─ Exception Handling                                  │
│  └─ Temporary File Management                           │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Flow обработки

```
User Input (CLI / Web)
    │
    ▼
Argument Parsing & Validation
    │
    ▼
Load Configuration (.env)
    │
    ▼
Initialize Service
    │
    ▼
Process Video
    ├─ 1. Validate Input (format, size, accessibility)
    ├─ 2. Extract Audio (MoviePy)
    ├─ 3. Transcribe (Whisper)
    ├─ 4. Process Video (VideoProcessor) [TBD]
    ├─ 5. Generate Instructions (LLMProcessor) [TBD]
    └─ 6. Cleanup Temp Files
    │
    ▼
Return Results
    │
    ▼
Output (Console / JSON / Web)
```

## 📦 Компоненты

### 1. Configuration System (src/config.py)

**Назначение:** Централизованное управление конфигурацией

**Компоненты:**
```
AppConfig (главный класс)
├── WhisperConfig (параметры Whisper)
├── VideoConfig (параметры видео)
├── AudioConfig (параметры аудио)
├── ProcessingConfig (управление обработкой)
└── LoggingConfig (логирование)
```

**Особенности:**
- Валидация через Pydantic
- Загрузка из .env файлов
- Поддержка переменных окружения
- Singleton pattern для глобального доступа

**Использование:**
```python
config = get_config()  # получить сингл config
setup_logging(config)  # инициализировать логирование
```

### 2. Exception Handling (src/exceptions.py)

**Назначение:** Структурированная обработка ошибок

**Иерархия:**
```
ProcessingError (базовый класс)
├── ConfigurationError (проблемы с конфиг)
├── ValidationError (неверный input)
├── AudioProcessingError (ошибки Whisper/MoviePy)
├── VideoProcessingError (ошибки обработки видео)
├── ModelLoadError (ошибки загрузки моделей)
└── TemporaryFileError (проблемы с temps)
```

**Преимущества:**
- Точная обработка разных типов ошибок
- Легко логировать и отлаживать
- Хорошо читается в кода

**Использование:**
```python
try:
    service.process_video("video.mp4")
except ValidationError as e:
    logger.error(f"Ошибка входных данных: {e}")
except AudioProcessingError as e:
    logger.error(f"Ошибка обработки аудио: {e}")
```

### 3. AudioProcessor (src/modules/audio_processor.py)

**Назначение:** Обработка аудио (извлечение + транскрипция)

**Методы:**
```python
class AudioProcessor:
    def validate_video(video_path, max_size_gb)
        # Валидация видеофайла перед обработкой
    
    def extract_audio(video_path, output_path=None)
        # Извлечение аудио в безопасный temp dir
    
    def transcribe(audio_path, language=None)
        # Транскрипция аудио в текст с временем
    
    def cleanup(file_path)
        # Удаление временного файла
```

**Особенности:**
- Использует MoviePy для извлечения аудио
- Использует Whisper для транскрипции
- Поддержка GPU/CPU
- Безопасная работа с временными файлами
- Полная обработка ошибок

**Пример:**
```python
processor = AudioProcessor(
    model_size="base",
    device="cuda",
    temp_dir="./temp",
    cleanup_temp=True
)

audio_path = processor.extract_audio("video.mp4")
result = processor.transcribe(audio_path)
processor.cleanup(audio_path)
```

### 4. InstructionProcessingService (src/core/processor.py)

**Назначение:** Главный сервис, координирует обработку

**Методы:**
```python
class InstructionProcessingService:
    def __init__(model_size, device, use_config)
        # Инициализация со значениями из конфига
    
    def process_video(video_path, validate, cleanup)
        # Главный метод обработки видео
    
    def get_status()
        # Получить статус сервиса
```

**Особенности:**
- Использует конфиг для параметров
- Координирует разные модули
- Управляет временными файлами
- Обработка ошибок и логирование

**Пример:**
```python
service = InstructionProcessingService(use_config=True)
result = service.process_video("video.mp4")

print(result['language'])
print(f"Сегментов: {len(result['transcript'])}")
```

## 🔮 Будущие компоненты

### VideoProcessor (планируется)

```python
class VideoProcessor:
    """Обработка видео контента"""
    
    def extract_frames(video_path, fps=None):
        """Извлечение кадров с заданной частотой"""
        # Использовать OpenCV или MoviePy
        # Возвращать список PIL Image объектов
    
    def cut_video(video_path, segments):
        """Нарезка видео по временным меткам"""
        # Использовать MoviePy для нарезки
        # segments: [(start, end), ...]
    
    def synchronize_with_transcript(video_path, transcript):
        """Синхронизация видео с транскрипцией"""
        # Создать видео с субтитрами
        # Или разбить на сегменты по речи
    
    def extract_metadata(video_path):
        """Извлечение метаданных видео"""
        # Разрешение, fps, длительность, кодеки
```

**Интеграция с AudioProcessor:**
```
video.mp4
    ├─ AudioProcessor.extract_audio() -> audio.wav
    │   ├─ AudioProcessor.transcribe() -> transcript
    │   │   └─ synchronize_with_transcript() -> [segments]
    │   └─ cleanup(audio.wav)
    │
    └─ VideoProcessor.extract_frames() -> [frames]
        ├─ VideoProcessor.cut_video() -> [video_clips]
        └─ combine_with_transcript()
```

### LLMProcessor (планируется)

```python
class LLMProcessor:
    """Генерация инструкций через LLM"""
    
    def __init__(llm_provider, model, api_key):
        # Поддержка разных провайдеров:
        # - OpenAI (GPT-3.5, GPT-4)
        # - HuggingFace (Llama 2, Mistral)
        # - Локальные модели (ollama)
    
    def generate_instructions(transcript):
        """Генерация структурированных инструкций"""
        # Input: список сегментов с текстом и временем
        # Output: структурированные инструкции в JSON/Markdown
    
    def format_output(instructions, format='json'):
        """Форматирование результата"""
        # json, markdown, html, docx
    
    def validate_quality(instructions):
        """Проверка качества сгенерированного текста"""
        # Проверка полноты, связности, формальности
```

**Интеграция:**
```
InstructionProcessingService
    ├─ AudioProcessor.process_video()
    │   └─ transcript: [{"start": 0, "end": 2.5, "text": "..."}]
    │
    └─ LLMProcessor.generate_instructions(transcript)
        └─ instructions: {"title": "...", "steps": [...]}
```

## 🔌 Расширяемость

### Добавление нового модуля

**1. Создать файл модуля:**
```python
# src/modules/my_processor.py

from src.exceptions import ProcessingError
import logging

logger = logging.getLogger(__name__)

class MyProcessor:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
        logger.info("MyProcessor инициализирован")
    
    def process(self, data):
        try:
            # Обработка данных
            return result
        except Exception as e:
            logger.error(f"Ошибка в MyProcessor: {e}")
            raise ProcessingError(f"Ошибка обработки: {e}") from e
```

**2. Экспортировать из modules/__init__.py:**
```python
from .my_processor import MyProcessor
__all__ = ["MyProcessor"]
```

**3. Интегрировать в InstructionProcessingService:**
```python
class InstructionProcessingService:
    def __init__(self, use_config=True):
        # ... существующий код ...
        self.my_processor = MyProcessor(
            param1=config.my_setting.param1,
            param2=config.my_setting.param2
        )
    
    def process_video(self, video_path):
        # ... существующий код ...
        result = self.my_processor.process(data)
        return result
```

**4. Добавить конфиг:**
```python
# src/config.py

class MyConfig(BaseSettings):
    param1: str = Field(default="value")
    param2: int = Field(default=10, gt=0)
    
    class Config:
        env_prefix = "MY_"
        case_sensitive = False

class AppConfig(BaseSettings):
    my_setting: MyConfig = Field(default_factory=MyConfig)
```

## 💾 Управление состоянием

### Временные файлы

```
Project Root
├── temp/                    # Временная директория
│   ├── audio_xxxxxx.wav    # Временное аудио
│   ├── frame_000001.jpg    # Извлеченные кадры
│   └── ...
└── generator.log           # Логи
```

**Безопасность:**
- Использование `tempfile.NamedTemporaryFile`
- Автоматическое удаление при cleanup=True
- Перезапись при конфликтах имен

### Логирование

```python
# 3 уровня логирования:

# 1. File logging (всегда)
generator.log

# 2. Console logging (если enable_console_logging=true)
stdout / stderr

# 3. Структурированное логирование (будущее)
JSON в БД для аналитики
```

## 🚀 Производительность

### Оптимизации

1. **Ленивая загрузка моделей**
   - Модель Whisper загружается только при первом use
   - Экономит память и время инициализации

2. **GPU поддержка**
   - Использование CUDA для ускорения
   - Квантизация моделей (int8) для меньшей памяти

3. **Параллелизм (будущее)**
   - Обработка нескольких видео одновременно
   - Использование Celery для async tasks

### Бенчмарки

```
Модель base на GPU (CUDA):     ~2x скорость видео
Модель base на CPU:            ~0.5x скорость видео
Модель large-v3 на GPU:        ~1x скорость видео
Модель large-v3 на CPU:        ~0.1x скорость видео

Пример: 1 часовое видео
- GPU (base): ~30 минут
- CPU (base): ~2 часа
- GPU (large-v3): ~1 час
- CPU (large-v3): ~10 часов
```

## 🔐 Безопасность

### Валидация входных данных

```python
# 1. Проверка пути
if not Path(video_path).exists():
    raise ValidationError("Видеофайл не найден")

# 2. Проверка формата
if path.suffix.lower() not in valid_extensions:
    raise ValidationError("Неподдерживаемый формат")

# 3. Проверка размера
if file_size_gb > max_size_gb:
    raise ValidationError("Файл слишком большой")
```

### Обработка исключений

```python
try:
    # опасная операция
    process_video(path)
except ProcessingError as e:
    # Явная обработка
    logger.error(f"Ошибка: {e}")
    cleanup()  # гарантированная очистка
    raise
finally:
    # cleanup всегда выполнится
    cleanup_temps()
```

## 📊 Мониторинг (будущее)

### Метрики для отслеживания

- Время обработки (по этапам)
- Использование памяти (GPU/CPU)
- Точность транскрипции
- Количество ошибок
- Success rate

### Logging в БД

```python
# Сохранять каждый run в БД:
{
    'timestamp': '2026-04-24 10:30:00',
    'video_file': 'video.mp4',
    'file_size': '500MB',
    'duration': '1:30:00',
    'model_used': 'base',
    'device': 'cuda',
    'processing_time': '1800s',
    'language': 'ru',
    'confidence': 0.95,
    'status': 'success',
    'error': null
}
```

## ✅ Чек-лист для новых разработчиков

- [ ] Прочитать README.md
- [ ] Прочитать ARCHITECTURE.md (этот файл)
- [ ] Установить зависимости
- [ ] Запустить примеры (examples.py)
- [ ] Запустить тесты (pytest)
- [ ] Читать комментарии в коде (особенно в exceptions.py и config.py)
- [ ] Использовать IDE с type checking (PyCharm, VS Code + Pylance)

---

**Последнее обновление:** 24 апреля 2026 г.
