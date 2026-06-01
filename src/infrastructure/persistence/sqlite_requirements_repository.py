# src/infrastructure/persistence/sqlite_requirements_repository.py

"""SQLite реализация репозиториев для инструкций и результатов (requirements.db)"""

import sqlite3
import json
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from src.domain.entities import (
    Instruction, InstructionStep, Keywords, ResourceRegistry
)
from src.domain.repositories import (
    IInstructionRepository, IInstructionStepRepository,
    IKeywordsRepository, IResourceRegistryRepository
)
from src.domain.exceptions import DatabaseError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


def _init_requirements_db(db_path: str):
    """Инициализация БД requirements.db и создание таблиц"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица инструкций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS instructions (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    keywords_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keywords_id) REFERENCES keywords(id)
                )
            """)
            
            # Таблица шагов инструкции
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS instruction_steps (
                    id TEXT PRIMARY KEY,
                    instruction_id TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    time_start REAL,
                    time_end REAL,
                    image_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instruction_id) REFERENCES instructions(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица ключевых слов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id TEXT PRIMARY KEY,
                    instruction_id TEXT NOT NULL UNIQUE,
                    keywords_list TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instruction_id) REFERENCES instructions(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица реестра ресурсов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_registry (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    instruction_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instruction_id) REFERENCES instructions(id) ON DELETE CASCADE
                )
            """)
            
            # Индексы для оптимизации
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_instructions_task_id 
                ON instructions(task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_instruction_id 
                ON instruction_steps(instruction_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keywords_instruction_id 
                ON keywords(instruction_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_resources_instruction_id 
                ON resources_registry(instruction_id)
            """)
            
            conn.commit()
            logger.info(f"Requirements database initialized at {db_path}")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise DatabaseError(f"Failed to initialize requirements database: {e}")


# ============================================================================
# SQLiteInstructionRepository
# ============================================================================

class SQLiteInstructionRepository(BaseRepository, IInstructionRepository):
    """SQLite реализация репозитория для инструкций"""
    
    def __init__(self, db_path: str = "requirements.db"):
        self.db_path = db_path
        _init_requirements_db(db_path)
    
    def _init_db(self):
        """Инициализация БД (уже вызвана в __init__)"""
        pass
    
    def create_instruction(self, instruction: Instruction) -> None:
        """Создать инструкцию"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO instructions (id, task_id, title, description, keywords_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    instruction.id,
                    instruction.task_id,
                    instruction.title,
                    instruction.description,
                    instruction.keywords_id,
                    instruction.created_at,
                    instruction.updated_at
                ))
                conn.commit()
                logger.info(f"Instruction {instruction.id} created")
        except sqlite3.Error as e:
            logger.error(f"Error creating instruction: {e}")
            raise DatabaseError(f"Failed to create instruction: {e}")
    
    def get_instruction_by_id(self, instruction_id: str) -> Optional[Instruction]:
        """Получить инструкцию по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task_id, title, description, keywords_id, created_at, updated_at
                    FROM instructions
                    WHERE id = ?
                """, (instruction_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_instruction(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting instruction: {e}")
            raise DatabaseError(f"Failed to get instruction: {e}")
    
    def get_instruction_by_task_id(self, task_id: str) -> Optional[Instruction]:
        """Получить инструкцию по task_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task_id, title, description, keywords_id, created_at, updated_at
                    FROM instructions
                    WHERE task_id = ?
                """, (task_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_instruction(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting instruction by task_id: {e}")
            raise DatabaseError(f"Failed to get instruction by task_id: {e}")
    
    def update_instruction(self, instruction: Instruction) -> None:
        """Обновить инструкцию"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE instructions
                    SET title = ?, description = ?, keywords_id = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    instruction.title,
                    instruction.description,
                    instruction.keywords_id,
                    datetime.now(),
                    instruction.id
                ))
                conn.commit()
                logger.info(f"Instruction {instruction.id} updated")
        except sqlite3.Error as e:
            logger.error(f"Error updating instruction: {e}")
            raise DatabaseError(f"Failed to update instruction: {e}")
    
    def get_all_instructions(self, limit: int = 50, offset: int = 0) -> List[Instruction]:
        """Получить все инструкции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task_id, title, description, keywords_id, created_at, updated_at
                    FROM instructions
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                rows = cursor.fetchall()
                return [self._row_to_instruction(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting all instructions: {e}")
            raise DatabaseError(f"Failed to get all instructions: {e}")
    
    def delete_instruction(self, instruction_id: str) -> None:
        """Удалить инструкцию (каскадно удаляет все связанные данные)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM instructions WHERE id = ?", (instruction_id,))
                conn.commit()
                logger.info(f"Instruction {instruction_id} deleted")
        except sqlite3.Error as e:
            logger.error(f"Error deleting instruction: {e}")
            raise DatabaseError(f"Failed to delete instruction: {e}")
    
    @staticmethod
    def _row_to_instruction(row) -> Instruction:
        """Преобразовать строку БД в объект Instruction"""
        return Instruction(
            id=row[0],
            task_id=row[1],
            title=row[2],
            description=row[3],
            keywords_id=row[4],
            created_at=row[5],
            updated_at=row[6]
        )


# ============================================================================
# SQLiteInstructionStepRepository
# ============================================================================
  
class SQLiteInstructionStepRepository(BaseRepository, IInstructionStepRepository):
    """SQLite реализация репозитория для шагов инструкции"""
    
    def __init__(self, db_path: str = "requirements.db"):
        self.db_path = db_path
        _init_requirements_db(db_path)
    
    def _init_db(self):
        """Инициализация БД (уже вызвана в __init__)"""
        pass
    
    def create_step(self, step: InstructionStep) -> None:
        """Создать шаг"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO instruction_steps 
                    (id, instruction_id, step_order, title, text, time_start, time_end, image_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    step.id,
                    step.instruction_id,
                    step.step_order,
                    step.title,
                    step.text,
                    step.time_start,
                    step.time_end,
                    step.image_id,
                    step.created_at
                ))
                conn.commit()
                logger.info(f"Step {step.id} created")
        except sqlite3.Error as e:
            logger.error(f"Error creating step: {e}")
            raise DatabaseError(f"Failed to create step: {e}")
    
    def get_step_by_id(self, step_id: str) -> Optional[InstructionStep]:
        """Получить шаг по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, instruction_id, step_order, title, text, time_start, time_end, image_id, created_at
                    FROM instruction_steps
                    WHERE id = ?
                """, (step_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_step(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting step: {e}")
            raise DatabaseError(f"Failed to get step: {e}")
    
    def get_steps_by_instruction_id(self, instruction_id: str) -> List[InstructionStep]:
        """Получить все шаги инструкции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, instruction_id, step_order, title, text, time_start, time_end, image_id, created_at
                    FROM instruction_steps
                    WHERE instruction_id = ?
                    ORDER BY step_order
                """, (instruction_id,))
                rows = cursor.fetchall()
                return [self._row_to_step(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting steps: {e}")
            raise DatabaseError(f"Failed to get steps: {e}")
    
    def update_step(self, step: InstructionStep) -> None:
        """Обновить шаг"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE instruction_steps
                    SET step_order = ?, title = ?, text = ?, time_start = ?, time_end = ?, image_id = ?
                    WHERE id = ?
                """, (
                    step.step_order,
                    step.title,
                    step.text,
                    step.time_start,
                    step.time_end,
                    step.image_id,
                    step.id
                ))
                conn.commit()
                logger.info(f"Step {step.id} updated")
        except sqlite3.Error as e:
            logger.error(f"Error updating step: {e}")
            raise DatabaseError(f"Failed to update step: {e}")
    
    def delete_step(self, step_id: str) -> None:
        """Удалить шаг"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM instruction_steps WHERE id = ?", (step_id,))
                conn.commit()
                logger.info(f"Step {step_id} deleted")
        except sqlite3.Error as e:
            logger.error(f"Error deleting step: {e}")
            raise DatabaseError(f"Failed to delete step: {e}")
    
    @staticmethod
    def _row_to_step(row) -> InstructionStep:
        """Преобразовать строку БД в объект InstructionStep"""
        return InstructionStep(
            id=row[0],
            instruction_id=row[1],
            step_order=row[2],
            title=row[3],
            text=row[4],
            time_start=row[5],
            time_end=row[6],
            image_id=row[7],
            created_at=row[8]
        )


# ============================================================================
# SQLiteKeywordsRepository
# ============================================================================

class SQLiteKeywordsRepository(BaseRepository, IKeywordsRepository):
    """SQLite реализация репозитория для ключевых слов"""
    
    def __init__(self, db_path: str = "requirements.db"):
        self.db_path = db_path
        _init_requirements_db(db_path)
    
    def _init_db(self):
        """Инициализация БД (уже вызвана в __init__)"""
        pass
    
    def create_keywords(self, keywords: Keywords) -> None:
        """Создать ключевые слова"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                keywords_json = json.dumps(keywords.keywords_list)
                cursor.execute("""
                    INSERT INTO keywords (id, instruction_id, keywords_list, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    keywords.id,
                    keywords.instruction_id,
                    keywords_json,
                    keywords.created_at
                ))
                conn.commit()
                logger.info(f"Keywords {keywords.id} created")
        except sqlite3.Error as e:
            logger.error(f"Error creating keywords: {e}")
            raise DatabaseError(f"Failed to create keywords: {e}")
    
    def get_keywords_by_id(self, keywords_id: str) -> Optional[Keywords]:
        """Получить ключевые слова по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, instruction_id, keywords_list, created_at
                    FROM keywords
                    WHERE id = ?
                """, (keywords_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_keywords(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting keywords: {e}")
            raise DatabaseError(f"Failed to get keywords: {e}")
    
    def get_keywords_by_instruction(self, instruction_id: str) -> Optional[Keywords]:
        """Получить ключевые слова для инструкции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, instruction_id, keywords_list, created_at
                    FROM keywords
                    WHERE instruction_id = ?
                """, (instruction_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_keywords(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting keywords by instruction: {e}")
            raise DatabaseError(f"Failed to get keywords by instruction: {e}")
    
    def update_keywords(self, keywords: Keywords) -> None:
        """Обновить ключевые слова"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                keywords_json = json.dumps(keywords.keywords_list)
                cursor.execute("""
                    UPDATE keywords
                    SET keywords_list = ?
                    WHERE id = ?
                """, (keywords_json, keywords.id))
                conn.commit()
                logger.info(f"Keywords {keywords.id} updated")
        except sqlite3.Error as e:
            logger.error(f"Error updating keywords: {e}")
            raise DatabaseError(f"Failed to update keywords: {e}")
    
    def delete_keywords(self, keywords_id: str) -> None:
        """Удалить ключевые слова"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM keywords WHERE id = ?", (keywords_id,))
                conn.commit()
                logger.info(f"Keywords {keywords_id} deleted")
        except sqlite3.Error as e:
            logger.error(f"Error deleting keywords: {e}")
            raise DatabaseError(f"Failed to delete keywords: {e}")
    
    @staticmethod
    def _row_to_keywords(row) -> Keywords:
        """Преобразовать строку БД в объект Keywords"""
        return Keywords(
            id=row[0],
            instruction_id=row[1],
            keywords_list=json.loads(row[2]),
            created_at=row[3]
        )


# ============================================================================
# SQLiteResourceRegistryRepository
# ============================================================================

class SQLiteResourceRegistryRepository(BaseRepository, IResourceRegistryRepository):
    """SQLite реализация репозитория для реестра ресурсов"""
    
    def __init__(self, db_path: str = "requirements.db"):
        self.db_path = db_path
        _init_requirements_db(db_path)
    
    def _init_db(self):
        """Инициализация БД (уже вызвана в __init__)"""
        pass
    
    def create_resource(self, resource: ResourceRegistry) -> None:
        """Создать запись ресурса"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO resources_registry (id, filename, filepath, resource_type, instruction_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    resource.id,
                    resource.filename,
                    resource.filepath,
                    resource.resource_type,
                    resource.instruction_id,
                    resource.created_at
                ))
                conn.commit()
                logger.info(f"Resource {resource.id} created")
        except sqlite3.Error as e:
            logger.error(f"Error creating resource: {e}")
            raise DatabaseError(f"Failed to create resource: {e}")
    
    def get_resource_by_id(self, resource_id: str) -> Optional[ResourceRegistry]:
        """Получить ресурс по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename, filepath, resource_type, instruction_id, created_at
                    FROM resources_registry
                    WHERE id = ?
                """, (resource_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_resource(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting resource: {e}")
            raise DatabaseError(f"Failed to get resource: {e}")
    
    def get_all_resources(self, limit: int = 50, offset: int = 0) -> List[ResourceRegistry]:
        """Получить все ресурсы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename, filepath, resource_type, instruction_id, created_at
                    FROM resources_registry
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                rows = cursor.fetchall()
                return [self._row_to_resource(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting all resources: {e}")
            raise DatabaseError(f"Failed to get all resources: {e}")
    
    def get_resources_by_instruction(self, instruction_id: str) -> List[ResourceRegistry]:
        """Получить все ресурсы инструкции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename, filepath, resource_type, instruction_id, created_at
                    FROM resources_registry
                    WHERE instruction_id = ?
                    ORDER BY created_at
                """, (instruction_id,))
                rows = cursor.fetchall()
                return [self._row_to_resource(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting resources by instruction: {e}")
            raise DatabaseError(f"Failed to get resources by instruction: {e}")
    
    def update_resource(self, resource: ResourceRegistry) -> None:
        """Обновить ресурс"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE resources_registry
                    SET filename = ?, filepath = ?, resource_type = ?, instruction_id = ?
                    WHERE id = ?
                """, (
                    resource.filename,
                    resource.filepath,
                    resource.resource_type,
                    resource.instruction_id,
                    resource.id
                ))
                conn.commit()
                logger.info(f"Resource {resource.id} updated")
        except sqlite3.Error as e:
            logger.error(f"Error updating resource: {e}")
            raise DatabaseError(f"Failed to update resource: {e}")
    
    def delete_resource(self, resource_id: str) -> None:
        """Удалить ресурс"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM resources_registry WHERE id = ?", (resource_id,))
                conn.commit()
                logger.info(f"Resource {resource_id} deleted")
        except sqlite3.Error as e:
            logger.error(f"Error deleting resource: {e}")
            raise DatabaseError(f"Failed to delete resource: {e}")
    
    @staticmethod
    def _row_to_resource(row) -> ResourceRegistry:
        """Преобразовать строку БД в объект ResourceRegistry"""
        return ResourceRegistry(
            id=row[0],
            filename=row[1],
            filepath=row[2],
            resource_type=row[3],
            instruction_id=row[4],
            created_at=row[5]
        )
