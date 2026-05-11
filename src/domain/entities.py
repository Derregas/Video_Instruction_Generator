# src/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class TaskStatus(Enum):
    """Статусы задачи"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class User:
    """Entity - представляет пользователя"""
    id: str  # UUID
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id or not self.email:
            raise ValueError("User ID и email не могут быть пустыми")
        if '@' not in self.email:
            raise ValueError("Некорректный email")

@dataclass
class Task:
    """
    Entity - представляет задачу в системе.
    Теперь связана с пользователем.
    """
    id: str
    status: TaskStatus
    video_filename: str
    user_id: str  # Связь с пользователем
    document_names: List[str] = field(default_factory=list)
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.id or not self.user_id:
            raise ValueError("Task ID и user_id не могут быть пустыми")
        if not isinstance(self.status, TaskStatus):
            raise ValueError(f"Invalid status: {self.status}")
    
    """Методы для явного указания статуса"""
    def mark_processing(self):
        if self.status != TaskStatus.PENDING:
            raise ValueError(
                f"Невозможно начать задачу со статусом {self.status.value}."
                f"Только задачи со статусом {TaskStatus.PENDING.value} могут быть начаты.")
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, result: str):
        if self.status != TaskStatus.PROCESSING:
            raise ValueError(
                f"Невозможно завершить задачу со статусом {self.status.value}."
                f"Только задачи со статусом {TaskStatus.PROCESSING.value} могут быть завершены.")
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.ended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.ended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()