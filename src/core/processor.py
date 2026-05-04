# src/core/processor.py

import os
import logging
import multiprocessing
import logging.handlers

from enum import Enum
from typing import Optional
from ..modules import video_analyzer
from ..config import AppConfig, setup_logging
from src.modules.audio_processor import AudioProcessor
from src.modules.extract_doc_data import DocumentExtractor
from src.modules.llm_processor import LLMManager, DataManager 

logger = logging.getLogger(__name__)

# Варианты сообщений в очереди
class TaskType(Enum):
    TRANSCRIPT = "video"
    DOCS = "docs"
    ERR_DOCS = "docs_error"
    ERR_TRANSCRIPT = "transcript_error"

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
    
    @staticmethod
    def _setup_worker_logging(log_queue: multiprocessing.Queue):
        handler = logging.handlers.QueueHandler(log_queue)
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.handlers = [handler]

    @staticmethod
    def _document_worker(q: multiprocessing.Queue, 
                         lq: multiprocessing.Queue, 
                         documents: list[str],
                         temp_dir: str
                        ):
        # Чтобы логи из подпроцесса передавались в файл логов
        InstructionProcessingService._setup_worker_logging(lq)
        logger = logging.getLogger(__name__)
        try:
            extractor = DocumentExtractor(
                strategy="hi_res", 
                save_json=True, 
                save_text=True, 
                temp_dir=temp_dir
            )
            all_docs = []
            for doc_path in documents:
                logger.info(f"Обработка документа: {doc_path}")
                doc_data = extractor.extract_doc_data(doc_path)
                all_docs.append((doc_path, doc_data))
            q.put((TaskType.DOCS, all_docs))

        except Exception as e:
            logger.error(f"Ошибка в процессе обработки документов: {e}")
            q.put((TaskType.ERR_DOCS, f"\nОшибка при обработке документов: {e}"))

    @staticmethod
    def _transcript_worker(q: multiprocessing.Queue, 
                           lq: multiprocessing.Queue, 
                           video_path: str, 
                           temp_dir: str, 
                           scenes: list
                           ):
        # Чтобы логи из подпроцесса передавались в файл логов
        InstructionProcessingService._setup_worker_logging(lq)
        logger = logging.getLogger(__name__)
        try:
            processor = AudioProcessor(
                model_size=AppConfig.AUDIO.MODEL_SIZE, 
                device=AppConfig.AUDIO.DEVICE, 
                compute_type=AppConfig.AUDIO.COMPUTE_TYPE
            )
            logger.info("Шаг 1: Извлечение аудио и транскрипция...")
            temp_audio = os.path.join(temp_dir, "temp_audio.wav")
            audio_path = processor.extract_audio(video_path, temp_audio)
            transcript = processor.transcribe(audio_path)
            logger.info("Шаг 2: Сопоставление транскрипции с видео...")
            aligned_data = video_analyzer.align_data(transcript, scenes, video_path)
            if not aligned_data:
                raise ValueError("Не удалось сопоставить транскрипцию со сценами видео.")
            q.put((TaskType.TRANSCRIPT, aligned_data))
        except Exception as e:
            logger.error(f"Ошибка в процессе транскрипции видео: {e}")
            q.put((TaskType.ERR_TRANSCRIPT, str(e)))

    def generate_instruction(self, video_path: str, 
                             documents: Optional[list[str]] = None, 
                             task_id: Optional[str]=None) -> str:
        """Основной метод для обработки видео и получения транскрипции."""

        processes = []
        audio_path = None
        documents_process = None
        transcript_process = None
        log_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()

        listener = logging.handlers.QueueListener(log_queue, *logging.getLogger().handlers)
        listener.start()

        try:
            # 0. ПРОВЕРКА ОТЛАДКИ: Если включен режим USE_LAST_DATA, пропускаем обработку видео
            if AppConfig.LLM.USE_LAST_DATA:
                logger.info("--- [DEBUG] Загрузка данных из кэша ---")
                try:
                    cached_prompt = self.debug_manager.load_data()
                    return self.llm_manager.get_response(AppConfig.LLM.SYSTEM_PROMPT, cached_prompt)
                except FileNotFoundError:
                    logger.warning("Файл кэша не найден. Переходим к полной обработке видео.")

            # 1. АНАЛИЗ СЦЕН
            logger.info("Поиск смен планов (сцен)...")
            scenes = video_analyzer.get_video_scenes(video_path)
            # Путь к папке задачи
            task_path = AppConfig.TEMP_DIR
            if task_id:
                task_path = os.path.join(AppConfig.TEMP_DIR, task_id)

            # ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА ДОКУМЕНТОВ
            if documents:
                logger.info("Запуск процессов для паралельной обработки документов...")
                documents_process = multiprocessing.Process(
                    target=self._document_worker,
                    args=(result_queue, log_queue, documents, task_path)
                )
                processes.append(documents_process)
                documents_process.start()

            # ТРАНСКРИПЦИЯ В ОТДЕЛЬНОМ ПОТОКЕ
            logger.info("Трансрипция в отдельном потоке")
            transcript_process = multiprocessing.Process(
                target=self._transcript_worker,
                args=(result_queue, log_queue, video_path, task_path, scenes)
            )
            processes.append(transcript_process)
            transcript_process.start()

            # ОЖИДАНИЕ ОЧЕРЕДИ
            results = {}
            logger.info("Ожидание данных из очереди...")
            try:
                for _ in processes:
                    key, value = result_queue.get(timeout=AppConfig.CHILD_TIME_OUT)
                    results[key] = value
                    logger.info(f"Получены данные из {key}")   
            except multiprocessing.Queue.empty:
                logger.error("Один из процессов завершён по таймауту")
                
            # ЗАВЕРШЕНИЕ ПРОЦЕССОВ
            logger.info("Ожидание звершения процессов...")
            for p in processes:
                p.join()
            logger.info("Все процессы завершены")

            aligned_data = results[TaskType.TRANSCRIPT]

            # Сохраняем результат сопоставления для будущей отладки
            prompt_data = self.llm_manager._format_prompt(aligned_data)
            self.debug_manager.save_data(prompt_data)

            for doc_path, doc_data in results[TaskType.DOCS]:
                logger.info(f"Документ {doc_path} обработан. Добавляем данные к промпту.")
                prompt_data += f"\n\n[Документ: {os.path.basename(doc_path)}]\n{doc_data}"

            """4. Обработка документов
            if documents_process:
                logger.info("Шаг 4: Ожидание завершения обработки документов...")
                try:
                    key, value = result_queue.get()
                    if key == "docs":
                        for doc_path, doc_data in value:
                            logger.info(f"Документ {doc_path} обработан. Добавляем данные к промпту.")
                            prompt_data += f"\n\n[Документ: {os.path.basename(doc_path)}]\n{doc_data}"
                    elif key == "docs_error":
                        logger.error(f"Ошибка из воркера документов: {value}")
                        prompt_data += f"\n\n[Ошибка обработки документов]: {value}"
                except Exception as e:
                    logger.error(f"Ошибка при получении данных из очереди: {e}")
                documents_process.join()
            TODO: Добавить таймаут на join и get, а также обработку зависания """
            # Сохранения сообщения для LLM в отдельный файл для отладки
            with open(os.path.join(task_path, "prompt_data.txt"), "w", encoding="utf-8") as f:
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
            listener.stop()
            if documents_process and documents_process.is_alive():
                documents_process.terminate()
                logger.warning("Процесс обработки документов был принудительно завершен.")
            if transcript_process and transcript_process.is_alive():
                transcript_process.terminate()
                logger.warning("Процесс обработки видео был принудительно завершен.")
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
