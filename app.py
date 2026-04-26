# app.py

from src.config import setup_logging
from flask_app import create_app

if __name__ == '__main__':
    setup_logging()
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)