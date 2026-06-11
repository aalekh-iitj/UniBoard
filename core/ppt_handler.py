import io
import copy
import os
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE_TYPE

from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QPen, QFont, QFontInfo,
    QBrush, QTransform, QFontMetrics
)
from PySide6.QtCore import Qt, QRectF, QPointF, QBuffer, QIODevice
from PySide6.QtWidgets import QGraphicsScene


EMU_PER_INCH = 914400
DEFAULT_DPI = 96
EMU_PER_PT = 12700


def _emu_to_px(emu, dpi=DEFAULT_DPI):
    return int(emu / EMU_PER_INCH * dpi)


class PptSlideRenderer:
    """Renders a pptx slide to a QPixmap using python-pptx extracted data."""

    @staticmethod
    def render(slide, slide_width_emu, slide_height_emu, dpi=DEFAULT_DPI):
        width_px = _emu_to_px(slide_width_emu, dpi)
        height_px = _emu_to_px(slide_height_emu, dpi)

        pixmap = QPixmap(width_px, height_px)
        pixmap.fill(QColor("#ffffff"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        try:
            bg = slide.background
            if bg.fill is not None:
                fill = bg.fill
                try:
                    if hasattr(fill, 'fore_color') and fill.fore_color is not None:
                        try:
                            rgb = fill.fore_color.rgb
                            painter.fillRect(
                                QRectF(0, 0, width_px, height_px),
                                QColor(rgb[0], rgb[1], rgb[2])
                            )
                        except (AttributeError, ValueError):
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        for shape in slide.shapes:
            PptSlideRenderer._render_shape(painter, shape, slide_width_emu, slide_height_emu, width_px, height_px, dpi)

        painter.end()
        return pixmap

    @staticmethod
    def _render_shape(painter, shape, sw_emu, sh_emu, w_px, h_px, dpi):
        left_px = _emu_to_px(shape.left, dpi) if shape.left is not None else 0
        top_px = _emu_to_px(shape.top, dpi) if shape.top is not None else 0
        width_px = _emu_to_px(shape.width, dpi) if shape.width is not None else 0
        height_px = _emu_to_px(shape.height, dpi) if shape.height is not None else 0

        if width_px <= 0 or height_px <= 0:
            return

        rect = QRectF(left_px, top_px, width_px, height_px)

        # --- Render shape fill ---
        try:
            fill = shape.fill
            if fill is not None:
                try:
                    fill_type = fill.type
                except Exception:
                    fill_type = None
                if fill_type is not None:
                    try:
                        if hasattr(fill, 'fore_color') and fill.fore_color is not None:
                            rgb = fill.fore_color.rgb
                            painter.save()
                            painter.setBrush(QColor(rgb[0], rgb[1], rgb[2]))
                            painter.setPen(Qt.NoPen)
                            painter.drawRect(rect)
                            painter.restore()
                    except (AttributeError, ValueError):
                        pass
        except Exception:
            pass

        # --- Render image (Picture shape) ---
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                image_data = shape.image.blob
                qimg = QImage.fromData(image_data)
                if not qimg.isNull():
                    painter.save()
                    painter.drawImage(rect, qimg)
                    painter.restore()
        except Exception:
            pass

        # --- Render text ---
        if shape.has_text_frame:
            tf = shape.text_frame
            PptSlideRenderer._render_text_frame(painter, tf, rect, dpi)

        # --- Render shape outline ---
        try:
            line = shape.line
            if line is not None and hasattr(line, 'fill') and line.fill is not None:
                try:
                    lf = line.fill
                    if hasattr(lf, 'fore_color') and lf.fore_color is not None:
                        rgb = lf.fore_color.rgb
                        try:
                            line_width = line.width / EMU_PER_PT if line.width else 1.5
                        except Exception:
                            line_width = 1.5
                        painter.save()
                        painter.setBrush(Qt.NoBrush)
                        painter.setPen(QPen(QColor(rgb[0], rgb[1], rgb[2]), max(1, int(line_width))))
                        painter.drawRect(rect)
                        painter.restore()
                except (AttributeError, ValueError):
                    pass
        except Exception:
            pass

    @staticmethod
    def _render_text_frame(painter, tf, rect, dpi):
        current_y = rect.top() + 4
        right_margin = rect.right() - 4
        left_margin = rect.left() + 4
        max_width = right_margin - left_margin

        for para in tf.paragraphs:
            para_text = para.text
            if not para_text.strip():
                current_y += 8
                continue

            font_size = None
            font_bold = False
            font_italic = False
            font_color = QColor("#000000")
            font_name = "Calibri"

            space_before = 0
            space_after = 0

            if para.runs:
                run = para.runs[0]
                font = run.font
                if font.size:
                    font_size = font.size / EMU_PER_PT
                if font.bold:
                    font_bold = font.bold
                if font.italic:
                    font_italic = font.italic
                try:
                    if font.color and font.color.rgb:
                        rgb = font.color.rgb
                        font_color = QColor(rgb[0], rgb[1], rgb[2])
                except AttributeError:
                    pass
                if font.name:
                    font_name = font.name

            try:
                space_before = para.space_before.emu / EMU_PER_PT if para.space_before else 0
            except Exception:
                pass
            try:
                space_after = para.space_after.emu / EMU_PER_PT if para.space_after else 0
            except Exception:
                pass

            if font_size is None:
                font_size = 18

            current_y += space_before * 1.2

            qfont = QFont(font_name, int(font_size))
            qfont.setBold(font_bold)
            qfont.setItalic(font_italic)

            align = PP_ALIGN.LEFT
            try:
                align = para.alignment or PP_ALIGN.LEFT
            except Exception:
                pass

            qt_align = Qt.AlignLeft
            if align == PP_ALIGN.CENTER:
                qt_align = Qt.AlignHCenter
            elif align == PP_ALIGN.RIGHT:
                qt_align = Qt.AlignRight

            painter.save()
            painter.setFont(qfont)
            painter.setPen(QPen(font_color))

            fm = QFontMetrics(qfont)
            line_height = fm.height() + 4

            para_rect = QRectF(left_margin, current_y, max_width, line_height)
            painter.drawText(para_rect, int(qt_align | Qt.AlignTop | Qt.TextWordWrap), para_text)

            from PySide6.QtCore import QRect
            actual_height = fm.boundingRect(
                QRect(0, 0, int(max_width), 10000),
                int(qt_align | Qt.AlignTop | Qt.TextWordWrap),
                para_text
            ).height() + 4

            current_y += max(actual_height, line_height) + space_after * 0.8
            painter.restore()

            if current_y > rect.bottom():
                break


class PptHandler:
    """Handles PPTX loading, slide rendering, annotation storage, and export."""

    def __init__(self):
        self.prs = None
        self.file_path = None
        self.slides = []
        self.slide_width_emu = 0
        self.slide_height_emu = 0
        self.slide_count = 0
        self._slide_renders = {}
        self._annotations = {}
        self._annotation_scenes = {}

    def load(self, file_path):
        self.file_path = file_path
        self.prs = Presentation(file_path)
        self.slides = list(self.prs.slides)
        self.slide_width_emu = self.prs.slide_width
        self.slide_height_emu = self.prs.slide_height
        self.slide_count = len(self.slides)
        self._slide_renders.clear()
        self._annotations.clear()
        self._annotation_scenes.clear()
        return self.slide_count

    def get_slide_pixmap(self, index):
        if index in self._slide_renders:
            return self._slide_renders[index]
        if 0 <= index < self.slide_count:
            pm = PptSlideRenderer.render(
                self.slides[index], self.slide_width_emu, self.slide_height_emu
            )
            self._slide_renders[index] = pm
            return pm
        return None

    def get_slide_size(self):
        w = _emu_to_px(self.slide_width_emu)
        h = _emu_to_px(self.slide_height_emu)
        return w, h

    def get_annotation_scene(self, index):
        if index not in self._annotation_scenes:
            self._annotation_scenes[index] = QGraphicsScene()
        return self._annotation_scenes[index]

    def save_current_annotations(self, index, scene):
        if index not in self._annotation_scenes:
            self._annotation_scenes[index] = scene
        else:
            old_scene = self._annotation_scenes[index]
            for item in old_scene.items():
                old_scene.removeItem(item)
            for item in scene.items():
                old_scene.addItem(item)

    def get_slide_thumbnail(self, index, max_width=200):
        pm = self.get_slide_pixmap(index)
        if pm is None:
            return None
        return pm.scaledToWidth(max_width, Qt.SmoothTransformation)

    def export_annotated_pptx(self, output_path, annotation_map):
        if self.prs is None:
            return False

        prs_copy = Presentation(self.file_path)

        for i, slide in enumerate(prs_copy.slides):
            scene = annotation_map.get(i)
            if scene is None or not scene.items():
                continue

            w_px = _emu_to_px(self.slide_width_emu)
            h_px = _emu_to_px(self.slide_height_emu)

            annotation_pm = QPixmap(w_px, h_px)
            annotation_pm.fill(QColor(0, 0, 0, 0))
            ap = QPainter(annotation_pm)
            ap.setRenderHint(QPainter.Antialiasing)
            scene.render(ap)
            ap.end()

            img_buffer = QBuffer()
            img_buffer.open(QIODevice.ReadWrite)
            annotation_pm.save(img_buffer, "PNG")
            img_bytes = img_buffer.data().data()
            img_buffer.close()

            import io
            python_buffer = io.BytesIO(img_bytes)

            slide.shapes.add_picture(
                python_buffer,
                0, 0,
                self.slide_width_emu, self.slide_height_emu,
            )

        prs_copy.save(output_path)
        return True
