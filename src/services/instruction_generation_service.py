# src/services/instruction_generation_service.py
import os
import logging
from typing import Literal
from src.config import AppConfig
from src.domain.entities import TaskStatus
from src.domain.exceptions import TaskNotFoundError
from src.domain.repositories import ITaskRepository
from src.services.instruction_result_service import InstructionResultService
from flask_app.document_generators import DocumentCreator

logger = logging.getLogger(__name__)

class InstructionGenerationService:
    """Сервис для генерации инструкций в разных форматах"""
    
    ALLOWED_FORMATS = ('pdf', 'docx', 'txt')
    
    def __init__(self, task_repo: ITaskRepository, result_service: InstructionResultService):
        self.task_repo = task_repo
        self.result_service = result_service
    
    def generate_instruction(self,
                            task_id: str,
                            doc_format: Literal['pdf', 'docx', 'txt'] = 'pdf') -> str:
        """
        Генерирует инструкцию в указанном формате.
        
        Args:
            task_id: ID задачи
            doc_format: Формат документа (pdf, docx, txt)
        
        Returns:
            Путь к сгенерированному файлу
        
        Raises:
            TaskNotFoundError: Если задача не найдена
            ValueError: Если формат не поддерживается или задача не завершена
        """
        # Валидируем формат
        if doc_format not in self.ALLOWED_FORMATS:
            raise ValueError(f'Недопустимый формат. Разрешены: {", ".join(self.ALLOWED_FORMATS)}')
        
        # Получаем задачу
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f'Задача {task_id} не найдена')
        
        # Проверяем статус
        if task.status != TaskStatus.COMPLETED:
            raise ValueError(f'Обработка не завершена. Статус: {task.status.value}')
        
        # Получаем структурированные данные из новой БД
        instruction_data = self.result_service.get_instruction_by_task_id(task_id)
        if not instruction_data:
            raise ValueError('Данные инструкции не найдены в базе результатов')
        
        try:
            # Генерируем файл
            task_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
            filename = f"instruction_{task_id}.{doc_format}"
            filepath = os.path.join(task_dir, filename)
            
            # Передаем структурированные данные вместо сырого JSON
            # Передаём task_id для правильного поиска картинок
            DocumentCreator.create(instruction_data, filepath, task_id=task_id)
            logger.info(f"[{task_id}] Инструкция сгенерирована: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"[{task_id}] Ошибка при генерации инструкции: {e}")
            raise