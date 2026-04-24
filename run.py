#!/usr/bin/env python
"""
Entry point для запуска приложения Video Instruction Generator.

Использование:
    python run.py <путь_к_видео>
    python run.py video.mp4 --device cpu --output results.json
"""

import sys
from pathlib import Path

# Убедиться, что проект находится в Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from src.main import main
    
    try:
        result = main()
        sys.exit(0 if result is not None else 1)
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        sys.exit(1)
