# src/services/file_management_service.py

import os
import shutil
import logging
from typing import List, Optional
from src.config import AppConfig

logger = logging.getLogger(__name__)


class FileManagementService:
    """Сервис для управления файлами задач (перемещение из temp в result)"""
    
    @staticmethod
    def move_completed_task_files(task_id: str, document_names: Optional[List[str]] = None, used_image_ids: Optional[List[str]] = None) -> bool:
        """
        Переносит результаты завершённой задачи из temp в result.
        
        В result переносится:
        - Видео
        - Документы (только те, что были в исходной задаче)
        - Используемые картинки (в подпапку images/)
        
        В temp остаётся:
        - Неиспользуемые картинки
        - Готовые инструкции
        
        Args:
            task_id: ID задачи
            document_names: Список имён документов из исходной задачи
            used_image_ids: Список ID используемых картинок (по имени файла)
        
        Returns:
            True если перенос успешен, False если ошибка
        """
        try:
            source_dir = os.path.join(AppConfig.TEMP_DIR, task_id)
            dest_dir = os.path.join(AppConfig.RESULT_DIR, task_id)
            images_dest_dir = os.path.join(dest_dir, 'images')
            
            # Проверяем, существует ли исходная директория
            if not os.path.exists(source_dir):
                logger.warning(f"[{task_id}] Исходная директория не найдена: {source_dir}")
                return False
            
            # Создаём директории результата
            os.makedirs(dest_dir, exist_ok=True)
            os.makedirs(images_dest_dir, exist_ok=True)
            
            # Получаем список всех файлов в исходной директории
            all_files = os.listdir(source_dir)
            
            # Переносим видео
            for filename in all_files:
                # Пропускаем директории
                if os.path.isdir(os.path.join(source_dir, filename)):
                    continue
                
                # Видеофайлы (расширения mp4, avi, mov, mkv, webm)
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    src_path = os.path.join(source_dir, filename)
                    dest_path = os.path.join(dest_dir, filename)
                    try:
                        shutil.move(src_path, dest_path)
                        logger.info(f"[{task_id}] Видео перенесено: {filename}")
                    except Exception as e:
                        logger.error(f"[{task_id}] Ошибка при переносе видео {filename}: {e}")
            
            # Переносим только документы из document_names (исходные документы задачи)
            if document_names:
                for doc_name in document_names:
                    src_path = os.path.join(source_dir, doc_name)
                    if os.path.exists(src_path):
                        dest_path = os.path.join(dest_dir, doc_name)
                        try:
                            shutil.move(src_path, dest_path)
                            logger.info(f"[{task_id}] Документ перенесён: {doc_name}")
                        except Exception as e:
                            logger.error(f"[{task_id}] Ошибка при переносе документа {doc_name}: {e}")
                    else:
                        logger.warning(f"[{task_id}] Документ не найден: {doc_name}")
            
            # Переносим используемые картинки в подпапку images/
            if used_image_ids:
                for image_id in used_image_ids:
                    src_path = os.path.join(source_dir, image_id)
                    if os.path.exists(src_path):
                        dest_path = os.path.join(images_dest_dir, image_id)
                        try:
                            shutil.move(src_path, dest_path)
                            logger.info(f"[{task_id}] Картинка перенесена: {image_id}")
                        except Exception as e:
                            logger.error(f"[{task_id}] Ошибка при переносе картинки {image_id}: {e}")
            
            logger.info(f"[{task_id}] Файлы успешно перенесены в result директорию")
            return True
            
        except Exception as e:
            logger.error(f"[{task_id}] Критическая ошибка при переносе файлов: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_task_file_path(task_id: str, filename: str, file_type: str = 'video') -> Optional[str]:
        """
        Получает полный путь к файлу задачи.
        
        Ищет сначала в result, потом в temp.
        Для картинок сначала ищет в result/images/, потом в temp.
        
        Args:
            task_id: ID задачи
            filename: Имя файла
            file_type: Тип файла ('video', 'document', 'image')
        
        Returns:
            Полный путь к файлу если найден, иначе None
        """
        # Для картинок проверяем подпапку images/
        if file_type == 'image':
            # Сначала ищем в result/images/ (завершённые задачи)
            result_path = os.path.join(AppConfig.RESULT_DIR, task_id, 'images', filename)
            if os.path.exists(result_path):
                logger.debug(f"[{task_id}] Картинка найдена в result/images/: {filename}")
                return result_path
            
            # Потом ищем в temp (обрабатываемые задачи)
            temp_path = os.path.join(AppConfig.TEMP_DIR, task_id, filename)
            if os.path.exists(temp_path):
                logger.debug(f"[{task_id}] Картинка найдена в temp/: {filename}")
                return temp_path
        else:
            # Для остального (видео, документы)
            # Сначала ищем в result (завершённые задачи)
            result_path = os.path.join(AppConfig.RESULT_DIR, task_id, filename)
            if os.path.exists(result_path):
                logger.debug(f"[{task_id}] Файл найден в result: {filename}")
                return result_path
            
            # Потом ищем в temp (обрабатываемые и новые задачи)
            temp_path = os.path.join(AppConfig.TEMP_DIR, task_id, filename)
            if os.path.exists(temp_path):
                logger.debug(f"[{task_id}] Файл найден в temp: {filename}")
                return temp_path
        
        logger.warning(f"[{task_id}] Файл не найден: {filename}")
        return None
