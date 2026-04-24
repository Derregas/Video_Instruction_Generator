# src/config.py
"""
Конфигурационная система для приложения.

Использует Pydantic Settings для валидации и загрузки переменных окружения.
Поддерживает .env файлы и переменные окружения.

Использование:
    config = AppConfig()  # Автоматически загружает из .env и окружения
    print(config.whisper_device)  # Доступ к параметрам
"""

import logging
from pathlib import Path
from typing import Optional, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from src.exceptions import ConfigurationError

# Корневая директория проекта
PROJECT_ROOT = Path(__file__).parent.parent


class WhisperConfig(BaseSettings):
    """Конфигурация для модели Whisper."""

    model_size: Literal["tiny", "base", "small", "medium", "large-v3"] = Field(
        default="base",
        description="Размер модели Whisper (tiny - маленькая/быстрая, large-v3 - большая/точная)"
    )
    device: Literal["cuda", "cpu"] = Field(
        default="cuda",
        description="Устройство для вычислений (cuda для GPU, cpu для CPU)"
    )
    compute_type: Optional[Literal["float16", "float32", "int8", "int8_float32"]] = Field(
        default=None,
        description="Тип вычислений (float16 для GPU, int8 для CPU)"
    )
    beam_size: int = Field(
        default=5,
        ge=1, le=100,
        description="Размер beam для транскрипции (больше = точнее но медленнее)"
    )
    language: Optional[str] = Field(
        default=None,
        description="Язык для транскрипции (iso-639-1 код, например 'en', 'ru'). None = auto-detect"
    )

    class Config:
        env_prefix = "WHISPER_"
        case_sensitive = False

    @field_validator("device")
    @classmethod
    def validate_device(cls, v):
        """Проверка доступности устройства."""
        if v == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    raise ConfigurationError(
                        "CUDA не доступна. Используйте device='cpu' или установите PyTorch с CUDA поддержкой."
                    )
            except ImportError:
                raise ConfigurationError("PyTorch не установлен")
        return v

    @field_validator("compute_type", mode="before")
    @classmethod
    def set_compute_type(cls, v, info):
        """Автоматически устанавливает compute_type на основе device."""
        if v is None:
            device = info.data.get("device", "cuda")
            return "float16" if device == "cuda" else "int8"
        return v


class VideoConfig(BaseSettings):
    """Конфигурация для обработки видео."""

    supported_formats: list[str] = Field(
        default=["mp4", "avi", "mov", "mkv", "flv", "wmv"],
        description="Поддерживаемые форматы видео"
    )
    max_file_size_gb: float = Field(
        default=4.0,
        gt=0,
        description="Максимальный размер видео в ГБ"
    )
    extract_fps: Optional[int] = Field(
        default=None,
        description="FPS для извлечения кадров (None = все кадры)"
    )

    class Config:
        env_prefix = "VIDEO_"
        case_sensitive = False


class AudioConfig(BaseSettings):
    """Конфигурация для обработки аудио."""

    sample_rate: int = Field(
        default=16000,
        gt=0,
        description="Частота дискретизации аудио в Гц"
    )
    channels: int = Field(
        default=1,
        ge=1, le=2,
        description="Количество каналов (1=моно, 2=стерео)"
    )

    class Config:
        env_prefix = "AUDIO_"
        case_sensitive = False


class ProcessingConfig(BaseSettings):
    """Конфигурация для обработки и временных файлов."""

    temp_dir: str = Field(
        default=str(PROJECT_ROOT / "temp"),
        description="Директория для временных файлов"
    )
    cleanup_temp: bool = Field(
        default=True,
        description="Удалять ли временные файлы после обработки"
    )
    max_workers: int = Field(
        default=2,
        ge=1, le=16,
        description="Максимальное количество параллельных обработчиков"
    )
    timeout_seconds: int = Field(
        default=3600,
        gt=0,
        description="Timeout для одной задачи обработки в секундах"
    )

    class Config:
        env_prefix = "PROCESSING_"
        case_sensitive = False

    def model_post_init(self, __context):
        """Создать директорию для временных файлов если её нет."""
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)


class LoggingConfig(BaseSettings):
    """Конфигурация для логирования."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Уровень логирования"
    )
    file_path: str = Field(
        default=str(PROJECT_ROOT / "generator.log"),
        description="Путь к файлу логов"
    )
    format: str = Field(
        default="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
        description="Формат логирования"
    )
    enable_file_logging: bool = Field(
        default=True,
        description="Логировать ли в файл"
    )
    enable_console_logging: bool = Field(
        default=True,
        description="Логировать ли в консоль"
    )

    class Config:
        env_prefix = "LOGGING_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """
    Главная конфигурация приложения.
    
    Загружает все переменные из .env файла и окружения.
    
    Использование:
        config = AppConfig()
        config.whisper.model_size
        config.video.max_file_size_gb
    """

    # Компоненты конфигурации
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Флаги приложения
    debug: bool = Field(
        default=False,
        description="Режим debug"
    )
    env_file: Optional[str] = Field(
        default=".env",
        description="Путь к .env файлу"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Поддержка загрузки вложенных конфигов
        nested_delimiter = "__"

    def get_logger(self, name: str):
        """Получить настроенный logger для модуля."""
        logger = logging.getLogger(name)
        return logger

    def __str__(self) -> str:
        """Красивый вывод конфигурации (скрывает чувствительные данные)."""
        return (
            f"AppConfig(\n"
            f"  whisper_device={self.whisper.device},\n"
            f"  whisper_model={self.whisper.model_size},\n"
            f"  video_max_size={self.video.max_file_size_gb}GB,\n"
            f"  processing_temp_dir={self.processing.temp_dir},\n"
            f"  debug={self.debug}\n"
            f")"
        )


def setup_logging(config: AppConfig) -> None:
    """
    Настройка логирования на основе конфигурации.
    
    Args:
        config: AppConfig объект с параметрами логирования
    """
    handlers = []
    formatter = logging.Formatter(config.logging.format)

    # File handler
    if config.logging.enable_file_logging:
        file_handler = logging.FileHandler(
            config.logging.file_path,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Console handler
    if config.logging.enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level))
    
    for handler in handlers:
        root_logger.addHandler(handler)


# Глобальный объект конфигурации (ленивая инициализация)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Получить глобальный объект конфигурации (singleton)."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Перезагрузить конфигурацию (для тестов)."""
    global _config
    _config = AppConfig()
    return _config