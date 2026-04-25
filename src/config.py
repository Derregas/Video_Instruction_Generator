# src/config.py

import os
import logging
from dotenv import load_dotenv
from dataclasses import dataclass

# Загружаем переменные окружения из .env файла
load_dotenv()  

@dataclass
class LLMSettings:
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL: str = os.getenv("LLM_MODEL", "gemma4:e4b")
    CONTEXT_SIZE: int = int(os.getenv("LLM_CONTEXT_SIZE", "16384"))
    USE_LAST_DATA: bool = os.getenv("USE_LAST_DATA", "false").lower() == "true"
    LAST_DATA_FILE_NAME: str = os.getenv("LAST_DATA_FILE_NAME", "last_data.txt")
    
    # Промпт лучше вынести в txt
    SYSTEM_PROMPT: str = (
        """Твоя задача: превратить лог транскрипции в чёткую техническую инструкцию.
        ПРАВИЛА:
        1. Игнорируй мусор (приветствия, 'Здарова всем', обзоры цен).
        2. Объединяй связанные короткие фразы в один логический шаг.
        3. Для каждого шага укажи:
        - 'title': краткое название действия.
        - 'description': подробная и четкая инструкция в повелительном наклонении.
        - 'start_time' и 'end_time': охват времени из исходных данных. Ты должен объеденить время фрагментов которые объеденил в один шаг. Если ты объеденил 10 фрагментов, то бери время начало самого первого и время окончания самого последнего.
        - 'best_image_id': ID самого важного фрагмента для этого шага. Возьми это изображение из самого подходящего по смыслу отрывка, котоые ты объеденил в один шаг.
        """ 
    )

@dataclass
class AudioSettings:
    MODEL_SIZE: str = os.getenv("WHISPER_MODEL", "base")
    DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    COMPUTE_TYPE: str = "float16" if DEVICE == "cuda" else "int8"

class AppConfig:
    LLM = LLMSettings()
    AUDIO = AudioSettings()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMP_DIR = os.path.join(BASE_DIR, "temp")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
        filename='generator.log',
        filemode='w',
        encoding='utf-8'
    )