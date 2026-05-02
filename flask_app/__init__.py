from flask import Flask

def create_app():
    """Создание Flask приложения"""
    app = Flask(__name__)
    
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
