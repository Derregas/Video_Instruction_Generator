# src/main.py

import logging
import argparse
from typing import Optional
from .config import setup_logging
from .core.processor import InstructionProcessingService
from .modules.video_analyzer import get_video_scenes, align_data
from .modules.llm_processor import generate_formal_instruction

logger = logging.getLogger(__name__)

def main():
    # Парсинг аргументов командной строки: python main.py <video_path>
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", help="Путь к видео")
    args = parser.parse_args()
    # Настройка логирования
    setup_logging()
    # Инициализация сервиса обработки инструкций и обработка видео
    service = InstructionProcessingService()
    result = service.generate_instruction(args.video_path)
    print(result)
if __name__ == "__main__":
    result = main()
    print(result)