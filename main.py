"""
main.py — Entry point for QuizSolver.
Launches the GUI. All bot logic is in bot.py, all settings in config.py.
"""

from gui import QuizSolverApp

if __name__ == "__main__":
    app = QuizSolverApp()
    app._setup_hotkeys()
    app.mainloop()