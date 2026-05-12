# src/services/upload_service.py
import os
import logging
from src.config import AppConfig
from typing import Tuple, List, Optional
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

class UploadConfig:
    """Конфигурация для загрузки файлов"""
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_DOCUMENTS = 5
    MAX_DOCUMENTS_SIZE = 30 * 1024 * 1024     # 30MB
    ALLOWED_VIDEO_FORMATS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
    ALLOWED_DOC_FORMATS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'png'}

class UploadService:
    """Сервис для обработки загрузок файлов"""
    
    def __init__(self, config: Optional[UploadConfig]):
        self.config = config or UploadConfig()
    
    def validate_video(self, video: FileStorage) -> Tuple[bool, str]:
        """
        Валидирует видеофайл.
        Возвращает (is_valid, error_message)
        """
        if not video or not video.filename or video.filename == '':
            return False, 'Файл видео не выбран'
        
        # Проверяем расширение
        ext = self._get_extension(video.filename) # type: ignore
        if ext not in self.config.ALLOWED_VIDEO_FORMATS:
            return False, f'Недопустимый формат видео. Разрешены: {", ".join(self.config.ALLOWED_VIDEO_FORMATS)}'
        
        # Проверяем размер
        video.seek(0, os.SEEK_END)
        size = video.tell()
        video.seek(0)
        
        if size > self.config.MAX_VIDEO_SIZE:
            return False, f'Размер видео превышает {self.config.MAX_VIDEO_SIZE // (1024**3)}GB'
        
        return True, ''
    
    def validate_documents(self, documents: List[FileStorage]) -> Tuple[bool, str]:
        """Валидирует документы"""
        if not documents:
            return True, ''
        
        if len(documents) > self.config.MAX_DOCUMENTS:
            return False, f'Максимум {self.config.MAX_DOCUMENTS} файлов'
        
        # Проверяем расширения и общий размер
        total_size = 0
        for doc in documents:
            ext = self._get_extension(doc.filename) # type: ignore
            if ext not in self.config.ALLOWED_DOC_FORMATS:
                return False, f'Недопустимый формат файла: {doc.filename}'
            
            doc.seek(0, os.SEEK_END)
            total_size += doc.tell()
            doc.seek(0)
        
        if total_size > self.config.MAX_DOCUMENTS_SIZE:
            return False, f'Общий размер документов превышает {self.config.MAX_DOCUMENTS_SIZE // (1024**2)}MB'
        
        return True, ''
    
    def save_video(self, video: FileStorage, task_id: str) -> str:
        """Сохраняет видео в temp директорию. Возвращает полный путь"""
        request_temp_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
        os.makedirs(request_temp_dir, exist_ok=True)
        
        video_path = os.path.join(request_temp_dir, video.filename) # type: ignore
        video.save(video_path)
        
        logger.info(f"[{task_id}] Видео сохранено: {video_path}")
        return video_path
    
    def save_documents(self, documents: List[FileStorage], task_id: str) -> List[str]:
        """Сохраняет документы. Возвращает список имён файлов"""
        request_temp_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
        os.makedirs(request_temp_dir, exist_ok=True)
        
        doc_names = []
        for doc in documents:
            doc_path = os.path.join(request_temp_dir, f"doc_{doc.filename}")
            doc.save(doc_path)
            doc_names.append(os.path.basename(doc_path))
        
        logger.info(f"[{task_id}] Сохранены документы: {doc_names}")
        return doc_names
    
    @staticmethod
    def _get_extension(filename: str) -> str:
        """Получает расширение файла"""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''