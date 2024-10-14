import io

import os

import re

import tempfile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, red

import fitz

class TestarImpactoAmbiental:
    def __init__(self):
        self.PATTERNS = {
            "rfc": r'(?:R[e|i]g[i|s]st[r|i|o]o Federal de Contribuyentes)\s*(\w+\s*\d*)',
            "ine": r'(?:Instituto Naciona[l|i] Electora[l|i] con c[l|i]ave)\s*(\w+\s*\d*)',
            "repPropia": r'(?:C\.)\s[A-Za-záéíóúñÑ\s]+,\s*(?:en representacion)',
            "acredita": r'(?:C\.)\s([A-Za-záéíóúñÑ\s]+)(?=\s*acredita)'
        }

    def DetectKeywords(self, pdf_path):
        document = fitz.open(pdf_path)
        patterns_found = {
            'is_individual': False,
            'is_corporate': False
        }

        for page_number in range(len(document)):
            page = document[page_number]
            text = page.get_text()

            if "en representacion" in text:
                patterns_found['is_individual'] = True
                break 
            else:
                patterns_found['is_corporate'] = True

        document.close()
        return patterns_found

    def DeleteTextByCoordinate(self, pdf_path, is_individual):
        doc = fitz.open(pdf_path)
        page = doc[0]

        if is_individual:
            text_rect = fitz.Rect(70, 180, 400, 295)
        else:
            text_rect = fitz.Rect(70, 235, 450, 300)

        text_to_redact = page.get_text("text", clip=text_rect)
        if text_to_redact:
            page.add_redact_annot(text_rect, fill=(0, 0, 0))

        page.apply_redactions()
        return doc  
    def AddWatermark(self, doc, is_individual): 
        packet = io.BytesIO()  
        can = canvas.Canvas(packet, pagesize=letter)

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

    def DeleteTextWithRegex(self, page, pattern):
        """Removes text based on regex patterns on a page."""
        matches = re.findall(pattern, page.get_text(), re.IGNORECASE | re.MULTILINE)
        for match in matches:
            rects = page.search_for(match, quads=True)
            for rect in rects:
                x0, y0 = rect[0].x, rect[0].y
                x1, y1 = rect[3].x, rect[3].y
                margin = 2
                adjusted_rect = fitz.Rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin)

                page.add_redact_annot(adjusted_rect, fill=(0, 0, 0))
        page.apply_redactions()  

    def AddSecondWatermark(self, page): 
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

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

    def ProcessPDF(self, pdf_path, output_path):
        resultado = self.DetectKeywords(pdf_path)
        is_individual = resultado['is_individual']
        doc = self.DeleteTextByCoordinate(pdf_path, is_individual)

        self.AddWatermark(doc, is_individual)

        for page_number in range(len(doc)):
            page = doc[page_number]
            for pattern in self.PATTERNS.values():
                self.DeleteTextWithRegex(page, pattern)

        for page_number in range(len(doc)):
            page = doc[page_number]
            for pattern in self.PATTERNS.values():
                if re.search(pattern, page.get_text(), re.IGNORECASE):
                    self.AddSecondWatermark(page)
                    break 

        doc.save(output_path)
        doc.close()
