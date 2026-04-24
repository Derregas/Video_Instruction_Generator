"""
Скрипт для проверки установки и конфигурации.

Использование:
    python check_installation.py
"""

import sys
from pathlib import Path

def check_imports():
    """Проверить что все импорты работают."""
    print("🔍 Проверка импортов...\n")
    
    checks = [
        ("torch", "PyTorch"),
        ("moviepy", "MoviePy"),
        ("faster_whisper", "Faster Whisper"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
    ]
    
    all_ok = True
    for module, name in checks:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - НЕ УСТАНОВЛЕН")
            all_ok = False
    
    return all_ok

def check_torch_gpu():
    """Проверить доступность GPU."""
    print("\n🔍 Проверка GPU...\n")
    
    try:
        import torch
        print(f"  PyTorch версия: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"  ✅ CUDA доступна")
            print(f"     GPU: {torch.cuda.get_device_name(0)}")
            print(f"     CUDA версия: {torch.version.cuda}")
            return True
        else:
            print(f"  ⚠️  CUDA НЕ доступна (используется CPU)")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка при проверке GPU: {e}")
        return False

def check_config():
    """Проверить конфигурацию."""
    print("\n🔍 Проверка конфигурации...\n")
    
    try:
        from src.config import get_config, AppConfig
        config = get_config()
        
        print(f"  ✅ Конфигурация загружена")
        print(f"     Model: {config.whisper.model_size}")
        print(f"     Device: {config.whisper.device}")
        print(f"     Temp dir: {config.processing.temp_dir}")
        print(f"     Logging level: {config.logging.level}")
        
        # Проверить что temp dir существует
        Path(config.processing.temp_dir).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Временная директория доступна")
        
        return True
    except Exception as e:
        print(f"  ❌ Ошибка при загрузке конфигурации: {e}")
        return False

def check_modules():
    """Проверить что модули импортируются."""
    print("\n🔍 Проверка модулей...\n")
    
    checks = [
        ("src.exceptions", "Исключения"),
        ("src.config", "Конфигурация"),
        ("src.modules.audio_processor", "AudioProcessor"),
        ("src.core.processor", "InstructionProcessingService"),
        ("src.main", "Main модуль"),
    ]
    
    all_ok = True
    for module, name in checks:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Проверить что .env файл существует."""
    print("\n🔍 Проверка .env файла...\n")
    
    env_path = Path(".env")
    if env_path.exists():
        print(f"  ✅ .env файл существует ({env_path.stat().st_size} байт)")
        return True
    else:
        print(f"  ⚠️  .env файл не найден")
        print(f"     Используются значения по умолчанию")
        return True  # не критично

def main():
    """Главная функция проверки."""
    print("=" * 60)
    print("ПРОВЕРКА УСТАНОВКИ VIDEO INSTRUCTION GENERATOR")
    print("=" * 60 + "\n")
    
    results = []
    
    # Выполнить проверки
    results.append(("Импорты", check_imports()))
    results.append(("GPU", check_torch_gpu()))
    results.append(("Конфигурация", check_config()))
    results.append(("Модули", check_modules()))
    results.append((".env файл", check_env_file()))
    
    # Вывести результаты
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 60 + "\n")
    
    all_ok = True
    for name, result in results:
        status = "✅ OK" if result else "❌ ОШИБКА"
        print(f"{name}: {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    
    if all_ok:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("\nВы можете запустить:")
        print("  python run.py video.mp4")
        print("  python examples.py")
        print("  pytest tests.py -v")
        return 0
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("\nСм. выше детали и решения")
        return 1
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
