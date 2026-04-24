# src/core/processor.py

"""
Основной сервис для обработки видео и генерации инструкций.

Архитектура:
- Использует AudioProcessor для транскрипции
- Использует конфигурацию из AppConfig
- Обрабатывает ошибки и логирует процесс
- Управляет временными файлами
"""

import logging
from typing import Optional

from src.config import get_config
from src.exceptions import ProcessingError, ValidationError, AudioProcessingError
from src.modules import AudioProcessor

logger = logging.getLogger(__name__)


class InstructionProcessingService:
    """
    Сервис для обработки видео и генерации инструкций.
    
    Функциональность:
    - Валидация входных параметров
    - Обработка видео с использованием подключаемых модулей
    - Управление временными файлами
    - Логирование и обработка ошибок
    """
    
    def __init__(
            self, 
            model_size: Optional[str] = None,
            device: Optional[str] = None,
            compute_type: Optional[str] = None,
            use_config: bool = True
        ):
        """
        Инициализация сервиса.
        
        Args:
            model_size: Размер модели Whisper (переопределяет конфиг)
            device: GPU/CPU (переопределяет конфиг)
            compute_type: Тип вычислений (переопределяет конфиг)
            use_config: Использовать ли конфиг из AppConfig
            
        Raises:
            ConfigurationError: Если ошибка в конфигурации
        """
        self.config = get_config() if use_config else None
        
        # Использовать переданные параметры или конфиг
        if use_config and self.config:
            model_size = model_size or self.config.whisper.model_size
            device = device or self.config.whisper.device
            compute_type = compute_type or self.config.whisper.compute_type
            temp_dir = self.config.processing.temp_dir
            cleanup_temp = self.config.processing.cleanup_temp
            language = self.config.whisper.language or None
            beam_size = self.config.whisper.beam_size
        else:
            temp_dir = "./temp"
            cleanup_temp = True
            language = None
            beam_size = 5
        
        # Инициализация AudioProcessor
        self.audio_processor = AudioProcessor(
            model_size=model_size or "base",
            device=device or "cuda",
            compute_type=compute_type,
            temp_dir=temp_dir,
            cleanup_temp=cleanup_temp,
            language=language,
            beam_size=beam_size
        )
        
        logger.info("InstructionProcessingService инициализирован")

    def process_video(
        self, 
        video_path: str,
        validate: bool = True,
        cleanup: bool = True
    ) -> dict:
        """
        Основной метод для обработки видео и получения транскрипции.
        
        Args:
            video_path: Путь к видеофайлу
            validate: Валидировать ли видеофайл
            cleanup: Удалять ли временные файлы после обработки
            
        Returns:
            Словарь с результатами:
            {
                'transcript': [...],  # список сегментов
                'language': 'ru',
                'confidence': 0.95,
                'video_file': 'video.mp4'
            }
            
        Raises:
            ValidationError: Если видеофайл невалиден
            AudioProcessingError: Если ошибка при обработке аудио
            ProcessingError: Если общая ошибка обработки
        """
        audio_path = None
        try:
            logger.info(f"Начало обработки видео: {video_path}")
            
            # Валидация видеофайла
            if validate:
                max_size = self.config.video.max_file_size_gb if self.config else 4.0
                self.audio_processor.validate_video(video_path, max_size)
            
            # Извлечение аудио
            logger.info("Извлечение аудио...")
            audio_path = self.audio_processor.extract_audio(video_path, validate=False)
            
            # Транскрипция
            logger.info("Транскрипция аудио...")
            result = self.audio_processor.transcribe(audio_path)
            
            # Добавить информацию о видеофайле
            result['video_file'] = video_path
            
            logger.info("Обработка видео успешно завершена")
            return result
        
        except (ValidationError, AudioProcessingError) as e:
            logger.error(f"Ошибка обработки: {e}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке видео: {e}")
            raise ProcessingError(f"Ошибка при обработке видео: {e}") from e
        finally:
            # Очистка временных файлов
            if cleanup and audio_path:
                self.audio_processor.cleanup(audio_path)

    def get_status(self) -> dict:
        """Получить статус сервиса."""
        return {
            "model_size": self.audio_processor.model_size,
            "device": self.audio_processor.device,
            "compute_type": self.audio_processor.compute_type,
            "temp_dir": self.audio_processor.temp_dir
        }
