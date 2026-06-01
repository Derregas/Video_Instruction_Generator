# flask_app/document_generators.py
import os
import json
import logging
from fpdf import FPDF
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, Cm
from abc import ABC, abstractmethod
from typing import Type, Dict, Literal, Optional
from docx.enum.text import WD_ALIGN_PARAGRAPH
from src.services.file_management_service import FileManagementService

logger = logging.getLogger(__name__)

class BaseDocument(ABC):
    base_fonts_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
    
    def __init__(self, task_id: Optional[str] = None):
        """
        Инициализирует документ.
        
        Args:
            task_id: ID задачи, используется для поиска картинок в result/temp директориях
        """
        self.task_id = task_id
    
    @abstractmethod
    def create(self, content: str, filename: str) -> None:
        pass
    
    def _find_image_path(self, image_id: str) -> Optional[str]:
        """
        Находит путь к картинке.
        
        Если task_id известен, ищет в result/images/ и temp директориях.
        Иначе ищет в директории выходного файла (для обратной совместимости).
        """
        if self.task_id and image_id:
            # Ищем в result/images и temp директориях
            path = FileManagementService.get_task_file_path(self.task_id, image_id, file_type='image')
            if path:
                return path
        return None
    
    @staticmethod
    def _to_json(content):
        if isinstance(content, dict):
            return content
        return json.loads(content)
    
    @staticmethod
    def format_time(seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02}:{s:02}"

class DocxDocument(BaseDocument):
    # TODO: Проще не заморачиваться со стилями, а создать шаблон документа с
    # готовыми стилями заголовков, так и редактировать проще будет
    @staticmethod
    def set_style_font(style, font_name):
        # Стандартная установка
        style.font.name = font_name
        # Глубокая установка через XML для всех типов символов (ascii, кириллица и т.д.)
        rFonts = style.element.rPr.get_or_add_rFonts()
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
        rFonts.set(qn('w:cs'), font_name)

    @staticmethod
    def set_style(document):
        if 'Title' in document.styles:
            t_style = document.styles['Title']
            DocxDocument.set_style_font(t_style, 'Times New Roman')
            t_style.font.size = Pt(18)
            t_style.font.bold = True
            t_style.font.color.rgb = None # Сброс цвета
            # Убираем рамку программно
            pPr = t_style.element.get_or_add_pPr()
            pBdr = pPr.find(qn('w:pBdr'))
            if pBdr is not None:
                pPr.remove(pBdr)
        if 'Heading 1' in document.styles:
            h1_style = document.styles['Heading 1']
            DocxDocument.set_style_font(h1_style, 'Times New Roman')
            h1_style.font.size = Pt(14)
            h1_style.font.bold = True
            h1_style.font.color.rgb = None
        if 'Normal' in document.styles:
            normal = document.styles['Normal']
            DocxDocument.set_style_font(normal, 'Times New Roman')
            normal.font.size = Pt(14)

    def create(self, content: str, filename: str) -> None:
        doc = Document()
        json_content = self._to_json(content)
        # Настраиваем основные стили
        self.set_style(doc)
        # --- 1. НАСТРОЙКА ОТСТУПОВ СТРАНИЦЫ ---
        section = doc.sections[0]
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(1.5)

        title = doc.add_heading(json_content['instruction'].title, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in title.runs:
            run.font.name = 'Times New Roman'

        key_words_h = doc.add_heading("Ключевые слова:", level=2)
        for run in key_words_h.runs:
            run.font.name = 'Times New Roman'
        words = ", ".join(json_content['keywords'].keywords_list)
        k_words = doc.add_paragraph(words)
        k_words.paragraph_format.first_line_indent = Cm(0.75)

        description_h = doc.add_heading("Назначение", level=1)
        for run in description_h.runs:
            run.font.name = 'Times New Roman'
        desc_p = doc.add_paragraph(json_content['instruction'].description)
        desc_p.paragraph_format.first_line_indent = Cm(0.75)

        for index, step in enumerate(json_content['steps'], start=1):
            # Добавляем заголовок шага
            heading = doc.add_heading(f"{index}. {step.title}", level=1)
            for run in heading.runs:
                run.font.name = 'Times New Roman'

            # Описание
            p = doc.add_paragraph(step.text)
            p.paragraph_format.first_line_indent = Cm(0.75) # Красная строка
            p.paragraph_format.space_after = Pt(10)         # Отступ после абзаца
            
            # ВСТАВКА КАРТИНКИ
            # Ищем картинку с использованием task_id
            img_path = self._find_image_path(step.image_id)
            
            # Для обратной совместимости: ищем в директории документа
            if not img_path:
                fallback_path = os.path.join(os.path.dirname(filename), step.image_id)
                if os.path.exists(fallback_path):
                    img_path = fallback_path
            
            if img_path and os.path.exists(img_path):
                try:
                    doc.add_picture(img_path, width=Cm(12))
                    # Центрируем картинку (она считается как отдельный параграф)
                    last_paragraph = doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    logger.error(f"Ошибка вставки картинки {img_path}: {e}")
                    doc.add_paragraph(f"[Ошибка изображения: {step.image_id}]")
            else:
                logger.warning(f"Файл картинки не найден: {step.image_id}")

            # Таймкоды
            time_text = f"Таймкод: {self.format_time(float(step.time_start))} - {self.format_time(float(step.time_end))}"
            caption = doc.add_paragraph(time_text)
            caption.italic = True # type: ignore
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.save(filename)
        
class PdfDocument(BaseDocument):

    def _setup_fonts(self, pdf):
        """Вспомогательный метод для регистрации шрифтов"""
        font_styles: list[tuple[Literal['', 'B', 'I', 'BI'], str]] = [
            ('', 'times.ttf'), ('B', 'timesbd.ttf'),
            ('I', 'timesi.ttf'), ('BI', 'timesbi.ttf'),
        ]
        for style, font_file in font_styles:
            path = os.path.join(self.base_fonts_path, font_file)
            if os.path.exists(path):
                pdf.add_font('TimesNewRoman', style, path, uni=True)
            else:
                logger.warning(f"Файл шрифта не найден: {path}")

    def create(self, content: str, filename: str) -> None:
        json_content = self._to_json(content)

        pdf = FPDF()
        
        self._setup_fonts(pdf)

        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Заголовок
        pdf.set_font('TimesNewRoman', 'B', 16)
        pdf.cell(0, 10, json_content['instruction'].title, 0, 1, 'C')
        # Ключевые слова
        pdf.set_font('TimesNewRoman', '', 14)
        pdf.cell(0, 10, "Ключевые слова:", ln=True)
        pdf.set_font('TimesNewRoman', '', 13)
        pdf.set_x(pdf.l_margin + 8)
        words = ", ".join(json_content['keywords'].keywords_list)
        pdf.multi_cell(0, 8, words)
        pdf.ln(3)
        pdf.set_x(pdf.l_margin)
        # Введение
        pdf.set_font('TimesNewRoman', 'B', 14)
        pdf.cell(0, 10, "Назначение", ln=True)
        pdf.set_font('TimesNewRoman', '', 14)
        pdf.multi_cell(0, 8, json_content['instruction'].description)
        pdf.ln(3)

        for index, step in enumerate(json_content['steps'], start=1):
            y = pdf.get_y()
            if pdf.get_y() > (297 - 50): 
                pdf.add_page()

            pdf.set_font('TimesNewRoman', 'B', 14)
            pdf.cell(0, 10, f"{index}. \t{step.title}", ln=True)

            pdf.set_font('TimesNewRoman', '', 14)
            pdf.multi_cell(0, 8, step.text)
            pdf.ln(3)

            if pdf.get_y() > (270 - 120): 
                pdf.add_page()

            # Вставляем картинку
            # Ищем картинку с использованием task_id
            img_path = self._find_image_path(step.image_id)
            
            # Для обратной совместимости: ищем в директории документа
            if not img_path:
                fallback_path = os.path.join(os.path.dirname(filename), step.image_id)
                if os.path.exists(fallback_path):
                    img_path = fallback_path
            
            if img_path and os.path.exists(img_path):
                try:
                    pdf.image(img_path, x=10, w=100)
                    pdf.ln(1)
                except Exception as e:
                    logger.error(f"Ошибка вставки картинки {img_path}: {e}")

            pdf.set_font('TimesNewRoman', 'I', 10)
            pdf.cell(0, 10, f"Время: {self.format_time(float(step.time_start))} - {self.format_time(float(step.time_end))}", ln=True)
            pdf.ln(5)

        pdf.output(filename)

class DocumentFactory:
    _rigestry: Dict[str, Type[BaseDocument]] = {}

    @classmethod
    def register(cls, ext: str, doc_cls: Type[BaseDocument]) -> None:
        cls._rigestry[ext.lower()] = doc_cls
    @classmethod
    def create_document(cls, ext: str, task_id: Optional[str] = None) -> BaseDocument:
        ext = ext.lower()
        if ext not in cls._rigestry:
            raise ValueError(f"Неподдерживаемое расширение: {ext}")
        return cls._rigestry[ext](task_id=task_id)

DocumentFactory.register(ext=".docx", doc_cls=DocxDocument)
DocumentFactory.register(ext=".pdf", doc_cls=PdfDocument)

class DocumentCreator:
    @staticmethod
    def create(text: str, path: str, task_id: Optional[str] = None) -> None:
        _, doc_suffix = os.path.splitext(path)
        document = DocumentFactory.create_document(ext=doc_suffix, task_id=task_id)
        document.create(text, path)