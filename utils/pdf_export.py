from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os

def export_images_to_pdf(image_paths, output_path):
    """Create a PDF from a list of image file paths.

    Args:
        image_paths (list[str]): Paths to PNG/JPEG images.
        output_path (str): Destination PDF file.
    """
    if not image_paths:
        raise ValueError("No images provided for PDF export")
    c = pdfcanvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    for img_path in image_paths:
        if not os.path.exists(img_path):
            continue
        img = ImageReader(img_path)
        iw, ih = img.getSize()
        # Scale to fit page while preserving aspect ratio
        scale = min(width / iw, height / ih) * 0.95
        iw_scaled, ih_scaled = iw * scale, ih * scale
        x = (width - iw_scaled) / 2
        y = (height - ih_scaled) / 2
        c.drawImage(img, x, y, width=iw_scaled, height=ih_scaled)
        c.showPage()
    c.save()
