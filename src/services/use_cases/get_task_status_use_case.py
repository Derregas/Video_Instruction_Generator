# src/services/use_cases/get_task_status_use_case.py
import logging
from typing import Optional, Union
from datetime import datetime
from src.domain.repositories import ITaskRepository
from src.domain.entities import TaskStatus
from src.domain.exceptions import TaskNotFoundError

logger = logging.getLogger(__name__)

class GetTaskStatusResponse:
    """DTO для ответа о статусе задачи"""
    def __init__(self, 
                 task_id: str,
                 status: str,
                 video_filename: str,
                 created_at: datetime,
                 result: Optional[str],
                 error: Optional[str],
                 progress: Optional[dict]):
        self.task_id = task_id
        self.status = status
        self.video_filename = video_filename
        self.created_at = created_at
        self.result = result
        self.error = error
        self.progress = progress or {}
    
    def to_dict(self):
        response: dict[str, Union[str, int, dict, None]] = {
            'task_id': self.task_id,
            'status': self.status,
            'video_filename': self.video_filename,
            'created_at': self.created_at.isoformat(),
        }
        
        if self.status == TaskStatus.COMPLETED.value:
            response['result'] = self.result
        elif self.status == TaskStatus.FAILED.value:
            response['error'] = self.error
        elif self.status == TaskStatus.PROCESSING.value:
            response['progress'] = self.progress
        
        return response

class GetTaskStatusUseCase:
    """
    Use Case для получения статуса задачи.
    
    Используется для polling из JavaScript.
    """
    
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo
    
    def execute(self, task_id: str) -> GetTaskStatusResponse:
        """
        Получает статус задачи.
        
        Args:
            task_id: ID задачи
        
        Returns:
            GetTaskStatusResponse со статусом
        
        Raises:
            TaskNotFoundError: Если задача не найдена
        """
        try:
            task = self.task_repo.get_by_id(task_id)
            
            if not task:
                logger.warning(f"Задача {task_id} не найдена")
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            logger.debug(f"[{task_id}] Статус: {task.status.value}")
            
            # Формируем ответ в зависимости от статуса
            return GetTaskStatusResponse(
                task_id=task.id,
                status=task.status.value,
                video_filename=task.video_filename,
                created_at=task.created_at,
                result=task.result if task.status == TaskStatus.COMPLETED else None,
                error=task.error_message if task.status == TaskStatus.FAILED else None,
                progress={
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'processing_time': self._get_processing_time(task),
                } if task.status == TaskStatus.PROCESSING else None
            )
            
        except TaskNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[{task_id}] Ошибка при получении статуса: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _get_processing_time(task) -> int:
        """Считает время обработки в секундах"""
        if not task.started_at:
            return 0
        
        end_time = task.ended_at or datetime.utcnow()
        elapsed = end_time - task.started_at
        return int(elapsed.total_seconds())