"""
Custom exceptions для приложения Video Instruction Generator.

Иерархия исключений:
ProcessingError (базовое)
├── VideoProcessingError
├── AudioProcessingError
├── ConfigurationError
└── ValidationError
"""


class ProcessingError(Exception):
    """Базовое исключение для всех ошибок обработки."""
    pass


class ConfigurationError(ProcessingError):
    """Ошибка конфигурации (неверные параметры, отсутствие .env файла и т.д.)"""
    pass


class ValidationError(ProcessingError):
    """Ошибка валидации входных данных."""
    pass


class VideoProcessingError(ProcessingError):
    """Ошибка при обработке видео."""
    pass


class AudioProcessingError(ProcessingError):
    """Ошибка при обработке аудио."""
    pass


class ModelLoadError(ProcessingError):
    """Ошибка при загрузке модели (Whisper, LLM и т.д.)"""
    pass


class TemporaryFileError(ProcessingError):
    """Ошибка при работе с временными файлами."""
    pass
