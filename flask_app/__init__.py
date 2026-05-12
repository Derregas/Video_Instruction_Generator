from flask import Flask
from flask_app.extensions import app_services
from src.services.task_queue import TaskQueue
from src.core.processor import InstructionProcessingService
from flask_app.task_processor import VideoInstructionProcessor
from src.infrastructure.persistence.sqlite_task_repository import SQLiteTaskRepository

task_queue: TaskQueue = None # type: ignore

def create_app():
    """Создание Flask приложения"""
    global task_queue

    app = Flask(__name__)
    
    # Инициализируем репозиторий
    task_repo = SQLiteTaskRepository(db_path="tasks.db")
    service = InstructionProcessingService()

    processor = VideoInstructionProcessor(task_repo, service)

    # Создаём очередь
    task_queue = TaskQueue(task_repo, processor)
    task_queue.start()

    # Загружаем pending задачи при старте
    task_queue.load_pending_tasks()
    app_services.init_app(app, task_queue, task_repo)

    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
