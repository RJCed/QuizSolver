import pyautogui
import time

pyautogui.FAILSAFE = True


def click_coordinates(x, y):
    """Click at specific screen coordinates."""
    time.sleep(0.3)
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    print(f"✅ Clicked at ({x}, {y})")