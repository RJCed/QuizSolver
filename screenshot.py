import pyautogui
import os
from datetime import datetime
from paths import app_path


def take_screenshot():
    screenshots_dir = app_path("screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    filename = os.path.join(
        screenshots_dir,
        f"quiz_{datetime.now().strftime('%H%M%S_%f')}.png"
    )

    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    print(f"Screenshot saved: {filename}")
    return filename


if __name__ == "__main__":
    take_screenshot()
    print("Screenshot module working!")