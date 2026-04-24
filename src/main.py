# src/main.py

"""
Главная точка входа приложения.

Использование:
    python run.py <путь_к_видео>
    python run.py video.mp4
"""

import logging
import argparse
import json
from pathlib import Path
from typing import Optional

from src.config import get_config, setup_logging
from src.exceptions import ProcessingError, ValidationError, AudioProcessingError
from src import InstructionProcessingService

logger = logging.getLogger(__name__)


def parse_arguments():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Video Instruction Generator - преобразование видео в инструкции",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run.py video.mp4                          # базовая обработка
  python run.py video.mp4 --model large-v3         # более точная модель
  python run.py video.mp4 --device cpu             # на CPU
  python run.py video.mp4 --output results.json    # сохранить результат
        """
    )
    
    parser.add_argument(
        "video_path",
        help="Путь к видеофайлу для обработки"
    )
    
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        default=None,
        help="Размер модели Whisper (по умолчанию: значение из .env)"
    )
    
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        default=None,
        help="Устройство для обработки (по умолчанию: значение из .env)"
    )
    
    parser.add_argument(
        "--language",
        default=None,
        help="Язык транскрипции (например: en, ru, fr). По умолчанию: auto-detect"
    )
    
    parser.add_argument(
        "--output",
        default=None,
        help="Путь для сохранения результата в JSON"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Не удалять временные файлы"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Режим debug (подробное логирование)"
    )
    
    return parser.parse_args()


def save_result(result: dict, output_path: str) -> None:
    """Сохраняет результат обработки в JSON файл."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Результат сохранён в {output_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении результата: {e}")
        raise


def print_result(result: dict) -> None:
    """Красиво выводит результат обработки."""
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ТРАНСКРИПЦИИ")
    print("="*60)
    
    print(f"\nВидеофайл: {result.get('video_file')}")
    print(f"Язык: {result.get('language')}")
    print(f"Уверенность: {result.get('confidence'):.1%}")
    
    transcript = result.get('transcript', [])
    print(f"\nВсего сегментов: {len(transcript)}")
    print("\n" + "-"*60)
    
    for i, segment in enumerate(transcript, 1):
        start = segment.get('start')
        end = segment.get('end')
        text = segment.get('text')
        print(f"\n[{i}] {start:.1f}s - {end:.1f}s")
        print(f"    {text}")
    
    print("\n" + "="*60)


def main() -> Optional[dict]:
    """
    Главная функция приложения.
    
    Returns:
        Словарь с результатами обработки или None в случае ошибки
    """
    try:
        # Парсинг аргументов
        args = parse_arguments()
        
        # Загрузка конфигурации
        config = get_config()
        
        # Переопределить debug режим если указан в CLI
        if args.debug:
            config.debug = True
            config.logging.level = "DEBUG"
        
        # Инициализация логирования
        setup_logging(config)
        logger.info("Приложение запущено")
        logger.debug(f"Конфигурация: {config}")
        
        # Валидация видеофайла
        video_path = args.video_path
        if not Path(video_path).exists():
            raise ValidationError(f"Видеофайл не найден: {video_path}")
        
        # Создание сервиса
        logger.info("Инициализация сервиса обработки...")
        service = InstructionProcessingService(
            model_size=args.model,
            device=args.device,
            use_config=True
        )
        
        # Обработка видео
        logger.info(f"Начало обработки видео: {video_path}")
        result = service.process_video(
            video_path,
            cleanup=not args.no_cleanup
        )
        
        # Вывод результатов
        print_result(result)
        
        # Сохранение результата если указан путь
        if args.output:
            save_result(result, args.output)
        
        logger.info("Обработка завершена успешно")
        return result
    
    except ValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        print(f"\n❌ Ошибка валидации: {e}")
        return None
    
    except AudioProcessingError as e:
        logger.error(f"Ошибка обработки аудио: {e}")
        print(f"\n❌ Ошибка обработки аудио: {e}")
        return None
    
    except ProcessingError as e:
        logger.error(f"Ошибка обработки: {e}")
        print(f"\n❌ Ошибка обработки: {e}")
        return None
    
    except KeyboardInterrupt:
        logger.warning("Обработка прервана пользователем")
        print("\n⚠️ Обработка отменена")
        return None
    
    except Exception as e:
        logger.exception(f"Непредвиденная ошибка: {e}")
        print(f"\n❌ Непредвиденная ошибка: {e}")
        return None


if __name__ == "__main__":
    result = main()