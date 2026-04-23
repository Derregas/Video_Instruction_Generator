# src/core/processor.py

import os
from typing import Optional
from ..modules import AudioProcessor

class InstructionProcessingService:
    """Сервис для обработки видео и генерации инструкций.""" 
    
    def __init__(
            self, 
            model_size: str = "base",
            device: Optional[str] = None,
            compute_type: Optional[str] = None
        ):
        self.audio_processor = AudioProcessor(
            model_size=model_size, 
            device=device, 
            compute_type=compute_type
            )

    def process_video(self, video_path: str) -> Optional[list]:
        """Основной метод для обработки видео и получения транскрипции."""

        audio_path = self.audio_processor.extract_audio(video_path)
        transcript = self.audio_processor.transcribe(audio_path)

        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

        return transcript
