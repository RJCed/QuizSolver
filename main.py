import keyboard
import time
import os
import glob
from screenshot import take_screenshot
from ai_solver import solve_quiz, find_next_button
from clicker import click_coordinates


def cleanup_screenshots():
    """Delete all files in the screenshots folder."""
    files = glob.glob("screenshots/*")
    for f in files:
        try:
            os.remove(f)
        except:
            pass
    if files:
        print(f"🗑️ Cleaned up {len(files)} files")


def run_bot():
    print("🤖 Quiz Bot is running!")
    print("Press F9 to START")
    print("Press ESC to STOP everything")
    print("-" * 40)

    def stop():
        print("\n🛑 Stopped! (ESC)")
        cleanup_screenshots()
        os._exit(0)

    keyboard.add_hotkey('esc', stop)

    while True:
        if keyboard.is_pressed('F9'):
            print("\n🚀 Bot started!")
            time.sleep(0.5)

            while True:
                # Step 1: Screenshot + analyse question
                print("\n📸 Taking screenshot...")
                image_path = take_screenshot()

                print("🤖 Analysing quiz...")
                result = solve_quiz(image_path)

                if result is None:
                    print("❌ Could not analyse quiz — stopping")
                    cleanup_screenshots()
                    break

                print(f"\n=== RESULT ===")
                print(f"  State:   {result.get('state')}")
                print(f"  Answer:  {result.get('correct_answer')}")
                print(f"  Coords:  ({result.get('answer_x')}, {result.get('answer_y')})")
                print("==============\n")

                state = result.get("state", "question")
                meta = result.get("_meta", {})

                if state == "question":
                    ax, ay = result.get("answer_x", 0), result.get("answer_y", 0)
                    if not (ax and ay):
                        print("❌ No valid button coords — stopping")
                        cleanup_screenshots()
                        break

                    # Step 2: Click the answer
                    print(f"🎯 Clicking: {result.get('correct_answer')}")
                    click_coordinates(ax, ay)
                    time.sleep(1)

                    # Step 3: Check for submit button (e.g. Quipper's "Answer" button)
                    print("📸 Checking for submit button...")
                    submit_path = take_screenshot()
                    sx, sy = find_next_button(submit_path, meta)

                    if sx and sy:
                        print(f"📨 Clicking submit at ({sx},{sy})")
                        click_coordinates(sx, sy)
                        print("⏳ Waiting for result screen...")
                        time.sleep(2.5)
                    else:
                        print("⏩ No submit button — assuming auto-advance")
                        time.sleep(2)

                # Step 4: Wait for Next button to load then click it
                print("⏳ Waiting for Next button to load...")
                time.sleep(5)
                print("📸 Looking for Next button...")
                next_path = take_screenshot()
                nx, ny = find_next_button(next_path, meta)

                if nx and ny:
                    print(f"⏭️ Clicking Next at ({nx},{ny})")
                    click_coordinates(nx, ny)
                    cleanup_screenshots()
                    print("⏳ Loading next question...")
                    time.sleep(2)
                else:
                    print("⚠️ No Next button found — quiz may be finished!")
                    cleanup_screenshots()
                    break

        time.sleep(0.1)


if __name__ == "__main__":
    run_bot()