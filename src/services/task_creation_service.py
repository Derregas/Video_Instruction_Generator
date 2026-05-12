# src/services/task_creation_service.py
import uuid
import logging
from typing import Optional
from src.services.task_queue import TaskQueue
from src.domain.entities import Task, TaskStatus
from src.domain.repositories import ITaskRepository
from src.domain.exceptions import DatabaseError, TaskAlreadyExistsError

logger = logging.getLogger(__name__)

class TaskCreationService:
    """Сервис для создания задач и добавления в очередь"""
    
    def __init__(self, 
                 task_repo: ITaskRepository, 
                 task_queue: TaskQueue):
        self.task_repo = task_repo
        self.task_queue = task_queue
    
    def create_and_queue(self,
                         task_id: str,
                         video_filename: str,
                         document_names: Optional[list[str]],
                         user_id: str = "0") -> str:
        """
        Создаёт новую задачу и добавляет в очередь.
        
        Args:
            task_id: Уникальный ID задачи
            video_filename: Имя видеофайла
            document_names: Список имён документов
            user_id: ID пользователя
        
        Returns:
            task_id новой задачи
        
        Raises:
            TaskAlreadyExistsError: Если задача уже существует
            DatabaseError: Если ошибка БД
        """
        
        try:
            # Создаём объект задачи
            task = Task(
                id=task_id,
                user_id=user_id,
                status=TaskStatus.PENDING,
                video_filename=video_filename,
                document_names=document_names or []
            )
            
            # Записываем в БД
            self.task_repo.create(task)
            logger.info(f"[{task_id}] Задача создана в БД")
            
            # Добавляем в очередь
            if self.task_queue.enqueue(task_id):
                logger.info(f"[{task_id}] Добавлена в очередь. Размер: {self.task_queue.get_queue_size()}")
            
            return task_id
            
        except TaskAlreadyExistsError:
            logger.error(f"[{task_id}] Задача уже существует")
            raise
        except DatabaseError as e:
            logger.error(f"[{task_id}] Ошибка БД: {e}")
            raise
    
    @staticmethod
    def generate_task_id() -> str:
        """Генерирует уникальный ID задачи"""
        return str(uuid.uuid4())[:8]