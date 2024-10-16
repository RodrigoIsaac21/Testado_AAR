#TODO class to delete QR
import fitz

import io

import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import red, black

import tempfile

from PIL import Image



class DeleteQR:
    def __init__(self, pdf_path, output_path):
        self.pdf_path = pdf_path
        self.output_path = output_path

    def FindQRCoordinates(self):
        pdf_document = fitz.open(self.pdf_path)
        pages_data = []

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

        final_page = len(pages_data) - 1
        last_page_coordinates = {tuple(round(coord) for coord in img_data['coords']) 
                                 for img_data in pages_data[final_page]['images']}

        previous_coordinates = set()
        for page in range(final_page):
            previous_coordinates.update(tuple(round(coord) for coord in img_data['coords']) 
                                        for img_data in pages_data[page]['images'])

        different_coordinates = last_page_coordinates - previous_coordinates

        for coords in different_coordinates:
            rect_coords = list(coords)  
            rect_color = (0, 0, 0)  
            fill_color = (0, 0, 0)  
            page = pdf_document[final_page]
            page.draw_rect(rect_coords, color=rect_color, width=2, fill=fill_color)

        pdf_document.save(self.output_path)
        self.AddQrWatermark()
        pdf_document.close()

    def AddQrWatermark(self):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        text = "QR art. 113"
        rect_x, rect_y, rect_width, rect_height = 70, 100, 250, 75

        can.setFillColor((0, 0, 0))  
        can.rect(rect_x, rect_y, rect_width, rect_height, fill=True, stroke=False)

        text_object = can.beginText()
        text_object.setTextOrigin(rect_x + 5, rect_y + rect_height - 15)
        text_object.setFont("Helvetica", 9)
        can.setFillColor((1, 0, 0)) 

        text_object.textLine(text)
        can.drawText(text_object)
        can.save()

        packet.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(packet.getvalue())
            temp_pdf_path = temp_file.name

        doc = fitz.open(self.output_path) 
        page = doc[-1] 
        new_pdf = fitz.open(temp_pdf_path)
        page.show_pdf_page(page.rect, new_pdf, 0)
        
        doc.saveIncr()
        doc.close()
