import fitz
import io
import os
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor
from PySide6.QtCore import Qt, QIODevice, QBuffer
from PySide6.QtWidgets import QGraphicsScene


class PdfHandler:
    """Handles PDF loading, page rendering, annotation storage, and export."""

    def __init__(self):
        self.doc = None
        self.file_path = None
        self.page_count = 0
        self._page_renders = {}
        self._annotation_scenes = {}

    def load(self, file_path):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self.page_count = self.doc.page_count
        self._page_renders.clear()
        self._annotation_scenes.clear()
        return self.page_count

    def get_page_pixmap(self, index, dpi=150):
        if index in self._page_renders:
            return self._page_renders[index]
        if self.doc is None or index < 0 or index >= self.page_count:
            return None
        page = self.doc.load_page(index)
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pm = QPixmap.fromImage(img)
        self._page_renders[index] = pm
        return pm

    def get_page_size(self, index, dpi=150):
        if self.doc is None:
            return 0, 0
        page = self.doc.load_page(index)
        zoom = dpi / 72
        return int(page.rect.width * zoom), int(page.rect.height * zoom)

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

    def get_page_thumbnail(self, index, max_width=200, dpi=72):
        pm = self.get_page_pixmap(index, dpi)
        if pm is None:
            return None
        return pm.scaledToWidth(max_width, Qt.SmoothTransformation)

    def export_annotated_pdf(self, output_path, annotation_map, dpi=150):
        if self.doc is None:
            return False

        zoom = dpi / 72
        new_doc = fitz.open()

        for i in range(self.page_count):
            page = self.doc.load_page(i)
            w = int(page.rect.width * zoom)
            h = int(page.rect.height * zoom)

            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pm = QPixmap.fromImage(img)

            scene = annotation_map.get(i)
            if scene is not None and scene.items():
                ap = QPainter(pm)
                ap.setRenderHint(QPainter.Antialiasing)
                scene.render(ap)
                ap.end()

            img_buffer = QBuffer()
            img_buffer.open(QIODevice.ReadWrite)
            pm.save(img_buffer, "PNG")
            img_bytes = img_buffer.data().data()
            img_buffer.close()

            python_buffer = io.BytesIO(img_bytes)
            new_page = new_doc.new_page(width=w, height=h)
            new_page.insert_image(new_page.rect, stream=python_buffer.read())

        new_doc.save(output_path)
        new_doc.close()
        return True

    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None
