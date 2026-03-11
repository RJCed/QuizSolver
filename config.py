"""
config.py — Central configuration for QuizSolver.
"""

import json
import os
from paths import app_path

CONFIG_FILE = app_path("quizsolver_config.json")

# ---------------------------------------------------------------------------
# AI Providers
# ---------------------------------------------------------------------------

PROVIDERS = {
    "Groq  (Free — No Credit Card)": {
        "id":          "groq",
        "url":         "https://api.groq.com/openai/v1/chat/completions",
        "key_env":     "GROQ_API_KEY",
        "key_url":     "https://console.groq.com/keys",
        "key_hint":    "Starts with  gsk_...",
        "key_note":    "Sign up free at console.groq.com — no credit card, no billing, ever.",
        "models": [
            "meta-llama/llama-4-scout-17b-16e-instruct  (Free — Recommended)",
            "llama-3.2-90b-vision-preview  (Free)",
            "llama-3.2-11b-vision-preview  (Free — Fastest)",
        ],
        "model_ids": {
            "meta-llama/llama-4-scout-17b-16e-instruct  (Free — Recommended)": "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.2-90b-vision-preview  (Free)":                            "llama-3.2-90b-vision-preview",
            "llama-3.2-11b-vision-preview  (Free — Fastest)":                  "llama-3.2-11b-vision-preview",
        },
        "default_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "free_models":   {
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.2-90b-vision-preview",
            "llama-3.2-11b-vision-preview",
        },
    },
    "OpenRouter  (Free Tier Available)": {
        "id":          "openrouter",
        "url":         "https://openrouter.ai/api/v1/chat/completions",
        "key_env":     "OPENROUTER_API_KEY",
        "key_url":     "https://openrouter.ai/keys",
        "key_hint":    "Starts with  sk-or-...",
        "key_note":    "Free tier: ~200 questions/day. Resets at midnight UTC (8 AM PH).",
        "models": [
            "openrouter/free  (Free — ~200/day)",
            "openrouter/auto  (Paid — most accurate)",
            "openai/gpt-4o-mini  (Paid — fast & cheap)",
            "openai/gpt-4o  (Paid — most powerful)",
            "anthropic/claude-3-haiku  (Paid)",
        ],
        "model_ids": {
            "openrouter/free  (Free — ~200/day)":        "openrouter/free",
            "openrouter/auto  (Paid — most accurate)":   "openrouter/auto",
            "openai/gpt-4o-mini  (Paid — fast & cheap)": "openai/gpt-4o-mini",
            "openai/gpt-4o  (Paid — most powerful)":     "openai/gpt-4o",
            "anthropic/claude-3-haiku  (Paid)":          "anthropic/claude-3-haiku",
        },
        "default_model": "openrouter/free",
        "free_models":   {"openrouter/free"},
    },
}

# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------

DEFAULTS = {
    # --- Provider / API ---
    "provider":    "Groq  (Free — No Credit Card)",
    "model":       "meta-llama/llama-4-scout-17b-16e-instruct",
    "max_tokens":  500,

    # --- Image compression ---
    "image_max_width": 900,
    "image_quality":   70,

    # --- Timing (seconds) ---
    "wait_after_answer":    1.0,   # brief pause after clicking answer before looking for Submit
    "wait_after_submit":    2.5,   # pause after Submit click before looking for Next button
    "wait_for_next_button": 5.0,   # pause before searching for the Next Question button
    "wait_after_next":      2.0,   # pause after clicking Next before starting next cycle

    # --- Detection thresholds ---
    "min_button_area":   500,
    "min_button_height": 15,
    "min_button_width":  50,
    "top_ignore_pct":    0.0,

    # --- Submit step ---
    # True  = bot takes a screenshot + AI call to look for a Submit/Answer button
    # False = site auto-advances after clicking, skip that step entirely (saves 1 API call)
    "has_submit_button": True,
}

# ---------------------------------------------------------------------------
# Site profiles
# ---------------------------------------------------------------------------
# Each entry teaches the bot how to behave on a specific quiz website.
#
# ── HOW TO ADD A NEW SITE ────────────────────────────────────────────────────
# 1. Add a new key to SITE_PROFILES below (the key becomes the dropdown label).
# 2. Fill in the fields you need — unset fields fall back to DEFAULTS above.
# 3. Test with "Custom" first to find the right timings, then lock them in.
#
# ── FIELD REFERENCE ──────────────────────────────────────────────────────────
#
# REQUIRED:
#
#   detection (str) — which button-detection strategy to use:
#       "colored"  → fill-based detection. Best for sites with solid coloured
#                    answer buttons (e.g. Quizalize, Kahoot-style).
#       "bordered" → edge/outline detection. Best for sites where buttons are
#                    plain boxes with a visible border (e.g. Quipper, Google Forms).
#       "auto"     → try "colored" first; fall back to "bordered" automatically.
#                    Safe default when you're unsure.
#
#   has_submit_button (bool) — does clicking an answer require a second click?
#       True  → after clicking the answer the site shows a separate
#               Submit / Answer / Confirm button; the bot will look for it.
#       False → the site records the answer immediately on click and
#               auto-advances; skip the submit step entirely (saves 1 API call).
#
#   TIMING_LOCKED (bool) — lock timing sliders in the GUI for this profile.
#       True  → baked timings below are used as-is; sliders shown as read-only.
#       False → user can freely adjust timing sliders (use for "Custom").
#
# OPTIONAL — timing overrides (seconds). Omit to inherit from DEFAULTS:
#   wait_after_answer    → pause after clicking the answer before looking for Submit.
#   wait_after_submit    → pause after clicking Submit before looking for Next.
#   wait_for_next_button → pause before searching for the Next Question button.
#   wait_after_next      → pause after clicking Next before starting the next cycle.
#
# OPTIONAL — detection tuning. Omit to inherit from DEFAULTS:
#   min_button_height (int)   → minimum pixel height to count as a button.
#   min_button_width  (int)   → minimum pixel width to count as a button.
#   min_button_area   (int)   → minimum pixel area to count as a button.
#   top_ignore_pct   (float)  → fraction (0.0–1.0) of the card's top area to
#                               ignore during detection. Use this to prevent the
#                               question text block from being mistaken for a button.
#                               e.g. 0.20 = ignore the top 20% of the card.
#
# ─────────────────────────────────────────────────────────────────────────────

SITE_PROFILES = {
    # ── Custom ────────────────────────────────────────────────────────────────
    # Default profile — works on most sites. Timing sliders are fully editable.
    "Custom": {
        "detection":         "auto",
        "has_submit_button": True,   # search for Submit to be safe on unknown sites
        "TIMING_LOCKED":     False,
    },

    # ── Quizalize ─────────────────────────────────────────────────────────────
    # Solid-coloured answer buttons (red/blue/yellow/green).
    # Clicking an answer immediately records it — no Submit button exists.
    "Quizalize": {
        "detection":            "colored",
        "has_submit_button":    False,  # auto-advances on click — skip submit step
        "wait_after_submit":    2.5,
        "wait_for_next_button": 5.0,
        "top_ignore_pct":       0.0,
        "TIMING_LOCKED":        True,
    },

    # ── Quipper ───────────────────────────────────────────────────────────────
    # Bordered answer boxes. After selecting, user must click an "Answer" button.
    # top_ignore_pct=0.20 hides the question block from button detection.
    "Quipper": {
        "detection":            "bordered",
        "has_submit_button":    True,   # must click the "Answer" button to confirm
        "wait_after_answer":    1.0,
        "wait_after_submit":    2.5,
        "wait_for_next_button": 5.0,
        "min_button_height":    30,
        "top_ignore_pct":       0.20,
        "TIMING_LOCKED":        True,
    },
}

TIMING_LOCKED_PROFILES = {k for k, v in SITE_PROFILES.items() if v.get("TIMING_LOCKED")}


# ---------------------------------------------------------------------------
# Config load / save
# ---------------------------------------------------------------------------

def load_config() -> dict:
    config = DEFAULTS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            config.update(saved)
        except Exception:
            pass

    # Migration: old "Auto (detect automatically)" → "Custom"
    if config.get("site_profile") == "Auto (detect automatically)":
        config["site_profile"] = "Custom"

    # Ensure provider is valid; fall back to Groq
    if config.get("provider") not in PROVIDERS:
        config["provider"] = DEFAULTS["provider"]

    # Ensure site_profile is valid; fall back to Custom
    if config.get("site_profile") not in SITE_PROFILES:
        config["site_profile"] = "Custom"

    return config


def save_config(config: dict):
    """Persist config — strip internal-only UPPER_CASE keys before writing."""
    saveable = {k: v for k, v in config.items() if not k.isupper()}
    with open(CONFIG_FILE, "w") as f:
        json.dump(saveable, f, indent=2)


def get_active_config(config: dict) -> dict:
    """Merge base config with the selected site profile overrides."""
    merged = config.copy()
    profile_name = config.get("site_profile", "Custom")
    profile = SITE_PROFILES.get(profile_name, {})
    merged.update(profile)
    return merged


def get_provider_cfg(config: dict) -> dict:
    """Return the PROVIDERS entry for the currently selected provider."""
    key = config.get("provider", DEFAULTS["provider"])
    return PROVIDERS.get(key, list(PROVIDERS.values())[0])