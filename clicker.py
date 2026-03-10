import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import time

# Point to Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Safety feature
pyautogui.FAILSAFE = True

def find_text_on_screen(answer_text):
    """Find where the answer text is located on screen"""
    print(f"🔍 Looking for: {answer_text}")
    
    # Take a fresh screenshot
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    
    # Convert to grayscale for better OCR
    gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
    
    # Get all text and their locations from screen
    data = pytesseract.image_to_data(
        gray, 
        output_type=pytesseract.Output.DICT
    )
    
    # Clean up answer text for comparison
    answer_words = answer_text.lower().strip().split()
    
    # Search for matching text on screen
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        word = data['text'][i].lower().strip()
        if not word:
            continue
            
        # Check if this word matches any word in the answer
        for answer_word in answer_words:
            if len(answer_word) > 3 and answer_word in word:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # Calculate center of the found text
                center_x = x + w // 2
                center_y = y + h // 2
                
                print(f"✅ Found '{word}' at ({center_x}, {center_y})")
                return center_x, center_y
    
    print("❌ Could not find answer text on screen")
    return None, None

def auto_click_answer(answer_text):
    """Automatically find and click the answer on screen"""
    x, y = find_text_on_screen(answer_text)
    
    if x and y:
        print(f"🖱️ Moving to answer and clicking in 1 second...")
        time.sleep(1)
        
        # Smoothly move mouse to answer and click
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(0.2)
        pyautogui.click()
        print(f"✅ Clicked answer at ({x}, {y})!")
        return True
    else:
        print("❌ Could not auto-click, answer not found on screen")
        return False

def click_coordinates(x, y):
    """Click at specific coordinates"""
    time.sleep(0.5)
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    print(f"✅ Clicked at ({x}, {y})")

# Test
if __name__ == "__main__":
    test_answer = input("Enter a word that's visible on your screen: ")
    auto_click_answer(test_answer)