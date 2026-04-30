from flask import Blueprint, render_template, request, jsonify
import os
import logging
from src.core.processor import InstructionProcessingService

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)
service = InstructionProcessingService()

@main_bp.route('/')
def index():
    return render_template('index.html')

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
    
    # Сохраняем видео
    video_path = os.path.join('temp', str(video.filename))
    os.makedirs('temp', exist_ok=True)
    video.save(video_path)
    logger.info(f"Видео сохранено: {video_path}")
    
    # Обрабатываем документы если они есть
    document_paths = None
    if 'documents' in request.files:
        docs = request.files.getlist('documents')
        
        # Валидация: максимум 5 файлов
        if len(docs) > 5:
            logger.error(f"Превышено максимальное количество файлов: {len(docs)}")
            return jsonify({'error': 'Максимум 5 файлов'}), 400
        
        # Валидация: общий размер не более 30МБ
        total_size = 0
        for doc in docs:
            # Получаем размер файла
            doc.seek(0, os.SEEK_END)
            size = doc.tell()
            doc.seek(0)
            total_size += size
        
        max_size_bytes = 30 * 1024 * 1024  # 30МБ
        if total_size > max_size_bytes:
            logger.error(f"Общий размер документов превышает лимит: {total_size} > {max_size_bytes}")
            return jsonify({'error': 'Общий размер документов превышает 30МБ'}), 400
        
        # Сохраняем документы
        document_paths = []
        for doc in docs:
            doc_path = os.path.join('temp', f"doc_{doc.filename}")
            doc.save(doc_path)
            document_paths.append(doc_path)
            logger.info(f"Документ сохранен: {doc_path}")
    
    try:
        logger.info(f"Начало обработки видео: {video.filename} с документами: {len(document_paths) if document_paths else 0}")
        result = service.generate_instruction(video_path, documents=document_paths)
        logger.info(f"Обработка завершена успешно")
        logger.debug(f"Результат: {result[:200]}..." if len(str(result)) > 200 else f"Результат: {result}")
        
        return jsonify({
            'success': True,
            'instruction': result,
            'video_path': video.filename,
            'documents_count': len(document_paths) if document_paths else 0
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при обработке видео: {str(e)}", exc_info=True)
        return jsonify({'error': f'Ошибка при обработке: {str(e)}'}), 500
