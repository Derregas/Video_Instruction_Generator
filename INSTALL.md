# Инструкция по установке (Windows GPU)

1. **Создайте виртуальное окружение:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Установите PyTorch с поддержкой CUDA 12.1:**
   Это необходимо для работы Whisper на видеокарте.
   ```powershell
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```
   *Также может потребоваться установка CUDA toolkit, если он не поставиться вместе с torch*


3. **Установите остальные зависимости:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Установите FFmpeg:**
   FFmpeg необходим для извлечения аудио. Если он не установлен в системе, скачайте его с [ffmpeg.org](https://ffmpeg.org/download.html) и добавьте путь к `bin` в PATH.

5. **Установите Ollama:**
   Скачайте с официального сайта: [https://ollama.com/download/windows](https://ollama.com/download/windows)
   Затем скачайте модель:
   ```powershell
   ollama pull gemma4:e4b
   ```

6. **Настройте конфигурацию:**
   Скопируйте шаблон настроек в новый файл `.env`:
   ```powershell
   cp .env.example .env
   ```

7. **Запуск проекта:**
   ```powershell
   python -m src.main path/to/your/video.mp4
   ```
