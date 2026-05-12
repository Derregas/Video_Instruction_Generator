# app.py
from src.modules import setup_environment
from src.config import setup_logging
from flask_app import create_app

if __name__ == '__main__':
    setup_logging()
    setup_environment()
    app = create_app()
    app.run(debug=True, use_reloader=False)