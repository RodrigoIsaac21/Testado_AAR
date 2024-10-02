from flask import Blueprint

pdf_bp = Blueprint('pdf', __name__, template_folder='templates/pdf')

from . import routes  # Importar las rutas después de definir el blueprint
