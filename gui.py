"""
gui.py — QuizSolver GUI
Built with CustomTkinter. Orange & black theme.
"""

import customtkinter as ctk
import tkinter as tk
import webbrowser
import os
from PIL import Image, ImageDraw, ImageTk
from dotenv import load_dotenv, set_key

from paths import app_path
from config import (
    load_config, save_config, get_active_config,
    SITE_PROFILES, PROVIDERS, TIMING_LOCKED_PROFILES,
)
import bot

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT    = "#ff6b2b"
ACCENT2   = "#ff8c42"
BG_DARK   = "#0c0c0c"
BG_CARD   = "#161616"
BG_INPUT  = "#222222"
TEXT_MAIN = "#e8e8e8"
TEXT_DIM  = "#888888"
TEXT_HINT = "#555555"
SUCCESS   = "#4ade80"
DANGER    = "#f87171"
WARNING   = "#fbbf24"
LOCKED_C  = "#3a3a3a"

HOW_TO_USE = [
    ("1️⃣", "Choose your AI provider",
     "Groq is recommended — it's 100% free, no credit card.\n"
     "Click 'Get free key' to get your key in 30 seconds."),
    ("2️⃣", "Paste & save your key",
     "Paste the key in the API Key box and click Save Key.\n"
     "✔ You only need to do this once per provider."),
    ("3️⃣", "Pick your quiz site",
     "Select your site from the Quiz Website dropdown.\n"
     "Not sure? Leave it on Custom — it works on most sites."),
    ("4️⃣", "Open your quiz in the browser",
     "Go to the quiz so the first question is visible on screen."),
    ("5️⃣", "Press START  (or press F9)",
     "This window minimizes automatically.\n"
     "The bot reads the screen and clicks the answer for you."),
    ("6️⃣", "Stop anytime  (press ESC)",
     "Press ESC or click the STOP button that floats on screen."),
    ("⚠️", "Tips for best results",
     "• Don't move the mouse while the bot is running\n"
     "• Keep the quiz fully visible — no other windows on top\n"
     "• If it misses answers, try a higher Image Quality setting"),
]


# ---------------------------------------------------------------------------
# Floating STOP overlay
# ---------------------------------------------------------------------------

class StopOverlay(tk.Toplevel):
    def __init__(self, parent, stop_callback):
        super().__init__(parent)
        self.stop_callback = stop_callback
        self.title("")
        self.geometry("160x52+20+20")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)
        self.overrideredirect(True)
        self.configure(bg="#1a0a00")
        self._drag_x = self._drag_y = 0

        border = tk.Frame(self, bg=ACCENT, padx=1, pady=1)
        border.pack(fill="both", expand=True)
        inner = tk.Frame(border, bg="#1a0a00")
        inner.pack(fill="both", expand=True)

        drag = tk.Label(inner, text="QuizSolver  ⠿", bg="#1a0a00", fg="#555555",
                        font=("Segoe UI", 8), cursor="fleur")
        drag.pack(fill="x", padx=6, pady=(4, 0))
        drag.bind("<ButtonPress-1>", self._drag_start)
        drag.bind("<B1-Motion>",     self._drag_motion)

        tk.Button(inner, text="■  STOP", bg=DANGER, fg="white",
                  activebackground="#c0392b", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", bd=0,
                  command=stop_callback).pack(fill="x", padx=6, pady=(2, 6))

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.winfo_x()
        self._drag_y = e.y_root - self.winfo_y()

    def _drag_motion(self, e):
        self.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class QuizSolverApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QuizSolver")
        self.geometry("880x720")
        self.minsize(760, 600)
        self.configure(fg_color=BG_DARK)

        self.config_data   = load_config()
        self.is_running    = False
        self._last_error   = None
        self._stop_overlay = None
        self._how_to_expanded      = False
        self._error_banner_visible = False

        # Slider widget registries
        self._timing_sliders:     dict = {}   # config_key → CTkSlider
        self._timing_val_labels:  dict = {}   # config_key → CTkLabel (value)
        self._timing_lock_labels: dict = {}   # config_key → CTkLabel (🔒)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_app_icon()
        self._build_ui()
        self._load_api_key()
        self._update_timing_lock(self.config_data.get("site_profile", "Custom"))

    # -----------------------------------------------------------------------
    # Icon
    # -----------------------------------------------------------------------

    def _set_app_icon(self):
        import tempfile
        try:
            size = 64
            img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([0, 0, size-1, size-1], radius=10, fill="#ff6b2b")
            draw.polygon([(38,5),(21,30),(31,30),(26,59),(43,33),(33,33)], fill="white")
            tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            tmp_path = tmp.name
            tmp.close()
            img.save(tmp_path, format="ICO", sizes=[(64,64),(32,32),(16,16)])
            self.iconbitmap(tmp_path)
            self._icon_tmp = tmp_path
        except Exception:
            try:
                self._icon_img = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_img)
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Build UI
    # -----------------------------------------------------------------------

    def _build_ui(self):
        self._build_header()
        self._build_controls()

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=(10, 8))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=4)
        content.rowconfigure(0, weight=1)

        self._build_settings_panel(content)
        self._build_log_panel(content)

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=58)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="⚡ QuizSolver",
                     font=ctk.CTkFont(family="Courier New", size=21, weight="bold"),
                     text_color=ACCENT).pack(side="left", padx=20, pady=14)

        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right", padx=20)

        self.question_label = ctk.CTkLabel(right, text="",
                                           font=ctk.CTkFont(size=12), text_color=TEXT_DIM)
        self.question_label.pack(side="left", padx=(0, 16))

        self.status_label = ctk.CTkLabel(right, text="● Ready",
                                         font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                                         text_color=TEXT_DIM)
        self.status_label.pack(side="left")

    def _build_settings_panel(self, parent):
        panel = ctk.CTkScrollableFrame(parent, fg_color=BG_CARD, corner_radius=10, width=290)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # ── Helpers ──────────────────────────────────────────────────────
        def divider():
            ctk.CTkFrame(panel, fg_color=ACCENT, height=1).pack(fill="x", padx=12, pady=(16, 0))

        def section_title(icon, title, subtitle=None):
            divider()
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(6, 2))
            ctk.CTkLabel(row, text=f"{icon}  {title}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT_MAIN).pack(side="left")
            if subtitle:
                ctk.CTkLabel(panel, text=subtitle,
                             font=ctk.CTkFont(size=10), text_color=TEXT_HINT
                             ).pack(anchor="w", padx=12, pady=(0, 4))

        def hint(text, color=None):
            ctk.CTkLabel(panel, text=text, font=ctk.CTkFont(size=10),
                         text_color=color or TEXT_HINT,
                         wraplength=250, justify="left"
                         ).pack(anchor="w", padx=14, pady=(1, 0))

        # ── HOW TO USE (collapsible) ──────────────────────────────────────
        ctk.CTkFrame(panel, fg_color="#2a2a2a", height=1).pack(fill="x", padx=12, pady=(12, 0))
        toggle_row = ctk.CTkFrame(panel, fg_color="transparent")
        toggle_row.pack(fill="x", padx=12, pady=(4, 0))
        self._how_to_arrow = ctk.CTkLabel(toggle_row, text="▶  📖  How to Use",
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          text_color=ACCENT, cursor="hand2")
        self._how_to_arrow.pack(side="left")
        self._how_to_arrow.bind("<Button-1>", lambda e: self._toggle_how_to())
        ctk.CTkLabel(toggle_row, text="(click to expand)",
                     font=ctk.CTkFont(size=10), text_color=TEXT_HINT).pack(side="left", padx=(8, 0))

        self._how_to_frame   = ctk.CTkFrame(panel, fg_color="#111111", corner_radius=8)
        self._toggle_row_ref = toggle_row

        for icon, title, body in HOW_TO_USE:
            sr = ctk.CTkFrame(self._how_to_frame, fg_color="transparent")
            sr.pack(fill="x", padx=10, pady=(8, 0))
            ctk.CTkLabel(sr, text=icon, font=ctk.CTkFont(size=14), width=28
                         ).pack(side="left", anchor="n", pady=(2, 0))
            txt = ctk.CTkFrame(sr, fg_color="transparent")
            txt.pack(side="left", fill="x", expand=True, padx=(4, 0))
            ctk.CTkLabel(txt, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=ACCENT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt, text=body, font=ctk.CTkFont(size=10),
                         text_color=TEXT_MAIN, anchor="w", justify="left",
                         wraplength=210).pack(anchor="w")
        ctk.CTkLabel(self._how_to_frame, text="", height=8).pack()

        # ── STEP 1: AI PROVIDER ───────────────────────────────────────────
        section_title("🤖", "Step 1 — AI Provider")

        self.provider_var = ctk.StringVar(
            value=self.config_data.get("provider", list(PROVIDERS.keys())[0])
        )
        ctk.CTkOptionMenu(
            panel, values=list(PROVIDERS.keys()),
            variable=self.provider_var,
            fg_color=BG_INPUT, button_color="#333333",
            button_hover_color=ACCENT, dropdown_fg_color=BG_CARD,
            text_color=TEXT_MAIN, font=ctk.CTkFont(size=11),
            command=self._on_provider_change,
        ).pack(fill="x", padx=12, pady=(4, 0))

        # Provider note (changes dynamically)
        self._provider_note_label = ctk.CTkLabel(
            panel, text="",
            font=ctk.CTkFont(size=10), text_color=SUCCESS,
            wraplength=250, justify="left",
        )
        self._provider_note_label.pack(anchor="w", padx=14, pady=(2, 0))
        self._refresh_provider_note()

        # ── STEP 2: API KEY ───────────────────────────────────────────────
        section_title("🔑", "Step 2 — API Key")

        # Key hint label (updates per provider)
        self._key_hint_label = ctk.CTkLabel(
            panel, text="",
            font=ctk.CTkFont(size=10), text_color=TEXT_HINT,
        )
        self._key_hint_label.pack(anchor="w", padx=14, pady=(2, 0))

        self.api_key_entry = ctk.CTkEntry(
            panel, show="•", placeholder_text="Paste your API key here...",
            fg_color=BG_INPUT, border_color="#333333",
            border_width=1, height=34, font=ctk.CTkFont(size=12),
        )
        self.api_key_entry.pack(fill="x", padx=12, pady=(4, 0))

        btn_row = ctk.CTkFrame(panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(4, 0))

        ctk.CTkButton(btn_row, text="Save Key", height=30, width=100,
                      fg_color=ACCENT, hover_color=ACCENT2,
                      text_color="white", font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._save_api_key).pack(side="left")

        self._get_key_btn = ctk.CTkButton(
            btn_row, text="Get free key →", height=30,
            fg_color="transparent", hover_color="#1e1e1e",
            text_color=ACCENT, font=ctk.CTkFont(size=11), border_width=0,
            command=self._open_key_url,
        )
        self._get_key_btn.pack(side="left", padx=(8, 0))

        self._refresh_key_hint()

        # ── STEP 3: AI MODEL ──────────────────────────────────────────────
        section_title("🧠", "Step 3 — AI Model")

        # Model dropdown (values change per provider)
        provider_cfg = PROVIDERS[self.provider_var.get()]
        saved_model  = self.config_data.get("model", provider_cfg["default_model"])
        # Find display label for saved model id
        model_id_to_display = {v: k for k, v in provider_cfg["model_ids"].items()}
        display_val = model_id_to_display.get(saved_model, provider_cfg["models"][0])

        self.model_var = ctk.StringVar(value=display_val)
        self._model_menu = ctk.CTkOptionMenu(
            panel, values=provider_cfg["models"],
            variable=self.model_var,
            fg_color=BG_INPUT, button_color="#333333",
            button_hover_color=ACCENT, dropdown_fg_color=BG_CARD,
            text_color=TEXT_MAIN, font=ctk.CTkFont(size=11),
            command=lambda _: self._save_settings(),
        )
        self._model_menu.pack(fill="x", padx=12, pady=(4, 0))

        ctk.CTkLabel(panel, text="Custom model ID (advanced)",
                     font=ctk.CTkFont(size=10), text_color=TEXT_HINT
                     ).pack(anchor="w", padx=12, pady=(8, 0))
        self.model_custom_entry = ctk.CTkEntry(
            panel, placeholder_text="Leave blank to use selection above",
            fg_color=BG_INPUT, border_color="#333333",
            border_width=1, height=30, font=ctk.CTkFont(size=10),
        )
        # Populate custom field if the saved model isn't in the current provider's list
        all_known = set(provider_cfg["model_ids"].values())
        if saved_model not in all_known:
            self.model_custom_entry.insert(0, saved_model)
        self.model_custom_entry.pack(fill="x", padx=12, pady=(2, 0))

        # ── STEP 4: QUIZ WEBSITE ──────────────────────────────────────────
        section_title("🌐", "Step 4 — Quiz Website")

        self.site_var = ctk.StringVar(
            value=self.config_data.get("site_profile", "Custom")
        )
        ctk.CTkOptionMenu(
            panel, values=list(SITE_PROFILES.keys()),
            variable=self.site_var,
            fg_color=BG_INPUT, button_color="#333333",
            button_hover_color=ACCENT, dropdown_fg_color=BG_CARD,
            text_color=TEXT_MAIN, font=ctk.CTkFont(size=12),
            command=self._on_site_change,
        ).pack(fill="x", padx=12, pady=(4, 0))
        hint("Quizalize & Quipper use optimised timings (locked).")
        hint("Custom lets you tweak the timing sliders below.")

        # ── ADVANCED SETTINGS ─────────────────────────────────────────────
        section_title("⚙️", "Advanced Settings")

        # Timing sliders — lockable
        self._timing_slider_row(
            panel,
            label="⏩  After Submit Wait",
            config_key="wait_after_submit",
            from_=0.5, to=8.0,
            hint_text=(
                "Seconds to wait after clicking the answer before the bot "
                "searches for the Submit / Next button. Increase if the bot "
                "clicks too fast."
            ),
        )
        self._timing_slider_row(
            panel,
            label="⏭  Next Question Wait",
            config_key="wait_for_next_button",
            from_=1.0, to=15.0,
            hint_text=(
                "Seconds to wait after submitting before the bot searches for "
                "the Next Question button. Increase if the next question loads slowly."
            ),
        )

        # Non-lockable sliders
        self._free_slider_row(
            panel, "Image Quality",
            "image_quality", 30, 95, integer=True,
            hint_text="Higher = AI reads answers more accurately (uses more data)",
        )
        self._free_slider_row(
            panel, "AI Response Length (tokens)",
            "max_tokens", 200, 2000, integer=True,
            hint_text="Increase if answers appear cut off",
        )

        ctk.CTkLabel(panel, text="", height=12).pack()

    # -----------------------------------------------------------------------
    # Provider helpers
    # -----------------------------------------------------------------------

    def _current_provider_cfg(self) -> dict:
        return PROVIDERS.get(self.provider_var.get(), list(PROVIDERS.values())[0])

    def _refresh_provider_note(self):
        pcfg = self._current_provider_cfg()
        self._provider_note_label.configure(text=pcfg.get("key_note", ""))

    def _refresh_key_hint(self):
        pcfg = self._current_provider_cfg()
        self._key_hint_label.configure(text=pcfg.get("key_hint", ""))

    def _open_key_url(self):
        pcfg = self._current_provider_cfg()
        webbrowser.open(pcfg.get("key_url", "https://openrouter.ai/keys"))

    def _on_provider_change(self, value: str):
        """Called when user picks a different provider."""
        self.config_data["provider"] = value
        pcfg = PROVIDERS[value]

        # Update provider note + key hint
        self._refresh_provider_note()
        self._refresh_key_hint()

        # Swap model dropdown options
        self._model_menu.configure(values=pcfg["models"])
        self.model_var.set(pcfg["models"][0])

        # Clear custom model field
        self.model_custom_entry.delete(0, "end")

        # Load saved key for this provider (if any)
        load_dotenv(app_path(".env"), override=True)
        key = os.getenv(pcfg["key_env"], "")
        self.api_key_entry.delete(0, "end")
        if key:
            self.api_key_entry.insert(0, key)

        self._save_settings()

    # -----------------------------------------------------------------------
    # How To expand/collapse
    # -----------------------------------------------------------------------

    def _toggle_how_to(self):
        self._how_to_expanded = not self._how_to_expanded
        if self._how_to_expanded:
            self._how_to_frame.pack(fill="x", padx=12, pady=(4, 0),
                                    after=self._toggle_row_ref)
            self._how_to_arrow.configure(text="▼  📖  How to Use")
        else:
            self._how_to_frame.pack_forget()
            self._how_to_arrow.configure(text="▶  📖  How to Use")

    # -----------------------------------------------------------------------
    # Slider builders
    # -----------------------------------------------------------------------

    def _timing_slider_row(self, parent, label, config_key, from_, to, hint_text=None):
        """Slider that can be locked by preset site profiles."""
        init_val = self.config_data.get(config_key, (from_ + to) / 2)
        var = ctk.DoubleVar(value=float(init_val))
        setattr(self, f"_var_{config_key}", var)

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(row, text=label,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MAIN).pack(side="left")

        lock_lbl = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=10),
                                text_color=TEXT_DIM, width=65)
        lock_lbl.pack(side="right")
        self._timing_lock_labels[config_key] = lock_lbl

        val_lbl = ctk.CTkLabel(row, text=f"{float(init_val):.1f}s",
                               font=ctk.CTkFont(family="Courier New", size=11),
                               text_color=ACCENT, width=46)
        val_lbl.pack(side="right")
        self._timing_val_labels[config_key] = val_lbl

        def on_change(val):
            v = round(float(val), 1)
            val_lbl.configure(text=f"{v:.1f}s")
            var.set(v)
            self._save_settings()

        slider = ctk.CTkSlider(parent, from_=from_, to=to, variable=var,
                               progress_color=ACCENT, button_color=ACCENT,
                               button_hover_color=ACCENT2, command=on_change)
        slider.pack(fill="x", padx=12, pady=(2, 0))
        self._timing_sliders[config_key] = slider

        if hint_text:
            ctk.CTkLabel(parent, text=hint_text, font=ctk.CTkFont(size=10),
                         text_color=TEXT_HINT, wraplength=248,
                         justify="left").pack(anchor="w", padx=14, pady=(2, 0))

    def _free_slider_row(self, parent, label, config_key,
                         from_, to, integer=False, hint_text=None):
        """Always-editable slider."""
        init_val = self.config_data.get(config_key, (from_ + to) / 2)
        var = ctk.IntVar(value=int(init_val)) if integer else ctk.DoubleVar(value=float(init_val))
        setattr(self, f"_var_{config_key}", var)

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(row, text=label,
                     font=ctk.CTkFont(size=11), text_color=TEXT_MAIN).pack(side="left")

        disp = str(int(init_val)) if integer else f"{float(init_val):.1f}"
        val_lbl = ctk.CTkLabel(row, text=disp,
                               font=ctk.CTkFont(family="Courier New", size=11),
                               text_color=ACCENT, width=42)
        val_lbl.pack(side="right")

        def on_change(val):
            v = int(float(val)) if integer else round(float(val), 1)
            val_lbl.configure(text=str(v))
            var.set(v)
            self._save_settings()

        ctk.CTkSlider(parent, from_=from_, to=to, variable=var,
                      progress_color=ACCENT, button_color=ACCENT,
                      button_hover_color=ACCENT2, command=on_change
                      ).pack(fill="x", padx=12, pady=(2, 0))

        if hint_text:
            ctk.CTkLabel(parent, text=hint_text, font=ctk.CTkFont(size=10),
                         text_color=TEXT_HINT, wraplength=248,
                         justify="left").pack(anchor="w", padx=14, pady=(2, 0))

    # -----------------------------------------------------------------------
    # Timing slider lock / unlock
    # -----------------------------------------------------------------------

    def _update_timing_lock(self, profile_name: str):
        locked  = profile_name in TIMING_LOCKED_PROFILES
        profile = SITE_PROFILES.get(profile_name, {})

        for key, slider in self._timing_sliders.items():
            val_lbl  = self._timing_val_labels.get(key)
            lock_lbl = self._timing_lock_labels.get(key)
            var      = getattr(self, f"_var_{key}", None)

            if locked:
                baked = profile.get(key)
                if baked is not None and var:
                    var.set(float(baked))
                    if val_lbl:
                        val_lbl.configure(text=f"{float(baked):.1f}s", text_color=TEXT_DIM)
                slider.configure(state="disabled",
                                 progress_color=LOCKED_C,
                                 button_color=LOCKED_C,
                                 button_hover_color=LOCKED_C)
                if lock_lbl:
                    lock_lbl.configure(text="🔒 locked", text_color=TEXT_HINT)
            else:
                slider.configure(state="normal",
                                 progress_color=ACCENT,
                                 button_color=ACCENT,
                                 button_hover_color=ACCENT2)
                cur = var.get() if var else 0
                if val_lbl:
                    val_lbl.configure(text=f"{float(cur):.1f}s", text_color=ACCENT)
                if lock_lbl:
                    lock_lbl.configure(text="")

    # -----------------------------------------------------------------------
    # Log panel
    # -----------------------------------------------------------------------

    def _build_log_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        panel.grid(row=0, column=1, sticky="nsew")

        hrow = ctk.CTkFrame(panel, fg_color="transparent")
        hrow.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(hrow, text="Activity Log",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkButton(hrow, text="Clear", height=22, width=50,
                      fg_color="transparent", hover_color="#1e1e1e",
                      text_color=TEXT_DIM, font=ctk.CTkFont(size=10),
                      command=self._clear_log).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            panel, fg_color=BG_INPUT, text_color="#d4d4d4",
            font=ctk.CTkFont(family="Courier New", size=11),
            border_width=0, wrap="word", state="disabled",
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.log_box.tag_config("error",     foreground=DANGER)
        self.log_box.tag_config("fix",       foreground=WARNING)
        self.log_box.tag_config("success",   foreground=SUCCESS)
        self.log_box.tag_config("dim",       foreground=TEXT_DIM)
        self.log_box.tag_config("accent",    foreground=ACCENT)
        self.log_box.tag_config("answer",    foreground="#a78bfa")   # purple
        self.log_box.tag_config("separator", foreground="#2a2a2a")

        # Error banner (hidden until needed)
        self.error_banner = ctk.CTkFrame(panel, fg_color="#1f0f0f", corner_radius=6)
        self.error_title  = ctk.CTkLabel(self.error_banner, text="",
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         text_color=DANGER, anchor="w",
                                         justify="left", wraplength=480)
        self.error_title.pack(fill="x", padx=12, pady=(8, 2))
        self.error_fix = ctk.CTkLabel(self.error_banner, text="",
                                      font=ctk.CTkFont(size=11), text_color=WARNING,
                                      anchor="w", justify="left", wraplength=480)
        self.error_fix.pack(fill="x", padx=12, pady=(0, 8))

    # -----------------------------------------------------------------------
    # Bottom controls
    # -----------------------------------------------------------------------

    def _build_controls(self):
        bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=62)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.start_btn = ctk.CTkButton(
            bar, text="▶   START  [F9]",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT2,
            text_color="white", height=40, width=200,
            corner_radius=8, command=self._start_bot,
        )
        self.start_btn.pack(side="left", padx=16, pady=11)

        self.stop_btn = ctk.CTkButton(
            bar, text="■   STOP  [ESC]",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2a2a2a", hover_color=DANGER,
            text_color=TEXT_DIM, height=40, width=200,
            corner_radius=8, command=self._stop_bot, state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 16), pady=11)

        ctk.CTkLabel(bar,
                     text="1. Open your quiz in the browser\n2. Come back here and press START",
                     font=ctk.CTkFont(size=10), text_color=TEXT_DIM,
                     justify="left").pack(side="left", padx=8)

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------

    def _start_bot(self):
        if self.is_running:
            return

        pcfg = self._current_provider_cfg()
        load_dotenv(app_path(".env"), override=True)
        key  = os.getenv(pcfg["key_env"], "").strip()
        if not key:
            self._log(f"❌ No API key saved for {pcfg['id'].title()} — enter your key and click Save Key", "error")
            return

        self._save_settings()
        config = get_active_config(self.config_data)
        self.is_running = True

        self._set_status("Running...", ACCENT)
        self.question_label.configure(text="")
        self.start_btn.configure(state="disabled", fg_color="#333333", text_color=TEXT_DIM)
        self.stop_btn.configure(state="normal", fg_color=DANGER,
                                hover_color="#c0392b", text_color="white")
        self._log("🚀 Starting bot...", "success")
        self._hide_error_banner()

        self.after(500, self.iconify)
        self._stop_overlay = StopOverlay(self, self._stop_bot)

        bot.start_bot(
            config,
            log_callback=self._log_threadsafe,
            on_stop_callback=self._on_bot_stopped,
            status_callback=self._on_question_answered,
        )

    def _stop_bot(self):
        bot.stop_bot()
        self._log_threadsafe("🛑 Stopping...")

    def _on_bot_stopped(self):
        self.is_running = False
        try:
            self.after(0, self._restore_after_stop)
        except Exception:
            pass

    def _restore_after_stop(self):
        if self._stop_overlay:
            try:
                self._stop_overlay.destroy()
            except Exception:
                pass
            self._stop_overlay = None
        self.deiconify()
        self.lift()
        self.focus_force()
        self._reset_ui()

    def _on_question_answered(self, count):
        try:
            self.after(0, lambda c=count: self.question_label.configure(
                text=f"✅ {c} question{'s' if c != 1 else ''} answered"
            ))
        except Exception:
            pass

    def _reset_ui(self):
        self._set_status("Ready", TEXT_DIM)
        self.start_btn.configure(state="normal", fg_color=ACCENT,
                                 hover_color=ACCENT2, text_color="white")
        self.stop_btn.configure(state="disabled", fg_color="#2a2a2a",
                                hover_color=DANGER, text_color=TEXT_DIM)

    def _set_status(self, text, color):
        self.status_label.configure(text=f"● {text}", text_color=color)

    def _on_site_change(self, value):
        self.config_data["site_profile"] = value
        self._update_timing_lock(value)
        self._save_settings()

    def _on_close(self):
        if self.is_running:
            bot.stop_bot()
        if self._stop_overlay:
            try:
                self._stop_overlay.destroy()
            except Exception:
                pass
        try:
            if hasattr(self, "_icon_tmp") and os.path.exists(self._icon_tmp):
                os.unlink(self._icon_tmp)
        except Exception:
            pass
        self.destroy()

    # -----------------------------------------------------------------------
    # API Key — load / save (per provider)
    # -----------------------------------------------------------------------

    def _save_api_key(self):
        key = self.api_key_entry.get().strip()
        if not key:
            self._log("⚠️ API key field is empty — nothing saved", "error")
            return
        pcfg     = self._current_provider_cfg()
        env_path = app_path(".env")
        if not os.path.exists(env_path):
            open(env_path, "w").close()
        set_key(env_path, pcfg["key_env"], key)
        load_dotenv(env_path, override=True)
        self._log(f"✅ {pcfg['id'].title()} API key saved!", "success")

    def _load_api_key(self):
        """Load the saved key for the currently selected provider."""
        load_dotenv(app_path(".env"), override=True)
        pcfg = self._current_provider_cfg()
        key  = os.getenv(pcfg["key_env"], "")
        self.api_key_entry.delete(0, "end")
        if key:
            self.api_key_entry.insert(0, key)

    # -----------------------------------------------------------------------
    # Settings persistence
    # -----------------------------------------------------------------------

    def _save_settings(self):
        pcfg   = self._current_provider_cfg()
        custom = self.model_custom_entry.get().strip()

        if custom:
            model = custom
        else:
            display = self.model_var.get()
            model   = pcfg["model_ids"].get(display, pcfg["default_model"])

        self.config_data["provider"]      = self.provider_var.get()
        self.config_data["model"]         = model
        self.config_data["site_profile"]  = self.site_var.get()

        # Timing sliders: only persist when in Custom mode
        if self.site_var.get() == "Custom":
            for key in ("wait_after_submit", "wait_for_next_button"):
                var = getattr(self, f"_var_{key}", None)
                if var:
                    self.config_data[key] = var.get()

        # Non-timing sliders always persist
        for key in ("image_quality", "max_tokens"):
            var = getattr(self, f"_var_{key}", None)
            if var:
                self.config_data[key] = var.get()

        save_config(self.config_data)

    # -----------------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------------

    def _log(self, message: str, tag: str = None):
        self.log_box.configure(state="normal")

        if tag is None:
            if "API_ERROR" in message or message.startswith("❌"):
                tag = "error"
            elif message.startswith("💡 FIX:"):
                tag = "fix"
            elif message.startswith("✅"):
                tag = "success"
            elif message.startswith("💡 Answer:"):
                tag = "answer"
            elif message.startswith("🚀") or message.startswith("🏁"):
                tag = "accent"
            elif message.startswith(("🛑", "⚠️", "⏩")):
                tag = "dim"

        # Show / update error banner
        if "API_ERROR" in message and tag == "error":
            self._last_error = message
            self._show_error_banner(message, None)
        elif message.startswith("💡 FIX:"):
            self._show_error_banner(self._last_error,
                                    message.replace("💡 FIX:", "").strip())

        if message.strip() == "🚀 Bot started!":
            self.log_box.insert("end", "─" * 48 + "\n", "separator")

        self.log_box.insert("end", message + "\n", tag or "")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _show_error_banner(self, error_msg, fix_msg):
        if not self._error_banner_visible:
            self.error_banner.pack(fill="x", padx=10, pady=(0, 8))
            self._error_banner_visible = True

        if error_msg:
            display = error_msg
            for prefix, label in [
                ("❌ API_ERROR:DAILY_LIMIT — ",    "Daily limit reached"),
                ("❌ API_ERROR:NO_CREDITS — ",     "Not enough credits"),
                ("❌ API_ERROR:NO_ENDPOINTS — ",   "Model unavailable"),
                ("❌ API_ERROR:BAD_MODEL — ",      "Model not found"),
                ("❌ API_ERROR:RATE_LIMIT — ",     "Too many requests"),
                ("❌ API_ERROR:NO_KEY — ",         "No API key"),
                ("❌ API_ERROR:BAD_KEY — ",        "Invalid API key"),
                ("❌ API_ERROR:TIMEOUT — ",        "Connection timed out"),
                ("❌ API_ERROR:NO_INTERNET — ",    "No internet connection"),
                ("❌ API_ERROR:EMPTY_RESPONSE — ", "Empty response"),
                ("❌ API_ERROR:UNKNOWN — ",        "Unknown error"),
            ]:
                if error_msg.startswith(prefix):
                    display = f"⚠  {label}:  {error_msg[len(prefix):]}"
                    break
            self.error_title.configure(text=display)

        self.error_fix.configure(
            text=f"→  How to fix:  {fix_msg}" if fix_msg else ""
        )

    def _hide_error_banner(self):
        if self._error_banner_visible:
            self.error_banner.pack_forget()
            self._error_banner_visible = False
        self._last_error = None

    def _log_threadsafe(self, message: str):
        try:
            self.after(0, lambda m=message: self._log(m))
        except Exception:
            pass

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._hide_error_banner()

    # -----------------------------------------------------------------------
    # Hotkeys
    # -----------------------------------------------------------------------

    def _setup_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey("F9",  self._start_bot)
            keyboard.add_hotkey("esc", self._stop_bot)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QuizSolverApp()
    app._setup_hotkeys()
    app.mainloop()