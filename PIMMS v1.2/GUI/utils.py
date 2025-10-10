import os
import sys


def resource_path(relative_path):
    """
    Get the absolute path to a resource.
    This works for development (running from your IDE) and for a packaged
    PyInstaller application (running the .exe).
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not running in a PyInstaller bundle, so use the normal project path
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
