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
    service = InstructionProcessingService(device="cuda", compute_type="float16", model_size="small")
    
    # Для теста
    result = service.process_video(args.video_path)
    print("Результат обработки видео:", result)
    scenes = get_video_scenes(args.video_path)
    print("Сцены в видео:", scenes)
    matchs = align_data(result, scenes, args.video_path)
    print("Сопоставление транскрипта с сценами:", matchs)
    formal_instruction = generate_formal_instruction(matchs)
    print("Сформированная инструкция:", formal_instruction)

if __name__ == "__main__":
    result = main()
    print(result)