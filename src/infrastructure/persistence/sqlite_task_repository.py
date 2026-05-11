# src/infrastructure/persistence/sqlite_repository.py

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional

from src.domain.entities import Task, TaskStatus
from src.domain.repositories import ITaskRepository
from src.domain.exceptions import (
    TaskNotFoundError, 
    TaskAlreadyExistsError,
    DatabaseError
)
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class SQLiteTaskRepository(BaseRepository, ITaskRepository):
    """Реализация Repository для Task в SQLite"""
    
    def _init_db(self):
        """Инициализирует таблицу tasks"""
        try:
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                # Создаём таблицу tasks
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        video_filename TEXT NOT NULL,
                        document_names TEXT,
                        result TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        ended_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
                conn.commit()
                logger.info(f"Таблица tasks инициализирована: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации таблицы tasks: {e}")
            raise DatabaseError(f"Failed to initialize tasks table: {e}")
    
    def create(self, task: Task) -> None:
        """Создаёт новую задачу"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                doc_names_json = json.dumps(task.document_names) if task.document_names else None
                
                conn.execute('''
                    INSERT INTO tasks 
                    (id, user_id, status, video_filename, document_names, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id,
                    task.user_id,
                    task.status.value,
                    task.video_filename,
                    doc_names_json,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat()
                ))
                conn.commit()
                self._log_create(task.id, "Task")
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                raise TaskAlreadyExistsError(f"Task {task.id} already exists")
            elif "FOREIGN KEY" in str(e):
                raise DatabaseError(f"User {task.user_id} not found")
            raise
        except sqlite3.Error as e:
            self._log_error("create", task.id, str(e))
            raise DatabaseError(f"Failed to create task: {e}")
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Получает задачу по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
                
                if not row:
                    return None
                
                return self._row_to_task(row)
        except sqlite3.Error as e:
            self._log_error("get_by_id", task_id, str(e))
            raise DatabaseError(f"Failed to get task: {e}")
    
    def update(self, task: Task) -> None:
        """Обновляет задачу"""
        try:
            existing = self.get_by_id(task.id)
            if not existing:
                raise TaskNotFoundError(f"Task {task.id} not found")
            
            with sqlite3.connect(self.db_path) as conn:
                doc_names_json = json.dumps(task.document_names) if task.document_names else None
                
                conn.execute('''
                    UPDATE tasks 
                    SET status = ?, result = ?, error_message = ?, 
                        started_at = ?, ended_at = ?, updated_at = ?,
                        document_names = ?
                    WHERE id = ?
                ''', (
                    task.status.value,
                    task.result,
                    task.error_message,
                    task.started_at.isoformat() if task.started_at else None,
                    task.ended_at.isoformat() if task.ended_at else None,
                    task.updated_at.isoformat(),
                    doc_names_json,
                    task.id
                ))
                conn.commit()
                self._log_update(task.id, "Task")
        except sqlite3.Error as e:
            self._log_error("update", task.id, str(e))
            raise DatabaseError(f"Failed to update task: {e}")
    
    def get_all(self, limit: int = 50, offset: int = 0) -> List[Task]:
        """Получает все задачи"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    'SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (limit, offset)
                ).fetchall()
                
                return [self._row_to_task(row) for row in rows]
        except sqlite3.Error as e:
            self._log_error("get_all", "", str(e))
            raise DatabaseError(f"Failed to get tasks: {e}")
    
    def get_by_user_id(self, user_id: str, limit: int = 50) -> List[Task]:
        """Получает все задачи конкретного пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    'SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                    (user_id, limit)
                ).fetchall()
                
                return [self._row_to_task(row) for row in rows]
        except sqlite3.Error as e:
            self._log_error("get_by_user_id", user_id, str(e))
            raise DatabaseError(f"Failed to get user tasks: {e}")
    
    def delete(self, task_id: str) -> None:
        """Удаляет задачу"""
        try:
            existing = self.get_by_id(task_id)
            if not existing:
                raise TaskNotFoundError(f"Task {task_id} not found")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.commit()
                self._log_delete(task_id, "Task")
        except sqlite3.Error as e:
            self._log_error("delete", task_id, str(e))
            raise DatabaseError(f"Failed to delete task: {e}")
    
    @staticmethod
    def _row_to_task(row) -> Task:
        """Преобразует строку SQLite в Entity Task"""
        doc_names = []
        if row['document_names']:
            try:
                doc_names = json.loads(row['document_names'])
            except json.JSONDecodeError:
                doc_names = []
        
        return Task(
            id=row['id'],
            user_id=row['user_id'],
            status=TaskStatus(row['status']),
            video_filename=row['video_filename'],
            document_names=doc_names,
            result=row['result'],
            error_message=row['error_message'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow(),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
        )