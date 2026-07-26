import os
import sys
import time

# Add current directory to path just in case
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication


def _prewarm_webengine(app):
    """Pre-initialize the Qt WebEngine process so the first HTML/
    Browser canvas switch doesn't cause a visible pause or UI freeze."""
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        dummy = QWebEngineView()
        dummy.setHtml("<html><body></body></html>")
        dummy.hide()
        # Process events to let the WebEngine process spawn
        app.processEvents()
        time.sleep(0.5)
        dummy.deleteLater()
    except Exception:
        pass


def main():
    # Set high DPI scaling properties for sharp rendering
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("UniBoard")
    app.setApplicationVersion("0.0.2")

    # Pre-warm WebEngine so first HTML canvas switch is instant
    _prewarm_webengine(app)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
