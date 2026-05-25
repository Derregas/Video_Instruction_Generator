# src/services/auth_service.py

import logging
import uuid
from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from src.domain.entities import User, UserRole
from src.domain.repositories import IUserRepository
from src.domain.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class AuthService:
    """
    Сервис аутентификации и авторизации.
    
    Предоставляет методы для:
    - Регистрации новых пользователей (с хешированием пароля)
    - Проверки пароля
    - Получения пользователя по учётным данным
    - Проверки прав доступа
    """
    
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
    
    def generate_user_id(self) -> str:
        """Генерирует уникальный ID пользователя"""
        return str(uuid.uuid4())
    
    def hash_password(self, password: str) -> str:
        """
        Хеширует пароль
        
        Args:
            password: Открытый пароль
        
        Returns:
            Хешированный пароль
        """
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Проверяет пароль против хеша
        
        Args:
            password: Открытый пароль
            password_hash: Хеш пароля
        
        Returns:
            True если пароль верный, False иначе
        """
        return check_password_hash(password_hash, password)
    
    def register_user(self, 
                     username: str, 
                     email: str, 
                     password: str,
                     role: UserRole = UserRole.VIEW) -> Tuple[bool, Optional[User], str]:
        """
        Регистрирует нового пользователя
        
        Args:
            username: Имя пользователя
            email: Email пользователя
            password: Открытый пароль
            role: Роль пользователя (по умолчанию VIEW)
        
        Returns:
            Tuple[success: bool, user: User | None, message: str]
        """
        try:
            # Нормализуем email (приводим к нижнему регистру)
            email = email.lower().strip()
            
            # Проверяем, существует ли пользователь с таким email
            existing = self.user_repo.get_by_email(email)
            if existing:
                return False, None, f"Email '{email}' уже зарегистрирован"
            
            # Проверяем username
            existing = self.user_repo.get_by_username(username) if hasattr(self.user_repo, 'get_by_username') else None
            if existing:
                return False, None, f"Username '{username}' уже занят"
            
            # Создаём пользователя с хешированным паролем
            user = User(
                id=self.generate_user_id(),
                username=username,
                email=email,
                password_hash=self.hash_password(password),
                role=role
            )
            
            self.user_repo.create(user)
            logger.info(f"Пользователь зарегистрирован: {username} ({user.id})")
            return True, user, "Пользователь успешно зарегистрирован"
            
        except DatabaseError as e:
            logger.error(f"Ошибка при регистрации пользователя {username}: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при регистрации: {e}", exc_info=True)
            return False, None, "Ошибка при регистрации"
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Аутентифицирует пользователя по email и паролю
        
        Args:
            email: Email пользователя
            password: Открытый пароль
        
        Returns:
            Tuple[success: bool, user: User | None, message: str]
        """
        try:
            # Нормализуем email (приводим к нижнему регистру)
            email = email.lower().strip()
            user = self.user_repo.get_by_email(email)
            
            if not user:
                return False, None, "Пользователь не найден"
            
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Неверный пароль для {email}")
                return False, None, "Неверный пароль"
            
            logger.info(f"Пользователь вошёл: {email}")
            return True, user, "Успешно вошли"
            
        except Exception as e:
            logger.error(f"Ошибка при аутентификации {email}: {e}", exc_info=True)
            return False, None, "Ошибка при входе"
    
    def can_manage_tasks(self, user: User) -> bool:
        """Проверяет, может ли пользователь управлять задачами"""
        return user.role in (UserRole.MANAGE, UserRole.ADMIN)
    
    def can_view_tasks(self, user: User) -> bool:
        """Проверяет, может ли пользователь просматривать задачи"""
        return True  # Все аутентифицированные пользователи могут просматривать
    
    def can_manage_users(self, user: User) -> bool:
        """Проверяет, может ли пользователь управлять пользователями"""
        return user.role == UserRole.ADMIN
    
    def create_admin_user(self, 
                         username: str, 
                         email: str, 
                         password: str) -> Tuple[bool, Optional[User], str]:
        """
        Создаёт администратора (для инициализации)
        
        Args:
            username: Имя пользователя
            email: Email
            password: Пароль
        
        Returns:
            Tuple[success: bool, user: User | None, message: str]
        """
        logger.info(f"Создаём администратора: {username}")
        return self.register_user(username, email, password, role=UserRole.ADMIN)
