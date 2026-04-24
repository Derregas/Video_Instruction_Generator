# Инструкция по установке и запуску

## Windows (с GPU NVIDIA - CUDA 12.1)

### Шаг 1: Создайте виртуальное окружение
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Шаг 2: Установите PyTorch с поддержкой CUDA 12.1
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Шаг 3: Установите остальные зависимости
```powershell
pip install -r requirements.txt
```

### Шаг 4: Создайте конфигурацию
```powershell
# Скопируйте пример конфигурации
copy .env.example .env

# Отредактируйте .env в зависимости от ваших нужд
# (опционально, значения по умолчанию должны работать)
```

### Шаг 5: Проверьте установку
```powershell
python run.py --help
```

Если вы видите справку - все установлено правильно!

## Windows (только CPU - без GPU)

### Шаг 1-2: Виртуальное окружение и PyTorch
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Для CPU вместо CUDA версии
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Шаг 3-5: Остальные шаги как выше

**! ПРИМЕЧАНИЕ:** CPU обработка будет медленнее (~10-20x медленнее чем GPU)

## Linux (Ubuntu/Debian)

### Шаг 1: Установите зависимости системы
```bash
sudo apt-get update
sudo apt-get install python3.9-dev python3.9-venv git build-essential
```

### Шаг 2-5: Как Windows
```bash
python3.9 -m venv .venv
source .venv/bin/activate

pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

cp .env.example .env
python run.py --help
```

## macOS

### Шаг 1: Установите Homebrew (если нет)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Шаг 2: Установите Python и зависимости
```bash
brew install python@3.9 ffmpeg

python3.9 -m venv .venv
source .venv/bin/activate
```

### Шаг 3: Установите PyTorch
```bash
# Для MacBook с Metal GPU:
pip install torch torchvision torchaudio

# Для Intel Mac или если выше не сработает:
pip install torch
```

### Шаг 4-5: Остальные шаги
```bash
pip install -r requirements.txt
cp .env.example .env
python run.py --help
```

## 🔧 Проверка и Troubleshooting

### Проверьте что PyTorch установлен правильно
```python
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Ожидаемый результат:**
```
PyTorch version: 2.x.x
CUDA available: True  # или False если CPU
```

### Если CUDA не доступна
```python
# Проверьте что NVIDIA GPU драйвер установлен
nvidia-smi

# Если команда не найдена - установите драйвер с https://www.nvidia.com/Download/driverDetails.aspx

# Переустановите PyTorch
pip install --upgrade --force-reinstall torch --index-url https://download.pytorch.org/whl/cu121
```

### Проверьте что все модули установлены
```powershell
# Windows
python -c "from src import InstructionProcessingService; print('✅ All modules loaded')"

# Linux/macOS
python -c "from src import InstructionProcessingService; print('✅ All modules loaded')"
```

## Быстрый старт

После успешной установки:

```bash
# 1. Обработать видео базовой моделью
python run.py test_video.mp4

# 2. Обработать с GPU ускорением
python run.py test_video.mp4 --device cuda

# 3. Сохранить результат в JSON
python run.py test_video.mp4 --output results.json

# 4. Использовать более точную модель (медленнее)
python run.py test_video.mp4 --model large-v3
```

Больше примеров в README.md и examples.py

## 📊 Требования к системе

### Минимальные
- Python 3.9+
- 4 GB RAM
- 2 GB свободного места на диске (для моделей)
- Windows 10, Ubuntu 18.04 LTS, macOS 10.14+

### Рекомендуемые (с GPU)
- NVIDIA GPU с 6+ GB памяти (CUDA Compute Capability 6.1+)
- GPU драйвер 550.54+
- 16 GB RAM
- 10 GB свободного места на диске

### Для CPU обработки
- 4 ядра процессора минимум
- 8 GB RAM рекомендуется
- Может быть очень медленно на слабых системах

## Частые проблемы

### 1. "ModuleNotFoundError: No module named 'torch'"

**Решение:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 2. "CUDA not available"

**Решение:**
- Проверьте драйверы: `nvidia-smi`
- Переключитесь на CPU: `python run.py video.mp4 --device cpu`

### 3. "Out of Memory" при GPU обработке

**Решение:**
```bash
# Используйте меньшую модель
python run.py video.mp4 --model tiny

# Или используйте CPU
python run.py video.mp4 --device cpu
```

### 4. "Permission denied" на Linux

**Решение:**
```bash
# Дайте права на выполнение
chmod +x run.py

# Или запустите через python
python run.py video.mp4
```

## 📚 Дальнейшее изучение

- **README.md** - полная документация
- **ARCHITECTURE.md** - архитектура проекта
- **examples.py** - примеры использования
- **tests.py** - unit-тесты (и примеры использования API)
- **.env.example** - все доступные параметры конфигурации

## ❓ Помощь

Если что-то не работает:

1. Проверьте выше указанные решения
2. Посмотрите файл `generator.log` (содержит подробные ошибки)
3. Попробуйте с `--debug` флагом: `python run.py video.mp4 --debug`
4. Откройте Issue на GitHub

---

**Последнее обновление:** 24 апреля 2026 г.