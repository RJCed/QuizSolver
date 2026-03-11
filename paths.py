"""
paths.py — Central path resolver for QuizSolver.

When running as a PyInstaller .exe, sys.frozen is True and sys.executable
points to the .exe file. All user-writable files (config, .env, screenshots)
are saved in the same folder as the .exe so users can find them easily.

When running as plain Python scripts (dev mode), files are saved next to
this script as usual.
"""

import sys
import os


def app_dir() -> str:
    """
    Return the folder that contains the .exe (packaged) or this script (dev).
    All user data files should live here.
    """
    if getattr(sys, "frozen", False):
        # Packaged exe — use the folder the .exe lives in
        return os.path.dirname(sys.executable)
    # Dev mode — use the folder this script lives in
    return os.path.dirname(os.path.abspath(__file__))


def app_path(filename: str) -> str:
    """Return full path to a file that lives next to the .exe / script."""
    return os.path.join(app_dir(), filename)