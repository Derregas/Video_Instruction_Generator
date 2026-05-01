# src/main.py

import logging
from .config import setup_logging
from .core.processor import InstructionProcessingService

logger = logging.getLogger(__name__)

def main(video_path, documents):
    # Парсинг аргументов командной строки: python main.py <video_path>
    # parser = argparse.ArgumentParser()
    # parser.add_argument("video_path", help="Путь к видео")
    # args = parser.parse_args()
    # Настройка логирования
    setup_logging()
    # Инициализация сервиса обработки инструкций и обработка видео
    service = InstructionProcessingService()
    result = service.generate_instruction(video_path, documents)
    print(result)
if __name__ == "__main__":
    result = main(
        r"D:\Projects\Video_instructions\СОБИРАЕМ ВМЕСТЕ САМЫЙ НАРОДНЫЙ ПК 2025 ГАЙД ПО СБОРКЕ [get.gt].mp4",
        [r"D:\D Загрузки\materinskaa-plata-gigabyte-b650m-d3hp_instrukcia_074339_05082025.pdf"]
        )
    print(result)