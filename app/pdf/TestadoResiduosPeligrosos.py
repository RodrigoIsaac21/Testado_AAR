import io

import os

import re

import tempfile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, red

import fitz

class TestarResiduosPeligrosos:

    def __init__(self):
        self.PATTERNS_CORPORATE = {
            'Addresses': r'(?<=\sC\.V\.)\s+(?!Ubicación de la instalación)([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+)\s*([^\.]+)\.',
            'EmailAddresses': r'\s*(CORREO:|Correo electrónico:)\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'PhoneNumber': r'(?:Teléfono:|\sTEL:)\s*(?:\+52\s*|\s*52\s*)?\(?\d+\)?(?:[\s-]?\d+)*(?:\s*(?:,\s*|\sy\s*)\s*(?:\+52\s*|\s*52\s*)?\(?\d+\)?(?:[\s-]?\d+)*)*',
            'CURP': r'\b[A-Z]{4}\d{6}[HM]\d{2}[A-Z]{3}[A-Z\d]\b', 
            'RFC': r'\b[A-ZÑ&]{3,4}-?\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[-]?[A-Z\d]{2}[A\d]\b',
        }
        self.PATTERN_INDIVIDUAL = {
            'IndividualNames': r'C\.\s([A-ZÁÉÍÓÚÑ][a-záéíóúñÁÉÍÓÚÑ]*(\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñÁÉÍÓÚÑ]*)*)\s*((?=Ubicación de la instalación)|(?:Persona física con actividad empresarial)|(?=\s\s))',
            'EmailAddresses': r'\s*(CORREO:|Correo electrónico:)\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'PhoneNumber': r'(?:Teléfono:|\sTEL:)\s*(?:\+52\s*|\s*52\s*)?\(?\d+\)?(?:[\s-]?\d+)*(?:\s*(?:,\s*|\sy\s*)\s*(?:\+52\s*|\s*52\s*)?\(?\d+\)?(?:[\s-]?\d+)*)*',
            'CURP': r'\b[A-Z]{4}\d{6}[HM]\d{2}[A-Z]{3}[A-Z\d]\b',
            'RFC': r'\b[A-ZÑ&]{3,4}-?\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[-]?[A-Z\d]{2}[A\d]\b',
            'IndividualAddresses': r'(?<=Persona física con actividad empresarial)\s+(?!Ubicación de la instalación)([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+)\s*([^\.]+)\.'
        }

    def DetectKeywords(self, pdf_path):
        with fitz.open(pdf_path) as document:
            patterns_found = {'is_individual': False, 'is_corporate': False}

            for page in document:
                text = page.get_text()

                if "Persona física" in text:
                    patterns_found['is_individual'] = True
                    break
                else:
                    patterns_found['is_corporate'] = True

        return patterns_found
    
    def RedactMatches(self, doc, is_individual):
        already_redacted = set()  
        patterns = self.PATTERN_INDIVIDUAL if is_individual else self.PATTERNS_CORPORATE
        watermark_patterns = ['IndividualNames', 'RFC', 'CURP'] if is_individual else ['RFC', 'CURP']

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            page_height = page.rect.height
            one_third_height = page_height / 3
            
            for pattern_name, pattern in patterns.items():
                if pattern_name in ['Addresses', 'IndividualAddresses'] and page_num == 0:
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        found_text = match.group().strip()
                        
                        if found_text not in already_redacted:
                            already_redacted.add(found_text)  
                            text_instances = page.search_for(found_text)
                            
                            for inst in text_instances:
                                x0, y0 = inst[0], inst[1]
                                x1, y1 = inst[2], inst[3]
                                
                                margin = 2 
                                adjusted_rect = fitz.Rect(x0 + margin, y0 + margin, x1 - margin, y1 - margin)

                                if adjusted_rect.y1 <= one_third_height:
                                    page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))  
                else:
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        found_text = match.group().strip()
                        
                        if found_text not in already_redacted:
                            already_redacted.add(found_text) 
                            text_instances = page.search_for(found_text)
                            
                            for inst in text_instances:
                                x0, y0 = inst[0], inst[1]
                                x1, y1 = inst[2], inst[3]
                                
                                margin = 2  
                                adjusted_rect = fitz.Rect(x0 + margin, y0 + margin, x1 - margin, y1 - margin)

                                page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))  
            page.apply_redactions()

            for pattern_name in watermark_patterns:
                pattern = patterns[pattern_name]
                if re.search(pattern, text):
                    self.AddSecondWatermark(page)

    def AddSecondWatermark(self, page): 
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        rect_x = 0
        rect_y = 200
        rect_width = 55
        rect_height = 150
        text_lines = [
            "Nombre de",
            "Persona",
            "Física",
            "art. 113,",
            "fracción",
            "I de la",
            "LFTAIP ",
            "y art 16,",
            "primer",
            "párrafo de",
            "la LGTAIP."
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

    def AddWatermark(self, doc, is_individual):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        if is_individual:
            rect_x, rect_y, rect_width, rect_height = 270, 600, 300, 35
            text_lines = [
                "Nombre, domicilio, teléfono y correo electrónico de Persona Física, art.",
                "113, fracción I de la LFTAIP y art. 116, primer párrafo de la LGTAIP."
            ]
        else:
            rect_x, rect_y, rect_width, rect_height = 270, 560, 300, 35
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

    def ProcessPDF(self, pdf_path, output_path):
        resultado = self.DetectKeywords(pdf_path)
        is_individual = resultado['is_individual']

        with fitz.open(pdf_path) as doc:
            self.RedactMatches(doc, is_individual)
            self.AddWatermark(doc, is_individual)  
            doc.save(output_path)