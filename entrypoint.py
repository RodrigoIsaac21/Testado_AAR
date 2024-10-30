# entrypoint.py
import os
from app import create_app

def create_app_wrapper():
    # Construye la ruta completa para el archivo de configuración en `instance`
    config_path = os.path.join(os.getcwd(), 'instance', os.getenv('APP_SETTINGS_MODULE', 'config.py'))
    return create_app(config_path)

app = create_app_wrapper()

if __name__ == "__main__":
    app.run(debug=True)
