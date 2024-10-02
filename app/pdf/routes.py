from flask import Blueprint, render_template, request, redirect, url_for, send_file, send_from_directory
import os
from .processing import TestarResiduosPeligrosos, DeleteQR, TestarImpactoAmbiental

pdf_bp = Blueprint('pdf', __name__, template_folder='templates/pdf')

UPLOAD_FOLDER = os.path.abspath('app/uploads')
ALLOWED_EXTENSIONS = {'pdf'}

# Crear el directorio de subida si no existe
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
    """ Ruta para mostrar la lista de archivos PDF subidos en DragAndDrop.html. """
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('DragAndDrop.html', files=files)

@pdf_bp.route('/impacto-ambiental')
def impacto_ambiental():
    """ Ruta para mostrar la lista de archivos PDF subidos en DragAndDrop.html. """
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('DragAndDrop.html', files=files)

@pdf_bp.route('/atmosfera')
def atmosfera():
    """ Ruta para mostrar la lista de archivos PDF subidos en DragAndDrop.html. """
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('DragAndDrop.html', files=files)

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
    """ Ruta para procesar y modificar un archivo PDF. """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    temp_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_temp.pdf')
    final_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_testado.pdf')

    # Crear una instancia de TestarResiduosPeligrosos
    processor = TestarResiduosPeligrosos()
    
    # Procesar el PDF
    try:
        # Procesar el PDF usando la clase TestarResiduosPeligrosos
        processor.process_pdf(file_path, temp_output_path)

        # Pasar el archivo procesado a DeleteQR
        delete_qr_processor = DeleteQR(temp_output_path, final_output_path)
        delete_qr_processor.FindQRCoordinates()

        # Enviar el archivo para descargar con el nuevo nombre
        return send_file(final_output_path, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_testado.pdf')
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.residuos_peligrosos'))
    

@pdf_bp.route('/testar-impacto/<filename>', methods=['POST'])
def testar_impacto(filename):
    """ Ruta para procesar y modificar un archivo PDF de impacto ambiental. """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    temp_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_temp.pdf')
    final_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_testado.pdf')

    # Crear una instancia de TestarImpactoAmbiental
    processor = TestarImpactoAmbiental()
    
    # Procesar el PDF
    try:
        # Procesar el PDF usando la clase TestarImpactoAmbiental
        processor.ProcessPDF(file_path, final_output_path)  # Sin el archivo temporal

        # Enviar el archivo para descargar con el nuevo nombre
        return send_file(final_output_path, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_impactado.pdf')
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.mostrar_archivos'))  # Redirige a la función de mostrar archivos


"""
@pdf_bp.route('/testar-atmosfera/<filename>', methods=['POST'])
def testar_atmosfera(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    temp_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_temp.pdf')
    final_output_path = os.path.join(UPLOAD_FOLDER, f'{os.path.splitext(filename)[0]}_atmosferico.pdf')

    # Crear una instancia de TestarAtmosfera
    processor = TestarAtmosfera()
    
    # Procesar el PDF
    try:
        processor.process_pdf(file_path, temp_output_path)

        # Pasar el archivo procesado a DeleteQR
        delete_qr_processor = DeleteQR(temp_output_path, final_output_path)
        delete_qr_processor.FindQRCoordinates()

        # Enviar el archivo para descargar con el nuevo nombre
        return send_file(final_output_path, as_attachment=True, download_name=f'{os.path.splitext(filename)[0]}_atmosferico.pdf')
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return redirect(url_for('pdf.mostrar_archivos'))  # Redirige a la función de mostrar archivos
"""



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
    return redirect(url_for('pdf.residuos_peligrosos'))
