import os

import re

import fitz

import io

import tempfile

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, red

class TestarAtmosefera:
    def __init__(self):
        self.PATTERNS_CORPORATE = {
        }

        self.PATTERN_INDIVIDUAL = {
            r'(?<=por medio de la cual la)\s+(C\.\s*)+([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)+',
            r'(?<=personalidad jurídica de la)\s+(C\.\s*)+([A-Z][a-z]*(?:\s+[A-Z][a-z]*)+)'
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

    def DeleteTextByCoordinate(self, pdf_path, is_individual):
        doc = fitz.open(pdf_path)
        page = doc[0]

        y_offset = 0  
        if is_individual:
            text_rect = fitz.Rect(55, 180, 300, 265)
        else:
            text_rect = fitz.Rect(55, 220, 500, 240)

        def adjust_coordinates(rect, offset):
            return fitz.Rect(rect.x0, rect.y0 + offset, rect.x1, rect.y1 + offset)

        text_to_redact = page.get_text("text", clip=text_rect).strip()

        if "PPPP" in text_to_redact:
            text_rect = adjust_coordinates(text_rect, -5) 

        if "C.V." in text_to_redact:
            text_rect = adjust_coordinates(text_rect, 5)  

        keywords_positive = ["alcaldía", "municipio", "estado"]
        keywords_negative = ["Calle", "pueblo", "estado"]

        if not any(word in text_to_redact.lower() for word in keywords_positive):
            text_rect = adjust_coordinates(text_rect, 5)  

        if not any(word in text_to_redact.lower() for word in keywords_negative):
            text_rect = adjust_coordinates(text_rect, -5)  

        text_to_redact = page.get_text("text", clip=text_rect).strip() 
        if text_to_redact:
            page.add_redact_annot(text_rect, fill=(0, 0, 0))

        page.apply_redactions()
        return doc

    def RedactMatches(self, doc, is_individual):
        if not is_individual:
            return set()

        all_matches = []
        redacted_pages = set()  
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            for pattern in self.PATTERN_INDIVIDUAL:
                matches = list(re.finditer(pattern, text))
                all_matches.extend(matches)
                
                for match in matches:
                    found_text = match.group().strip()
                    text_instances = page.search_for(found_text)
                    
                    for inst in text_instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))  
                    redacted_pages.add(page_num)  

            page.apply_redactions()

        print("Coincidencias encontradas:")
        for match in all_matches:
            print(match.group().strip())
        
        return redacted_pages 
 

    def AddWatermark(self, doc, is_individual): 
        """Adds a watermark to the document based on the type."""
        packet = io.BytesIO() 
        can = canvas.Canvas(packet, pagesize=letter)

        if is_individual:
            rect_x, rect_y, rect_width, rect_height = 450, 540, 200, 80
            text_lines = [
                "Domicilio, teléfono y correo electrónico",
                "del Representante Legal, art. 113,",
                "fracción I de la LFTAIP",
                "y art. 116, primer párrafo de la LGTAIP."
            ]
        else:
            rect_x, rect_y, rect_width, rect_height = 450, 540, 200, 80
            text_lines = [
                "Domicilio, teléfono y correo electrónico",
                "del Representante Legal, art. 113,",
                "fracción I de la LFTAIP",
                "y art. 116, primer párrafo de la LGTAIP."
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


    def ProcessPDF(self, pdf_path, output_path):
        resultado = self.DetectKeywords(pdf_path)
        is_individual = resultado['is_individual']
        doc = self.DeleteTextByCoordinate(pdf_path, is_individual)

        redacted_pages = self.RedactMatches(doc, is_individual)

        self.AddWatermark(doc, is_individual)

        for page_num in redacted_pages:
            self.AddSecondWatermark(doc[page_num])

        doc.save(output_path)
        doc.close()