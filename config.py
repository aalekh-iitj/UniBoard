import os

from PySide6.QtGui import QColor

# Application Details
APP_NAME = "UniBoard"
VERSION = "1.0.0"

# Directories
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
SANDBOX_DIR = os.path.join(WORKSPACE_DIR, "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

# Default API Configs
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
API_KEY_ENV_VAR = "GEMINI_API_KEY"

# Drawing Tool Modes
MODE_SELECT = 0
MODE_PEN = 1
MODE_HIGHLIGHTER = 2
MODE_ERASER = 3
MODE_TEXT = 4
MODE_LINE = 5
MODE_RECT = 6
MODE_CIRCLE = 7

# Canvas Constants
GRID_SIZE = 40
MIN_ZOOM = 0.1
MAX_ZOOM = 10.0

# Canvas Types
CANVAS_PLAIN = "plain"
CANVAS_HTML = "html"
CANVAS_COMPILER = "compiler"
CANVAS_BROWSER = "browser"

# Handwriting Recognition Configuration
HANDWRITING_RECOGNITION_DELAY = 900
GOOGLE_INPUT_TOOLS_URL = "https://www.google.com/inputtools/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8"
