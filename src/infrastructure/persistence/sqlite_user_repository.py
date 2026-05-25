# src/infrastructure/persistence/sqlite_user_repository.py

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional

from src.domain.entities import User, UserRole
from src.domain.repositories import IUserRepository
from src.domain.exceptions import (
    DatabaseError
)
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class SQLiteUserRepository(BaseRepository, IUserRepository):
    """Реализация Repository для User в отдельной SQLite БД"""
    
    def _init_db(self):
        """Инициализирует таблицу users"""
        try:
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                # Создаём таблицу users
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'view',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                conn.commit()
                logger.info(f"Таблица users инициализирована: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации таблицы users: {e}")
            raise DatabaseError(f"Failed to initialize users table: {e}")
    
    def create(self, user: User) -> None:
        """Создаёт нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO users 
                    (id, username, email, password_hash, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.id,
                    user.username,
                    user.email,
                    user.password_hash,
                    user.role.value,
                    user.created_at.isoformat(),
                    user.updated_at.isoformat()
                ))
                conn.commit()
                self._log_create(user.id, "User")
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise DatabaseError(f"Username '{user.username}' already exists")
            elif "email" in str(e):
                raise DatabaseError(f"Email '{user.email}' already exists")
            else:
                raise DatabaseError(f"User {user.id} already exists")
        except sqlite3.Error as e:
            self._log_error("create", user.id, str(e))
            raise DatabaseError(f"Failed to create user: {e}")
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Получает пользователя по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                
                if not row:
                    return None
                
                return self._row_to_user(row)
        except sqlite3.Error as e:
            self._log_error("get_by_id", user_id, str(e))
            raise DatabaseError(f"Failed to get user: {e}")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                
                if not row:
                    return None
                
                return self._row_to_user(row)
        except sqlite3.Error as e:
            self._log_error("get_by_email", email, str(e))
            raise DatabaseError(f"Failed to get user by email: {e}")
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Получает пользователя по username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                
                if not row:
                    return None
                
                return self._row_to_user(row)
        except sqlite3.Error as e:
            self._log_error("get_by_username", username, str(e))
            raise DatabaseError(f"Failed to get user by username: {e}")
    
    def update(self, user: User) -> None:
        """Обновляет пользователя"""
        try:
            existing = self.get_by_id(user.id)
            if not existing:
                raise DatabaseError(f"User {user.id} not found")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE users 
                    SET username = ?, email = ?, password_hash = ?, role = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    user.username,
                    user.email,
                    user.password_hash,
                    user.role.value,
                    user.updated_at.isoformat(),
                    user.id
                ))
                conn.commit()
                self._log_update(user.id, "User")
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise DatabaseError(f"Username '{user.username}' already exists")
            elif "email" in str(e):
                raise DatabaseError(f"Email '{user.email}' already exists")
            raise
        except sqlite3.Error as e:
            self._log_error("update", user.id, str(e))
            raise DatabaseError(f"Failed to update user: {e}")
    
    def get_all(self, limit: int = 50, offset: int = 0) -> List[User]:
        """Получает всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    'SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (limit, offset)
                ).fetchall()
                
                return [self._row_to_user(row) for row in rows]
        except sqlite3.Error as e:
            self._log_error("get_all", "", str(e))
            raise DatabaseError(f"Failed to get users: {e}")
    
    def delete(self, user_id: str) -> None:
        """Удаляет пользователя"""
        try:
            existing = self.get_by_id(user_id)
            if not existing:
                raise DatabaseError(f"User {user_id} not found")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                self._log_delete(user_id, "User")
        except sqlite3.Error as e:
            self._log_error("delete", user_id, str(e))
            raise DatabaseError(f"Failed to delete user: {e}")
    
    @staticmethod
    def _row_to_user(row) -> User:
        """Преобразует строку SQLite в Entity User"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=UserRole(row['role']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow(),
        )