# src/modules/audio_processor.py

import os
import logging
from typing import Optional
from moviepy import VideoFileClip
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Класс для обработки аудио из видеофайлов"""

    def __init__(
            self, 
            model_size: str = "base", 
            device: Optional[str] = None, 
            compute_type: Optional[str] = None
        ):
        """
        Инициализация процессора и загрузка модели Whisper.
        
        :param model_size: Размер модели (tiny, base, small, medium, large-v3)
        :param device: "cuda" или "cpu". Если None, определится автоматически.
        :param compute_type: Тип вычислений (float16 для GPU, int8 для CPU).
        """
        self.model_size = model_size
        self.device, self.compute_type = self._setup_device(device, compute_type)

        self._model = None

    @property
    def model(self):
        """Геттер для модели, чтобы обеспечить ленивую загрузку."""
        if self._model is None:
            logger.info(f"Загрузка Whisper модели '{self.model_size}' на {self.device}...")
            self._model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
        return self._model

    def _setup_device(self, device, compute_type):
        """Внутренний метод для настройки устройства (GPU/CPU)."""
        if device is None:
            device = "cuda" if os.environ.get("USE_GPU") == "1" else "cpu"
        
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"
            
        return device, compute_type
    
    def extract_audio(self, video_path: str, output_path: str = "temp_audio.wav") -> str:
        """
        Извлекает аудиодорожку из видеофайла.
        """
        try:
            logger.info(f"Извлечение аудио из {video_path}...")
            with VideoFileClip(video_path) as video:
                video.audio.write_audiofile(output_path, logger=None) # type: ignore
            return output_path
        except Exception as e:
            logger.error(f"Ошибка при извлечении аудио: {e}")
            raise

    def transcribe(self, audio_path: str):
        """
        Транскрибирует аудиофайл в текст с временными метками.
        """
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            logger.info(f"Язык определён как {info.language} ({info.language_probability:.2f})")

            transcript_data = []
            for segment in segments:
                chunk = {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip()
                }
                transcript_data.append(chunk)
            return transcript_data
        
        except Exception as e:
            logger.error(f"Ошибка при транскрипции аудио: {e}")
            raise

        return transcript_data