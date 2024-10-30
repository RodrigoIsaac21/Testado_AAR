# app/__init__.py
from flask import Flask

def create_app(config_filename='config.py'):
    # Establece la aplicación Flask y usa instance_relative_config para que busque en el directorio `instance`
    app = Flask(__name__, instance_relative_config=True)
    
    # Cargar la configuración desde el archivo `config.py` en el directorio `instance`
    try:
        app.config.from_pyfile(config_filename, silent=False)
    except FileNotFoundError:
        print(f"Archivo de configuración no encontrado: {config_filename}")
    
    # Registrar blueprints
    from app.pdf.routes import pdf_bp
    app.register_blueprint(pdf_bp, url_prefix='/pdf')  # Registrar el blueprint con prefijo '/pdf'
    
    return app
