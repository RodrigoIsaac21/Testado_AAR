import fitz  # PyMuPDF

# Ruta del archivo PDF
pdf_path = r'C:\Users\operadora\Documents\Prueba5.pdf'
output_path = r'C:\Users\operadora\Documents\CoordenadasPrueba.pdf'

# Crear una nueva instancia de documento PDF
doc = fitz.open(pdf_path)

# Definir coordenadas y color para la figura
rect_coords = [0, 180, 400, 295]  # Coordenadas del rectángulo (x0, y0, x1, y1)
rect_color = (0, 1, 0)  # Color verde en RGB (0, 1, 0) (para verde)
fill_color = (0, 1, 0)  # Color verde en RGB (0, 1, 0) (para rellenar)

# Iterar a través de las páginas del documento
for page in doc:
    # Dibujar un rectángulo relleno en la página
    page.draw_rect(rect_coords, color=rect_color, width=2, fill=fill_color)

# Guardar el documento modificado
doc.save(output_path)

# Cerrar el documento
doc.close()

print(f"PDF modificado guardado en {output_path}")
