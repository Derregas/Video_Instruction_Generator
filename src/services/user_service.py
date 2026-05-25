# src/services/user_service.py

import logging
import uuid
from typing import Optional
from src.domain.entities import User, UserRole
from src.domain.repositories import IUserRepository
from src.domain.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class UserService:
    """
    Сервис для работы с пользователями.
    
    Предоставляет методы для:
    - Получения данных пользователя
    - Обновления ролей пользователей
    - Управления пользователями
    
    Примечание: Для аутентификации и регистрации используйте AuthService
    """
    
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    def generate_user_id(self) -> str:
        """Генерирует уникальный ID пользователя"""
        return str(uuid.uuid4())
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Получает пользователя по ID"""
        try:
            return self.user_repo.get_by_id(user_id)
        except DatabaseError as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email"""
        try:
            return self.user_repo.get_by_email(email)
        except DatabaseError as e:
            logger.error(f"Ошибка при получении пользователя с email {email}: {e}")
            raise
    
    def update_user_role(self, user_id: str, new_role: UserRole) -> User:
        """
        Обновляет роль пользователя
        
        Args:
            user_id: ID пользователя
            new_role: Новая роль
        
        Returns:
            Обновленный объект User
        
        Raises:
            DatabaseError: Если пользователь не найден
        """
        user = self.get_user(user_id)
        if not user:
            raise DatabaseError(f"Пользователь {user_id} не найден")
        
        user.role = new_role
        try:
            self.user_repo.update(user)
            logger.info(f"Роль пользователя {user_id} обновлена на {new_role.value}")
            return user
        except DatabaseError as e:
            logger.error(f"Ошибка при обновлении роли пользователя {user_id}: {e}")
            raise
    
    def get_all_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        """Получает всех пользователей с пагинацией"""
        try:
            return self.user_repo.get_all(limit=limit, offset=offset)
        except DatabaseError as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            raise
    
    def delete_user(self, user_id: str) -> None:
        """
        Удаляет пользователя
        
        Args:
            user_id: ID пользователя
        
        Raises:
            DatabaseError: Если пользователь не найден
        """
        user = self.get_user(user_id)
        if not user:
            raise DatabaseError(f"Пользователь {user_id} не найден")
        
        try:
            self.user_repo.delete(user_id)
            logger.info(f"Пользователь удален: {user_id}")
        except DatabaseError as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            raise
