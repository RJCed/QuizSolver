import keyboard
import time
import re
from screenshot import take_screenshot
from ai_solver import solve_quiz
from clicker import auto_click_answer, find_and_click_next

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
    print("Press F9 to START the bot on a quiz")
    print("Press F10 to quit")
    print("⚠️  Move mouse to top-left corner to emergency stop")
    print("-" * 40)

    while True:
        if keyboard.is_pressed('F9'):
            print("\n🚀 Bot started! Running automatically...")
            time.sleep(0.5)
            
            # Keep answering questions automatically
            while True:
                # Step 1: Screenshot
                print("\n📸 Taking screenshot...")
                image_path = take_screenshot()

                # Step 2: Ask AI
                print("🤖 Asking AI for answer...")
                ai_response = solve_quiz(image_path)

                if ai_response is None:
                    print("❌ AI could not find an answer, stopping")
                    break

                print("\n=== AI RESPONSE ===")
                print(ai_response)
                print("===================\n")

                # Step 3: Extract correct answer
                correct_answer = extract_correct_answer(ai_response)

                if correct_answer:
                    print(f"🎯 Correct answer: {correct_answer}")
                    # Step 4: Click the answer
                    success = auto_click_answer(correct_answer)
                    
                    if success:
                        # Step 5: Wait for result then click Next
                        print("⏳ Waiting for result...")
                        time.sleep(2)
                        next_found = find_and_click_next()
                        
                        if not next_found:
                            print("⚠️ Next button not found - stopping bot")
                            break
                            
                        # Wait for next question to load
                        print("⏳ Loading next question...")
                        time.sleep(2)
                    else:
                        print("❌ Could not click answer - stopping bot")
                        break
                else:
                    print("⚠️ Could not extract answer - stopping bot")
                    break
                    
                # Check if F10 pressed during run
                if keyboard.is_pressed('F10'):
                    print("\n👋 Bot stopped mid-quiz!")
                    break

        if keyboard.is_pressed('F10'):
            print("\n👋 Bot stopped. Goodbye!")
            break

        time.sleep(0.1)

if __name__ == "__main__":
    run_bot()