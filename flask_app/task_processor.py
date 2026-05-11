# flask_app/task_processor.py

import os
import logging
from src.config import AppConfig
from src.domain.repositories import ITaskRepository
from src.domain.exceptions import TaskNotFoundError, DatabaseError
from src.core.processor import InstructionProcessingService

logger = logging.getLogger(__name__)

class VideoInstructionProcessor():
    """
    Реализация обработчика для видео инструкций.
    """
    
    def __init__(self, task_repo: ITaskRepository, service: InstructionProcessingService):
        self.task_repo = task_repo
        self.service = service
    
    def process(self, task_id: str) -> None:
        """
        Обрабатывает видео и генерирует инструкцию.
        """
        task = None
        
        try:
            logger.info(f"[{task_id}] Начало обработки из очереди")
            
            # Поучаем объект задачи
            task = self.task_repo.get_by_id(task_id)
            # Выводим ошибку, если пусто
            if not task:
                raise TaskNotFoundError(f"Задача {task_id} не найдена в БД")
            
            # Пути к файлам
            request_temp_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
            video_path = os.path.join(request_temp_dir, task.video_filename)
            
            # Документы
            document_paths = None
            if task.document_names:
                document_paths = [
                    os.path.join(request_temp_dir, f"doc_{name}") 
                    for name in task.document_names
                ]
            
            # Отмечаем как обработка
            task.mark_processing()
            self.task_repo.update(task)
            
            # Обрабатываем видео
            result = self.service.generate_instruction(
                video_path, 
                documents=document_paths, 
                task_id=task_id
            )
            
            # Отмечаем как завершено
            task.mark_completed(result)
            self.task_repo.update(task)
            logger.info(f"[{task_id}] Обработка завершена успешно")
            
        except (TaskNotFoundError, DatabaseError) as e:
            logger.error(f"[{task_id}] Ошибка обработки: {str(e)}", exc_info=True)
            self._mark_failed(task_id, str(e))
        except Exception as e:
            logger.error(f"[{task_id}] Критическая ошибка: {str(e)}", exc_info=True)
            self._mark_failed(task_id, str(e))
    
    def _mark_failed(self, task_id: str, error_message: str):
        """Помечает задачу как ошибка"""
        try:
            task = self.task_repo.get_by_id(task_id)
            if task:
                task.mark_failed(error_message)
                self.task_repo.update(task)
                logger.info(f"[{task_id}] Статус обновлен на FAILED")
        except Exception as e:
            logger.critical(f"[{task_id}] Ошибка при обновлении статуса: {e}", exc_info=True)