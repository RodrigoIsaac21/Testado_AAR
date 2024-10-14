from flask import Blueprint, render_template, request, redirect, url_for, send_file, send_from_directory
from flask import send_file

import os

import io

from .TestadoResiduosPeligrosos import TestarResiduosPeligrosos
from .TestadoImpactoAmbiental import TestarImpactoAmbiental
from .TestadoAtmosfera import TestarAtmosefera

import zipfile

pdf_bp = Blueprint('pdf', __name__, template_folder='templates/pdf')

UPLOAD_FOLDER = os.path.abspath('app/uploads')
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """ Verificar si el archivo tiene una extensión permitida. """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pdf_bp.route('/')
def index():
    """ Ruta principal para mostrar la lista de archivos PDF en index.html. """
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('index.html', files=files)

@pdf_bp.route('/residuos-peligrosos')
def residuos_peligrosos():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    file_count = len(files)
    return render_template('DragAndDrop.html', files=files, file_count=file_count)

@pdf_bp.route('/impacto-ambiental')
def impacto_ambiental():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    file_count = len(files)
    return render_template('DragAndDrop.html', files=files, file_count=file_count)

@pdf_bp.route('/atmosfera')
def atmosfera():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    file_count = len(files)
    return render_template('DragAndDrop.html', files=files, file_count=file_count)

@pdf_bp.route('/permisos')
def permisos():
    """ Ruta alternativa para mostrar la lista de archivos PDF subidos en DragAndDrop.html. """
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('DragAndDrop.html', files=files)

@pdf_bp.route('/upload', methods=['POST'])
def upload():
    """ Ruta para manejar la subida de archivos PDF. """
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        return redirect(url_for('pdf.residuos_peligrosos'))
    return redirect(request.url)

@pdf_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """ Ruta para servir archivos PDF subidos. """
    return send_from_directory(UPLOAD_FOLDER, filename)

@pdf_bp.route('/testar-residuos/<filename>', methods=['POST'])
def testar_residuos(filename):
    try:
        output = io.BytesIO()
        processor = TestarResiduosPeligrosos()
        processor.ProcessPDF(os.path.join(UPLOAD_FOLDER, filename), output)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_testado.pdf', mimetype='application/pdf')
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.residuos_peligrosos'))
 
@pdf_bp.route('/testar-impacto/<filename>', methods=['POST'])
def testar_impacto(filename):
    try:
        output = io.BytesIO()
        processor = TestarImpactoAmbiental()
        processor.ProcessPDF(os.path.join(UPLOAD_FOLDER, filename), output)

        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_impacto_testado.pdf', mimetype='application/pdf')

    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.impacto_ambiental'))

@pdf_bp.route('/testar-atmosfera/<filename>', methods=['POST'])
def testar_atmosfera(filename):
    try:
        output = io.BytesIO()

        processor = TestarAtmosefera()
        processor.ProcessPDF(os.path.join(UPLOAD_FOLDER, filename), output)

        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_atmosfera_testado.pdf', mimetype='application/pdf')

    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.atmosfera'))

@pdf_bp.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    """ Ruta para eliminar un archivo PDF subido. """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            print(f"Archivo eliminado: {file_path}")
        except Exception as e:
            print(f"Error al eliminar el archivo: {e}")

    current_route = request.form.get('current_route', 'pdf.residuos_peligrosos') 
    return redirect(url_for(current_route))


@pdf_bp.route('/process_all', methods=['POST'])
def process_all():
    """ Procesar todos los PDFs según la ruta actual y guardarlos en un archivo ZIP. """
    current_route = request.form.get('current_route', 'pdf.residuos_peligrosos')
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]

    zip_output = io.BytesIO()
    zip_filename = 'procesados.zip'

    with zipfile.ZipFile(zip_output, 'w') as zip_file:
        for filename in files:
            try:
                output = io.BytesIO()
                
                if current_route == 'pdf.residuos_peligrosos':
                    processor = TestarResiduosPeligrosos()
                elif current_route == 'pdf.impacto_ambiental':
                    processor = TestarImpactoAmbiental()
                elif current_route == 'pdf.atmosfera':
                    processor = TestarAtmosefera()
                else:
                    continue 
                
                processor.ProcessPDF(os.path.join(UPLOAD_FOLDER, filename), output)

                output.seek(0)
                zip_file.writestr(f'{os.path.splitext(filename)[0]}_testado.pdf', output.read())
                
            except Exception as e:
                print(f"Error al procesar el archivo {filename}: {e}")

    zip_output.seek(0)
    
    return send_file(zip_output, as_attachment=True, download_name=zip_filename, mimetype='application/zip')


@pdf_bp.route('/delete_all', methods=['POST'])
def delete_all():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    for filename in files:
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
        current_route = request.form.get('current_route', 'pdf.index')  
    return redirect(url_for(current_route))

