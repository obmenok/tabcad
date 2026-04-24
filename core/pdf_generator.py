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

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.graphics import renderPDF
from io import BytesIO
from PIL import Image
import base64
import numpy as np
from datetime import datetime
from core.preset_naming import build_preset_base_name
from core.tip_force import calculate_tip_force

try:
    from svglib.svglib import svg2rlg
except Exception:
    svg2rlg = None


def pdf_supports_svg_drawings():
    return svg2rlg is not None

# "portrait" (default) keeps current layout.
# Switch to "landscape" to test landscape PDF layout.
PDF_ORIENTATION = "landscape"
# ISO 5455 preferred scales: enlargement and reduction factors.
ISO_SCALE_FACTORS = (10.0, 5.0, 4.0, 2.5, 2.0, 1.0, 0.5, 0.4, 0.25, 0.2, 0.1)

class TabletPDFGenerator:
    def __init__(self, filename, params, metrics, drawing_2d_b64=None, views_3d=None):
        self.filename = filename
        self.params = params
        self.metrics = metrics
        self.drawing_2d_b64 = drawing_2d_b64
        self.views_3d = views_3d or []
        
        ori = self.params.get("pdf_orientation", "portrait")
        self.is_landscape = str(ori).lower() == "landscape"
        self.page_size = landscape(A4) if self.is_landscape else A4
        self.c = canvas.Canvas(filename, pagesize=self.page_size)
        self.width, self.height = self.page_size
        
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

    def _full_title_name(self):
        shape = str(self.params.get("shape", "")).lower()
        profile = str(self.params.get("profile", "")).lower()
        is_modified = bool(self.params.get("is_modified"))

        shape_name = {
            "round": "Round",
            "capsule": "Modified Capsule" if is_modified else "Capsule",
            "oval": "Oval",
        }.get(shape, str(self.params.get("shape", "")).title())

        profile_name = {
            "concave": "Concave",
            "compound": "Compound Cup",
            "cbe": "Concave Bevel Edge",
            "ffre": "Flat Face Radius Edge",
            "ffbe": "Flat Face Bevel Edge",
            "modified_oval": "Modified Oval",
        }.get(profile, str(self.params.get("profile", "")).replace("_", " ").title())

        return f"{shape_name} {profile_name}".strip()

    def _landscape_regions(self):
        right_table_w = 88 * mm
        gap = 8 * mm
        x_right_table = self.width - self.right_m - right_table_w
        left_x = self.left_m
        left_w = max(40 * mm, x_right_table - self.left_m - gap)

        return {
            "right_table_x": x_right_table,
            "right_table_w": right_table_w,
            "left_x": left_x,
            "left_w": left_w,
            "title_w": 180 * mm,
            "title_h": 36 * mm,
        }

    def _model_bbox_mm(self):
        bounds = self.params.get("_render_2d_bounds")
        if isinstance(bounds, dict):
            req = [
                "content_xmin",
                "content_xmax",
                "content_ymin",
                "content_ymax",
                "view_xmin",
                "view_xmax",
                "view_ymin",
                "view_ymax",
            ]
            if all(k in bounds for k in req):
                obj_xmin = float(bounds["content_xmin"])
                obj_xmax = float(bounds["content_xmax"])
                obj_ymin = float(bounds["content_ymin"])
                obj_ymax = float(bounds["content_ymax"])
                view_xmin = float(bounds["view_xmin"])
                view_xmax = float(bounds["view_xmax"])
                view_ymin = float(bounds["view_ymin"])
                view_ymax = float(bounds["view_ymax"])
                view_w = max(1e-6, view_xmax - view_xmin)
                view_h = max(1e-6, view_ymax - view_ymin)
                return {
                    "obj_w": max(1e-6, obj_xmax - obj_xmin),
                    "obj_h": max(1e-6, obj_ymax - obj_ymin),
                    "obj_cx": (obj_xmin + obj_xmax) / 2,
                    "obj_cy": (obj_ymin + obj_ymax) / 2,
                    "view_w": view_w,
                    "view_h": view_h,
                    "view_xmin": view_xmin,
                    "view_ymin": view_ymin,
                }

        # Geometry-only bounds used for scale selection (ignores web white frame).
        w_val = float(self.params["W"])
        l_val = float(self.params["L"])
        tt = float(self.params["Tt"])

        cx_top, cy_top = 0.0, 0.0
        cx_side, cy_side = -(w_val / 2 + tt / 2 + 15.0), 0.0
        cx_front, cy_front = 0.0, -(l_val / 2 + tt / 2 + 15.0)

        obj_xmin = cx_side - tt / 2
        obj_xmax = cx_top + w_val / 2
        obj_ymin = cy_front - tt / 2
        obj_ymax = cy_top + l_val / 2

        x_min_val = cx_side - tt / 2 - 12.0
        x_max_val = cx_top + w_val / 2 + 15.0
        y_min_val = cy_front - tt / 2 - 8.0
        y_max_val = cy_top + l_val / 2 + 8.0
        center_x = (x_max_val + x_min_val) / 2
        center_y = (y_max_val + y_min_val) / 2
        max_range = max(x_max_val - x_min_val, y_max_val - y_min_val)
        view_w = max_range * 1.10
        view_h = max_range * 1.10
        view_xmin = center_x - view_w / 2
        view_ymin = center_y - view_h / 2

        return {
            "obj_w": obj_xmax - obj_xmin,
            "obj_h": obj_ymax - obj_ymin,
            "obj_cx": (obj_xmin + obj_xmax) / 2,
            "obj_cy": (obj_ymin + obj_ymax) / 2,
            "view_w": view_w,
            "view_h": view_h,
            "view_xmin": view_xmin,
            "view_ymin": view_ymin,
        }

    def _pick_iso_scale(self, zone_w_mm, zone_h_mm):
        forced_scale = self.params.get("_render_2d_scale_ratio")
        try:
            forced_scale = float(forced_scale)
            if forced_scale > 0:
                return forced_scale
        except Exception:
            pass

        bbox = self._model_bbox_mm()
        fits = [
            s
            for s in ISO_SCALE_FACTORS
            if bbox["obj_w"] * s <= zone_w_mm and bbox["obj_h"] * s <= zone_h_mm
        ]
        if fits:
            return max(fits)
        return 1.0

    def _format_scale_text(self, scale_ratio):
        scale_ratio = float(scale_ratio)
        if scale_ratio >= 1.0:
            return f"{scale_ratio:g}:1"
        return f"1:{(1.0 / scale_ratio):g}"

    def _landscape_drawing_zone(self):
        zone_x = 50 * mm
        zone_y = 60 * mm
        zone_w = 130 * mm
        zone_h = 130 * mm
        return zone_x, zone_y, zone_w, zone_h

    def _portrait_drawing_zone(self):
        zone_x = 50 * mm
        zone_y = 140 * mm
        zone_w = 130 * mm
        zone_h = 130 * mm
        return zone_x, zone_y, zone_w, zone_h

    def _drawing_zone(self):
        if self.is_landscape:
            return self._landscape_drawing_zone()
        return self._portrait_drawing_zone()

    def draw_frame(self):
        """Тонкая внешняя рамка (0.3мм)"""
        self.c.setLineWidth(0.3 * mm)
        self.c.rect(self.left_m, self.bot_m, self.content_w, self.height - self.top_m - self.bot_m)

    def draw_title_block(self):
        """Отрисовка штампа (основной надписи) в стиле ISO 7200"""
        if self.is_landscape:
            title_w = 180 * mm
            bx = self.width - self.right_m - title_w
            scale = 1.0
        else:
            bx = self.left_m
            # Portrait keeps historical behavior (stretched title block).
            scale = self.content_w / (180 * mm)
        by = self.bot_m
        
        def s(val):
            return val * scale

        line_width_mm = 0.3
        
        # Внешняя рамка штампа
        self.c.setLineWidth(line_width_mm * mm)
        self.c.rect(bx, by, s(180 * mm), s(36 * mm))
        
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
        
        title_name = self._full_title_name()
        dwg_no = build_preset_base_name(
            self.params.get("shape"),
            self.params.get("profile"),
            self.params.get("is_modified"),
            self.params.get("W"),
            self.params.get("L"),
            self.params.get("Tt"),
            self.params.get("b_type"),
            self.params.get("b_cruciform"),
            self.params.get("b_double_sided"),
        )
        date_str = datetime.now().strftime('%d.%m.%Y')
        _, _, zone_w, zone_h = self._drawing_zone()
        scale_ratio = self._pick_iso_scale(zone_w / mm, zone_h / mm)
        scale_text = self._format_scale_text(scale_ratio)

        pdf_created_by = self.params.get("pdf_created_by", "TabCAD Pro")
        pdf_approved_by = self.params.get("pdf_approved_by", "Buyakov S.")

        # Row 1 (top, y=24..36)
        draw_cell(0, 24*mm, 80*mm, 12*mm, "Title:", title_name, val_size=10, bold=True)
        draw_cell(80*mm, 24*mm, 60*mm, 12*mm, "Created by:", pdf_created_by)

        # Owner Cell (y=12..36)
        self.c.setFont(self.font_name, s(7))
        self.c.drawString(bx + s(140*mm) + s(1*mm), by + s(12*mm + 24*mm) - s(3*mm), "Owner:")
        self.c.setFont(self.font_name, s(10))
        self.c.drawCentredString(bx + s(140*mm + 20*mm), by + s(12*mm + 10*mm), "TabCAD AI")

        # Row 2 (middle, y=12..24)
        draw_cell(0, 12*mm, 80*mm, 12*mm, "Document type:", "Tablet Specification")
        draw_cell(80*mm, 12*mm, 60*mm, 12*mm, "Approved by:", pdf_approved_by)        
        # Row 3 (bottom, y=0..12)
        draw_cell(0, 0, 80*mm, 12*mm, "Drawing number:", dwg_no)
        draw_cell(80*mm, 0, 20*mm, 12*mm, "Language:", "EN", val_align="center")
        draw_cell(100*mm, 0, 40*mm, 12*mm, "Issue date:", date_str, val_align="center")
        draw_cell(140*mm, 0, 20*mm, 12*mm, "Scale:", scale_text, val_align="center")
        draw_cell(160*mm, 0, 20*mm, 12*mm, "Sheet:", "1 / 1", val_align="center")

    def insert_main_drawing(self):
        if not self.drawing_2d_b64:
            return

        header, encoded = self.drawing_2d_b64.split(",", 1)
        zone_x, zone_y, zone_w, zone_h = self._drawing_zone()
        bbox = self._model_bbox_mm()
        scale_ratio = self._pick_iso_scale(zone_w / mm, zone_h / mm)

        # Requested printed size based on model bounds (not render frame).
        img_w = bbox["view_w"] * scale_ratio * mm
        img_h = bbox["view_h"] * scale_ratio * mm

        rel_x = (bbox["obj_cx"] - bbox["view_xmin"]) / bbox["view_w"]
        rel_y = (bbox["obj_cy"] - bbox["view_ymin"]) / bbox["view_h"]
        zone_cx = zone_x + zone_w / 2
        zone_cy = zone_y + zone_h / 2

        # Align model center with zone center; clip to zone to hide extra frame.
        x_draw = zone_cx - rel_x * img_w
        y_draw = zone_cy - rel_y * img_h

        path = self.c.beginPath()
        path.rect(zone_x, zone_y, zone_w, zone_h)
        self.c.saveState()
        self.c.clipPath(path, stroke=0, fill=0)

        if self._draw_svg_main_drawing(header, encoded, x_draw, y_draw, img_w, img_h):
            self.c.restoreState()
            return

        ir = ImageReader(BytesIO(base64.b64decode(encoded)))
        self.c.drawImage(
            ir,
            x_draw,
            y_draw,
            width=img_w,
            height=img_h,
            preserveAspectRatio=False,
            mask="auto",
        )
        self.c.restoreState()

    def _draw_svg_main_drawing(self, header, encoded, x_draw, y_bot, width_pt, height_pt):
        if "image/svg+xml" not in header or svg2rlg is None:
            return False

        try:
            drawing = svg2rlg(BytesIO(base64.b64decode(encoded)))
        except Exception:
            return False

        if drawing is None or not getattr(drawing, "width", None) or not getattr(drawing, "height", None):
            return False

        scale = min(width_pt / drawing.width, height_pt / drawing.height)
        draw_w = drawing.width * scale
        draw_h = drawing.height * scale
        x = x_draw + (width_pt - draw_w) / 2
        y = y_bot + (height_pt - draw_h) / 2

        self.c.saveState()
        self.c.translate(x, y)
        self.c.scale(scale, scale)
        renderPDF.draw(drawing, self.c, 0, 0)
        self.c.restoreState()
        return True

    def draw_data_tables(self):
        scale = self.content_w / (180 * mm)
        x, y = self.left_m, self.bot_m + 36 * mm * scale
        m = self.metrics
        vol = m.get("Tablet_Vol", 0)
        sa = m.get("Tablet_SA", 0)
        density = float(self.params["density"])
        weight = vol * density

        tip_force_data = calculate_tip_force(self.params)
        tip_force_val = tip_force_data.get("selected_force")
        tip_force_str = str(int(round(float(tip_force_val)))) if tip_force_val is not None else "N/A"
        steel = self.params.get("tip_force_steel", "S7")

        b_type = str(self.params.get("b_type", "none") or "none").lower()
        shape = str(self.params.get("shape", "") or "").lower()
        has_scoring = b_type != "none"

        scoring_type = {
            "none": "None",
            "standard": "Standard",
            "cut_through": "Cut Through",
            "decreasing": "Decreasing",
        }.get(b_type, b_type.replace("_", " ").title())

        if not has_scoring:
            scoring_option = "None"
        elif shape == "round" and bool(self.params.get("b_cruciform")):
            scoring_option = "Cross-Scored"
        elif shape in ("capsule", "oval") and bool(self.params.get("b_double_sided")):
            scoring_option = "Double-sided"
        else:
            scoring_option = "None"

        def fmt_score_value(value, unit):
            if not has_scoring or value is None:
                return ""
            try:
                return f"{float(value):.2f} {unit}"
            except (TypeError, ValueError):
                return ""

        def fmt_score_angle(value, unit):
            if not has_scoring or value is None:
                return ""
            try:
                return f"{int(round(float(value)))} {unit}"
            except (TypeError, ValueError):
                return ""

        if self.is_landscape:
            regions = self._landscape_regions()
            tx = regions["right_table_x"] + 10 * mm
            ty = self.bot_m + 45 * mm
            col_label = 40 * mm
            col_value = 25 * mm

            table_data = [
                ["ENGINEERING DATA", ""],
                ["Perimeter", f"{m.get('Perimeter', 0):.2f} mm"],
                ["Die Hole SA", f"{m.get('Die_Hole_SA', 0):.2f} mm2"],
                ["Cup SA", f"{m.get('Cup_SA', 0):.2f} mm2"],
                ["Cup Volume", f"{m.get('Cup_Volume', 0):.2f} mm3"],
                ["Tablet SA", f"{sa:.2f} mm2"],
                ["Tablet Volume", f"{vol:.2f} mm3"],
                ["Tablet SA/V", f"{sa/vol if vol else 0:.2f} 1/mm"],
                ["PHYSICAL PARAMETERS", ""],
                ["Tablet Density", f"{density:.2f} mg/mm3"],
                ["Tablet Weight", f"{weight:.2f} mg"],
                ["TIP FORCE DATA", ""],
                ["Punch Steel Grade", steel],
                ["Max Tip Force", f"{tip_force_str} kN" if tip_force_str != "N/A" else "N/A"],
            ]

            table_styles = [
                ("GRID", (0,0), (-1,-1), 0.3*mm, colors.black),
                ("FONTNAME", (0,0), (-1,-1), self.font_name),
                ("FONTSIZE", (0,0), (-1,-1), 10),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
                ("SPAN", (0,0), (-1,0)),
                ("BACKGROUND", (0,8), (-1,8), colors.whitesmoke),
                ("SPAN", (0,8), (-1,8)),
                ("BACKGROUND", (0,11), (-1,11), colors.whitesmoke),
                ("SPAN", (0,11), (-1,11)),
            ]

            if has_scoring:
                start = len(table_data)
                table_data.extend([
                    ["SCORING DATA", ""],
                    ["Scoring type", scoring_type],
                    ["Scoring option", scoring_option],
                    ["Width", fmt_score_value(self.params.get("b_width"), "mm")],
                    ["Depth", fmt_score_value(self.params.get("b_depth"), "mm")],
                    ["Angle", fmt_score_angle(self.params.get("b_angle"), "deg")],
                    ["Inner Radius", fmt_score_value(self.params.get("b_Ri"), "mm")],
                    ["Outer Radius", "0.38 mm"],
                ])
                table_styles.extend([
                    ("BACKGROUND", (0,start), (-1,start), colors.whitesmoke),
                    ("SPAN", (0,start), (-1,start)),
                ])

            t = Table(table_data, colWidths=[col_label, col_value])
            t.setStyle(TableStyle(table_styles))
            t.wrapOn(self.c, self.width, self.height)
            t.drawOn(self.c, tx, ty)
            return

        x = self.width - self.right_m - 120 * mm - 5 * mm
        y = self.bot_m + 36 * mm * scale + 5 * mm

        data = [
            ["ENGINEERING DATA", ""],
            ["Perimeter", f"{m.get('Perimeter', 0):.2f} mm"],
            ["Die Hole SA", f"{m.get('Die_Hole_SA', 0):.2f} mm2"],
            ["Cup SA", f"{m.get('Cup_SA', 0):.2f} mm2"],
            ["Cup Volume", f"{m.get('Cup_Volume', 0):.2f} mm3"],
            ["Tablet SA", f"{sa:.2f} mm2"],
            ["Tablet Volume", f"{vol:.2f} mm3"],
            ["Tablet SA/V", f"{sa/vol if vol else 0:.2f} 1/mm"],
            ["PHYSICAL PARAMETERS", ""],
            ["Tablet Density", f"{density:.2f} mg/mm3"],
            ["Tablet Weight", f"{weight:.2f} mg"],
        ]

        col_data = 35 * mm
        col_value = 25 * mm
        t = Table(data, colWidths=[col_data, col_value])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3*mm, colors.black),
            ("FONTNAME", (0,0), (-1,-1), self.font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("SPAN", (0,0), (-1,0)),
            ("BACKGROUND", (0,8), (-1,8), colors.whitesmoke),
            ("SPAN", (0,8), (-1,8)),
        ]))
        t.wrapOn(self.c, self.width, self.height)
        t.drawOn(self.c, x, y)

        t2_data = []
        t2_styles = [
            ("GRID", (0,0), (-1,-1), 0.3*mm, colors.black),
            ("FONTNAME", (0,0), (-1,-1), self.font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ]
        row_idx = 0

        if has_scoring:
            t2_data.extend([
                ["SCORING DATA", ""],
                ["Scoring type", scoring_type],
                ["Scoring option", scoring_option],
                ["Width", fmt_score_value(self.params.get("b_width"), "mm")],
                ["Depth", fmt_score_value(self.params.get("b_depth"), "mm")],
                ["Angle", fmt_score_angle(self.params.get("b_angle"), "deg")],
                ["Inner Radius", fmt_score_value(self.params.get("b_Ri"), "mm")],
                ["Outer Radius", "0.38 mm"],
            ])
            t2_styles.extend([
                ("BACKGROUND", (0,row_idx), (-1,row_idx), colors.whitesmoke),
                ("SPAN", (0,row_idx), (1,row_idx)),
            ])
            row_idx += 8

        t2_data.extend([
            ["TIP FORCE DATA", ""],
            ["Punch Steel Grade", steel],
            ["Max Tip Force", f"{tip_force_str} kN" if tip_force_str != "N/A" else "N/A"],
        ])
        t2_styles.extend([
            ("BACKGROUND", (0,row_idx), (-1,row_idx), colors.whitesmoke),
            ("SPAN", (0,row_idx), (1,row_idx)),
        ])

        sx = x + 60 * mm
        s_col_label = 35 * mm
        s_col_value = 25 * mm

        t2 = Table(t2_data, colWidths=[s_col_label, s_col_value])
        t2.setStyle(TableStyle(t2_styles))
        t2.wrapOn(self.c, self.width, self.height)
        t2.drawOn(self.c, sx, y)

    def draw_visuals_block(self):
        """Одиночный 3D вид (без рамок)"""
        if self.is_landscape:
            regions = self._landscape_regions()
            x_start, y_start = regions["left_x"] + 6 * mm, self.bot_m + 10 * mm
            v_size = 40 * mm
        else:
            x_start, y_start = self.left_m + 142 * mm, self.bot_m + 127 * mm
            v_size = 25 * mm
        views_dict = {label: b64 for b64, label in self.views_3d}

        def place_v(label, vx, vy):
            if label in views_dict:
                _, encoded = views_dict[label].split(",", 1)
                img = ImageReader(BytesIO(base64.b64decode(encoded)))
                self.c.drawImage(img, vx, vy, width=v_size, height=v_size, preserveAspectRatio=True, mask='auto')
                self.c.setFont(self.font_name, 8)
                self.c.drawCentredString(vx + v_size/2, vy - 3*mm, label.upper())

        place_v("Isometric", x_start, y_start)

    def generate(self):
        self.draw_frame()
        self.insert_main_drawing()
        self.draw_data_tables()
        self.draw_visuals_block()
        self.draw_title_block()
        self.c.showPage()
        self.c.save()
        return self.filename









