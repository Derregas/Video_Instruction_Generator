# flask_app/routes.py
import os
import uuid
import logging
import threading
from src.config import AppConfig
from src.models import TaskManager, TaskStatus
from flask_app.utils import docs_size, docs_save
from src.core.processor import InstructionProcessingService
from flask import Blueprint, render_template, request, jsonify, redirect, send_file

task_manager = TaskManager()
logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)
service = InstructionProcessingService()

@main_bp.route('/')
@main_bp.route('/<task_id>')
def index(task_id=None):
    """
    Одинаковый шаблон для:
      - '/'  → пустая форма загрузки (task_id=None)
      - '/<task_id>' → страница статуса задачи
    """
    task = None
    if task_id:
        task = task_manager.get_task(task_id)
    return render_template('index.html.j2', task_id=task_id, task=task)

@main_bp.route('/api/process', methods=['POST'])
def process_video():
    """Обработка загруженного видео с опциональными документами"""
    if 'video' not in request.files:
        logger.error("Видео файл не найден в запросе")
        return jsonify({'error': 'Видео файл не найден'}), 400
    
    video = request.files['video']
    if video.filename == '':
        logger.error("Файл видео не выбран")
        return jsonify({'error': 'Файл видео не выбран'}), 400
    
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
    
    # Записываем задачу в БД
    task_manager.create_task(task_id, video.filename, document_names)
    task_manager.update_task(task_id, status=TaskStatus.PROCESSING.value)
    
    # Запускаем обработку в фоне
    thread = threading.Thread(
        target=_process_task_async,
        args=(task_id, video_path, document_paths),
        daemon=True
    )
    thread.start()

    # Перенаправляем пользователя незаметно
    return redirect(f'/{task_id}', code=303)

# Периодический опрос статуса задачи
@main_bp.route('/api/task/<task_id>')
def get_task_status(task_id):
    """Возвращает текущий статус задачи для polling из JS"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Задача не найдена'}), 404

    response = {
        'task_id': task['id'],
        'status': task['status'],
        'video_filename': task['video_filename'],
        'created_at': task['created_at'],
    }

    if task['status'] == TaskStatus.COMPLETED.value:
        response['result'] = task['result']
    elif task['status'] == TaskStatus.FAILED.value:
        response['error'] = task['error_message']

    return jsonify(response)

def _process_task_async(task_id, video_path, document_paths):
    """Выполняется в отдельном потоке: обрабатывает видео и записывает результат"""
    try:
        logger.info(f"[{task_id}] Начало обработки видео")
        result = service.generate_instruction(video_path, documents=document_paths, task_id=task_id)
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED.value, result=result)
        logger.info(f"[{task_id}] Обработка завершена успешно")
    except Exception as e:
        logger.error(f"[{task_id}] Ошибка: {str(e)}", exc_info=True)
        task_manager.update_task(task_id, status=TaskStatus.FAILED.value, error_message=str(e))

@main_bp.route('/api/task/<task_id>/video')
def get_task_video(task_id):
    """Отдаёт видеофайл задачи для воспроизведения на странице /<task_id>"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    video_path = os.path.join(AppConfig.TEMP_DIR, task_id, task['video_filename'])
    if os.path.exists(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return jsonify({'error': 'Video file not found'}), 404

@main_bp.route('/api/task/<task_id>/instruction')
def get_task_instruction(task_id):
    """Отдаёт готовую свормированную инструкцию в формате docx"""
    # Заглушка
    return jsonify({'error': 'Instruction file not found'}), 204