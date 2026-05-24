import json
import requests
from PySide6.QtCore import QThread, Signal

class HandwritingRecognizer:
    @staticmethod
    def recognize(strokes, width=800, height=600, lang="en"):
        """
        Sends coordinates to Google Input Tools Handwriting API.
        Strokes format: List of strokes, where each stroke is a list of (x, y) tuples.
        """
        if not strokes or len(strokes) == 0:
            return ""

        # Format input ink for Google Input Tools:
        # Ink is [[[x1, x2, ...], [y1, y2, ...], [t1, t2, ...]], ...]
        ink = []
        time_offset = 0
        for stroke in strokes:
            x_coords = []
            y_coords = []
            t_coords = []
            for i, pt in enumerate(stroke):
                # pt is (x, y)
                x_coords.append(int(pt[0]))
                y_coords.append(int(pt[1]))
                t_coords.append(time_offset + (i * 10))
            time_offset += len(stroke) * 10 + 200
            ink.append([x_coords, y_coords, t_coords])

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        payload = {
            "app_version": 0.4,
            "api_level": "5.3",
            "device": "",
            "input_type": 0,
            "options": "enable_pre_space",
            "requests": [
                {
                    "writing_guide": {
                        "writing_area_width": int(width),
                        "writing_area_height": int(height)
                    },
                    "ink": ink,
                    "language": lang
                }
            ]
        }

        try:
            url = "https://www.google.com/inputtools/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8"
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                result = response.json()
                # Structure: ['SUCCESS', [['Hello', ['H', 'e', 'l', 'l', 'o']]]]
                if len(result) > 1 and result[0] == "SUCCESS":
                    candidates = result[1][0][1]
                    if candidates:
                        return candidates[0]  # Return the best candidate
            return ""
        except Exception as e:
            print(f"Handwriting recognition request failed: {e}")
            return ""


class HandwritingWorker(QThread):
    finished_recognition = Signal(str, list)  # Emits recognized text and original stroke items for deletion

    def __init__(self, strokes, stroke_items, width, height):
        super().__init__()
        self.strokes = strokes
        self.stroke_items = stroke_items
        self.width = width
        self.height = height

    def run(self):
        text = HandwritingRecognizer.recognize(self.strokes, self.width, self.height)
        self.finished_recognition.emit(text, self.stroke_items)
