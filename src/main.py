# src/main.py

import logging
import argparse
from typing import Optional
from .config import setup_logging
from .core.processor import InstructionProcessingService

logger = logging.getLogger(__name__)

def main() -> Optional[list]:
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", help="Путь к видео")
    args = parser.parse_args()

    setup_logging()
    service = InstructionProcessingService(device="cuda", compute_type="float16", model_size="base")
    return service.process_video(args.video_path)

if __name__ == "__main__":
    result = main()
    print(result)