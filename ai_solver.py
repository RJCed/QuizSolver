import requests
import base64
import os
import json
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")


# ---------------------------------------------------------------------------
# Card detection
# ---------------------------------------------------------------------------

def find_white_card(img_np):
    """Find the largest white card/panel bounding box in the screenshot."""
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    _, white = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for cnt in contours:
        if cv2.contourArea(cnt) > 30000:
            x, y, w, h = cv2.boundingRect(cnt)
            return x, y, w, h
    return None


# ---------------------------------------------------------------------------
# Element detection — two strategies
# ---------------------------------------------------------------------------

def detect_colored_elements(card_np, min_area=500):
    """
    Strategy A: Find non-white filled elements (colored buttons).
    Works for: Quizalize, Kahoot, Quizizz, etc.
    """
    gray = cv2.cvtColor(card_np, cv2.COLOR_RGB2GRAY)
    _, white_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    non_white = cv2.bitwise_not(white_mask)

    kernel = np.ones((8, 8), np.uint8)
    closed = cv2.morphologyEx(non_white, cv2.MORPH_CLOSE, kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    card_h, card_w = card_np.shape[:2]

    elements = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if w > card_w * 0.85:
            continue
        elements.append((x + w // 2, y + h // 2, x, y, w, h))

    elements.sort(key=lambda e: (round(e[1] / 60) * 60, e[0]))
    return elements


def detect_bordered_elements(card_np, min_area=2000):
    """
    Strategy B: Find bordered/outlined boxes via edge detection.
    Works for: Quipper, Google Forms, and other sites with white outlined boxes.
    """
    gray = cv2.cvtColor(card_np, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 30, 100)

    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    card_h, card_w = card_np.shape[:2]

    elements = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if w > card_w * 0.85:
            continue
        if w < 80 or h < 25:
            continue
        elements.append((x + w // 2, y + h // 2, x, y, w, h))

    elements.sort(key=lambda e: (round(e[1] / 60) * 60, e[0]))
    return elements


def find_elements_in_card(card_np, min_area=500):
    """
    Try colored detection first; fall back to edge/border detection.
    Filters result to likely answer buttons (wider than tall, not too wide).
    """
    card_h, card_w = card_np.shape[:2]

    # Try Strategy A first
    elements = detect_colored_elements(card_np, min_area)
    buttons = _filter_buttons(elements, card_w)

    if len(buttons) >= 2:
        print("  🎨 Using colored element detection")
        return buttons, "colored"

    # Fall back to Strategy B
    elements = detect_bordered_elements(card_np, min_area=2000)
    buttons = _filter_buttons(elements, card_w)

    if len(buttons) >= 2:
        print("  📐 Using edge/border detection")
        return buttons, "bordered"

    # Last resort: return whatever we found
    print("  ⚠️ Falling back to all detected elements")
    return elements, "fallback"


def _filter_buttons(elements, card_w):
    """Keep only elements that look like answer buttons."""
    buttons = []
    for e in elements:
        cx, cy, x, y, w, h = e
        if w > card_w * 0.7:
            continue
        if h > w:
            continue
        if w < 50 or h < 15:
            continue
        buttons.append(e)
    return buttons


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def crop_element(card_np, element, padding=8, upscale=2):
    cx, cy, x, y, w, h = element
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(card_np.shape[1], x + w + padding)
    y2 = min(card_np.shape[0], y + h + padding)
    crop = card_np[y1:y2, x1:x2]
    if upscale > 1:
        crop = cv2.resize(crop, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)
    return crop


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_ai(content):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "openrouter/auto", "messages": [{"role": "user", "content": content}]}
    )
    result = response.json()
    if "error" in result:
        print("❌ API Error:", result["error"]["message"])
        return None
    raw = result["choices"][0]["message"]["content"]
    print("=== AI Raw Response ===")
    print(raw)
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        print("❌ AI did not return valid JSON")
        return None


# ---------------------------------------------------------------------------
# Main quiz solver
# ---------------------------------------------------------------------------

def solve_quiz(image_path):
    """
    Find card → detect answer buttons (colored or bordered) →
    send crops to AI → return screen coords to click.
    """
    img = Image.open(image_path)
    img_np = np.array(img)
    img_h, img_w = img_np.shape[:2]

    try:
        import pyautogui
        real_w, real_h = pyautogui.size()
        scale_x, scale_y = real_w / img_w, real_h / img_h
    except:
        scale_x = scale_y = 1.0

    # Find card
    card_bounds = find_white_card(img_np)
    if card_bounds:
        card_x, card_y, card_w, card_h = card_bounds
        print(f"📋 Found card at ({card_x},{card_y}) size {card_w}x{card_h}")
    else:
        print("⚠️ No white card — using full screenshot")
        card_x, card_y, card_w, card_h = 0, 0, img_w, img_h

    card_np = img_np[card_y:card_y+card_h, card_x:card_x+card_w]

    # Find buttons using best available strategy
    buttons, strategy = find_elements_in_card(card_np)
    print(f"🔲 Found {len(buttons)} buttons ({strategy})")
    for i, btn in enumerate(buttons):
        print(f"   {i+1}: center=({btn[0]},{btn[1]}) size={btn[4]}x{btn[5]}")

    if not buttons:
        print("❌ No buttons detected")
        return None

    # Save crops
    base = image_path.replace(".png", "")
    card_path = base + "_card.png"
    Image.fromarray(card_np).save(card_path)

    button_paths = []
    for i, btn in enumerate(buttons):
        crop = crop_element(card_np, btn, upscale=2)
        path = base + f"_btn{i+1}.png"
        Image.fromarray(crop).save(path)
        button_paths.append(path)

    # Ask AI which button is correct
    content = []
    content.append({"type": "text", "text": "Here is the quiz card:"})
    content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image(card_path)}"}})
    content.append({"type": "text", "text": f"\nHere are the {len(button_paths)} answer buttons individually:"})
    for i, path in enumerate(button_paths):
        content.append({"type": "text", "text": f"Button {i+1}:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"}})
    content.append({"type": "text", "text": """
Which answer is correct?
Respond ONLY with JSON, no explanation, no markdown:
{
    "state": "question" or "result",
    "correct_button": <1 to N>,
    "correct_answer": "<exact text of correct answer>"
}
state is "result" only if showing right/wrong feedback after answering.
correct_button is the number of the correct answer button shown above."""})

    ai_result = call_ai(content)
    if not ai_result:
        return None

    state = ai_result.get("state", "question")
    correct_button = ai_result.get("correct_button", 0)
    correct_answer = ai_result.get("correct_answer", "")
    print(f"🤖 AI: state={state}, button={correct_button}, answer='{correct_answer}'")

    answer_x, answer_y = 0, 0
    if correct_button and 1 <= correct_button <= len(buttons):
        btn = buttons[correct_button - 1]
        answer_x = int((card_x + btn[0]) * scale_x)
        answer_y = int((card_y + btn[1]) * scale_y)
        print(f"🎯 Button {correct_button} → screen ({answer_x},{answer_y})")

    return {
        "state": state,
        "correct_answer": correct_answer,
        "answer_x": answer_x,
        "answer_y": answer_y,
        "_meta": {
            "image_path": image_path,
            "card_x": card_x, "card_y": card_y,
            "card_w": card_w, "card_h": card_h,
            "scale_x": scale_x, "scale_y": scale_y,
            "strategy": strategy,
        }
    }


# ---------------------------------------------------------------------------
# Next button finder
# ---------------------------------------------------------------------------

def find_next_button(image_path, meta):
    """
    Find the Next/Continue/Answer button on the result or submission screen.
    Uses same dual detection strategy — works on any quiz site.
    """
    img = Image.open(image_path)
    img_np = np.array(img)
    img_h, img_w = img_np.shape[:2]

    scale_x = meta.get("scale_x", 1.0)
    scale_y = meta.get("scale_y", 1.0)

    card_bounds = find_white_card(img_np)
    if card_bounds:
        card_x, card_y, card_w, card_h = card_bounds
    else:
        card_x, card_y, card_w, card_h = 0, 0, img_w, img_h

    card_np = img_np[card_y:card_y+card_h, card_x:card_x+card_w]

    # Get ALL elements (both strategies, smaller min_area to catch small buttons)
    colored = detect_colored_elements(card_np, min_area=500)
    bordered = detect_bordered_elements(card_np, min_area=1000)

    # Merge and deduplicate by proximity
    all_elements = colored.copy()
    for be in bordered:
        is_dup = any(abs(be[0]-e[0]) < 30 and abs(be[1]-e[1]) < 30 for e in all_elements)
        if not is_dup:
            all_elements.append(be)

    all_elements.sort(key=lambda e: (round(e[1] / 60) * 60, e[0]))
    print(f"🔍 Found {len(all_elements)} elements for Next button search")

    if not all_elements:
        print("❌ No elements found")
        return None, None

    # Save crops
    base = image_path.replace(".png", "")
    card_path = base + "_next_card.png"
    Image.fromarray(card_np).save(card_path)

    element_paths = []
    for i, el in enumerate(all_elements):
        crop = crop_element(card_np, el, upscale=2)
        path = base + f"_nel{i+1}.png"
        Image.fromarray(crop).save(path)
        element_paths.append(path)
        print(f"   {i+1}: center=({el[0]},{el[1]}) size={el[4]}x{el[5]}")

    # Ask AI which is the submit/next button
    content = []
    content.append({"type": "text", "text": "This is a quiz screen:"})
    content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image(card_path)}"}})
    content.append({"type": "text", "text": f"\nHere are all {len(element_paths)} clickable elements, numbered:"})
    for i, path in enumerate(element_paths):
        content.append({"type": "text", "text": f"Element {i+1}:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"}})
    content.append({"type": "text", "text": """
Which element is the button to proceed forward? This could be:
- A "Next" or "Next Question" button
- A "Continue" button  
- An arrow/→ button
- An "Answer" or "Submit" button (if the answer hasn't been submitted yet)

Respond ONLY with JSON, no explanation, no markdown:
{
    "found": true or false,
    "element_number": <1 to N>
}"""})

    ai_result = call_ai(content)
    if not ai_result or not ai_result.get("found"):
        print("❌ AI could not find Next button")
        return None, None

    el_num = ai_result.get("element_number", 0)
    if not el_num or el_num < 1 or el_num > len(all_elements):
        print("❌ Invalid element number from AI")
        return None, None

    el = all_elements[el_num - 1]
    screen_x = int((card_x + el[0]) * scale_x)
    screen_y = int((card_y + el[1]) * scale_y)
    print(f"✅ Next/Submit button is element {el_num} → screen ({screen_x},{screen_y})")
    return screen_x, screen_y


if __name__ == "__main__":
    from screenshot import take_screenshot
    path = take_screenshot()
    result = solve_quiz(path)
    print("\n=== Final Result ===")
    print(result)