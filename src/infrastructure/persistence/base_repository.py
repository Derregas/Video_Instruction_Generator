# src/infrastructure/persistence/base_repository.py

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """
    Базовый класс для всех репозиториев.
    Содержит общую логику: логирование, обработка ошибок, преобразование данных.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    @abstractmethod
    def _init_db(self):
        """Реализуется подклассом для инициализации БД"""
        pass
    
    def _log_create(self, entity_id: str, entity_type: str):
        logger.info(f"{entity_type} создан: {entity_id}")
    
    def _log_update(self, entity_id: str, entity_type: str):
        logger.info(f"{entity_type} обновлен: {entity_id}")
    
    def _log_delete(self, entity_id: str, entity_type: str):
        logger.info(f"{entity_type} удален: {entity_id}")
    
    def _log_error(self, operation: str, entity_id: str, error: str):
        logger.error(f"Ошибка при {operation} {entity_id}: {error}")