# src/domain/repositories.py

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Task, User

# Тут чисто интерфейсы без реализации

class ITaskRepository(ABC):
    """Интерфейс репозитория для задач"""
    
    @abstractmethod
    def create(self, task: Task) -> None:
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        pass
    
    @abstractmethod
    def update(self, task: Task) -> None:
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 50, offset: int = 0) -> List[Task]:
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str, limit: int = 50) -> List[Task]:
        """Получить все задачи пользователя"""
        pass
    
    @abstractmethod
    def delete(self, task_id: str) -> None:
        pass


class IUserRepository(ABC):
    """Интерфейс репозитория для пользователей"""
    
    @abstractmethod
    def create(self, user: User) -> None:
        """Создать пользователя"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Получить пользователя по ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> None:
        """Обновить пользователя"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 50, offset: int = 0) -> List[User]:
        """Получить всех пользователей"""
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> None:
        """Удалить пользователя"""
        pass