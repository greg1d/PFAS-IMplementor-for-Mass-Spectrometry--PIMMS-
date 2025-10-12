import os
import sys


def resource_path(relative_path):
    """
    Get the absolute path to a resource that is BUNDLED with the application.
    This works for development and for the packaged PyInstaller .exe.
    Use this ONLY for files you include with --add-data, like your 'Import libraries'.
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # --- MODIFIED FOR ROBUSTNESS ---
        # In development, calculate the project's root directory based on this file's location.
        # This is more reliable than using the current working directory.
        script_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # This is the 'GUI' directory
        base_path = os.path.dirname(script_dir)  # This is the project root

    return os.path.join(base_path, relative_path)


def get_app_path(relative_path):
    """
    Get the absolute path to a file or folder in the USER'S application directory.
    Use this for user-provided input ('Raw data') and for writing output files ('PIMMS output').
    This ensures files are read from/written to the folder where the .exe is located.
    """
    if getattr(sys, "frozen", False):
        # We are running in a bundled .exe, so the base is the .exe's directory
        application_path = os.path.dirname(sys.executable)
    else:
        # --- MODIFIED FOR ROBUSTNESS ---
        # In development, calculate the project's root directory based on this file's location.
        script_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # This is the 'GUI' directory
        application_path = os.path.dirname(script_dir)  # This is the project root

    return os.path.join(application_path, relative_path)


def setup_user_folders():
    """
    Creates the necessary user-facing folders if they don't already exist.
    Call this function once when your application starts up.
    """
    os.makedirs(get_app_path("Raw data"), exist_ok=True)
    os.makedirs(get_app_path("PIMMS output"), exist_ok=True)
