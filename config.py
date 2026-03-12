"""
config.py — Central configuration for QuizSolver.

ARCHITECTURE FOR DEVELOPERS
============================
This file is the single source of truth for everything the bot does.
You should never need to edit bot.py or ai_solver.py just to support a new
quiz website — add a profile here and everything else picks it up automatically.

  PROVIDERS   — AI providers (Groq, OpenRouter). Add new providers here.
  DEFAULTS    — Safe fallback values used when no profile overrides a key.
  SITE_PROFILES — Per-site overrides. Read the HOW TO ADD A NEW SITE guide below.
  BEHAVIOR_SWITCHES (gui.py) — Each flow flag in DEFAULTS/SITE_PROFILES should
                               have a matching entry there so users can toggle it.

Quick-start: copy the "Custom" profile block, rename it, adjust the fields,
and restart the app — your new site appears in the dropdown automatically.
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
        "id":            "groq",
        "url":           "https://api.groq.com/openai/v1/chat/completions",
        "key_env":       "GROQ_API_KEY",
        "key_url":       "https://console.groq.com/keys",
        "key_hint":      "Starts with  gsk_...",
        "key_note":      "Sign up free at console.groq.com — no credit card, no billing, ever.",
        "key_btn_label": "Get free key →",
        "models_url":    "https://console.groq.com/docs/models",
        "models": [
            "meta-llama/llama-4-scout-17b-16e-instruct  (Free — Recommended)",
        ],
        "model_ids": {
            "meta-llama/llama-4-scout-17b-16e-instruct  (Free — Recommended)": "meta-llama/llama-4-scout-17b-16e-instruct",
        },
        "default_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "free_models": {
            "meta-llama/llama-4-scout-17b-16e-instruct",
        },
    },
    "OpenRouter  (Free Tier Available)": {
        "id":            "openrouter",
        "url":           "https://openrouter.ai/api/v1/chat/completions",
        "key_env":       "OPENROUTER_API_KEY",
        "key_url":       "https://openrouter.ai/keys",
        "key_hint":      "Starts with  sk-or-...",
        "key_note":      "Free tier: ~200 questions/day. Resets at midnight UTC (8 AM PH).",
        "key_btn_label": "Get API key →",
        "models_url":    "https://openrouter.ai/models",
        "models": [
            "openrouter/free  (Free — ~200/day)",
            "openrouter/auto  (Paid — most accurate)",
            "openai/gpt-4o-mini  (Paid — fast & cheap)",
            "openai/gpt-4o  (Paid — most powerful)",
            "anthropic/claude-3-haiku  (Paid)",
        ],
        "model_ids": {
            "openrouter/free  (Free — ~200/day)":         "openrouter/free",
            "openrouter/auto  (Paid — most accurate)":    "openrouter/auto",
            "openai/gpt-4o-mini  (Paid — fast & cheap)":  "openai/gpt-4o-mini",
            "openai/gpt-4o  (Paid — most powerful)":      "openai/gpt-4o",
            "anthropic/claude-3-haiku  (Paid)":           "anthropic/claude-3-haiku",
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
    "wait_after_answer":    1.0,   # pause after clicking answer, before looking for Submit
    "wait_after_submit":    2.5,   # pause after clicking Submit, before looking for Next
    "wait_for_next_button": 3.0,   # pause before searching for the Next Question button
    "wait_after_next":      2.0,   # pause after clicking Next, before starting next cycle

    # --- Detection thresholds ---
    "min_button_area":   500,
    "min_button_height": 15,
    "min_button_width":  50,
    "top_ignore_pct":    0.0,

    # ---------------------------------------------------------------------------
    # Flow flags — booleans that control which steps the bot takes per question.
    #
    # HOW TO ADD A NEW FLOW FLAG (for future developers):
    #   1. Add it here in DEFAULTS with a safe fallback value.
    #   2. Override it in each relevant SITE_PROFILES entry below.
    #   3. Read it in bot.py:  config.get("your_flag", DEFAULTS["your_flag"])
    #   4. Add a CTkSwitch for it in gui.py inside _build_behavior_section().
    #      Register it in self._behavior_switches and self._behavior_switch_vars.
    # ---------------------------------------------------------------------------

    # True  → bot takes a 2nd screenshot + AI call to find and click a
    #         Submit / Answer / Confirm button after clicking the answer.
    # False → site records the click immediately; skip the submit step
    #         (saves 1 screenshot + 1 API call per question).
    "has_submit_button": True,

    # True  → if no Next button is found, assume the site already advanced
    #         to the next question and loop back automatically.
    # False → if no Next button is found, treat the quiz as finished and stop.
    "next_button_optional": False,
}

# ---------------------------------------------------------------------------
# Site profiles
# ---------------------------------------------------------------------------
# Each entry teaches the bot exactly how to behave on a specific quiz site.
#
# ── HOW TO ADD A NEW SITE ────────────────────────────────────────────────────
# 1. Add a new key here (the string becomes the dropdown label in the GUI).
# 2. Fill in only the fields you need — everything else inherits from DEFAULTS.
# 3. Test timings with "Custom" first, then hard-code them and set TIMING_LOCKED.
#
# ── FIELD REFERENCE ──────────────────────────────────────────────────────────
#
# detection (str)              "colored" | "bordered" | "auto"
#   "colored"  → fill/colour-based detection. For solid-coloured buttons.
#   "bordered" → edge/outline detection. For plain bordered boxes.
#   "auto"     → try colored first, fall back to bordered. Safe default.
#
# has_submit_button (bool)     see DEFAULTS comment above
# next_button_optional (bool)  see DEFAULTS comment above
#
# TIMING_LOCKED (bool)
#   True  → timing sliders AND behavior switches in the GUI are read-only.
#            The profile's baked values are shown but cannot be changed.
#   False → user can adjust everything freely (only for "Custom").
#
# Timing overrides (seconds) — omit any to inherit from DEFAULTS:
#   wait_after_answer | wait_after_submit | wait_for_next_button | wait_after_next
#
# ⚠️  If you add a NEW timing key, also add it to the STEP_SLIDER dict in
#   gui.py → _build_behavior_section() so users see a slider for it.
#
# Detection tuning — omit any to inherit from DEFAULTS:
#   min_button_height | min_button_width | min_button_area
#   top_ignore_pct  — fraction (0.0–1.0) of card top to skip so the question
#                     text block isn't mistaken for an answer button.
#                     e.g. 0.20 = ignore the top 20% of the card.
#
# ─────────────────────────────────────────────────────────────────────────────

SITE_PROFILES = {
    # ── Custom ────────────────────────────────────────────────────────────────
    # All timing sliders and behavior switches are freely editable by the user.
    "Custom": {
        "detection":            "auto",
        "has_submit_button":    True,   # safe default — user can toggle freely
        "next_button_optional": False,  # safe default — user can toggle freely
        "TIMING_LOCKED":        False,
    },

    # ── Quizalize ─────────────────────────────────────────────────────────────
    # Solid-coloured buttons (red/blue/yellow/green).
    # Clicking an answer records it immediately — no Submit button exists.
    # A "Next Question" button always appears after each answer is recorded.
    "Quizalize": {
        "detection":            "colored",
        "has_submit_button":    False,  # no Submit — answer is recorded on click
        "next_button_optional": False,  # Next button always appears
        "wait_after_answer":    1.0,
        "wait_for_next_button": 3.0,
        "top_ignore_pct":       0.0,
        "TIMING_LOCKED":        True,
    },

    # ── Quipper ───────────────────────────────────────────────────────────────
    # Bordered answer boxes. After selecting, an "Answer" button must be clicked.
    # A "Next" button then appears. top_ignore_pct hides the question block.
    "Quipper": {
        "detection":            "bordered",
        "has_submit_button":    True,   # must click "Answer" button to confirm
        "next_button_optional": False,  # Next button always appears after submit
        "wait_after_answer":    1.0,
        "wait_after_submit":    2.5,
        "wait_for_next_button": 3.0,
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

    # Migration: old profile name → "Custom"
    if config.get("site_profile") == "Auto (detect automatically)":
        config["site_profile"] = "Custom"

    # Migration: broken/removed model IDs → working default
    _broken_models = {
        "llama-3.2-90b-vision-preview",
        "llama-3.2-11b-vision-preview",
        "meta-llama/llama-4-maverick-17b-128e-instruct",  # removed — not functional on Groq
    }
    if config.get("model") in _broken_models:
        config["model"] = DEFAULTS["model"]

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
    """
    Merge the user's saved config with the selected site profile.
    Profile values always win — they represent known-correct site settings.
    """
    merged = config.copy()
    profile_name = config.get("site_profile", "Custom")
    profile = SITE_PROFILES.get(profile_name, {})
    merged.update(profile)
    return merged


def get_provider_cfg(config: dict) -> dict:
    """Return the PROVIDERS entry for the currently selected provider."""
    key = config.get("provider", DEFAULTS["provider"])
    return PROVIDERS.get(key, list(PROVIDERS.values())[0])