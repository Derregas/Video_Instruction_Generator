# flask_app/extensions.py

from src.services.task_queue import TaskQueue
from src.domain.repositories import ITaskRepository
from src.services.task_creation_service import TaskCreationService
from src.services.upload_service import UploadService, UploadConfig
from src.services.instruction_generation_service import InstructionGenerationService
from src.services.use_cases import (
    CreateTaskUseCase,
    GetTaskStatusUseCase,
    GenerateInstructionUseCase,
)

class AppServices:
    """
    Flask extension для хранения сервисов приложения.
    
    Содержит:
    - task_queue: Очередь обработки задач
    - task_repo: Репозиторий задач
    - Use Cases для бизнес-логики
    - Service Layer для работы с файлами и БД
    """
    task_queue: TaskQueue = None  # type: ignore
    task_repo: ITaskRepository = None  # type: ignore
    
    def init_app(self, app, task_queue: TaskQueue, task_repo: ITaskRepository):
        """Инициализирует расширение"""
        self.task_queue = task_queue
        self.task_repo = task_repo

        # Инициализируем Service Layer
        upload_service = UploadService(config=UploadConfig())
        task_creation_service = TaskCreationService(
            task_repo=task_repo,
            task_queue=task_queue
        )
        instruction_service = InstructionGenerationService(
            task_repo=task_repo
        )
        
        # Инициализируем Use Cases
        self.create_task_use_case = CreateTaskUseCase(
            upload_service=upload_service,
            task_creation_service=task_creation_service,
            upload_config=UploadConfig()
        )
        
        self.get_task_status_use_case = GetTaskStatusUseCase(
            task_repo=task_repo
        )
        
        self.generate_instruction_use_case = GenerateInstructionUseCase(
            instruction_service=instruction_service
        )

        app.extensions['app_services'] = self

# Глобальный экземпляр
app_services = AppServices()