# src/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from flask_login import UserMixin

class TaskStatus(Enum):
    """Статусы задачи"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(Enum):
    """Роли пользователя в системе"""
    VIEW = "view"  # Только просмотр
    MANAGE = "manage"  # Управление: запуск работы, редактирование
    ADMIN = "admin"  # Администратор

@dataclass
class User(UserMixin):
    """Entity - представляет пользователя с поддержкой flask_login"""
    id: str  # UUID
    username: str
    email: str
    password_hash: str  # Хеш пароля
    role: UserRole = UserRole.VIEW  # Роль пользователя
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id or not self.email:
            raise ValueError("User ID и email не могут быть пустыми")
        if '@' not in self.email:
            raise ValueError("Некорректный email")
        if not isinstance(self.role, UserRole):
            raise ValueError(f"Invalid role: {self.role}")
        if not self.password_hash:
            raise ValueError("Password hash не может быть пустым")

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
        if self.status not in (TaskStatus.PENDING, TaskStatus.PROCESSING):
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


# ==================================================
# ENTITIES FOR INSTRUCTIONS (Results Storage)
# ==================================================

@dataclass
class Instruction:
    """
    Entity - представляет инструкцию.
    Одна инструкция создаётся из одной задачи обработки видео.
    """
    id: str
    task_id: str  # Связь с Task
    title: str  # Название инструкции
    description: str  # Описание инструкции
    keywords_id: Optional[str] = None  # Связь с Keywords
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id or not self.task_id or not self.title:
            raise ValueError("ID, task_id и title не могут быть пустыми")


@dataclass
class InstructionStep:
    """
    Entity - представляет шаг инструкции.
    Одна инструкция может содержать множество шагов.
    """
    id: str
    instruction_id: str  # Связь с Instruction
    step_order: int  # Порядок шага (1, 2, 3...)
    title: str  # Заголовок шага
    text: str  # Текст описания шага
    time_start: Optional[float] = None  # Время начала в видео (сек)
    time_end: Optional[float] = None  # Время конца в видео (сек)
    image_id: Optional[str] = None  # Связь с ResourceRegistry (изображение)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id or not self.instruction_id or self.step_order < 1:
            raise ValueError("ID, instruction_id и step_order (>= 1) обязательны")


@dataclass
class Keywords:
    """
    Entity - представляет ключевые слова для инструкции.
    """
    id: str
    instruction_id: str  # Связь с Instruction
    keywords_list: List[str] = field(default_factory=list)  # Список ключевых слов
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id or not self.instruction_id:
            raise ValueError("ID и instruction_id не могут быть пустыми")


@dataclass
class ResourceRegistry:
    """
    Entity - представляет ресурс (файл: изображение, видео и т.д.).
    """
    id: str
    filename: str  # Имя файла
    filepath: str  # Полный путь к файлу
    resource_type: str  # Тип ресурса: image, video, document и т.д.
    created_at: datetime = field(default_factory=datetime.utcnow)
    instruction_id: Optional[str] = None  # Связь с Instruction (опционально)
    
    def __post_init__(self):
        if not self.id or not self.filename or not self.filepath:
            raise ValueError("ID, filename и filepath не могут быть пустыми")