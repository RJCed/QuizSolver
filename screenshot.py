import pyautogui
import os
from datetime import datetime

def take_screenshot():
    # Create a folder to save screenshots if it doesn't exist
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    
    # Generate a filename with timestamp
    filename = f"screenshots/quiz_{datetime.now().strftime('%H%M%S')}.png"
    
    # Take the screenshot and save it
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    
    print(f"Screenshot saved: {filename}")
    return filename

# Test it when we run this file directly
if __name__ == "__main__":
    take_screenshot()
    print("Screenshot module working!")