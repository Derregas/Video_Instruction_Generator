# src/core/processor.py

import os
import logging
from typing import Optional
from ..config import AppConfig
from ..modules import AudioProcessor, LLMManager, DataManager, DocumentExtractor
from ..modules import video_analyzer

logger = logging.getLogger(__name__)

class InstructionProcessingService:
    """Сервис для обработки видео и генерации инструкций.""" 
    
    def __init__(self):
        # Инициализируем модули, используя настройки из единого AppConfig
        self.audio_processor = AudioProcessor(
            model_size=AppConfig.AUDIO.MODEL_SIZE, 
            device=AppConfig.AUDIO.DEVICE, 
            compute_type=AppConfig.AUDIO.COMPUTE_TYPE
        )
        
        self.llm_manager = LLMManager(
            model_name=AppConfig.LLM.MODEL,
            context_size=AppConfig.LLM.CONTEXT_SIZE,
            api_key=AppConfig.LLM.API_KEY
        )
        
        # Инструмент для отладки
        self.debug_manager = DataManager(
            temp_dir=AppConfig.TEMP_DIR, 
            data_file=AppConfig.LLM.LAST_DATA_FILE_NAME
        )

    def generate_instruction(self, video_path: str, documents: Optional[list[str]] = None) -> str:
        """Основной метод для обработки видео и получения транскрипции."""

        audio_path = None

        try:
            # 0. ПРОВЕРКА ОТЛАДКИ: Если включен режим USE_LAST_DATA, пропускаем обработку видео
            if AppConfig.LLM.USE_LAST_DATA:
                logger.info("--- [DEBUG] Загрузка данных из кэша ---")
                try:
                    cached_prompt = self.debug_manager.load_data()
                    return self.llm_manager.get_response(AppConfig.LLM.SYSTEM_PROMPT, cached_prompt)
                except FileNotFoundError:
                    logger.warning("Файл кэша не найден. Переходим к полной обработке видео.")

            # 1. ТРАНСКРИПЦИЯ
            logger.info("Шаг 1: Извлечение аудио и транскрипция...")
            # Временно сохраняем аудио в temp
            temp_audio = os.path.join(AppConfig.TEMP_DIR, "temp_audio.wav")
            audio_path = self.audio_processor.extract_audio(video_path, output_path=temp_audio)
            transcript = self.audio_processor.transcribe(audio_path)

            # 2. АНАЛИЗ СЦЕН
            logger.info("Шаг 2: Поиск смен планов (сцен)...")
            scenes = video_analyzer.get_video_scenes(video_path)

            # 3. СОПОСТАВЛЕНИЕ (ALIGNMENT)
            logger.info("Шаг 3: Связывание текста со сценами и извлечение кадров...")
            aligned_data = video_analyzer.align_data(transcript, scenes, video_path)

            if not aligned_data:
                raise ValueError("Не удалось сопоставить транскрипцию со сценами видео.")
            
            # Сохраняем результат сопоставления для будущей отладки
            prompt_data = self.llm_manager._format_prompt(aligned_data)
            self.debug_manager.save_data(prompt_data)

            # 4. Обработка документов
            if documents:
                logger.info("Шаг 4: Извлечение данных из документов...")
                extractor = DocumentExtractor(
                        strategy="hi_res", 
                        save_json=True, 
                        save_text=True, 
                        temp_dir=AppConfig.TEMP_DIR
                    )
                for doc_path in documents:
                    logger.info(f"Обработка документа: {doc_path}")
                    doc_data = extractor.extract_doc_data(doc_path)
                    prompt_data += f"\nДанные из документа {doc_path}:\n" + str(doc_data)

            with open(os.path.join(AppConfig.TEMP_DIR, "prompt_data.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_data)

            # 5. ГЕНЕРАЦИЯ LLM
            logger.info("Шаг 5: Генерация финальной инструкции...")
            instruction = self.llm_manager.get_response(
                system_message=AppConfig.LLM.SYSTEM_PROMPT,
                input_data=prompt_data
            )
            return instruction
        
        except Exception as e:
            logger.error(f"Критическая ошибка при генерации инструкции: {e}", exc_info=True)
            raise
        finally:
            # Очистка временных файлов (аудио)
            if audio_path:
                self._cleanup(audio_path)

    def _cleanup(self, file_path: str):
        """Удаление временных файлов."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Удален временный файл: {file_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
