# flask_app/auth_routes.py

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from src.decorators import login_required_custom, admin_required
from flask_app.extensions import app_services

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==================================================
# AUTH PAGES
# ==================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            
            # Валидация
            if not username or not email or not password:
                flash('Все поля обязательны', 'error')
                return redirect(url_for('auth.register'))
            
            if len(password) < 6:
                flash('Пароль должен быть не менее 6 символов', 'error')
                return redirect(url_for('auth.register'))
            
            if password != password_confirm:
                flash('Пароли не совпадают', 'error')
                return redirect(url_for('auth.register'))
            
            # Регистрируем пользователя
            success, user, message = app_services.auth_service.register_user(
                username=username,
                email=email,
                password=password
            )
            
            if success:
                flash('Регистрация успешна! Теперь войдите.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash(f'Ошибка: {message}', 'error')
                return redirect(url_for('auth.register'))
        
        except Exception as e:
            logger.error(f"Ошибка при регистрации: {e}", exc_info=True)
            flash('Ошибка при регистрации', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html.j2')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email и пароль обязательны', 'error')
                return redirect(url_for('auth.login'))
            
            # Аутентифицируем пользователя
            success, user, message = app_services.auth_service.authenticate_user(
                email=email,
                password=password
            )
            
            if success:
                login_user(user)
                logger.info(f"Пользователь вошёл: {user.username}")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.index'))
            else:
                flash(f'Ошибка: {message}', 'error')
                return redirect(url_for('auth.login'))
        
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}", exc_info=True)
            flash('Ошибка при входе', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html.j2')

@auth_bp.route('/logout', methods=['GET'])
@login_required_custom
def logout():
    """Выход из системы"""
    username = current_user.username
    logout_user()
    logger.info(f"Пользователь вышел: {username}")
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required_custom
def profile():
    """Страница профиля пользователя"""
    return render_template('auth/profile.html.j2', user=current_user)

# ==================================================
# ADMIN ROUTES
# ==================================================

@auth_bp.route('/users')
@admin_required
def list_users():
    """Список всех пользователей, кроме текущего (только для админа)"""
    try:
        users = app_services.user_service.get_all_users()
        # Исключаем текущего администратора из списка
        users = [u for u in users if u.id != current_user.id]
        return render_template('auth/users_list.html.j2', users=users)
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        flash('Ошибка при получении списка пользователей', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/users/<user_id>/role', methods=['POST'])
@admin_required
def update_user_role(user_id: str):
    """Обновить роль пользователя (только для админа). Админ не может менять свою роль"""
    try:
        # Администратор не может менять свою роль
        if user_id == current_user.id:
            flash('Вы не можете менять собственную роль', 'error')
            return redirect(url_for('auth.list_users'))
        
        new_role_str = request.form.get('role', '').strip()
        
        from src.domain.entities import UserRole
        
        try:
            new_role = UserRole(new_role_str)
        except ValueError:
            flash('Неверная роль', 'error')
            return redirect(url_for('auth.list_users'))
        
        user = app_services.user_service.update_user_role(user_id, new_role)
        logger.info(f"Роль пользователя {user.username} обновлена на {new_role.value}")
        flash(f'Роль пользователя обновлена на {new_role.value}', 'success')
        return redirect(url_for('auth.list_users'))
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении роли пользователя: {e}", exc_info=True)
        flash('Ошибка при обновлении роли пользователя', 'error')
        return redirect(url_for('auth.list_users'))

@auth_bp.route('/users/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id: str):
    """Удалить пользователя (только для админа)"""
    try:
        if user_id == current_user.id:
            flash('Вы не можете удалить свой аккаунт', 'error')
            return redirect(url_for('auth.list_users'))
        
        user = app_services.user_service.get_user(user_id)
        if not user:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('auth.list_users'))
        
        app_services.user_service.delete_user(user_id)
        logger.info(f"Пользователь удален: {user.username}")
        flash(f'Пользователь {user.username} удален', 'success')
        return redirect(url_for('auth.list_users'))
    
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя: {e}", exc_info=True)
        flash('Ошибка при удалении пользователя', 'error')
        return redirect(url_for('auth.list_users'))
