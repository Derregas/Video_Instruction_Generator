# flask_app/extensions.py

from src.services.task_queue import TaskQueue
from src.domain.repositories import (
    ITaskRepository, IUserRepository,
    IInstructionRepository, IInstructionStepRepository,
    IKeywordsRepository, IResourceRegistryRepository
)
from src.services.task_creation_service import TaskCreationService
from src.services.upload_service import UploadService, UploadConfig
from src.services.instruction_generation_service import InstructionGenerationService
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.services.instruction_result_service import InstructionResultService
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
    - user_repo: Репозиторий пользователей
    - Репозитории для инструкций и результатов
    - Use Cases для бизнес-логики
    - Service Layer для работы с файлами и БД
    - auth_service: Сервис аутентификации
    - user_service: Сервис работы с пользователями
    - instruction_result_service: Сервис для управления результатами инструкций
    """
    task_queue: TaskQueue = None  # type: ignore
    task_repo: ITaskRepository = None  # type: ignore
    user_repo: IUserRepository = None  # type: ignore
    instruction_repo: IInstructionRepository = None  # type: ignore
    step_repo: IInstructionStepRepository = None  # type: ignore
    keywords_repo: IKeywordsRepository = None  # type: ignore
    resource_repo: IResourceRegistryRepository = None  # type: ignore
    auth_service: AuthService = None  # type: ignore
    user_service: UserService = None  # type: ignore
    instruction_result_service: InstructionResultService = None  # type: ignore
    
    def init_app(self, app, task_queue: TaskQueue, task_repo: ITaskRepository, 
                 user_repo: IUserRepository,
                 instruction_repo: IInstructionRepository,
                 step_repo: IInstructionStepRepository,
                 keywords_repo: IKeywordsRepository,
                 resource_repo: IResourceRegistryRepository):
        """Инициализирует расширение"""
        self.task_queue = task_queue
        self.task_repo = task_repo
        self.user_repo = user_repo
        self.instruction_repo = instruction_repo
        self.step_repo = step_repo
        self.keywords_repo = keywords_repo
        self.resource_repo = resource_repo

        # Инициализируем Service Layer
        upload_service = UploadService(config=UploadConfig())
        task_creation_service = TaskCreationService(
            task_repo=task_repo,
            task_queue=task_queue
        )
        
        instruction_result_service = InstructionResultService(
            instruction_repo=instruction_repo,
            step_repo=step_repo,
            keywords_repo=keywords_repo,
            resource_repo=resource_repo
        )
        
        instruction_service = InstructionGenerationService(
            task_repo=task_repo,
            result_service=instruction_result_service
        )
        user_service = UserService(user_repo=user_repo)
        auth_service = AuthService(user_repo=user_repo)
        
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
        
        # Сохраняем сервисы в расширение
        self.user_service = user_service
        self.auth_service = auth_service
        self.instruction_result_service = instruction_result_service

        app.extensions['app_services'] = self

# Глобальный экземпляр
app_services = AppServices()