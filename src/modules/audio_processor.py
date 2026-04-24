# src/modules/audio_processor.py

"""
Модуль для обработки аудио из видеофайлов.

Функциональность:
- Извлечение аудио из видео
- Транскрипция речи с использованием Whisper
- Поддержка GPU и CPU
- Автоматическое определение языка
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Literal
from moviepy import VideoFileClip
from faster_whisper import WhisperModel

from src.exceptions import AudioProcessingError, ModelLoadError, ValidationError

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Класс для обработки аудио из видеофайлов.
    
    Функциональность:
    - Валидация видеофайлов
    - Извлечение аудио с обработкой ошибок
    - Безопасная работа с временными файлами
    - Транскрипция с поддержкой GPU/CPU
    """

    def __init__(
            self, 
            model_size: str = "base", 
            device: Optional[str] = None, 
            compute_type: Optional[str] = None,
            temp_dir: Optional[str] = None,
            cleanup_temp: bool = True,
            language: Optional[str] = None,
            beam_size: int = 5
        ):
        """
        Инициализация процессора и загрузка модели Whisper.
        
        Args:
            model_size: Размер модели (tiny, base, small, medium, large-v3)
            device: "cuda" или "cpu". Если None, определится автоматически.
            compute_type: Тип вычислений (float16 для GPU, int8 для CPU).
            temp_dir: Директория для временных файлов
            cleanup_temp: Удалять ли временные файлы после обработки
            language: Язык транскрипции (iso-639-1 код, например 'en', 'ru')
            beam_size: Размер beam для транскрипции (больше = точнее)
            
        Raises:
            ConfigurationError: Если конфигурация невалидна
        """
        self.model_size = model_size
        self.device, self.compute_type = self._setup_device(device, compute_type)
        self.temp_dir = temp_dir or "./temp"
        self.cleanup_temp = cleanup_temp
        self.language = language
        self.beam_size = beam_size
        
        # Создать директорию для временных файлов
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        self._model = None
        logger.info(
            f"AudioProcessor инициализирован: "
            f"model={model_size}, device={self.device}, compute_type={self.compute_type}"
        )

    @property
    def model(self):
        """Геттер для модели, чтобы обеспечить ленивую загрузку."""
        if self._model is None:
            try:
                logger.info(f"Загрузка Whisper модели '{self.model_size}' на {self.device}...")
                self._model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                logger.info("Модель Whisper успешно загружена")
            except Exception as e:
                logger.error(f"Ошибка при загрузке модели Whisper: {e}")
                raise ModelLoadError(f"Не удалось загрузить модель Whisper: {e}") from e
        return self._model

    @staticmethod
    def _setup_device(device: Optional[str], compute_type: Optional[str]) -> tuple[str, str]:
        """
        Внутренний метод для настройки устройства (GPU/CPU).
        
        Args:
            device: Переопределение device (cuda/cpu)
            compute_type: Переопределение compute_type
            
        Returns:
            Кортеж (device, compute_type)
        """
        if device is None:
            device = "cuda" if os.environ.get("USE_GPU") == "1" else "cpu"
        
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"
            
        return device, compute_type

    def validate_video(self, video_path: str, max_size_gb: float = 4.0) -> None:
        """
        Валидирует видеофайл перед обработкой.
        
        Args:
            video_path: Путь к видеофайлу
            max_size_gb: Максимальный размер файла в ГБ
            
        Raises:
            ValidationError: Если видеофайл невалиден
        """
        path = Path(video_path)
        
        # Проверка существования файла
        if not path.exists():
            raise ValidationError(f"Видеофайл не найден: {video_path}")
        
        # Проверка, что это файл
        if not path.is_file():
            raise ValidationError(f"Путь не является файлом: {video_path}")
        
        # Проверка расширения
        valid_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
        if path.suffix.lower() not in valid_extensions:
            raise ValidationError(
                f"Неподдерживаемый формат видео: {path.suffix}. "
                f"Поддерживаемые: {', '.join(valid_extensions)}"
            )
        
        # Проверка размера файла
        file_size_gb = path.stat().st_size / (1024 ** 3)
        if file_size_gb > max_size_gb:
            raise ValidationError(
                f"Размер файла ({file_size_gb:.1f} ГБ) превышает лимит ({max_size_gb} ГБ)"
            )
        
        logger.info(f"Видеофайл прошёл валидацию: {path.name} ({file_size_gb:.1f} ГБ)")
    
    def extract_audio(
        self, 
        video_path: str, 
        output_path: Optional[str] = None,
        validate: bool = True
    ) -> str:
        """
        Извлекает аудиодорожку из видеофайла в безопасную временную директорию.
        
        Args:
            video_path: Путь к видеофайлу
            output_path: Путь для сохранения аудио (если None, используется temp директория)
            validate: Валидировать ли видеофайл перед обработкой
            
        Returns:
            Путь к файлу аудио
            
        Raises:
            ValidationError: Если видеофайл невалиден
            AudioProcessingError: Если ошибка при извлечении аудио
        """
        try:
            # Валидация видеофайла
            if validate:
                self.validate_video(video_path)
            
            # Использовать временный файл если output_path не указан
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    dir=self.temp_dir,
                    delete=False
                )
                output_path = temp_file.name
                temp_file.close()
                logger.debug(f"Создан временный файл: {output_path}")
            
            logger.info(f"Извлечение аудио из {Path(video_path).name}...")
            with VideoFileClip(video_path) as video:
                if video.audio is None:
                    raise AudioProcessingError("Видеофайл не содержит аудиодорожку")
                
                # Из-за особенностей MoviePy, подавляем verbose logging
                video.audio.write_audiofile(output_path, verbose=False, logger=None)
            
            logger.info(f"Аудио успешно извлечено: {output_path}")
            return output_path
            
        except ValidationError:
            raise
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при извлечении аудио: {e}")
            raise AudioProcessingError(f"Не удалось извлечь аудио: {e}") from e

    def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None,
        return_language_info: bool = True
    ) -> dict:
        """
        Транскрибирует аудиофайл в текст с временными метками.
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Язык транскрипции (переопределяет настройку класса)
            return_language_info: Включать ли информацию о языке в результат
            
        Returns:
            Словарь с ключами:
                - 'transcript': список сегментов
                - 'language': определённый язык
                - 'confidence': уверенность определения языка
                
        Raises:
            FileNotFoundError: Если аудиофайл не найден
            AudioProcessingError: Если ошибка при транскрипции
        """
        try:
            # Проверка существования файла
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")
            
            # Использовать переданный язык или язык класса
            lang = language or self.language
            logger.info(
                f"Транскрипция аудио (язык: {lang or 'auto-detect'}, "
                f"beam_size: {self.beam_size})..."
            )
            
            # Транскрипция
            segments, info = self.model.transcribe(
                audio_path,
                language=lang,
                beam_size=self.beam_size
            )
            
            logger.info(
                f"Язык определён как {info.language} "
                f"(уверенность: {info.language_probability:.2%})"
            )

            # Формирование результатов
            transcript_data = []
            for segment in segments:
                chunk = {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip()
                }
                transcript_data.append(chunk)
            
            result = {
                "transcript": transcript_data,
                "language": info.language,
                "confidence": float(info.language_probability)
            }
            
            logger.info(f"Транскрипция завершена: {len(transcript_data)} сегментов")
            return result
        
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при транскрипции аудио: {e}")
            raise AudioProcessingError(f"Не удалось транскрибировать аудио: {e}") from e

    def cleanup(self, file_path: str) -> None:
        """
        Удаляет временный файл.
        
        Args:
            file_path: Путь к файлу для удаления
        """
        try:
            if self.cleanup_temp and Path(file_path).exists():
                Path(file_path).unlink()
                logger.debug(f"Удалён временный файл: {file_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")