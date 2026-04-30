import os
import re
import time
from typing import Iterable, Literal, Optional
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json

class DocumentExtractor:
    def __init__(self, 
                 strategy: Optional[Literal["fast", "hi_res"]] = "fast", 
                 save_json: Optional[bool] = False, 
                 save_text: Optional[bool] = False, 
                 temp_dir: Optional[str] = None):
        
        if strategy is not None and strategy not in ("fast", "hi_res"):
            raise ValueError("Стратегия может быть только 'fast' или 'hi_res'")
        if (save_json or save_text) and temp_dir is None:
            raise ValueError("При сохранении JSON и текста, temp_dir должен быть указан для хранения промежуточных файлов.")
        
        self.strategy = strategy or "fast"
        self.save_json = save_json
        self.save_text = save_text
        self.temp_dir = temp_dir
        self._extract_tables = True
        self._extract_images = False
        self._model_name = "yolox" if strategy == "hi_res" else None

    def _save_in_file(self, text, dir_path, file_prefix: Optional[str] = None):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_name = f"{file_prefix}_output.txt" if file_prefix else "output.txt"
        with open(os.path.join(dir_path, file_name), 'w', encoding='utf-8') as f:
            f.write(text)
            
    def _format_element(self, elements) -> str:
        document_text = ''
        last_is_text = False

        for element in elements:
            category = str(element.category)
            
            text = element.text
            if re.search(r'\.{5,}', text):  # Пропуск оглавлений
                continue
            text = re.sub(r'https?://\S+|www\.\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue

            if category in ('UncategorizedText', 'Image', 'Footer'):
                continue
            elif category in ('Title', 'ListItem', 'Table'):
                if last_is_text: document_text += '\n'
                document_text += f"{text}\n"
                last_is_text = False
            else:
                document_text += f"{text} "
                last_is_text = True

        return document_text.strip()

    def extract_doc_data(self, file_path) -> str:

        elements = partition(
            filename=file_path,             # Путь к обрабатываему файлу
            strategy="hi_res",              # Используемая стратегия. "hi-res" использует ИИ
            extract_images_in_pdf=False,    # Не извлекаем изображения из PDF, так как нам нужны только текстовые данные
            extract_tables=True,            # Включаем извлечение таблиц
            model_name="yolox"              # Модель для извлечения текста из изображений
        )
        """Возвращает list
        - category = ['Title', 'UncategorizedText', 'NarrativeText', 'Image', 'ListItem', 'Table', 'Footer']
        - embenddings
        - id
        - text
        """
        """chunks = chunk_by_title(
            elements,
            max_characters=10000,           # Максимальный размер чанка в символах
            new_after_n_chars=8000,         # Начинать новый чанк после этого порога, если встретится заголовок
            combine_text_under_n_chars=500, # Склеивать мелкие фрагменты, чтобы не плодить микро-чанки
            multipage_sections=True,        # Склеивать заголовки с секциями на следующей странице
            overlap=200                     # Повторение прошлого ченка в следующем
        )
        textchunks = ''
        for i, chunk in enumerate(chunks):
            textchunks += chunk.text
            print(f"Чанк №{i} (Тип: {type(chunk).__name__})")
            print(chunk.text[:100] + "...") """

        document_text = self._format_element(elements)
        
        # Получение имени файла
        filename = os.path.splitext(os.path.basename(file_path))[0]

        if self.save_text:
            self._save_in_file(document_text, self.temp_dir, file_prefix=filename)

        if self.save_json:
            if not os.path.exists(str(self.temp_dir)):
                os.makedirs(str(self.temp_dir))

            elements_to_json(
                elements, 
                os.path.join(str(self.temp_dir), 
                f"{filename}_output.json")
            )
            
        return document_text

# Тестовый запуск
if __name__ == "__main__":

    def _tokens(text):
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        tokens = tokenizer.encode(text)
        count = len(tokens)
        print(f"Использованно токенов: {count}")

    def init():
        import pytesseract
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        cudnn_path = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages", "nvidia", "cudnn", "bin")
        poppler_path = os.path.join(BASE_DIR, "tools", "poppler-25.12.0", "Library", "bin")
        tesseract_path = os.path.join(BASE_DIR, "tools", "tesseract-OCR")

        pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_path, "tesseract.exe")

        # Добавляем пути к cudnn, poppler и tesseract в переменную среды PATH
        for path in [cudnn_path, poppler_path, tesseract_path]:
            if os.path.exists(path):
                os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
                # Для Python 3.8+ в Windows нужно явно разрешить загрузку DLL из этих папок
                if hasattr(os, "add_dll_directory"):
                    try:
                        os.add_dll_directory(path)
                    except Exception as e:
                        print(f"Warning: Could not add DLL directory {path}: {e}")
            else:
                print(f"Warning: Path does not exist: {path}")

    print("Starting document data extraction...")
    init()
    start_time = time.time()
    doc = DocumentExtractor(strategy="hi_res")
    data = doc.extract_doc_data(r"D:\D Загрузки\materinskaa-plata-gigabyte-b650m-d3hp_instrukcia_074339_05082025.pdf")
    end_time = time.time()
    _tokens(data)


    print(f"Time taken: {end_time - start_time:.2f} seconds")


"""
Unstructed - кусок кала. При установке, часть пакетов не установиться.

Чтобы всё заработало надо ставить с флагом "pip install "unstructured[all-docs]" --prefer-binary"
Дальше возникает проблема при выборе стратегии hi-res. На стратегии fast работает нормально. 
Для работы hi-res, сначало надо поставить poppler. Качал его от сюда:
https://github.com/oschwartz10612/poppler-windows/releases/download/v25.12.0-0/Release-25.12.0-0.zip
После этого, надо добавить путь до папки bin в пути среды, это в init.py уже сделано.

Дальше, надо поставить tesseract. Качал его от сюда:
https://github.com/UB-Mannheim/tesseract/wiki "tesseract-ocr-w64-setup-5.5.0.20241111.exe":
https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe
Устанавливаем pytesseract.pytesseract.tesseract_cmd путь до .exe файла tesseract
на всякий случай добавляем папку tesseract в переменные среды.

Работа с OCR осуществляется через onnxruntime, но работает он только с CPU.
Чтобы модель ocr работала на видеокарте, потребуется установить ещё и CUDA-совместимую версию
pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
Брал инфу от сюда: https://github.com/Unstructured-IO/unstructured/issues/2506#issuecomment-2084594453
Для его работы нужен cudnn. Он ставился вместе с torch, так что просто добавляем его в переменную среды.

Что дают эти махинации? Вместо 300+ сек. файл обрабатывается за 230...
Так что, если нет желания всё это качать, можно просто поменять hi-res на fast.
"""