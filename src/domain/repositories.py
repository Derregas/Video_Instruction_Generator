# src/domain/repositories.py

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Task, User, Instruction, InstructionStep, Keywords, ResourceRegistry

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
    def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
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


# ==================================================
# REPOSITORIES FOR INSTRUCTIONS (Results Storage)
# ==================================================

class IInstructionRepository(ABC):
    """Интерфейс репозитория для инструкций"""
    
    @abstractmethod
    def create_instruction(self, instruction: Instruction) -> None:
        """Создать инструкцию"""
        pass
    
    @abstractmethod
    def get_instruction_by_id(self, instruction_id: str) -> Optional[Instruction]:
        """Получить инструкцию по ID"""
        pass
    
    @abstractmethod
    def get_instruction_by_task_id(self, task_id: str) -> Optional[Instruction]:
        """Получить инструкцию по task_id"""
        pass
    
    @abstractmethod
    def update_instruction(self, instruction: Instruction) -> None:
        """Обновить инструкцию"""
        pass
    
    @abstractmethod
    def get_all_instructions(self, limit: int = 50, offset: int = 0) -> List[Instruction]:
        """Получить все инструкции"""
        pass
    
    @abstractmethod
    def delete_instruction(self, instruction_id: str) -> None:
        """Удалить инструкцию"""
        pass


class IInstructionStepRepository(ABC):
    """Интерфейс репозитория для шагов инструкции"""
    
    @abstractmethod
    def create_step(self, step: InstructionStep) -> None:
        """Создать шаг"""
        pass
    
    @abstractmethod
    def get_step_by_id(self, step_id: str) -> Optional[InstructionStep]:
        """Получить шаг по ID"""
        pass
    
    @abstractmethod
    def get_steps_by_instruction_id(self, instruction_id: str) -> List[InstructionStep]:
        """Получить все шаги инструкции"""
        pass
    
    @abstractmethod
    def update_step(self, step: InstructionStep) -> None:
        """Обновить шаг"""
        pass
    
    @abstractmethod
    def delete_step(self, step_id: str) -> None:
        """Удалить шаг"""
        pass


class IKeywordsRepository(ABC):
    """Интерфейс репозитория для ключевых слов"""
    
    @abstractmethod
    def create_keywords(self, keywords: Keywords) -> None:
        """Создать ключевые слова"""
        pass
    
    @abstractmethod
    def get_keywords_by_id(self, keywords_id: str) -> Optional[Keywords]:
        """Получить ключевые слова по ID"""
        pass
    
    @abstractmethod
    def get_keywords_by_instruction(self, instruction_id: str) -> Optional[Keywords]:
        """Получить ключевые слова для инструкции"""
        pass
    
    @abstractmethod
    def update_keywords(self, keywords: Keywords) -> None:
        """Обновить ключевые слова"""
        pass
    
    @abstractmethod
    def delete_keywords(self, keywords_id: str) -> None:
        """Удалить ключевые слова"""
        pass


class IResourceRegistryRepository(ABC):
    """Интерфейс репозитория для реестра ресурсов"""
    
    @abstractmethod
    def create_resource(self, resource: ResourceRegistry) -> None:
        """Создать запись ресурса"""
        pass
    
    @abstractmethod
    def get_resource_by_id(self, resource_id: str) -> Optional[ResourceRegistry]:
        """Получить ресурс по ID"""
        pass
    
    @abstractmethod
    def get_all_resources(self, limit: int = 50, offset: int = 0) -> List[ResourceRegistry]:
        """Получить все ресурсы"""
        pass
    
    @abstractmethod
    def get_resources_by_instruction(self, instruction_id: str) -> List[ResourceRegistry]:
        """Получить ресурсы для инструкции"""
        pass
    
    @abstractmethod
    def update_resource(self, resource: ResourceRegistry) -> None:
        """Обновить ресурс"""
        pass
    
    @abstractmethod
    def delete_resource(self, resource_id: str) -> None:
        """Удалить ресурс"""
        pass