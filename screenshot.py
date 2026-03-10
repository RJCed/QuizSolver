import pyautogui
import os
from datetime import datetime

def take_screenshot():
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    filename = f"screenshots/quiz_{datetime.now().strftime('%H%M%S')}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)

    print(f"Screenshot saved: {filename}")
    return filename

if __name__ == "__main__":
    take_screenshot()
    print("Screenshot module working!")