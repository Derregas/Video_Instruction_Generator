# Инструкция по установке (Windows GPU)

1. Создайте виртуальное окружение:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Установите PyTorch с поддержкой CUDA 12.1 (обязательно первым шагом):
   ```powershell
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

3. Установите остальные зависимости:
   ```powershell
   pip install -r requirements.txt
   ```

4. Скачайте и установите Ollama с официального сайта:
   https://ollama.com/download/windows
   или
   ```powershell
   irm https://ollama.com/install.ps1 | iex
   ```

5. Скачайте любую подходящую модель с https://ollama.com/library/:
```
   ollama pull [имя_модели]
```

6. Скопируйте пример настроек виртуального окружения в .env