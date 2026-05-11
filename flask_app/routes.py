# flask_app/routes.py
import os
import uuid
import logging
import threading
from src.config import AppConfig
from flask_app.utils import docs_size, docs_save, DocumentCreator
from src.core.processor import InstructionProcessingService
from flask import Blueprint, render_template, request, jsonify, redirect, send_file, current_app
# БД
from src.domain.entities import Task, TaskStatus
from src.domain.repositories import ITaskRepository, IUserRepository
from src.infrastructure.persistence.sqlite_task_repository import SQLiteTaskRepository

from src.domain.exceptions import (
    DatabaseError, 
    TaskNotFoundError, 
    TaskAlreadyExistsError
    )

#task_manager = TaskManager()
logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)
service = InstructionProcessingService()
task_repository: ITaskRepository = SQLiteTaskRepository(db_path="tasks.db")
user_repository: IUserRepository # До делать

@main_bp.route('/')
@main_bp.route('/home')
def index():
    """Главная страница со списком всех задач"""
    tasks = task_repository.get_all()
    #tasks = task_manager.get_all_tasks(limit=50)
    return render_template('tasks_list.html.j2', tasks=tasks)

@main_bp.route('/task')
def new_task():
    """Пустая форма загрузки видео"""
    return render_template('task.html.j2', task_id=None, task=None)

@main_bp.route('/task/<task_id>')
def task(task_id=None):
    """
    Страница задачи с результатами обработки
    """
    task = None
    if task_id:
        task = task_repository.get_by_id(task_id)
        # task = task_manager.get_task(task_id)
        if not task:
            logger.error(f"Задача {task_id} не найдена")
            return jsonify({'error': 'Указанная задача не найдена'}), 400
    return render_template('task.html.j2', task_id=task_id, task=task)

@main_bp.route('/api/process', methods=['POST'])
def process_video():
    """Обработка загруженного видео с опциональными документами"""
    try:
        if 'video' not in request.files:
            logger.error("Видео файл не найден в запросе")
            return jsonify({'error': 'Видео файл не найден'}), 400
        
        video = request.files['video']
        if video.filename == '':
            logger.error("Файл видео не выбран")
            return jsonify({'error': 'Файл видео не выбран'}), 400
        
        task_repo = current_app.config['task_repo']
        task_queue = current_app.config['task_queue']

        # Создаём uuid
        task_id = str(uuid.uuid4())[:8]
        request_temp_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
        os.makedirs(request_temp_dir, exist_ok=True)
        # Сохраняем видео
        video_path = os.path.join(request_temp_dir, str(video.filename))
        video.save(video_path)
        logger.info(f"Видео сохранено: {video_path}")
        
        # Обрабатываем документы если они есть
        document_names = []
        document_paths = None
        if 'documents' in request.files:
            docs = request.files.getlist('documents')
            # Валидация: максимум 5 файлов
            if len(docs) > 5:
                logger.error(f"Превышено максимальное количество файлов: {len(docs)}")
                return jsonify({'error': 'Максимум 5 файлов'}), 400
            # Валидация: общий размер не более 30МБ
            total_size = docs_size(docs)
            max_size_bytes = 30 * 1024 * 1024  # 30МБ
            if total_size > max_size_bytes:
                logger.error(f"Общий размер документов превышает лимит: {total_size} > {max_size_bytes}")
                return jsonify({'error': 'Общий размер документов превышает 30МБ'}), 400
            
            # Сохраняем документы
            document_paths = docs_save(docs, request_temp_dir)
            document_names = [os.path.basename(p) for p in document_paths]
            logger.info(f"Сохраненены документы: {document_names}")
        
        # Создаём объект задачи
        new_task = Task(
            id=task_id,
            user_id="0",
            status=TaskStatus.PENDING,
            video_filename=video.filename, # type: ignore
            document_names=document_names
        )
        # Записываем задачу в БД и очередь
        task_repo.create(new_task)
        task_queue.enqueue(task_id)
        logger.info(f"Задача {task_id} добавлена в очередь обработки")
        # task_manager.create_task(task_id, video.filename, document_names)
        
        # Запускаем обработку в фоне
        # thread = threading.Thread(
        #     target=_process_task_async,
        #     args=(task_id, video_path, document_paths),
        #     daemon=True
        # )
        # thread.start()

        # Перенаправляем пользователя незаметно
        return redirect(f'/task/{task_id}', code=303)
    except TaskAlreadyExistsError:
        return jsonify({'error': 'Task already exists'}), 409
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500

# Периодический опрос статуса задачи
@main_bp.route('/api/task/<task_id>')
def get_task_status(task_id):
    """Возвращает текущий статус задачи для polling из JS"""
    try:
        task = task_repository.get_by_id(task_id)
        #task = task_manager.get_task(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404

        response = {
            'task_id': task.id,
            'status': task.status.value,
            'video_filename': task.video_filename,
            'created_at': task.created_at,
        }

        if task.status == TaskStatus.COMPLETED:
            response['result'] = task.result
        elif task.status == TaskStatus.FAILED:
            response['error'] = task.error_message
        return jsonify(response)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# def _process_task_async(task_id, video_path, document_paths):
#     """Выполняется в отдельном потоке: обрабатывает видео и записывает результат"""
#     task = None
#     try:
#         logger.info(f"[{task_id}] Начало обработки видео")
#         # Поучаем объект задачи
#         task = task_repository.get_by_id(task_id)
#         # Выводим ошибку, если пусто
#         if not task: 
#             raise TaskNotFoundError(f"Задача {task_id} не найдена в БД")
#         # Отмечаем, как обработка
#         task.mark_processing()
#         task_repository.update(task)
#         #task_manager.update_task(task_id, status=TaskStatus.PROCESSING.value)
#         result = service.generate_instruction(video_path, documents=document_paths, task_id=task_id)
#         # Отмечаем, как завершено
#         task.mark_completed(result)
#         task_repository.update(task)
#         logger.info(f"[{task_id}] Обработка завершена успешно")
#     except (TaskNotFoundError, DatabaseError) as e:
#         # Специфичные ошибки
#         logger.error(f"[{task_id}] Ошибка обработки: {str(e)}", exc_info=True)
#         _mark_task_failed(task_id, str(e))
#     except Exception as e:
#         logger.error(f"[{task_id}] Ошибка: {str(e)}", exc_info=True)
#         _mark_task_failed(task_id, str(e))

# def _mark_task_failed(task_id: str, error_message: str) -> bool:
#     """Безопасно отмечает задачу как ошибку"""
#     try:
#         task = task_repository.get_by_id(task_id)
#         if not task:
#             logger.error(f"[{task_id}] Не удалось найти задачу для обновления статуса")
#             return False
#         task.mark_failed(error_message)
#         task_repository.update(task)
#         logger.info(f"[{task_id}] Статус обновлен на FAILED")
#         return True
#     except DatabaseError as e:
#         logger.error(f"[{task_id}] Ошибка БД при обновлении статуса: {e}")
#         return False   
#     except Exception as e:
#         logger.critical(f"[{task_id}] Неожиданная ошибка при обновлении статуса: {e}", exc_info=True)
#         return False

@main_bp.route('/api/task/<task_id>/video')
def get_task_video(task_id):
    """Отдаёт видеофайл задачи для воспроизведения на странице /<task_id>"""
    task = task_repository.get_by_id(task_id)
    #task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    video_path = os.path.join(AppConfig.TEMP_DIR, task_id, task.video_filename)
    if os.path.exists(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return jsonify({'error': 'Video file not found'}), 404

@main_bp.route('/api/task/<task_id>/instruction')
def get_task_instruction(task_id):
    """Отдаёт готовую свормированную инструкцию в формате docx"""
    # Получаем формат из запроса. Если не указан, ставим 'pdf' по умолчанию
    doc_format = request.args.get('format', 'pdf').lower()

    task = task_repository.get_by_id(task_id)
    #task = task_manager.get_task(task_id)
    
    if not task:
        return jsonify({'error': 'Задача не найдена'}), 404
    
    if task.status.value != TaskStatus.COMPLETED.value:
        return jsonify({'error': 'Обработка еще не завершена'}), 102
    
    result = task.result
    if not result:
        return jsonify({'error': 'Получен пустой результат'}), 204
    
    # Путь, где будет лежать сгенерированный PDF
    fileName = f"instruction_{task_id}.{doc_format}"
    filePath = os.path.join(AppConfig.TEMP_DIR, task_id, fileName)

    try:
        DocumentCreator.create(result, filePath)
        # Отправляем файл пользователю
        return send_file(
            filePath,
            as_attachment=True,
            download_name=fileName,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Ошибка при генерации PDF: {e}")
        return jsonify({'error': 'Ошибка при создании файла инструкции'}), 500