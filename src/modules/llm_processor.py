import os
import ollama
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

"""
# Немного об протестированных моделях

- llama-3.1:8b - Потербляет 6.4 Гб при окне контекста в 8к токенов. Этого окна 
слишком мало для составления инструкции. Она получется не точной и короткой.

- llama-3.2:3b - Потребляет значительно меньше 3.4 Гб на те же 8к токенов.
в ответе много аномалий, так как не поддерживает русский. Также не вы даёт JSON.

- qwen2.5:3b - 2.5 Гб памяти на 8к контекста. При 32К ест 4.5 Гб, 
но даже так ответы короткие и не полные.

- gemma3:4b - 4.6 ГБ на 16к токенов. Показала себя лучше всего в плане ответов.
JSON точный. Слишком часто игнорирует инструкцию. При низкой температуре и top_p
зацикливается, При низкой температуре и при высоком top_p ответы не точные и 
повторяют предыдущие

- gemma4:e4b - сама модель весит 9Гб, в памяти при размере контекста 8к и 16к
потребляет 10Гб. Не смотря на то, что на половину рамзещана в оперативной 
памяти работает достаточно быстро. Даёт самый нормальный ответ, даже на 
стандартных настройках. 8К контекста не хватает для ответа - ответ обрезаный.
"""

"""
1. То что находиться в этом файле надо разнести по разным файлам. 
2. Логику класса по загрузке старых данных вывести в отдельный файл
3. Добавить обработку ошибок и кастомные ошибки
4. Вывод мыслей не работает - пересмотерть
5. Выводить полные входные параметры модели (system, promt) в отдельный файл (отдельный log?)
6. Проверка модели должна происходить через библиотечные функции ollama.list и
также для gemini
7. Добавить функционал для gemini, на случай нехватки контекста у локальных
моделей
8. Подумать над форматом передачи данных из документов

! Возможно, что текст длинных видео не будет влазить в контекст, может быть
хорошим решением разделять вход на несколько частей и скармливать их поочереди,
а в конце вызвать модель ещё раз, для логического соединения данных в один текст.
"""

logger = logging.getLogger(__name__)

class BaseLLMClient(ABC):
    """
    Абстрактный интерфейс для взаимодействия с языковыми моделями.
    """
    
    @abstractmethod
    def __init__(self, model_name: str, context_size: int):
        """
        Инициализация клиента.
        :param model_name: Название модели (например, 'gemma3' или 'gemini-1.5-flash').
        :param context_size: Лимит окна контекста.
        """
        pass

    @abstractmethod
    def process_request(self, system_message: str, user_data: Any) -> str:
        """
        Отправляет запрос к модели и возвращает результат в формате JSON.
        """
        pass

class DataManager():
    """Класс для отладки, чтобы не обрабатывать видео повторно"""

    def __init__(self, temp_dir: str, data_file: str):
        self.temp_dir = temp_dir
        self.data_file = os.path.join(temp_dir, data_file)

    def save_data(self, data: str):
        """Сохраняет промпт во временный файл."""
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write(data)

    def load_data(self) -> str:
        """Загружает промпт из временного файла."""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Старый промт не найден в {self.data_file}")
        with open(self.data_file, "r", encoding="utf-8") as f:
            return f.read()


class OllamaClient(BaseLLMClient):
    """
    Реализация взаимодействия с локальными моделями через Ollama.
    """
    
    def __init__(self, model_name: str, context_size: int):
        """
        Инициализация клиента Ollama.
            :param model_name: Название модели Ollama (например, 'gemma4:e4b').
            :param context_size: Размер контекста.
        """
        self.model_name = model_name
        self.context_size = context_size

    def process_request(self, system_message: str, user_data: Any) -> str:
        """
        Отправляет запрос к модели Ollama и возвращает результат в формате JSON.
        
            :param system_message: Системный промпт с инструкциями для модели.
            :param user_data: Данные пользователя (сырые данные или параметры запроса).
            :return: Строка с полным ответом от модели.
        """
        logger.info(f"Генерация через Ollama ({self.model_name})...")
        response_stream = ollama.generate(
            model=self.model_name, 
            system=system_message,
            prompt=user_data, 
            format='json',
            keep_alive=1,
            stream=True,
            think=True,
            options={
                "num_ctx": self.context_size
            }
        )

        full_response = ""
        full_thinking = ""
        header_printed = False

        for chunk in response_stream:
            # 1. Обработка "мыслей" модели (Chain of Thought)
            if chunk.get('thinking'):
                if not header_printed:
                    print("\n--- МЫСЛИ МОДЕЛИ ---")
                    header_printed = True
                think_chunk = chunk['thinking']
                print(think_chunk, end='', flush=True)
                full_thinking += think_chunk
                continue # Если есть мысли, 'response' в этом чанке обычно пустой

            # 2. Обработка основного ответа
            if chunk.get('response'):
                if header_printed: # Если раньше выводили мысли, отделим ответ
                    print("\n\n--- ФИНАЛЬНЫЙ ОТВЕТ ---")
                    header_printed = False # Сбрасываем, чтобы напечатать один раз
                
                text_chunk = chunk['response']
                print(text_chunk, end='', flush=True)
                full_response += text_chunk

            # 3. Обработка статистики (приходит в последнем чанке)
            if chunk.get('done'):
                prompt_tokens = chunk.get('prompt_eval_count', 0)
                eval_tokens = chunk.get('eval_count', 0)
                total_time = chunk.get('total_duration', 0) / 1e9 # Переводим в секунды

                print(f"\n\n--- СТАТИСТИКА ---")
                print(f"Промпт: {prompt_tokens} токенов")
                print(f"Ответ: {eval_tokens} токенов")
                print(f"Скорость: {eval_tokens / total_time:.2f} ток/сек" if total_time > 0 else "")
                print(f"Общее время: {total_time:.2f} сек")
        
        return full_response


class GeminiClient(BaseLLMClient):
    """
    Реализация взаимодействия с Google Gemini API.
    """
    
    def __init__(self, model_name: str, api_key: str, context_size: Optional[int] = None):
        # Инициализирует google.generativeai с переданным ключом
        pass

    def process_request(self, system_message: str, user_data: Any) -> Dict[str, Any]: # type: ignore
        # Настраивает GenerationConfig для получения JSON (response_mime_type)
        # Отправляет данные через genai.GenerativeModel
        pass


class LLMManager:
    """
    Единая точка входа для системы обработки запросов.
    """
    
    def __init__(self, model_name: str, context_size: int, api_key: Optional[str] = None):
        """
        Инициализация менеджера LLM.
        :param model_name: Название модели
        :param context_size: Размер контекста.
        :param api_key: API ключ для облачных сервисов (например, для Gemini).
        """
        self.api_key = api_key
        self.client = self._init_client(model_name, context_size, api_key)

    def _init_client(self, model, ctx, key) -> BaseLLMClient:
        if model.lower().startswith('gemini'):
            if not key:
                raise ValueError("API ключ Gemini не найден.")
            return GeminiClient(model, key)
        return OllamaClient(model, ctx)
    
    def _format_prompt(self, raw_data: List[Dict]) -> str:
        """Превращает список данных в текстовый блок для LLM."""
        return "\n".join([
            f"Time: {d['scene_start']:.2f}-{d['scene_end']:.2f} | Text: {d['text']} | Image: {d['image']}" 
            for d in raw_data
        ])

    def get_response(self, system_message: str, input_data: Any) -> str:
        """Формирует промпт и получает ответ."""
        # Если пришли сырые данные (список), форматируем их
        if isinstance(input_data, list):
            prompt = self._format_prompt(input_data)
        else:
            # Если пришла строка (из DataManager), используем как есть
            prompt = str(input_data)
            
        return self.client.process_request(system_message, prompt)


def generate_formal_instruction(raw_data: Optional[list] = None):
    """ФТ-5: Преобразование черновых шагов в чистовую инструкцию (для обратной совместимости)."""
    from src.config import AppConfig

    input_data = None

    # Для отладки
    if AppConfig.LLM.USE_LAST_DATA:
        debug_manager = DataManager(AppConfig.TEMP_DIR, AppConfig.LLM.LAST_DATA_FILE_NAME)
        input_data = debug_manager.load_data()
    # Нормальное поведение
    else:
        input_data = raw_data

    if not input_data:
        logger.warning("Генерация отменена: входные данные отсутствуют (raw_data is None).")
        return "Нет данных для обработки."
    
    manager = LLMManager(
        model_name=AppConfig.LLM.MODEL,
        context_size=AppConfig.LLM.CONTEXT_SIZE,
        api_key=AppConfig.LLM.API_KEY
    )

    result = manager.get_response(AppConfig.LLM.SYSTEM_PROMPT, input_data)
    
    return result