"""
bot.py — Bot runner, designed to run in a background thread.
Reads all settings from config. GUI calls start_bot() and stop_bot().
"""

import threading
import time
import os
import glob

from paths import app_path
from screenshot import take_screenshot
from ai_solver import solve_quiz, find_next_button
from clicker import click_coordinates

_stop_event = threading.Event()
_thread     = None
_question_count = 0


def cleanup_screenshots(log=None):
    """Delete all screenshots. Only logs if files actually existed."""
    screenshots_dir = app_path("screenshots")
    files = glob.glob(os.path.join(screenshots_dir, "*"))
    for f in files:
        try:
            os.remove(f)
        except Exception:
            pass
    if files and log:
        log(f"🗑️ Cleaned up {len(files)} screenshot(s)")


def run_bot(config: dict, log_callback=None, status_callback=None):
    """
    Main bot loop. Runs until _stop_event is set.
    config:          merged config dict from get_active_config()
    log_callback:    function(str) — sends log lines to GUI
    status_callback: function(int) — sends question count updates to GUI
    """
    global _question_count
    _question_count = 0
    _stop_event.clear()

    cleaned_up = False

    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    def cleanup():
        nonlocal cleaned_up
        if not cleaned_up:
            cleanup_screenshots(log)
            cleaned_up = True

    def reset_cleanup():
        nonlocal cleaned_up
        cleaned_up = False

    # Push config + log callback into ai_solver at runtime
    import ai_solver

    ai_solver.ACTIVE_CONFIG   = config
    ai_solver._log_callback   = log_callback

    log("🚀 Bot started!")

    # Wait for the QuizSolver window to fully minimize before first screenshot
    log("⏳ Waiting for window to minimize...")
    for _ in range(15):
        if _stop_event.is_set():
            break
        time.sleep(0.1)

    while not _stop_event.is_set():
        reset_cleanup()
        try:
            log("📸 Capturing screen...")
            image_path = take_screenshot()

            log("🤖 Reading the question...")
            result = solve_quiz(image_path)

            if result is None:
                log("❌ Could not read the quiz — stopping")
                cleanup()
                break

            state  = result.get("state", "question")
            answer = result.get("correct_answer", "")
            meta   = result.get("_meta", {})

            print(f"  State: {state} | Answer: {answer} | Coords: ({result.get('answer_x')},{result.get('answer_y')})")

            if _stop_event.is_set():
                break

            if state == "question":
                ax, ay = result.get("answer_x", 0), result.get("answer_y", 0)
                if not (ax and ay):
                    log("❌ Couldn't find where to click the answer — stopping")
                    cleanup()
                    break

                _question_count += 1
                log(f"✅ Question {_question_count} — answered!")
                if status_callback:
                    status_callback(_question_count)

                click_coordinates(ax, ay)
                time.sleep(config.get("wait_after_answer", 1.0))

                if _stop_event.is_set():
                    break

                # Check for a Submit button (e.g. Quipper's "Answer" button).
                # Skipped entirely for sites like Quizalize that auto-advance —
                # saves 1 screenshot + 1 API call per question.
                if config.get("has_submit_button", True):
                    log("🔍 Looking for Submit button...")
                    submit_path = take_screenshot()
                    sx, sy = find_next_button(submit_path, meta)
                    if sx and sy:
                        log("📨 Clicking Submit...")
                        click_coordinates(sx, sy)
                    else:
                        log("⏩ No Submit button found — site may auto-advance")
                else:
                    log("⏩ Skipping Submit step (not needed for this site)")

                time.sleep(config.get("wait_after_submit", 2.5))

            elif state == "result":
                # Already on a result/feedback screen — just wait for Next
                log("⏩ Result screen detected — waiting for Next button...")
                time.sleep(config.get("wait_after_submit", 2.5))

            if _stop_event.is_set():
                break

            # Interruptible wait before looking for Next Question button
            wait = config.get("wait_for_next_button", 5.0)
            log(f"⏳ Waiting {wait:.0f}s for next question to load...")
            for _ in range(int(wait * 10)):
                if _stop_event.is_set():
                    break
                time.sleep(0.1)

            if _stop_event.is_set():
                break

            log("🔍 Looking for Next button...")
            next_path = take_screenshot()
            nx, ny = find_next_button(next_path, meta)

            if nx and ny:
                log("⏭️ Moving to next question...")
                click_coordinates(nx, ny)
                cleanup()
                time.sleep(config.get("wait_after_next", 2.0))
            else:
                log(f"🏁 Quiz finished! Answered {_question_count} question(s).")
                cleanup()
                break

        except Exception as e:
            log(f"💥 Unexpected error: {e}")
            cleanup()
            break

    cleanup()
    log("🛑 Bot stopped.")


def start_bot(config: dict, log_callback=None, on_stop_callback=None, status_callback=None):
    """Start the bot in a background thread."""
    global _thread
    _stop_event.clear()

    def _run():
        run_bot(config, log_callback, status_callback)
        if on_stop_callback:
            on_stop_callback()

    _thread = threading.Thread(target=_run, daemon=True)
    _thread.start()


def stop_bot():
    """Signal the bot to stop at the next safe checkpoint."""
    _stop_event.set()