import sys
from pathlib import Path


def base_dir() -> Path:
    """
    Get the base directory of the application.

    If the program is running in a frozen state (e.g., packaged with PyInstaller),
    return the temporary directory created by the bundler. Otherwise, return the
    parent directory of the current file.

    :return: Path to the base directory.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent
