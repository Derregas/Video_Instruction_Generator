# flask_app/routes.py
import os
import logging
from src.config import AppConfig
from flask_app.extensions import app_services # Переменная для работы с бд и очередью задач
from flask import Blueprint, render_template, request, jsonify, redirect, send_file
from src.services.use_cases import (
    CreateTaskRequest,
    GenerateInstructionRequest,
)

from src.domain.exceptions import DatabaseError

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# ==================================================
# СТРАНИЦЫ
# ==================================================

@main_bp.route('/')
@main_bp.route('/home')
def index():
    """Главная страница со списком всех задач"""
    try:
        tasks = app_services.task_repo.get_all()
        return render_template('tasks_list.html.j2', tasks=tasks)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка задач: {e}")
        return render_template('tasks_list.html.j2', tasks=[], error="Ошибка при загрузке задач"), 500  

@main_bp.route('/task')
def new_task():
    """Пустая форма загрузки видео"""
    return render_template('task.html.j2', task_id=None, task=None)

@main_bp.route('/task/<task_id>')
def task(task_id: str):
    """
    Страница задачи с результатами обработки
    """
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            logger.warning(f"Задача {task_id} не найдена")
            return jsonify({'error': 'Указанная задача не найдена'}), 400
        return render_template('task.html.j2', task_id=task_id, task=task)
    except Exception as e:
        logger.error(f"Ошибка при загрузке задачи {task_id}: {e}")
        return jsonify({'error': 'Ошибка при загрузке задачи'}), 500
    
# ==================================================
# API
# ==================================================

@main_bp.route('/api/process', methods=['POST'])
def process_video():
    """Обработка загруженного видео с опциональными документами"""
    try:
        # Получаем файлы из request (могут быть None)
        video = request.files.get('video')
        documents = request.files.getlist('documents') if 'documents' in request.files else None
        
        # Создаём request для use case
        create_task_request = CreateTaskRequest(
            video=video, # type: ignore проверка осуществляется внутри сервиса
            documents=documents
        )
        
        # Выполняем use case (валидация происходит здесь)
        use_case = app_services.create_task_use_case
        response = use_case.execute(create_task_request)

        # Перенаправляем пользователя незаметно
        logger.info(f"Задача {response.task_id} успешно создана")
        return redirect(f'/task/{response.task_id}', code=303)
    
    except ValueError as e:
        logger.warning(f"Ошибка валидации: {e}")
        return jsonify({'error': str(e)}), 400
    except DatabaseError as e:
        logger.error(f"Ошибка БД: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.critical(f"Неожиданная ошибка: {e}", exc_info=True)
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Периодический опрос статуса задачи
@main_bp.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """Возвращает текущий статус задачи для polling из JS"""
    try:
        # Выполняем use case для получения статуса
        use_case = app_services.get_task_status_use_case
        response = use_case.execute(task_id)
        
        logger.debug(f"[{task_id}] Статус получен: {response.status}")
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Ошибка при получении статуса задачи {task_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка при получении статуса'}), 500


@main_bp.route('/api/task/<task_id>/video', methods=['GET'])
def get_task_video(task_id: str):
    """Отдаёт видеофайл задачи для воспроизведения на странице /<task_id>"""
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        video_path = os.path.join(AppConfig.TEMP_DIR, task_id, task.video_filename)
        if not os.path.exists(video_path):
            logger.warning(f"Видеофайл не найден: {video_path}")
            return jsonify({'error': 'Видеофайл не найден'}), 404

        logger.debug(f"[{task_id}] Отправка видеофайла")
        return send_file(video_path, mimetype='video/mp4')
    except Exception as e:
        logger.error(f"Ошибка при отправке видео {task_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка при отправке видеофайла'}), 500

@main_bp.route('/api/task/<task_id>/instruction', methods=['GET'])
def get_task_instruction(task_id: str):
    """Отдаёт готовую свормированную инструкцию в формате docx"""
    try:
        # Получаем формат из запроса. Если не указан, ставим 'pdf' по умолчанию
        doc_format = request.args.get('format', 'pdf').lower()

        # Создаём request для use case
        generate_request = GenerateInstructionRequest(
            task_id=task_id,
            format=doc_format  # type: ignore
        )
        
        # Выполняем use case
        use_case = app_services.generate_instruction_use_case
        response = use_case.execute(generate_request)
        
        logger.info(f"[{task_id}] Отправка инструкции в формате {doc_format}")
        # Определяем MIME тип в зависимости от формата
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }

        return send_file(
            response.filepath,
            as_attachment=True,
            download_name=response.filename,
            mimetype=mime_types.get(doc_format, 'application/octet-stream')
        )
    except ValueError as e:
        # Ошибки валидации (неподдерживаемый формат, задача не завершена и т.д.)
        logger.warning(f"Ошибка при генерации инструкции для {task_id}: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Ошибка при генерации инструкции для {task_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка при создании файла инструкции'}), 500