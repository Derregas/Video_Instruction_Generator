# src/config.py

import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
        filename='generator.log',
        filemode='w',
        encoding='utf-8'
    )