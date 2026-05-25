# src/services/use_cases/create_task_use_case.py
import logging
from typing import Optional
from werkzeug.datastructures import FileStorage
from src.services.task_creation_service import TaskCreationService
from src.services.upload_service import UploadService, UploadConfig
from src.domain.exceptions import TaskAlreadyExistsError, DatabaseError

logger = logging.getLogger(__name__)

class CreateTaskRequest:
    """DTO для запроса создания задачи"""
    def __init__(self, 
                 video: FileStorage,
                 documents: Optional[list[FileStorage]] = None,
                 user_id: Optional[str] = None):
        self.video = video
        self.documents = documents or []
        self.user_id = user_id or "0"  # Default user_id if not provided

class CreateTaskResponse:
    """DTO для ответа"""
    def __init__(self, task_id: str, message: str = "Task created successfully"):
        self.task_id = task_id
        self.message = message
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'message': self.message
        }

class CreateTaskUseCase:
    """
    Use Case для создания новой задачи обработки видео.
    
    Шаги:
    1. Валидирует видео и документы
    2. Сохраняет файлы на диск
    3. Создаёт задачу в БД
    4. Добавляет в очередь обработки
    """
    
    def __init__(self,
                 upload_service: UploadService,
                 task_creation_service: TaskCreationService,
                 upload_config: Optional[UploadConfig]):
        self.upload_service = upload_service
        self.task_creation_service = task_creation_service
        self.upload_config = upload_config or UploadConfig()
    
    def execute(self, request: CreateTaskRequest) -> CreateTaskResponse:
        """
        Выполняет use case.
        
        Args:
            request: CreateTaskRequest с видео и документами
        
        Returns:
            CreateTaskResponse с ID новой задачи
        
        Raises:
            ValueError: Если валидация не пройдена
            DatabaseError: Если ошибка БД
        """
        try:
            # ЭТАП 1: Валидируем видео
            is_valid, error = self.upload_service.validate_video(request.video)
            if not is_valid:
                logger.warning(f"Ошибка валидации видео: {error}")
                raise ValueError(error)
            
            # ЭТАП 2: Валидируем документы (если есть)
            if request.documents:
                is_valid, error = self.upload_service.validate_documents(request.documents)
                if not is_valid:
                    logger.warning(f"Ошибка валидации документов: {error}")
                    raise ValueError(error)
            
            # ЭТАП 3: Создаём ID задачи
            task_id = self.task_creation_service.generate_task_id()
            logger.info(f"[{task_id}] Начинаем создание задачи")
            
            # ЭТАП 4: Сохраняем видео
            self.upload_service.save_video(request.video, task_id)
            
            # ЭТАП 5: Сохраняем документы и получаем их имена
            document_names = []
            if request.documents:
                document_names = self.upload_service.save_documents(request.documents, task_id)
            
            # ЭТАП 6: Создаём задачу в БД и добавляем в очередь
            self.task_creation_service.create_and_queue(
                task_id=task_id,
                video_filename=request.video.filename, # type: ignore
                document_names=document_names,
                user_id=request.user_id
            )
            
            logger.info(f"[{task_id}] Задача успешно создана")
            return CreateTaskResponse(task_id=task_id)
            
        except ValueError as e:
            logger.error(f"Ошибка валидации: {e}")
            raise
        except TaskAlreadyExistsError as e:
            logger.error(f"Задача уже существует: {e}")
            raise ValueError(str(e))
        except DatabaseError as e:
            logger.error(f"Ошибка БД: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании задачи: {e}", exc_info=True)
            raise