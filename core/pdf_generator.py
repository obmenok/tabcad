import os
import sys
import hashlib

# Patch for Python 3.8 compatibility with reportlab >= 4.2
if sys.version_info < (3, 9):
    _original_md5 = hashlib.md5
    def _md5_patched(*args, **kwargs):
        kwargs.pop('usedforsecurity', None)
        return _original_md5(*args, **kwargs)
    hashlib.md5 = _md5_patched

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import base64
import numpy as np
from datetime import datetime
from core.tip_force import calculate_tip_force

class TabletPDFGenerator:
    def __init__(self, filename, params, metrics, drawing_2d_b64=None, views_3d=None):
        self.filename = filename
        self.params = params
        self.metrics = metrics
        self.drawing_2d_b64 = drawing_2d_b64
        self.views_3d = views_3d or []
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.width, self.height = A4
        
        # --- ШРИФТ ISO 3098 (OSIFONT) ---
        self.font_name = "Helvetica"
        # osifont.ttf - это наш гарантированно работающий TTF
        font_file = os.path.join("assets", "osifont.ttf")
        if os.path.exists(font_file):
            try:
                pdfmetrics.registerFont(TTFont('ISO3098', font_file))
                self.font_name = "ISO3098"
            except Exception as e:
                print(f"Font registration failed: {e}")
        
        self.font_bold = self.font_name

        self.left_m = 20 * mm
        self.right_m = 7 * mm
        self.top_m = 6 * mm
        self.bot_m = 6 * mm
        self.content_w = self.width - self.left_m - self.right_m

        self._require_params(["shape", "W", "Tt", "density", "Hb", "Dc"])

    def _require_params(self, keys):
        missing = [k for k in keys if k not in self.params or self.params[k] is None]
        if missing:
            raise ValueError(f"Отсутствует параметр(ы): {', '.join(missing)}")

    def _line(self, x1, y1, x2, y2, width=0.1):
        self.c.setLineWidth(width * mm)
        self.c.line(x1, y1, x2, y2)

    def draw_frame(self):
        """Тонкая внешняя рамка (0.3мм)"""
        self.c.setLineWidth(0.3 * mm)
        self.c.rect(self.left_m, self.bot_m, self.content_w, self.height - self.top_m - self.bot_m)

    def draw_title_block(self):
        """Отрисовка штампа (основной надписи) в стиле ISO 7200"""
        bx = self.left_m
        by = self.bot_m
        
        # Масштаб для растягивания с 180mm до ширины рамки (185mm)
        scale = self.content_w / (180 * mm)
        
        def s(val):
            return val * scale

        line_width_mm = 0.3
        
        # Внешняя рамка штампа
        self.c.setLineWidth(line_width_mm * mm)
        self.c.rect(bx, by, self.content_w, s(36 * mm))
        
        # Горизонтальные линии штампа
        self._line(bx, by + s(12*mm), bx + s(180*mm), by + s(12*mm), width=line_width_mm)
        self._line(bx, by + s(24*mm), bx + s(140*mm), by + s(24*mm), width=line_width_mm)
        
        # Вертикальные линии штампа
        self._line(bx + s(80*mm), by, bx + s(80*mm), by + s(36*mm), width=line_width_mm)
        self._line(bx + s(140*mm), by + s(12*mm), bx + s(140*mm), by + s(36*mm), width=line_width_mm)
        self._line(bx + s(100*mm), by, bx + s(100*mm), by + s(12*mm), width=line_width_mm)
        self._line(bx + s(140*mm), by, bx + s(140*mm), by + s(12*mm), width=line_width_mm)
        self._line(bx + s(160*mm), by, bx + s(160*mm), by + s(12*mm), width=line_width_mm)

        def draw_cell(cx, cy, cw, ch, label, value, val_align="left", val_size=10, bold=False):
            # Label (top-left of cell)
            self.c.setFont(self.font_name, s(7))
            self.c.drawString(bx + s(cx) + s(1*mm), by + s(cy + ch) - s(3*mm), label)
            # Value (bottom-left or centered)
            if bold:
                self.c.setFont(self.font_bold, s(val_size))
            else:
                self.c.setFont(self.font_name, s(val_size))
            
            val_y = by + s(cy) + s(3*mm)
            if val_align == "left":
                self.c.drawString(bx + s(cx) + s(2*mm), val_y, value)
            elif val_align == "center":
                self.c.drawCentredString(bx + s(cx + cw/2), val_y, value)
        
        shape = str(self.params["shape"]).upper()
        w_val = float(self.params["W"])
        tt_val = float(self.params["Tt"])
        dwg_no = f"PN-{w_val:g}-{tt_val:g}"
        date_str = datetime.now().strftime('%d.%m.%Y')

        # Row 1 (top, y=24..36)
        draw_cell(0, 24*mm, 80*mm, 12*mm, "Title:", f"{shape} TABLET", val_size=12, bold=True)
        draw_cell(80*mm, 24*mm, 60*mm, 12*mm, "Created by:", "TabCAD Pro")
        
        # Owner Cell (y=12..36)
        self.c.setFont(self.font_name, s(7))
        self.c.drawString(bx + s(140*mm) + s(1*mm), by + s(12*mm + 24*mm) - s(3*mm), "Owner:")
        self.c.setFont(self.font_name, s(10))
        self.c.drawCentredString(bx + s(140*mm + 20*mm), by + s(12*mm + 10*mm), "TabCAD AI")
        
        # Row 2 (middle, y=12..24)
        draw_cell(0, 12*mm, 80*mm, 12*mm, "Document type:", "Tablet Specification")
        draw_cell(80*mm, 12*mm, 60*mm, 12*mm, "Approved by:", "Buyakov S.")
        
        # Row 3 (bottom, y=0..12)
        draw_cell(0, 0, 80*mm, 12*mm, "Drawing number:", dwg_no)
        draw_cell(80*mm, 0, 20*mm, 12*mm, "Language:", "EN", val_align="center")
        draw_cell(100*mm, 0, 40*mm, 12*mm, "Issue date:", date_str, val_align="center")
        draw_cell(140*mm, 0, 20*mm, 12*mm, "Revision:", "A", val_align="center")
        draw_cell(160*mm, 0, 20*mm, 12*mm, "Sheet:", "1 / 1", val_align="center")

    def insert_main_drawing(self):
        if not self.drawing_2d_b64: return
        _, encoded = self.drawing_2d_b64.split(",", 1)
        ir = ImageReader(BytesIO(base64.b64decode(encoded)))
        y_bot = self.bot_m + 105 * mm
        h = (self.height - self.top_m - 10 * mm) - y_bot
        self.c.drawImage(ir, self.left_m, y_bot, width=self.content_w, height=h, preserveAspectRatio=True, mask='auto')

    def draw_data_tables(self):
        scale = self.content_w / (180 * mm)
        x, y = self.left_m, self.bot_m + 36 * mm * scale
        m = self.metrics
        vol = m.get('Tablet_Vol', 0)
        sa = m.get('Tablet_SA', 0)
        density = float(self.params["density"])
        weight = vol * density
        
        tip_force_data = calculate_tip_force(self.params)
        tip_force_val = tip_force_data.get("selected_force")
        tip_force_str = f"{tip_force_val:.2f}" if tip_force_val is not None else "N/A"
        steel = self.params.get("tip_force_steel", "S7")
        
        data = [
            ["ENGINEERING DATA", "VALUE", "UNIT"],
            ["Perimeter", f"{m.get('Perimeter', 0):.2f}", "mm"],
            ["Die Hole SA", f"{m.get('Die_Hole_SA', 0):.2f}", "mm²"],
            ["Cup SA", f"{m.get('Cup_SA', 0):.2f}", "mm²"],
            ["Cup Volume", f"{m.get('Cup_Volume', 0):.2f}", "mm³"],
            ["Tablet SA", f"{sa:.2f}", "mm²"],
            ["Tablet Volume", f"{vol:.2f}", "mm³"],
            ["Tablet SA/V", f"{sa/vol if vol else 0:.2f}", "1/mm"],
            ["Tablet Density", f"{density:.2f}", "mg/mm³"],
            ["Tablet Weight", f"{weight:.2f}", "mg"],
            ["Max Tip Force", tip_force_str, "kN"],
        ]
        
        col_value = 25 * mm
        col_unit = 15 * mm
        col_data = 80 * mm * scale - col_value - col_unit
        t = Table(data, colWidths=[col_data, col_value, col_unit])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.3*mm, colors.black),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ]))
        t.wrapOn(self.c, self.width, self.height)
        t.drawOn(self.c, x, y)

    def draw_visuals_block(self):
        """Одиночный 3D вид (без рамок)"""
        x_start, y_start = self.left_m + 100 * mm, self.bot_m + 50 * mm
        v_size = 25 * mm # Увеличим размер для одиночного вида
        views_dict = {label: b64 for b64, label in self.views_3d}
        
        def place_v(label, vx, vy):
            if label in views_dict:
                _, encoded = views_dict[label].split(",", 1)
                img = ImageReader(BytesIO(base64.b64decode(encoded)))
                self.c.drawImage(img, vx, vy, width=v_size, height=v_size, preserveAspectRatio=True, mask='auto')
                self.c.setFont(self.font_name, 8)
                self.c.drawCentredString(vx + v_size/2, vy - 3*mm, label.upper())

        # Isometric (Centered in the area)
        offset_x = 20 * mm
        place_v("Isometric", x_start + offset_x, y_start + 10*mm)

    def generate(self):
        self.draw_frame()
        self.insert_main_drawing()
        self.draw_data_tables()
        self.draw_visuals_block()
        self.draw_title_block()
        self.c.showPage()
        self.c.save()
        return self.filename
