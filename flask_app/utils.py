import os
import json
from werkzeug.datastructures import FileStorage

def docs_size(docs: list[FileStorage]) -> int:
    total_size = 0
    for doc in docs:
        doc.seek(0, os.SEEK_END)    # Перемещаем указатель в конец файла
        size = doc.tell()           # Получаем позицию указателя в байтах - размер файла
        doc.seek(0)                 # возвращаем указатель в начало
        total_size += size
    return total_size

def docs_save(docs: list[FileStorage], request_temp_dir: str) -> list[str]:
    document_paths = []
    for doc in docs:
        doc_path = os.path.join(request_temp_dir, f"doc_{doc.filename}")
        doc.save(doc_path)
        document_paths.append(doc_path)
    return document_paths

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Manual PC Assembly', 0, 1, 'C')

def generate_pdf(data, output_path):
    json_data = json.loads(data)
    pdf = PDF()
    # Обязательно добавь шрифт с поддержкой русского языка!
    pdf.add_font('DejaVu', '', r'D:\Projects\Video_Instruction_Generator\flask_app\static\fonts\DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', r'D:\Projects\Video_Instruction_Generator\flask_app\static\fonts\DejaVuSans.ttf', uni=True) # Если нужен жирный
    pdf.add_font('DejaVu', 'I', r'D:\Projects\Video_Instruction_Generator\flask_app\static\fonts\DejaVuSans.ttf', uni=True) # Если нужен курсив
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for step in json_data['instructions']:
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 10, step['title'], ln=True)
        
        pdf.set_font('DejaVu', 'I', 10)
        pdf.cell(0, 10, f"Time: {step['start_time']} - {step['end_time']}", ln=True)
        
        # Вставляем картинку
        pdf.image(step['best_image_id'], x=10, w=100)
        pdf.ln(5)
        
        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 10, step['description'])
        pdf.ln(10)

    pdf.output(output_path)