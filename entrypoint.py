import os
from app import create_app

def create_app_wrapper():
    settings_module = os.getenv('APP_SETTINGS_MODULE', 'config.py')
    return create_app(settings_module)

app = create_app_wrapper()

if __name__ == "__main__":
    app.run(debug=True)
