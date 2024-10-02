from flask import Flask

def create_app(config_filename='instance/config.py'):
    app = Flask(__name__, instance_relative_config=True)
    
    # Cargar la configuración
    app.config.from_pyfile(config_filename, silent=False)
    
    # Registrar blueprints
    from app.pdf.routes import pdf_bp
    app.register_blueprint(pdf_bp, url_prefix='/pdf')  # Registrar el blueprint con prefijo '/pdf'
    
    return app
