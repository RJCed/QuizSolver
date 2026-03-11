import requests
import base64
import os
import json
import io
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from paths import app_path

# Load .env from the folder next to the exe/script
load_dotenv(app_path(".env"))

# Active config — set by bot.py at runtime, falls back to safe defaults
ACTIVE_CONFIG = {
    "provider":        "Groq  (Free — No Credit Card)",
    "model":           "meta-llama/llama-4-scout-17b-16e-instruct",
    "max_tokens":      500,
    "image_max_width": 900,
    "image_quality":   70,
    "min_button_area": 500,
    "min_button_height": 15,
    "min_button_width":  50,
    "top_ignore_pct":    0.0,
    "detection":         "auto",
}

# Module-level log callback — set by bot.py so ai_solver can send to GUI
_log_callback = None


def _log(msg):
    print(msg)
    if _log_callback:
        _log_callback(msg)


# ---------------------------------------------------------------------------
# Resolve current provider config + API key at call time
# ---------------------------------------------------------------------------

def _get_provider_runtime():
    """
    Returns (url, api_key, is_free_model) for the currently active config.
    Reads the correct env var per provider so multi-provider support works.
    """
    from config import PROVIDERS, DEFAULTS

    provider_name = ACTIVE_CONFIG.get("provider", DEFAULTS["provider"])
    pcfg = PROVIDERS.get(provider_name, list(PROVIDERS.values())[0])

    url       = pcfg["url"]
    key_env   = pcfg["key_env"]
    api_key   = os.getenv(key_env, "").strip()
    model     = ACTIVE_CONFIG.get("model", pcfg["default_model"])
    is_free   = model in pcfg.get("free_models", set())

    return url, api_key, is_free, pcfg


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
    """Strategy A: Find non-white filled elements (colored buttons). Quizalize etc."""
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
    """Strategy B: Find bordered/outlined boxes via edge detection. Quipper etc."""
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


def find_elements_in_card(card_np, min_area=None):
    """
    Detect answer buttons. Detection mode controlled by ACTIVE_CONFIG["detection"]:
      "auto"     — try colored first, fall back to bordered
      "colored"  — force colored detection
      "bordered" — force edge/border detection
    """
    card_h, card_w = card_np.shape[:2]
    mode = ACTIVE_CONFIG.get("detection", "auto")
    if min_area is None:
        min_area = ACTIVE_CONFIG.get("min_button_area", 500)
    elements = []

    if mode in ("colored", "auto"):
        elements = detect_colored_elements(card_np, min_area)
        buttons = _filter_buttons(elements, card_w, card_h)
        if len(buttons) >= 2:
            print("  🎨 Using colored element detection")
            return buttons, "colored"
        if mode == "colored":
            print("  ⚠️ Colored detection found no buttons")
            return [], "colored"

    if mode in ("bordered", "auto"):
        elements = detect_bordered_elements(card_np, min_area=2000)
        buttons = _filter_buttons(elements, card_w, card_h)
        if len(buttons) >= 2:
            print("  📐 Using edge/border detection")
            return buttons, "bordered"
        if mode == "bordered":
            print("  ⚠️ Bordered detection found no buttons")
            return [], "bordered"

    print("  ⚠️ Falling back to all detected elements")
    return elements, "fallback"


def _filter_buttons(elements, card_w, card_h=None):
    """
    Keep only elements that look like answer buttons.
    Pass 1: basic size/position gates.
    Pass 2: height clustering — drop outliers much shorter than the median.
    """
    min_h = ACTIVE_CONFIG.get("min_button_height", 15)
    min_w = ACTIVE_CONFIG.get("min_button_width", 50)
    top_pct = ACTIVE_CONFIG.get("top_ignore_pct", 0.0)
    top_cutoff = (card_h * top_pct) if card_h else 0

    candidates = []
    for e in elements:
        cx, cy, x, y, w, h = e
        if top_cutoff and cy < top_cutoff:
            continue
        if w > card_w * 0.7:
            continue
        if h > w:
            continue
        if w < min_w or h < min_h:
            continue
        candidates.append(e)

    if len(candidates) <= 2:
        return candidates

    heights = sorted([e[5] for e in candidates])
    median_h = heights[len(heights) // 2]
    min_acceptable_h = median_h * 0.4
    buttons = [e for e in candidates if e[5] >= min_acceptable_h]
    return buttons if len(buttons) >= 2 else candidates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def crop_element(card_np, element, padding=8, upscale=2):
    """
    Crop a single element out of the card image with optional padding and upscaling.
    Not used by the main bot flow (which sends an annotated card image instead),
    but kept as a debugging/inspection utility — e.g. to visually verify detection.
    """
    cx, cy, x, y, w, h = element
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(card_np.shape[1], x + w + padding)
    y2 = min(card_np.shape[0], y + h + padding)
    crop = card_np[y1:y2, x1:x2]
    if upscale > 1:
        crop = cv2.resize(crop, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)
    return crop


def annotate_card(card_np, elements, color=(255, 100, 0)):
    """
    Draw a numbered bounding box on the card for each element.
    Returns a new annotated numpy array — original is not modified.
    Always produces exactly ONE image regardless of element count, so models
    with a per-request image cap (e.g. Llama's hard limit of 5) are never hit.

    Args:
        card_np:  H×W×C numpy array (RGB or RGBA — both handled safely).
        elements: list of (cx, cy, x, y, w, h) tuples from find_elements_in_card.
        color:    Border/badge colour as an RGB tuple. Default is orange (255,100,0).

    Returns:
        H×W×3 numpy array in RGB.
    """
    # Guard: convert to 3-channel RGB regardless of source format (RGB or RGBA).
    rgb = np.array(Image.fromarray(card_np).convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    b, g, r    = color[2], color[1], color[0]   # unpack RGB → BGR components
    h_img, w_img = bgr.shape[:2]

    for i, el in enumerate(elements):
        cx, cy, x, y, w, h = el
        label = str(i + 1)

        # Bold border around the button
        cv2.rectangle(bgr, (x, y), (x + w, y + h), (b, g, r), 3)

        # Number badge — filled rectangle at the button's top-left corner
        font       = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.55, min(1.1, h / 40))
        thickness  = 2
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        pad = 4

        # Clamp badge to stay within image bounds so it never clips off-screen
        bx1 = max(0, x)
        by1 = max(0, y)
        bx2 = min(bx1 + tw + pad * 2,            w_img - 1)
        by2 = min(by1 + th + pad * 2 + baseline,  h_img - 1)

        cv2.rectangle(bgr, (bx1, by1), (bx2, by2), (b, g, r), cv2.FILLED)

        # putText origin is the bottom-left of the text.
        # Using by1 + th + pad keeps the text anchored from the badge top,
        # which is stable even when the badge is at y=0 or near the bottom edge.
        text_x = bx1 + pad
        text_y = min(by1 + th + pad, h_img - 1)
        cv2.putText(bgr, label, (text_x, text_y),
                    font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def encode_image(path):
    """
    Encode an image FILE as a compressed JPEG base64 string.
    Not used by the main bot flow (which uses encode_numpy on in-memory arrays),
    but kept as a utility for external callers or debugging.
    """
    max_width = ACTIVE_CONFIG.get("image_max_width", 900)
    quality   = ACTIVE_CONFIG.get("image_quality", 70)
    img = Image.open(path).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def encode_numpy(img_np):
    """Encode a numpy RGB array as compressed JPEG — no temp file needed."""
    max_width = ACTIVE_CONFIG.get("image_max_width", 900)
    quality   = ACTIVE_CONFIG.get("image_quality", 70)
    img = Image.fromarray(img_np).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# AI call — provider-agnostic
# ---------------------------------------------------------------------------

def call_ai(content):
    url, api_key, is_free_model, pcfg = _get_provider_runtime()
    model      = ACTIVE_CONFIG.get("model", pcfg["default_model"])
    max_tokens = ACTIVE_CONFIG.get("max_tokens", 500)
    provider_id = pcfg["id"]   # "groq" or "openrouter"

    if not api_key:
        _log("❌ API_ERROR:NO_KEY — No API key entered")
        _log(f"💡 FIX: Paste your {pcfg.get('id', 'provider').title()} API key and click Save Key")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    # OpenRouter wants these extra headers
    if provider_id == "openrouter":
        headers["HTTP-Referer"] = "https://quizsolver.app"
        headers["X-Title"]      = "QuizSolver"

    try:
        response = requests.post(
            url=url,
            headers=headers,
            json={
                "model":      model,
                "max_tokens": max_tokens,
                "messages":   [{"role": "user", "content": content}],
            },
            timeout=30,
        )
        result = response.json()
    except requests.exceptions.Timeout:
        _log("❌ API_ERROR:TIMEOUT — Request timed out after 30s")
        _log("💡 FIX: Check your internet connection, or try again")
        return None
    except requests.exceptions.ConnectionError:
        _log(f"❌ API_ERROR:NO_INTERNET — Could not reach {pcfg.get('id', 'provider').title()}")
        _log("💡 FIX: Check your internet connection")
        return None
    except Exception as e:
        _log(f"❌ API_ERROR:UNKNOWN — {e}")
        return None

    # ---- Error handling ----
    if "error" in result:
        msg  = result["error"].get("message", "Unknown error")
        code = result["error"].get("code", 0)

        if "credits" in msg.lower() or "afford" in msg.lower():
            if is_free_model:
                _log("❌ API_ERROR:DAILY_LIMIT — Free model daily limit reached")
                if provider_id == "openrouter":
                    _log("💡 FIX: Wait until 8:00 AM PH time (midnight UTC) for reset")
                else:
                    _log("💡 FIX: Wait a few minutes — Groq rate limits reset frequently")
            else:
                _log("❌ API_ERROR:NO_CREDITS — Not enough credits for this model")
                _log("💡 FIX: Top up your account, or switch to a free model")

        elif "rate limit" in msg.lower() or code == 429:
            _log("❌ API_ERROR:RATE_LIMIT — Too many requests, slow down")
            _log("💡 FIX: Increase the 'After Submit Wait' slider in Advanced Settings")

        elif "no endpoints" in msg.lower():
            _log(f"❌ API_ERROR:NO_ENDPOINTS — Model \"{model}\" is unavailable right now")
            _log("💡 FIX: Switch to a different model in the AI settings")

        elif "invalid" in msg.lower() and "model" in msg.lower():
            _log(f"❌ API_ERROR:BAD_MODEL — Model \"{model}\" not found")
            _log("💡 FIX: Choose a different model from the dropdown")

        elif "daily" in msg.lower() or "quota" in msg.lower():
            _log("❌ API_ERROR:DAILY_LIMIT — Daily limit reached")
            _log("💡 FIX: Wait until tomorrow, or switch to a different provider")

        elif "auth" in msg.lower() or code in (401, 403):
            _log("❌ API_ERROR:BAD_KEY — API key was rejected")
            _log("💡 FIX: Re-enter your API key and click Save Key")

        else:
            _log(f"❌ API_ERROR:UNKNOWN — {msg}")

        return None

    if not result.get("choices"):
        _log("❌ API_ERROR:EMPTY_RESPONSE — API returned no answer")
        _log("💡 FIX: Increase Max Tokens slider, or switch to a different model")
        return None

    raw = result["choices"][0]["message"]["content"]
    print("=== AI Raw Response ===")
    print(raw)

    if not raw or not raw.strip():
        _log("❌ API_ERROR:EMPTY_RESPONSE — AI returned an empty response")
        _log("💡 FIX: Increase the Max Tokens slider in Advanced Settings")
        return None

    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        _log("❌ AI_ERROR:BAD_JSON — AI response was cut off or malformed")
        _log("💡 FIX: Increase the Max Tokens slider — response is being cut off")
        return None


# ---------------------------------------------------------------------------
# Main quiz solver
# ---------------------------------------------------------------------------

def solve_quiz(image_path):
    """
    Find card → detect answer buttons → send to AI → return coords to click.
    """
    img    = Image.open(image_path)
    img_np = np.array(img)
    img_h, img_w = img_np.shape[:2]

    try:
        import pyautogui
        real_w, real_h = pyautogui.size()
        scale_x, scale_y = real_w / img_w, real_h / img_h
    except Exception:
        scale_x = scale_y = 1.0

    card_bounds = find_white_card(img_np)
    if card_bounds:
        card_x, card_y, card_w, card_h = card_bounds
        print(f"📋 Found card at ({card_x},{card_y}) size {card_w}x{card_h}")
    else:
        print("⚠️ No white card — using full screenshot")
        card_x, card_y, card_w, card_h = 0, 0, img_w, img_h

    card_np = img_np[card_y:card_y+card_h, card_x:card_x+card_w]

    buttons, strategy = find_elements_in_card(card_np)
    print(f"🔲 Found {len(buttons)} buttons ({strategy})")
    for i, btn in enumerate(buttons):
        print(f"   {i+1}: center=({btn[0]},{btn[1]}) size={btn[4]}x{btn[5]}")

    if not buttons:
        _log("❌ No answer buttons found on screen — make sure your quiz is visible")
        return None

    # Draw numbered labels on ONE card image — always a single image sent to AI,
    # so models with a per-request image cap (Llama: 5) are never hit.
    annotated_np = annotate_card(card_np, buttons)

    content = []
    content.append({"type": "text", "text": (
        f"This is a quiz card with {len(buttons)} answer buttons. "
        f"Each button is outlined and labelled with a number (1–{len(buttons)})."
    )})
    content.append({"type": "image_url", "image_url": {
        "url": f"data:image/jpeg;base64,{encode_numpy(annotated_np)}"
    }})
    content.append({"type": "text", "text": f"""
Look at the quiz card. The answer buttons are numbered 1–{len(buttons)} with orange labels.

IMPORTANT — set "state" correctly:
- "question" = unanswered, buttons are clickable (most common)
- "result"   = answer ALREADY submitted, result is shown on screen

When in doubt, use "question". Only use "result" if you clearly see a score, checkmark, or Correct/Incorrect feedback.

Which numbered button contains the correct answer?
Respond ONLY with JSON, no markdown, no explanation:
{{
    "state": "question",
    "correct_button": <1 to {len(buttons)}>,
    "correct_answer": "<exact text of correct answer>"
}}"""})

    ai_result = call_ai(content)
    if not ai_result:
        return None

    state          = ai_result.get("state", "question")
    correct_button = ai_result.get("correct_button", 0)
    correct_answer = ai_result.get("correct_answer", "")

    if correct_answer:
        _log(f"💡 Answer: {correct_answer}")

    print(f"🤖 AI: state={state}, button={correct_button}, answer='{correct_answer}'")

    answer_x = answer_y = 0
    if correct_button and 1 <= correct_button <= len(buttons):
        btn      = buttons[correct_button - 1]
        answer_x = int((card_x + btn[0]) * scale_x)
        answer_y = int((card_y + btn[1]) * scale_y)
        print(f"🎯 Button {correct_button} → screen ({answer_x},{answer_y})")

    return {
        "state":          state,
        "correct_answer": correct_answer,
        "answer_x":       answer_x,
        "answer_y":       answer_y,
        "_meta": {
            "image_path": image_path,
            "card_x": card_x, "card_y": card_y,
            "card_w": card_w, "card_h": card_h,
            "scale_x": scale_x, "scale_y": scale_y,
            "strategy": strategy,
        },
    }


# ---------------------------------------------------------------------------
# Next button finder
# ---------------------------------------------------------------------------

def find_next_button(image_path, meta):
    """Find the Next/Continue/Submit button after an answer is submitted."""
    img    = Image.open(image_path)
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

    colored  = detect_colored_elements(card_np, min_area=500)
    bordered = detect_bordered_elements(card_np, min_area=1000)

    all_elements = colored.copy()
    for be in bordered:
        is_dup = any(abs(be[0]-e[0]) < 30 and abs(be[1]-e[1]) < 30 for e in all_elements)
        if not is_dup:
            all_elements.append(be)

    all_elements.sort(key=lambda e: (round(e[1] / 60) * 60, e[0]))
    print(f"🔍 Found {len(all_elements)} elements for Next button search")

    if not all_elements:
        _log("❌ No clickable elements found — quiz may have changed layout")
        return None, None

    # Single annotated image — same approach as solve_quiz, no per-element crops.
    annotated_np = annotate_card(card_np, all_elements)

    content = []
    content.append({"type": "text", "text": (
        f"This is a quiz screen. All {len(all_elements)} clickable elements "
        f"are outlined and labelled with numbers 1–{len(all_elements)}."
    )})
    content.append({"type": "image_url", "image_url": {
        "url": f"data:image/jpeg;base64,{encode_numpy(annotated_np)}"
    }})
    content.append({"type": "text", "text": f"""
Which numbered element is the button to proceed forward? Look for:
- "Next" / "Next Question" button
- "Continue" button
- Arrow / → button
- "Answer" or "Submit" button (if the answer hasn't been submitted yet)

Respond ONLY with JSON, no explanation, no markdown:
{{
    "found": true or false,
    "element_number": <1 to {len(all_elements)}>
}}"""})

    ai_result = call_ai(content)
    if not ai_result or not ai_result.get("found"):
        _log("❌ Could not find the Next button — try increasing the Next Question Wait slider")
        return None, None

    el_num = ai_result.get("element_number", 0)
    if not el_num or el_num < 1 or el_num > len(all_elements):
        _log("❌ AI returned an invalid element number — retrying next question")
        return None, None

    el       = all_elements[el_num - 1]
    screen_x = int((card_x + el[0]) * scale_x)
    screen_y = int((card_y + el[1]) * scale_y)
    print(f"✅ Next/Submit button is element {el_num} → screen ({screen_x},{screen_y})")
    return screen_x, screen_y


if __name__ == "__main__":
    from screenshot import take_screenshot
    path   = take_screenshot()
    result = solve_quiz(path)
    print("\n=== Final Result ===")
    print(result)