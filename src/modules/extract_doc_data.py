import time
from typing import Iterable
from transformers import AutoTokenizer
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json

#tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

def extract_doc_data(file_path):

    elements = partition(
        filename=file_path,             # Путь к обрабатываему файлу
        strategy="hi_res",              # Используемая стратегия. "hi-res" использует ИИ
        extract_images_in_pdf=False,    # Не извлекаем изображения из PDF, так как нам нужны только текстовые данные
        extract_tables=True,            # Включаем извлечение таблиц
        model_name="yolox"              # Модель для извлечения текста из изображений
    )
    chunks = chunk_by_title(
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
        print(chunk.text[:100] + "...")
    elements_json = elements_to_json(chunks, filename='output.json')

    #tokens = tokenizer.encode(textchunks)
    return elements_json

# print("Starting document data extraction...")
# start_time = time.time()
# data = extract_doc_data(r"D:\D Загрузки\materinskaa-plata-gigabyte-b650m-d3hp_instrukcia_074339_05082025.pdf")
# end_time = time.time()

# print(data)
# print(f"Time taken: {end_time - start_time:.2f} seconds")


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