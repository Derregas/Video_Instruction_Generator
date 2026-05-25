# src/decorators.py

import logging
from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user
from src.domain.entities import UserRole

logger = logging.getLogger(__name__)

def login_required_custom(f):
    """Декоратор для проверки, что пользователь авторизован"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """
    Декоратор для проверки, что пользователь имеет нужную роль
    
    Args:
        required_role: UserRole, требуемая роль
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите в систему', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role != required_role and current_user.role != UserRole.ADMIN:
                logger.warning(f"Пользователь {current_user.username} попытался получить доступ к ресурсу требующему роль {required_role.value}")
                flash(f'Доступ запрещён. Требуется роль: {required_role.value}', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Декоратор для проверки, что пользователь - администратор"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != UserRole.ADMIN:
            logger.warning(f"Пользователь {current_user.username} попытался получить доступ к админ-ресурсу")
            flash('Доступ запрещён. Требуются права администратора', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def can_manage_tasks(f):
    """Декоратор для проверки, может ли пользователь управлять задачами"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in (UserRole.MANAGE, UserRole.ADMIN):
            logger.warning(f"Пользователь {current_user.username} попытался управлять задачей без прав")
            flash('Доступ запрещён. Требуются права на управление задачами', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function
