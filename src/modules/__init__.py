# src/modules/__init__.py

#""" Для работы Unstructured на hi-res необходимо установить 
#Tesseract OCR и Poppler, а также указать пути к ним."""
import os
import pytesseract

print("Setting up paths for Tesseract OCR and Poppler...")

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

print("Modules imported successfully")

from . import video_analyzer
from .audio_processor import AudioProcessor
from .extract_doc_data import DocumentExtractor
from .llm_processor import LLMManager, DataManager