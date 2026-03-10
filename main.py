import keyboard
import time
import re
from screenshot import take_screenshot
from ai_solver import solve_quiz
from clicker import auto_click_answer

def extract_correct_answer(ai_response):
    """Pull just the correct answer text from AI response"""
    lines = ai_response.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'correct answer' in line_lower or '4.' in line:
            # Clean up the line to get just the answer text
            answer = re.sub(r'[\*\#\d\.\:]', '', line)
            answer = answer.replace('Correct Answer', '').replace('Text of Correct Answer', '')
            answer = answer.strip()
            if answer:
                return answer
    return None

def run_bot():
    print("🤖 Quiz Bot is running!")
    print("Press F9 to automatically answer a quiz question")
    print("Press F10 to quit")
    print("⚠️  Move mouse to top-left corner to emergency stop")
    print("-" * 40)

    while True:
        if keyboard.is_pressed('F9'):
            print("\n📸 Taking screenshot...")
            time.sleep(0.5)

            # Step 1: Screenshot
            image_path = take_screenshot()

            # Step 2: Ask AI
            print("🤖 Asking AI for answer...")
            ai_response = solve_quiz(image_path)

            if ai_response is None:
                print("❌ AI could not find an answer, try again")
                continue

            print("\n=== AI RESPONSE ===")
            print(ai_response)
            print("===================\n")

            # Step 3: Extract the correct answer
            correct_answer = extract_correct_answer(ai_response)
            
            if correct_answer:
                print(f"🎯 Correct answer is: {correct_answer}")
                # Step 4: Auto find and click it
                auto_click_answer(correct_answer)
            else:
                print("⚠️ Could not extract answer, please click manually")

            print("\n✅ Done! Press F9 for next question")
            time.sleep(1)

        if keyboard.is_pressed('F10'):
            print("\n👋 Bot stopped. Goodbye!")
            break

        time.sleep(0.1)

if __name__ == "__main__":
    run_bot()