import os
import time
import numpy as np
from PIL import ImageGrab
import cv2
from PySide6.QtCore import QThread, Signal

class ScreenRecorder(QThread):
    status_updated = Signal(str)
    finished_recording = Signal(str)

    def __init__(self, output_path, window_widget, fps=10):
        super().__init__()
        self.output_path = output_path
        self.window_widget = window_widget
        self.fps = fps
        self.is_recording = False

    def run(self):
        self.is_recording = True
        self.status_updated.emit("Recording started")
        
        # Determine initial bounding box
        geo = self.window_widget.geometry()
        # Map window position to absolute screen coordinates
        pos = self.window_widget.mapToGlobal(self.window_widget.rect().topLeft())
        width = self.window_widget.width()
        height = self.window_widget.height()
        
        # Ensure dimensions are even (required by some video codecs)
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))

        delay = 1.0 / self.fps
        
        try:
            while self.is_recording:
                start_time = time.time()
                
                # Dynamic update of window location
                pos = self.window_widget.mapToGlobal(self.window_widget.rect().topLeft())
                x = pos.x()
                y = pos.y()
                
                # Capture bounding box of the window
                bbox = (x, y, x + width, y + height)
                img = ImageGrab.grab(bbox=bbox)
                
                # Convert to BGR format for OpenCV
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                out.write(frame)
                
                # Balance execution timing to match target FPS
                elapsed = time.time() - start_time
                sleep_time = max(0.01, delay - elapsed)
                time.sleep(sleep_time)
                
        except Exception as e:
            self.status_updated.emit(f"Error during recording: {str(e)}")
            
        finally:
            out.release()
            self.finished_recording.emit(self.output_path)
            self.status_updated.emit("Recording stopped")

    def stop(self):
        self.is_recording = False
