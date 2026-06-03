# flask_app/routes.py
import os
import logging
from src.config import AppConfig
from flask_app.extensions import app_services # Переменная для работы с бд и очередью задач
from flask import Blueprint, render_template, request, jsonify, redirect, send_file, flash
from flask_login import current_user, login_required
from src.services.use_cases import (
    CreateTaskRequest,
    GenerateInstructionRequest,
)
from src.decorators import login_required_custom, can_manage_tasks
from src.domain.exceptions import DatabaseError
from src.services.file_management_service import FileManagementService

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# ==================================================
# СТРАНИЦЫ
# ==================================================

@main_bp.route('/')
@main_bp.route('/home')
def index():
    """Главная страница со списком всех задач"""
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    
    try:
        # Все пользователи видят все задачи
        tasks = app_services.task_repo.get_all()
        # Получаем информацию о пользователях для отображения в таблице
        users = app_services.user_repo.get_all()
        users_dict = {u.id: u.username for u in users}
        
        # Получаем названия инструкций и ключевые слова из БД
        instructions_dict = {}
        keywords_dict = {}
        for task in tasks:
            try:
                instruction_data = app_services.instruction_result_service.get_instruction_by_task_id(task.id)
                if instruction_data and isinstance(instruction_data, dict) and 'instruction' in instruction_data:
                    instruction = instruction_data.get('instruction')
                    if instruction and hasattr(instruction, 'title') and instruction.title:
                        instructions_dict[task.id] = instruction.title
                    else:
                        # Если нет title, используем название видео
                        instructions_dict[task.id] = task.video_filename
                    
                    # Получаем ключевые слова
                    keywords_list = instruction_data.get('keywords', [])
                    if keywords_list:
                        keywords_dict[task.id] = keywords_list.keywords_list
                    # if keywords_list.keywords_list:
                    #     keywords_dict[task.id] = [kw.word for kw in keywords_list if hasattr(kw, 'word')]
                    else:
                        keywords_dict[task.id] = []
                else:
                    # Если инструкции нет, используем название видео
                    instructions_dict[task.id] = task.video_filename
                    keywords_dict[task.id] = []
            except Exception:
                # Если ошибка при получении инструкции, используем название видео
                instructions_dict[task.id] = task.video_filename
                keywords_dict[task.id] = []
        
        return render_template('tasks_list.html.j2', tasks=tasks, users_dict=users_dict, instructions_dict=instructions_dict, keywords_dict=keywords_dict)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка задач: {e}")
        return render_template('tasks_list.html.j2', tasks=[], users_dict={}, instructions_dict={}, error="Ошибка при загрузке задач"), 500  

@main_bp.route('/task')
@can_manage_tasks
def new_task():
    """Пустая форма загрузки видео. Только для пользователей с правом управления задачами"""
    return render_template('task.html.j2', task_id=None, task=None)

@main_bp.route('/task/<task_id>')
@login_required_custom
def task(task_id: str):
    """
    Страница задачи с результатами обработки
    """
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            logger.warning(f"Задача {task_id} не найдена")
            return jsonify({'error': 'Указанная задача не найдена'}), 400
        
        # Получаем структурированные данные инструкции из новой БД
        instruction_data = app_services.instruction_result_service.get_instruction_by_task_id(task_id)
        
        return render_template('task.html.j2', task_id=task_id, task=task, instruction=instruction_data)
    except Exception as e:
        logger.error(f"Ошибка при загрузке задачи {task_id}: {e}")
        return jsonify({'error': 'Ошибка при загрузке задачи'}), 500
    
# ==================================================
# API
# ==================================================

@main_bp.route('/api/process', methods=['POST'])
@can_manage_tasks
def process_video():
    """Обработка загруженного видео с опциональными документами"""
    try:
        # Получаем файлы из request (могут быть None)
        video = request.files.get('video')
        documents = request.files.getlist('documents') if 'documents' in request.files else None
        
        # Получаем user_id из текущего пользователя
        user_id = current_user.id
        
        # Создаём request для use case
        create_task_request = CreateTaskRequest(
            video=video, # type: ignore проверка осуществляется внутри сервиса
            documents=documents,
            user_id=user_id
        )
        
        # Выполняем use case (валидация происходит здесь)
        use_case = app_services.create_task_use_case
        response = use_case.execute(create_task_request)
        # *routes -> create_task_use_case -> task_creation_service -> task_queue -> task_processor -> processor
        #                                                 ↓  -> ->  ->  task.db ->   ->  ->  ↑

        # Перенаправляем пользователя незаметно
        logger.info(f"Задача {response.task_id} успешно создана пользователем {current_user.username}")
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
@login_required_custom
def get_task_status(task_id: str):
    """Возвращает текущий статус задачи для polling из JS"""
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        # Выполняем use case для получения статуса
        use_case = app_services.get_task_status_use_case
        response = use_case.execute(task_id)
        
        logger.debug(f"[{task_id}] Статус получен: {response.status}")
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Ошибка при получении статуса задачи {task_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка при получении статуса'}), 500


@main_bp.route('/api/task/<task_id>/video', methods=['GET'])
@login_required_custom
def get_task_video(task_id: str):
    """Отдаёт видеофайл задачи для воспроизведения на странице /<task_id>"""
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        # Ищем видео в result (если задача завершена) или в temp (если обрабатывается)
        video_path = FileManagementService.get_task_file_path(task_id, task.video_filename)
        
        if not video_path or not os.path.exists(video_path):
            logger.warning(f"Видеофайл не найден: {task.video_filename} для задачи {task_id}")
            return jsonify({'error': 'Видеофайл не найден'}), 404

        logger.debug(f"[{task_id}] Отправка видеофайла")
        return send_file(video_path, mimetype='video/mp4')
    except Exception as e:
        logger.error(f"Ошибка при отправке видео {task_id}: {e}", exc_info=True)
        return jsonify({'error': 'Ошибка при отправке видеофайла'}), 500

@main_bp.route('/api/task/<task_id>/instruction', methods=['GET'])
@login_required_custom
def get_task_instruction(task_id: str):
    """Отдаёт готовую сформированную инструкцию в формате docx"""
    try:
        task = app_services.task_repo.get_by_id(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404

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

@main_bp.route('/api/instruction/<instruction_id>', methods=['GET'])
@login_required_custom
def get_instruction_data(instruction_id: str):
    """Возвращает данные инструкции для редактора"""
    try:
        data = app_services.instruction_result_service.get_instruction_with_steps(instruction_id)
        if not data:
            return jsonify({'error': 'Инструкция не найдена'}), 404
        
        # Преобразуем объекты в словари для JSON
        return jsonify({
            'instruction': {
                'id': data['instruction'].id,
                'title': data['instruction'].title,
                'description': data['instruction'].description,
            },
            'keywords': data['keywords'].keywords_list if data['keywords'] else [],
            'steps': [
                {
                    'id': s.id,
                    'title': s.title,
                    'text': s.text,
                    'time_start': s.time_start,
                    'time_end': s.time_end,
                    'image_id': s.image_id
                } for s in data['steps']
            ]
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при получении данных инструкции {instruction_id}: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500

@main_bp.route('/api/instruction/<instruction_id>/save', methods=['POST'])
@can_manage_tasks
def save_instruction(instruction_id: str):
    """Сохраняет отредактированную инструкцию"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных для сохранения'}), 400
        
        app_services.instruction_result_service.update_instruction_full(instruction_id, data)
        
        return jsonify({'status': 'success', 'message': 'Инструкция успешно сохранена'}), 200
    except DatabaseError as e:
        logger.error(f"Ошибка БД при сохранении инструкции {instruction_id}: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Ошибка при сохранении инструкции {instruction_id}: {e}", exc_info=True)
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500