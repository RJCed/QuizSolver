import keyboard
import time
import sys
from screenshot import take_screenshot
from ai_solver import solve_quiz, find_next_button
from clicker import click_coordinates


def run_bot():
    print("🤖 Quiz Bot is running!")
    print("Press F9 to START")
    print("Press F8 for EMERGENCY STOP")
    print("Press F10 to quit")
    print("-" * 40)

    def emergency_stop():
        print("\n🚨 EMERGENCY STOP triggered! (F8)")
        sys.exit(0)

    keyboard.add_hotkey('F8', emergency_stop)

    while True:
        if keyboard.is_pressed('F9'):
            print("\n🚀 Bot started!")
            time.sleep(0.5)

            while True:
                if keyboard.is_pressed('F8'):
                    emergency_stop()

                # Step 1: Screenshot + analyse question
                print("\n📸 Taking screenshot...")
                image_path = take_screenshot()

                print("🤖 Analysing quiz...")
                result = solve_quiz(image_path)

                if result is None:
                    print("❌ Could not analyse quiz — stopping")
                    break

                print(f"\n=== RESULT ===")
                print(f"  State:   {result.get('state')}")
                print(f"  Answer:  {result.get('correct_answer')}")
                print(f"  Coords:  ({result.get('answer_x')}, {result.get('answer_y')})")
                print("==============\n")

                state = result.get("state", "question")
                meta = result.get("_meta", {})

                # Step 2: Click answer if on question screen
                if state == "question":
                    ax, ay = result.get("answer_x", 0), result.get("answer_y", 0)
                    if ax and ay:
                        print(f"🎯 Clicking: {result.get('correct_answer')}")
                        click_coordinates(ax, ay)
                        print("⏳ Waiting for result screen...")
                        time.sleep(2.5)
                    else:
                        print("❌ No valid button coords — stopping")
                        break

                # Step 3: Take fresh screenshot, find Next button by element detection
                print("📸 Taking result screenshot...")
                result_path = take_screenshot()

                nx, ny = find_next_button(result_path, meta)

                if nx and ny:
                    print(f"⏭️ Clicking Next at ({nx},{ny})")
                    click_coordinates(nx, ny)
                    print("⏳ Loading next question...")
                    time.sleep(2)
                else:
                    print("⚠️ No Next button found — quiz may be finished!")
                    break

                if keyboard.is_pressed('F10'):
                    print("\n👋 Bot stopped mid-quiz!")
                    break

        if keyboard.is_pressed('F10'):
            print("\n👋 Goodbye!")
            break

        time.sleep(0.1)


if __name__ == "__main__":
    run_bot()