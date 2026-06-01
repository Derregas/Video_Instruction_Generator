from flask import Flask
from flask_login import LoginManager
from flask_app.extensions import app_services
from src.services.task_queue import TaskQueue
from src.core.processor import InstructionProcessingService
from flask_app.task_processor import VideoInstructionProcessor
from src.services.instruction_result_service import InstructionResultService
from src.infrastructure.persistence.sqlite_task_repository import SQLiteTaskRepository
from src.infrastructure.persistence.sqlite_user_repository import SQLiteUserRepository
from src.infrastructure.persistence.sqlite_requirements_repository import (
    SQLiteInstructionRepository,
    SQLiteInstructionStepRepository,
    SQLiteKeywordsRepository,
    SQLiteResourceRegistryRepository
)

task_queue: TaskQueue = None # type: ignore

def create_app():
    """Создание Flask приложения"""
    global task_queue

    app = Flask(__name__)
    app.config['SECRET_KEY'] = '123'
    
    # Инициализируем репозитории
    task_repo = SQLiteTaskRepository(db_path="tasks.db")
    user_repo = SQLiteUserRepository(db_path="users.db")
    
    # Инициализируем 4 отдельных репозитория для инструкций и результатов
    instruction_repo = SQLiteInstructionRepository(db_path="requirements.db")
    step_repo = SQLiteInstructionStepRepository(db_path="requirements.db")
    keywords_repo = SQLiteKeywordsRepository(db_path="requirements.db")
    resource_repo = SQLiteResourceRegistryRepository(db_path="requirements.db")
    
    # Создаем сервис результатов заранее, чтобы передать его в процессор
    result_service = InstructionResultService(
        instruction_repo=instruction_repo,
        step_repo=step_repo,
        keywords_repo=keywords_repo,
        resource_repo=resource_repo
    )
    
    service = InstructionProcessingService()

    processor = VideoInstructionProcessor(task_repo, service, result_service)

    # Создаём очередь
    task_queue = TaskQueue(task_repo, processor)
    task_queue.start()

    # Загружаем pending задачи при старте
    task_queue.load_pending_tasks()
    app_services.init_app(
        app, 
        task_queue, 
        task_repo, 
        user_repo,
        instruction_repo=instruction_repo,
        step_repo=step_repo,
        keywords_repo=keywords_repo,
        resource_repo=resource_repo
    )
    
    # Инициализируем Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Загружает пользователя по ID для Flask-Login"""
        return app_services.user_repo.get_by_id(user_id)

    from .routes import main_bp
    from .auth_routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    
    return app
