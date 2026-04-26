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
    """Обработка загруженного видео"""
    if 'video' not in request.files:
        logger.error("Видео файл не найден в запросе")
        return jsonify({'error': 'Видео файл не найден'}), 400
    
    video = request.files['video']
    if video.filename == '':
        logger.error("Файл не выбран")
        return jsonify({'error': 'Файл не выбран'}), 400
    
    video_path = os.path.join('temp', str(video.filename))
    os.makedirs('temp', exist_ok=True)
    video.save(video_path)
    logger.info(f"Видео сохранено: {video_path}")
    
    try:
        logger.info(f"Начало обработки видео: {video.filename}")
        result = service.generate_instruction(video_path)
        logger.info(f"Обработка завершена успешно")
        logger.debug(f"Результат: {result[:200]}..." if len(str(result)) > 200 else f"Результат: {result}")
        
        return jsonify({
            'success': True,
            'instruction': result,
            'video_path': video.filename
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при обработке видео: {str(e)}", exc_info=True)
        return jsonify({'error': f'Ошибка при обработке: {str(e)}'}), 500
