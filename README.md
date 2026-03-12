<div align="center">

# ⚡ QuizSolver

**An AI-powered bot that automatically reads and answers quiz questions on your screen.**

[![MIT License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Built with Claude](https://img.shields.io/badge/built%20with-Claude%20AI-blueviolet.svg)](https://anthropic.com)

</div>

---

## What is QuizSolver?

QuizSolver is a desktop app for Windows that uses AI vision to read quiz questions directly from your screen and automatically click the correct answer for you. It works by taking a screenshot, detecting the answer buttons using computer vision, sending the question to an AI model, and clicking the right one — all in a few seconds.

> ⚠️ **Disclaimer:** This tool is intended for educational and personal use only. Use it responsibly and in accordance with the terms of service of any platform you use it on.

---

## Features

- 🤖 **AI-powered** — uses real vision models, not keyword matching
- 🆓 **Free to use** — works with Groq's free API (no credit card required)
- 🖥️ **Simple GUI** — no command line needed
- ⚙️ **Configurable** — timing, detection, and behavior settings for different sites
- ⌨️ **Hotkeys** — F9 to start, ESC to stop
- 📋 **Answer history** — see every answer the bot gave this session

---

## Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| **Quizalize** | ✅ Built-in profile | Solid-colour answer buttons, no Submit step |
| **Quipper** | ✅ Built-in profile | Bordered answer boxes, requires Submit click |
| **Other sites** | ⚙️ Custom mode | May work — use Custom profile and adjust settings |

> Custom mode lets you toggle whether your site has a Submit button, tune timing sliders, and adjust button detection. Most sites with a visible card layout should work.

---

## Requirements

### For end users (running the `.exe`)
- Windows 10 or 11
- A free API key from [Groq](https://console.groq.com/keys) *(no credit card needed — takes 30 seconds)*

That's it.

### For developers (running from source or building)
- Python 3.10 or newer — [download here](https://python.org)
  - ✅ Check **"Add Python to PATH"** during install
- All dependencies installed via `pip` (see Option B below)

---

## Getting Started

### Option A — Run the pre-built `.exe` (recommended for most users)

1. Download the latest release zip from the [Releases](../../releases) page
2. Unzip it anywhere
3. Run `QuizSolver.exe`
4. Follow the in-app setup steps (Steps 1–4 in the sidebar)

### Option B — Run from source

```bash
git clone https://github.com/RJCed/QuizSolver.git
cd quizsolver
pip install customtkinter pillow pyautogui requests python-dotenv keyboard opencv-python numpy
python main.py
```

### Option C — Build it yourself

1. Make sure Python and all packages are installed (Option B above)
2. Place `logo.png` in the project folder
3. Double-click `build.bat`
4. Find your app in `dist\QuizSolver\`
5. Zip that folder and share it

---

## How to Use

### Step 1 — Choose your AI provider

Open the app and look at the left panel. Under **Step 1 — AI Provider**, choose:

- **Groq (Free — No Credit Card)** — recommended. No credit card, no billing. Free tier has generous rate limits that reset frequently.
- **OpenRouter (Free Tier Available)** — alternative option with a free tier (~200 questions/day).

---

### Step 2 — Get and save your API key

**For Groq (recommended):**
1. Click **"Get free key →"** in the app — it opens `console.groq.com/keys`
2. Sign up or log in (no credit card needed)
3. Click **"Create API Key"**, copy it
4. Paste it into the **API Key** field in the app
5. Click **Save Key** — you only need to do this once

**For OpenRouter:**
1. Click **"Get API key →"** — it opens `openrouter.ai/keys`
2. Sign up, go to Keys, create one
3. Paste and save it the same way

---

### Step 3 — Choose your AI model

The default model (`meta-llama/llama-4-scout-17b-16e-instruct`) is free and works well for most quizzes. Leave it as-is unless you have a reason to change it.

If you want to try a different model, click **"Browse Groq models →"** to see what's available, then paste the model ID into the **Custom model ID** field.

---

### Step 4 — Select your quiz site

Under **Step 4 — Quiz Website**, pick your site from the dropdown:

- **Quizalize** or **Quipper** — use the built-in profile (settings are locked to known-correct values)
- **Custom** — for any other site. You can adjust timing and behavior in Step 5

---

### Step 5 — Timing & Behavior

This section only matters if you're using **Custom** mode.

**Has Submit Button**
- Turn **ON** if your quiz site shows a Submit/Answer/Confirm button after you select an answer
- Turn **OFF** if the answer is recorded immediately when you click it

**Site auto-advances (no Next button needed)**
- Turn **ON** if your site automatically moves to the next question without a Next button
- Turn **OFF** if there's always a Next button to click (most common)

The sliders control how long the bot waits between steps. If the bot moves too fast for your internet connection or site, increase these.

---

### Starting the bot

1. Open your quiz in the browser so the **first question is visible** on screen
2. Come back to QuizSolver
3. Press **START** (or press **F9**)
4. The app minimizes automatically — a small floating **STOP** button appears on screen
5. The bot reads the screen, clicks the answer, and moves to the next question automatically
6. Press **ESC** or click **STOP** to stop at any time

---

### Tips for best results

- Don't move your mouse while the bot is running
- Keep the quiz fully visible — no other windows on top of it
- If the bot misses answers or reads them wrong, try increasing **Image Quality** in Advanced Settings
- If it moves too fast, increase the timing sliders in Step 5
- If you see an error in the log, the **💡 FIX:** line below it tells you exactly what to do

---

## Built With

| Tool / Library | Purpose |
|---|---|
| [Python](https://python.org) | Core language |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | GUI framework |
| [OpenCV](https://opencv.org) | Computer vision — button detection |
| [Pillow](https://python-pillow.org) | Image processing |
| [PyAutoGUI](https://pyautogui.readthedocs.io) | Screen capture & mouse control |
| [Groq API](https://console.groq.com) | Free AI inference (vision models) |
| [OpenRouter API](https://openrouter.ai) | Alternative AI provider |
| [PyInstaller](https://pyinstaller.org) | Packaging into a portable .exe |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | API key management |
| [keyboard](https://github.com/boppreh/keyboard) | Global hotkeys (F9, ESC) |

---

## AI Models Used

QuizSolver sends screenshots to vision-capable AI models to read and answer quiz questions.

| Provider | Default Model | Cost |
|---|---|---|
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | Free |
| OpenRouter | `openrouter/free` | Free (~200/day) |

Other models (including paid ones like GPT-4o) can be used by entering their ID in the Custom model field.

---

## 🤖 Built with Claude AI

This project was designed and built with the assistance of **Claude Sonnet 4.6** by [Anthropic](https://anthropic.com) — including the computer vision pipeline, GUI layout, bot logic, error handling, and all developer documentation.

---

## Contributing

Contributions are welcome! This project is fully open — you don't need to ask permission to fork it, modify it, or submit a pull request.

### Adding support for a new quiz site

You only need to edit **`config.py`** — no other files need to change:

```python
# In SITE_PROFILES, copy the "Custom" block and adjust:
"YourSiteName": {
    "detection":            "colored",   # or "bordered" or "auto"
    "has_submit_button":    False,       # does the site need a Submit click?
    "next_button_optional": False,       # does the site auto-advance?
    "wait_after_answer":    1.0,
    "wait_for_next_button": 3.0,
    "TIMING_LOCKED":        True,        # lock sliders for this preset
},
```

Restart the app — your new site appears in the dropdown automatically.

### Adding a new AI provider

Add a new entry to the `PROVIDERS` dict in `config.py`. The required fields are documented in the existing entries. No other files need editing.

### Adding a new behavior switch (flow flag)

1. Add it to `DEFAULTS` and relevant `SITE_PROFILES` in `config.py`
2. Add a tuple to `BEHAVIOR_SWITCHES` in `gui.py` — the switch appears automatically
3. Read the flag in `bot.py` with `config.get("your_flag", DEFAULTS["your_flag"])`

### File overview

| File | Role |
|---|---|
| `config.py` | All site profiles, providers, and defaults — **start here** |
| `bot.py` | Main question loop — reads config, calls ai_solver, clicks |
| `ai_solver.py` | Computer vision + AI API calls |
| `gui.py` | GUI — reads config.py dynamically, no hardcoded site logic |
| `paths.py` | Path resolver for user data vs bundled assets |
| `main.py` | Entry point |

---

## License

This project is licensed under the **MIT License** — you are free to use, copy, modify, merge, publish, distribute, and/or sell copies of this software without restriction and without needing to ask for permission.

See the [LICENSE](LICENSE) file for the full text.

---

## Author

**RJCed (Arjay Cedigo)**
Built with ❤️ and [Claude Sonnet 4.6](https://anthropic.com)
it serves its purpose lol

---

<div align="center">
<sub>QuizSolver is an independent open-source project and is not affiliated with Quizalize, Quipper, Groq, OpenRouter, or Anthropic.</sub>
</div>
