# flask_app/task_processor.py

import os
import logging
import json
from src.config import AppConfig
from abc import ABC, abstractmethod
from src.domain.repositories import ITaskRepository
from src.domain.exceptions import TaskNotFoundError, DatabaseError
from src.core.processor import InstructionProcessingService
from src.services.instruction_result_service import InstructionResultService
from src.services.file_management_service import FileManagementService
from src.modules.response_schema import Instruction as InstructionSchema

logger = logging.getLogger(__name__)

class ITaskProcessor(ABC):
    """
    Интерфейс для обработки задач.
    Любой обработчик должен реализовать этот интерфейс.
    """
    
    @abstractmethod
    def process(self, task_id: str) -> None:
        """
        Обрабатывает задачу по ID.
        
        Args:
            task_id: Идентификатор задачи
        
        Raises:
            TaskNotFoundError: Если задача не найдена
        """
        pass

class VideoInstructionProcessor(ITaskProcessor):
    """
    Реализация обработчика для видео инструкций.
    """
    
    def __init__(self, task_repo: ITaskRepository, service: InstructionProcessingService, result_service: InstructionResultService):
        self.task_repo = task_repo
        self.service = service
        self.result_service = result_service
    
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
                    os.path.join(request_temp_dir, f"{name}") 
                    for name in task.document_names
                ]
            
            # Отмечаем как обработка
            task.mark_processing()
            self.task_repo.update(task)
            
            # Обрабатываем видео
            result_json_str = self.service.generate_instruction(
                video_path, 
                documents=document_paths, 
                task_id=task_id
            )
            
            # ПАРСИНГ И СОХРАНЕНИЕ В НОВЫЕ ТАБЛИЦЫ
            used_image_ids = []
            try:
                # Парсим JSON строку в Pydantic модель
                parsed_result = InstructionSchema.model_validate_json(result_json_str)
                
                # 1. Создаем основную инструкцию
                instruction = self.result_service.create_instruction(
                    task_id=task_id,
                    title=parsed_result.name,
                    description=parsed_result.description
                )
                
                # 2. Сохраняем ключевые слова
                self.result_service.set_keywords(
                    instruction_id=instruction.id,
                    keywords_list=parsed_result.key_words
                )
                
                # 3. Сохраняем шаги и собираем ID используемых картинок
                for i, step_data in enumerate(parsed_result.steps, 1):
                    self.result_service.add_instruction_step(
                        instruction_id=instruction.id,
                        step_order=i,
                        title=step_data.title,
                        text=step_data.description,
                        time_start=step_data.start_time,
                        time_end=step_data.end_time,
                        image_id=step_data.best_image_id
                    )
                    # Собираем ID используемых картинок
                    if step_data.best_image_id:
                        used_image_ids.append(step_data.best_image_id)
                
                logger.info(f"[{task_id}] Структурированные данные сохранены в requirements.db")
                
            except Exception as parse_err:
                logger.error(f"[{task_id}] Ошибка парсинга JSON ответа: {parse_err}")
                # Если парсинг не удался, продолжаем, чтобы задача не висела, 
                # но в result задачи останется сырой JSON
            
            # ПЕРЕНОС ФАЙЛОВ ИЗ TEMP В RESULT
            # Переносим видео, документы (только исходные) и используемые картинки
            FileManagementService.move_completed_task_files(task_id, task.document_names, used_image_ids)
            
            # Отмечаем как завершено
            task.mark_completed()
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