# src/services/use_cases/generate_instruction_use_case.py
import os
import logging
from typing import Literal
from src.domain.exceptions import TaskNotFoundError
from src.services.instruction_generation_service import InstructionGenerationService

logger = logging.getLogger(__name__)

class GenerateInstructionRequest:
    """DTO для запроса генерации инструкции"""
    def __init__(self,
                 task_id: str,
                 format: Literal['pdf', 'docx', 'txt'] = 'pdf'):
        self.task_id = task_id
        self.format = format.lower()

class GenerateInstructionResponse:
    """DTO для ответа"""
    def __init__(self,
                 task_id: str,
                 filepath: str,
                 filename: str,
                 format: str):
        self.task_id = task_id
        self.filepath = filepath
        self.filename = filename
        self.format = format
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'filename': self.filename,
            'format': self.format,
            'message': 'Инструкция успешно сгенерирована'
        }

class GenerateInstructionUseCase:
    """
    Use Case для генерации инструкции в разных форматах.
    
    Проверяет:
    - Существует ли задача
    - Завершена ли обработка
    - Поддерживается ли формат
    """
    
    def __init__(self, instruction_service: InstructionGenerationService):
        self.instruction_service = instruction_service
    
    def execute(self, request: GenerateInstructionRequest) -> GenerateInstructionResponse:
        """
        Генерирует инструкцию.
        
        Args:
            request: GenerateInstructionRequest с task_id и format
        
        Returns:
            GenerateInstructionResponse с путём к файлу
        
        Raises:
            TaskNotFoundError: Если задача не найдена
            ValueError: Если задача не завершена или формат не поддерживается
        """
        try:
            logger.info(f"[{request.task_id}] Генерация инструкции в формате {request.format}")
            
            # Генерируем инструкцию
            filepath = self.instruction_service.generate_instruction(
                task_id=request.task_id,
                doc_format=request.format # type: ignore
            )
            
            filename = os.path.basename(filepath)
            
            logger.info(f"[{request.task_id}] Инструкция успешно сгенерирована: {filename}")
            
            return GenerateInstructionResponse(
                task_id=request.task_id,
                filepath=filepath,
                filename=filename,
                format=request.format
            )
            
        except TaskNotFoundError:
            logger.error(f"[{request.task_id}] Задача не найдена")
            raise
        except ValueError as e:
            logger.warning(f"[{request.task_id}] Ошибка валидации: {e}")
            raise
        except Exception as e:
            logger.error(f"[{request.task_id}] Ошибка при генерации инструкции: {e}", exc_info=True)
            raise