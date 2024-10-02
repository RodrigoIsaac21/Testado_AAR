"""
######################################################################################
This program aims to function as a backend for the section of the website responsible for cross text in PDF documents.
Each class is designed to test different PDF formats. This program primarily uses regex and PyMuPDF for analyzing
and processing the information to be cross text from the PDF, also PyPDF2 and ReportLab for creating the watermark after to process,
as indicated by Mexican law and its articles: "art. 113, fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
#####################################################################################
"""
import fitz

import io

import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import red, black

import tempfile

from pyzbar.pyzbar import decode

from PIL import Image

class TestarResiduosPeligrosos:
    """Class to store regex patterns used for data validation."""

    def __init__(self):

        """Regex used for corporate entities."""
        self.PATTERNS_CORPORATE = {
            'Addresses': ( 
                r'(?=.*\b(?:CALLE|AVENIDA|CARRETERA|PERIFÉRICO|BOULEVARD|RUA|VIA|PASEO|CALZADA)\b)'  
                r'[A-Za-zÁÉÍÓÚÑáéíóúñ\s\d\.,\#\-]*'    
                r'\b(?:CALLE|AVENIDA|CARRETERA|PERIFÉRICO|BOULEVARD|RUA|VIA|PASEO|CALZADA)\s+'  
                r'[A-Za-zÁÉÍÓÚÑáéíóúñ\s\d\.,\#\-]+(?:\s+NO\.\s*\d+)?(?:\s*[\d\+\-]+)?(?:,\s*[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+)?'
                r'(?:,\s*C\.P\.\s*\d{5})?\s*,\s*[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+(?:\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]+)*'
                r'(?:,\s*[A-ZÁÉÍÓÚÑáéíóúÑ\s]+(?:\s+[A-ZÁÉÍÓÚÑáéíóúÑ]+)*)?\b'
            ),
            'EmailAddresses': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'PhoneNumber': ( 
                r'(?<=\s)?' 
                r'^(?:\+52\s*|\s*52\s*)?'  
                r'(?:\(\d{2,4}\)[\s.-]?|\d{2,12}[\s.-]?)'
                r'(?:\d{2,8}|\d{2,6} \d{2,6}|\d{1,6} \d{1,6} \d{1,3}|\d{1,2} \d{1,2} \d{1,2} \d{2})'
                r'(?:\s|,)?$'
            ),
            'CURP': r'\b[A-Z]{4}\d{6}[HM]\d{2}[A-Z]{3}[A-Z\d]\b', 
            'RFC': r'\b[A-ZÑ&]{3,4}-?\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[-]?[A-Z\d]{2}[A\d]\b',
        }
        """Regex used for individuals."""
        self.PATTERN_INDIVIDUAL = {
            'IndividualNames': (
                r'(?:^|\b)C\.\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3}(?=\s|$)'
            ),
            'EmailAddresses': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'PhoneNumber': ( 
                r'^(?:\+52\s*|\s*52\s*)?'  
                r'(?:\(\d{2,4}\)[\s.-]?|\d{2,12}[\s.-]?)'
                r'(?:\d{2,8}|\d{2,6} \d{2,6}|\d{1,6} \d{1,6} \d{1,3}|\d{1,2} \d{1,2} \d{1,2} \d{2})'
                r'(?:\s|,)?$'
            ),
            'CURP': r'\b[A-Z]{4}\d{6}[HM]\d{2}[A-Z]{3}[A-Z\d]\b',
            'RFC': r'\b[A-ZÑ&]{3,4}-?\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[-]?[A-Z\d]{2}[A\d]\b',
            'IndivialAddresses': (
                r'^(?:Persona\s*física\s*con\s*actividad\s*empresaria\s*)'  
                r'(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]*(?:[\'-][A-ZÁÉÍÓÚÑa-záéíóúñ]+)*)?'  
                r'(?:\s*(?:CALLE|AVENIDA|CARRETERA|PERIFÉRICO|BOULEVARD|RUA|VIA|PASEO|CALZADA)\s*)?'  
                r'[A-Za-zÁÉÍÓÚÑáéíóúñ\s\d\.,\#\-]*(?:\s+NO\.\s*\d+)?(?=\s*\.\s|$)'
            )
        }

    def DetectKeywords(self, pdf_path):
        """Detects if the PDF belongs to an individual or a corporate entity."""
        document = fitz.open(pdf_path)
        patterns_found = {
            'is_individual': False,
            'is_corporate': False
        }

        for page_number in range(len(document)):
            page = document[page_number]
            text = page.get_text()

            if "Persona física con actividad empresarial" in text:
                patterns_found['is_individual'] = True
                break 
            else:
                patterns_found['is_corporate'] = True

        document.close()
        return patterns_found

    def DeleteTextWithRegex(self, page, patterns):
        """Removes text based on regex patterns on a page and returns whether matches were removed."""
        text = page.get_text()
        one_third_length = len(text) // 3  
        text_after_one_third = text[one_third_length:] 

        for pattern_name in ['Addresses', 'EmailAddresses', 'PhoneNumber']:
            if pattern_name in patterns:
                pattern = patterns[pattern_name]
                matches = re.findall(pattern, text[:one_third_length], re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    rects = page.search_for(match, quads=True)
                    for rect in rects:
                        x0, y0 = rect[0].x, rect[0].y
                        x1, y1 = rect[3].x, rect[3].y
                        margin = 1
                        adjusted_rect = fitz.Rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin)

                        if adjusted_rect.y1 <= (page.rect.height / 3):  
                            page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))

        found_any = False 
        for pattern_name, pattern in patterns.items():
            if pattern_name not in ['Addresses', 'EmailAddresses', 'PhoneNumber']:
                matches = re.findall(pattern, text_after_one_third, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    rects = page.search_for(match, quads=True)
                    for rect in rects:
                        x0, y0 = rect[0].x, rect[0].y
                        x1, y1 = rect[3].x, rect[3].y
                        margin = 1
                        adjusted_rect = fitz.Rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin)

                        page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))
                        found_any = True  
        page.apply_redactions()

        return found_any 

    def AddWatermark(self, doc, is_individual): 
        """Adds a watermark to the document based on the type."""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        if is_individual:
            rect_x, rect_y, rect_width, rect_height = 250, 580, 380, 40
            text_lines = [
                "Nombre, domicilio, teléfono y correo electrónico de Persona Física, art.",
                "113, fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
            ]
        else:
            rect_x, rect_y, rect_width, rect_height = 250, 580, 380, 40
            text_lines = [
                "Domicilio, teléfono y correo electrónico del Representante Legal, art. 113,",
                "fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
            ]

        can.setFillColor(black) 
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        line_height = 2
        can.setFillColor(red)

        for line in text_lines:
            text_object.textLine(line)
            text_object.moveCursor(0, -line_height)

        can.drawText(text_object)
        can.save() 

        packet.seek(0) 

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name
        
        page = doc[0]
        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0)

    def AddSecondWatermark(self, page): 
        """Adds a second watermark to the page if regex finds patterns in those coordinates."""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        rect_x = 0
        rect_y = 200
        rect_width = 70
        rect_height = 150
        
        text_lines = [
            "Nombre y RFC de",
            "Persona Física,",
            "art. 113,",
            "fracción I de la",
            "LFTAIP y art",
            "16, primer",
            "párrafo de la",
            "LGTAIP."
        ]


        can.setFillColor(black)
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        line_height = 2
        can.setFillColor(red)

        for line in text_lines:
            text_object.textLine(line)
            text_object.moveCursor(0, -line_height)

        can.drawText(text_object)
        can.save()
        packet.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name

        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0)

    def process_pdf(self, pdf_path, output_path):
        """Processes the PDF, detects type and adds watermarks."""
        resultado = self.DetectKeywords(pdf_path)
        is_individual = resultado['is_individual']

        doc = fitz.open(pdf_path)
        self.AddWatermark(doc, is_individual)
        
        for page_number in range(len(doc)):
            page = doc[page_number]
            if self.DeleteTextWithRegex(page, self.PATTERN_INDIVIDUAL if is_individual else self.PATTERNS_CORPORATE):
                self.AddSecondWatermark(page)

        doc.save(output_path)
        doc.close()


class TestarImpactoAmbiental:
    def __init__(self):
        # Definition of Regex patterns that will recognize RFC, INE, and names of individuals
        self.PATTERNS = {
            "rfc": r'(?:R[e|i]g[i|s]st[r|i|o]o Federal de Contribuyentes)\s*(\w+\s*\d*)',
            "ine": r'(?:Instituto Naciona[l|i] Electora[l|i] con c[l|i]ave)\s*(\w+\s*\d*)',
            "repPropia": r'(?:C\.)\s[A-Za-záéíóúñÑ\s]+,\s*(?:en representacion)',
            "acredita": r'(?:C\.)\s([A-Za-záéíóúñÑ\s]+)(?=\s*acredita)'
        }

    def DetectKeywords(self, pdf_path):
        """Detects whether the PDF belongs to an individual or a corporate entity."""
        document = fitz.open(pdf_path)
        patterns_found = {
            'is_individual': False,
            'is_corporate': False
        }

        for page_number in range(len(document)):
            page = document[page_number]
            text = page.get_text()

            # Checks if there is individual or corporate representation by a keyword found only in individual documents
            if "en representacion" in text:
                patterns_found['is_individual'] = True
                break 
            else:
                patterns_found['is_corporate'] = True

        document.close()
        return patterns_found

    def DeleteTextByCoordinate(self, pdf_path, is_individual):
        """Removes text in specific coordinates depending on the document type."""
        doc = fitz.open(pdf_path)
        page = doc[0]

        # Size and coordinates of the rectangle for text removal
        if is_individual:
            text_rect = fitz.Rect(70, 180, 400, 295)
        else:
            text_rect = fitz.Rect(70, 235, 450, 300)

        text_to_redact = page.get_text("text", clip=text_rect)
        if text_to_redact:
            page.add_redact_annot(text_rect, fill=(0, 0, 0))

        page.apply_redactions()
        return doc  # Returns the modified document
    
    def AddWatermark(self, doc, is_individual): 
        """Adds a watermark to the document based on the type."""
        packet = io.BytesIO()  # Creates an in-memory buffer for the temporary PDF.
        can = canvas.Canvas(packet, pagesize=letter)

        # Defines the text of the watermark according to the document type.
        if is_individual:
            rect_x, rect_y, rect_width, rect_height = 65, 490, 380, 125
            text_lines = [
                "Nombre, domicilio, teléfono y correo electrónico de Persona Física, art.",
                "113, fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
            ]
        else:
            rect_x, rect_y, rect_width, rect_height = 65, 485, 380, 80
            text_lines = [
                "Domicilio, teléfono y correo electrónico del Representante Legal, art. 113,",
                "fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
            ]

        # Configuration and values for the background of the rectangle
        can.setFillColor(black) 
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        # Values for the text to be written
        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        line_height = 2
        can.setFillColor(red)

        for line in text_lines:
            text_object.textLine(line)
            text_object.moveCursor(0, -line_height)

        can.drawText(text_object)
        can.save() 

        packet.seek(0) 

        # Creates a temporary file for the watermark.
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name
        
        # Responsible for printing the watermark only on the first page
        page = doc[0]
        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0) 

    def DeleteTextWithRegex(self, page, pattern):
        """Removes text based on regex patterns on a page."""
        matches = re.findall(pattern, page.get_text(), re.IGNORECASE | re.MULTILINE)
        for match in matches:
            rects = page.search_for(match, quads=True)
            # Size of the rectangle for text removal
            for rect in rects:
                x0, y0 = rect[0].x, rect[0].y
                x1, y1 = rect[3].x, rect[3].y
                margin = 2
                adjusted_rect = fitz.Rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin)

                # Adds the redaction annotation
                page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))
        # Applies the text removal
        page.apply_redactions()  

    def AddSecondWatermark(self, page): 
        """Adds a second watermark to the page if regex finds patterns in those coordinates."""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Defines the dimensions and content of the second watermark.
        rect_x = 0
        rect_y = 200
        rect_width = 70
        rect_height = 150
        text_lines = [
            "Nombre, RFC y",
            "número OCR",
            "de credencial",
            "de elector de,",
            "Persona Física,",
            "art. 113,",
            "fracción I de la",
            "LFTAIP y art",
            "16, primer",
            "párrafo de la",
            "LGTAIP."
        ]

        # Draws the background of the second watermark.
        can.setFillColor(black)
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        # Creates the text object for the watermark.
        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        line_height = 2
        can.setFillColor(red)

        for line in text_lines:
            text_object.textLine(line)
            text_object.moveCursor(0, -line_height)

        can.drawText(text_object)
        can.save()
        packet.seek(0)

        # Prepares the overlay of the watermark on the page.
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name

        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0)

    def ProcessPDF(self, pdf_path, output_path):
        """This function will handle processing the PDF document."""
        # Step 1: Call the function to recognize the document type
        resultado = self.DetectKeywords(pdf_path)
        is_individual = resultado['is_individual']
        # Step 2: Call the function to remove text by coordinates
        doc = self.DeleteTextByCoordinate(pdf_path, is_individual)
        # Step 3: Call the function to add watermark
        self.AddWatermark(doc, is_individual)

        # Step 4: Remove text using regex for each pattern on each page.
        for page_number in range(len(doc)):
            page = doc[page_number]
            for pattern in self.PATTERNS.values():
                self.DeleteTextWithRegex(page, pattern)

        # Step 5: Add the second watermark where patterns are detected.
        for page_number in range(len(doc)):
            page = doc[page_number]
            for pattern in self.PATTERNS.values():
                if re.search(pattern, page.get_text(), re.IGNORECASE):
                    self.AddSecondWatermark(page)
                    break  # Exit the loop if a pattern was found

        # Save the final document.
        doc.save(output_path)
        doc.close()
 

class DeleteQR:
    def __init__(self, pdf_path, output_path):
        self.pdf_path = pdf_path
        self.output_path = output_path

    def FindQRCoordinates(self):
        pdf_document = fitz.open(self.pdf_path)
        pages_data = []

        # Extraer imágenes y coordenadas
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            images = page.get_images(full=True)

            page_data = {'images': []}

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                image = Image.open(io.BytesIO(image_bytes))

                img_rect = page.get_image_rects(xref)[0]
                coords = (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)

                page_data['images'].append({'image': image, 'coords': coords})

            pages_data.append(page_data)

        for i, page_data in enumerate(pages_data):
            for img_data in page_data['images']:
                rounded_coords = tuple(round(coord) for coord in img_data["coords"])

        pagina_final = len(pages_data) - 1
        coordenadas_ultima_pagina = {tuple(round(coord) for coord in img_data['coords']) 
                                      for img_data in pages_data[pagina_final]['images']}

        coordenadas_previas = set()
        for pagina in range(pagina_final):
            coordenadas_previas.update(tuple(round(coord) for coord in img_data['coords']) 
                                       for img_data in pages_data[pagina]['images'])

        coordenadas_diferentes = coordenadas_ultima_pagina - coordenadas_previas

        # Dibujar figuras en las coordenadas diferentes
        for coords in coordenadas_diferentes:
            rect_coords = list(coords)  # Convertir tupla a lista
            rect_color = (0, 0, 0)  # Verde en RGB
            fill_color = (0, 0, 0)  # Relleno verde

            # Dibujar en la última página
            page = pdf_document[pagina_final]
            page.draw_rect(rect_coords, color=rect_color, width=2, fill=fill_color)

        # Guardar cambios antes de añadir la marca de agua
        pdf_document.save(self.output_path)
        
        # Añadir marca de agua
        self.AddQrWatermark()

        # Cerrar el documento
        pdf_document.close()

    def AddQrWatermark(self):
        """Añade una marca de agua a la última página del documento."""
        packet = io.BytesIO()  # Crea un buffer en memoria para el PDF temporal.
        can = canvas.Canvas(packet, pagesize=letter)

        text = "Arma mocho el QR."
        rect_x, rect_y, rect_width, rect_height = 70, 100, 250, 75

        can.setFillColor((0, 0, 0))  # Negro
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        can.setFillColor((1, 0, 0))  # Rojo

        text_object.textLine(text)
        can.drawText(text_object)
        can.save()

        packet.seek(0)

        # Crear un archivo temporal para la marca de agua
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name

        # Aplicar la marca de agua a la última página
        doc = fitz.open(self.output_path)  # Abrir en modo incremental
        page = doc[-1]  # Obtener la última página
        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0)
        
        # Guardar cambios
        doc.saveIncr()  # Guardar de manera incremental
        doc.close()
