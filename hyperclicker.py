"""
HyperClicker v1.1 - Rapid-Fire Macro Tool
==========================================
Hold any bound key or mouse button and it fires at ultra-high speed
instead of registering as a normal hold.

v1.1 - Uses raw Win32 SendInput with hardware scan codes so input
       is recognized by games and applications (not just browsers).

Setup:  pip install pynput
Run:    python hyperclicker.py
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
import os
import sys
import atexit
import ctypes
import ctypes.wintypes as wt

# ── Dependency check ──────────────────────────────────────────────
try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, KeyCode
    from pynput.mouse import Button
except ImportError:
    _r = tk.Tk(); _r.withdraw()
    messagebox.showerror("Missing Dependency",
                         "pynput is required.\n\nRun:  pip install pynput")
    sys.exit(1)

# ── Windows timer precision ──────────────────────────────────────
try:
    ctypes.windll.winmm.timeBeginPeriod(1)
    atexit.register(ctypes.windll.winmm.timeEndPeriod, 1)
except Exception:
    pass

# ── Paths & constants ────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")


# ═════════════════════════════════════════════════════════════════
#  WIN32 SENDINPUT  (raw hardware-level simulation)
#  This is what makes input work in games / real applications.
#  pynput's Controller sends high-level messages that apps ignore.
#  SendInput with scan codes looks like real keyboard hardware.
# ═════════════════════════════════════════════════════════════════

INPUT_KEYBOARD = 1
INPUT_MOUSE    = 0

KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         wt.WORD),
        ("wScan",       wt.WORD),
        ("dwFlags",     wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          wt.LONG),
        ("dy",          wt.LONG),
        ("mouseData",   wt.DWORD),
        ("dwFlags",     wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg",    wt.DWORD),
        ("wParamL", wt.WORD),
        ("wParamH", wt.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("union", _INPUT_UNION)]


user32 = ctypes.windll.user32
user32.SendInput.argtypes  = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype   = wt.UINT
user32.MapVirtualKeyW.argtypes = [wt.UINT, wt.UINT]
user32.MapVirtualKeyW.restype  = wt.UINT

# Keys that need the EXTENDED flag (arrows, nav, etc.)
EXTENDED_VKS = {
    0x21, 0x22, 0x23, 0x24,        # PgUp PgDn End Home
    0x25, 0x26, 0x27, 0x28,        # Arrow keys
    0x2D, 0x2E,                    # Insert Delete
    0x5B, 0x5C, 0x5D,              # Win keys, Menu
    0x6F,                          # Numpad /
    0x90, 0x91,                    # NumLock ScrollLock
    0x2C,                          # PrintScreen
}

# pynput Key name  →  Windows Virtual-Key code
KEY_NAME_TO_VK = {
    "shift": 0xA0, "shift_l": 0xA0, "shift_r": 0xA1,
    "ctrl":  0xA2, "ctrl_l":  0xA2, "ctrl_r":  0xA3,
    "alt":   0xA4, "alt_l":   0xA4, "alt_r":   0xA5, "alt_gr": 0xA5,
    "space": 0x20, "tab": 0x09, "enter": 0x0D,
    "backspace": 0x08, "delete": 0x2E,
    "esc": 0x1B, "caps_lock": 0x14,
    "home": 0x24, "end": 0x23,
    "page_up": 0x21, "page_down": 0x22,
    "insert": 0x2D,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "f13": 0x7C, "f14": 0x7D, "f15": 0x7E, "f16": 0x7F,
    "num_lock": 0x90, "scroll_lock": 0x91,
    "print_screen": 0x2C, "pause": 0x13,
    "cmd": 0x5B, "cmd_l": 0x5B, "cmd_r": 0x5C,
    "menu": 0x5D,
}

MOUSE_FLAGS = {
    "left":   (MOUSEEVENTF_LEFTDOWN,   MOUSEEVENTF_LEFTUP),
    "right":  (MOUSEEVENTF_RIGHTDOWN,  MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


def id_to_vk(key_id):
    """Convert a key ID string to a Windows VK code."""
    if key_id.startswith("Key."):
        return KEY_NAME_TO_VK.get(key_id[4:])
    if key_id.startswith("vk_"):
        return int(key_id[3:])
    if key_id.startswith("char_"):
        ch = key_id[5:]
        # VkKeyScanW returns VK in the low byte
        result = user32.VkKeyScanW(ord(ch))
        if result != -1:
            return result & 0xFF
    return None


def send_key_event(vk, down=True):
    """Send a keyboard event via SendInput with hardware scan codes."""
    scan = user32.MapVirtualKeyW(vk, 0)   # MAPVK_VK_TO_VSC

    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk   = vk               # VK  for high-level apps
    inp.union.ki.wScan = scan              # scan code for DirectInput / games
    inp.union.ki.dwFlags = 0 if down else KEYEVENTF_KEYUP
    if vk in EXTENDED_VKS:
        inp.union.ki.dwFlags |= KEYEVENTF_EXTENDEDKEY
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.c_void_p(0)

    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_event(button_name, down=True):
    """Send a mouse button event via SendInput."""
    flags = MOUSE_FLAGS.get(button_name)
    if not flags:
        return

    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flags[0] if down else flags[1]
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.c_void_p(0)

    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


# ═════════════════════════════════════════════════════════════════
#  COLORS  (Catppuccin Mocha)
# ═════════════════════════════════════════════════════════════════
BG       = "#1e1e2e"
BG_CARD  = "#313244"
BG_BTN   = "#45475a"
FG       = "#cdd6f4"
FG_DIM   = "#6c7086"
ACCENT   = "#89b4fa"
GREEN    = "#a6e3a1"
RED      = "#f38ba8"
YELLOW   = "#f9e2af"


# ═════════════════════════════════════════════════════════════════
#  KEY DISPLAY NAMES & UTILITIES
# ═════════════════════════════════════════════════════════════════

SPECIAL_KEY_NAMES = {
    Key.shift: "Left Shift", Key.shift_l: "Left Shift", Key.shift_r: "Right Shift",
    Key.ctrl_l: "Left Ctrl", Key.ctrl_r: "Right Ctrl",
    Key.alt_l: "Left Alt", Key.alt_r: "Right Alt", Key.alt_gr: "Alt Gr",
    Key.space: "Space", Key.tab: "Tab", Key.enter: "Enter",
    Key.backspace: "Backspace", Key.delete: "Delete",
    Key.esc: "Escape", Key.caps_lock: "Caps Lock",
    Key.home: "Home", Key.end: "End",
    Key.page_up: "Page Up", Key.page_down: "Page Down",
    Key.insert: "Insert",
    Key.up: "Up Arrow", Key.down: "Down Arrow",
    Key.left: "Left Arrow", Key.right: "Right Arrow",
    Key.f1: "F1", Key.f2: "F2", Key.f3: "F3", Key.f4: "F4",
    Key.f5: "F5", Key.f6: "F6", Key.f7: "F7", Key.f8: "F8",
    Key.f9: "F9", Key.f10: "F10", Key.f11: "F11", Key.f12: "F12",
    Key.num_lock: "Num Lock", Key.scroll_lock: "Scroll Lock",
    Key.print_screen: "Print Screen", Key.pause: "Pause",
    Key.cmd: "Windows", Key.cmd_l: "Left Win", Key.cmd_r: "Right Win",
    Key.menu: "Menu",
}

MOUSE_DISPLAY = {
    "Button.left":   "Left Click",
    "Button.right":  "Right Click",
    "Button.middle": "Middle Click",
}


def key_to_id(key):
    """Stable string ID for any pynput key."""
    if isinstance(key, Key):
        return f"Key.{key.name}"
    if isinstance(key, KeyCode):
        if key.vk is not None:
            return f"vk_{key.vk}"
        if key.char is not None:
            return f"char_{key.char}"
    return str(key)


def key_to_display(key):
    """Human-readable name for a pynput key object."""
    if isinstance(key, Key):
        return SPECIAL_KEY_NAMES.get(key, key.name.replace("_", " ").title())
    if isinstance(key, KeyCode):
        if key.char is not None:
            return key.char.upper()
        if key.vk is not None:
            if 0x30 <= key.vk <= 0x39:
                return chr(key.vk)
            if 0x41 <= key.vk <= 0x5A:
                return chr(key.vk)
            return f"Key {key.vk}"
    return str(key)


def id_to_display(key_id):
    """Human-readable name from a key ID string."""
    if key_id in MOUSE_DISPLAY:
        return MOUSE_DISPLAY[key_id]
    if key_id.startswith("Key."):
        name = key_id[4:]
        try:
            return SPECIAL_KEY_NAMES.get(Key[name], name.replace("_", " ").title())
        except KeyError:
            return name.replace("_", " ").title()
    if key_id.startswith("char_"):
        return key_id[5:].upper()
    if key_id.startswith("vk_"):
        vk = int(key_id[3:])
        if 0x30 <= vk <= 0x39:
            return chr(vk)
        if 0x41 <= vk <= 0x5A:
            return chr(vk)
        return f"Key {vk}"
    return key_id


# ── Precision timer ──────────────────────────────────────────────

def precise_sleep(seconds):
    """Sleep with sub-millisecond accuracy via busy-wait tail."""
    if seconds <= 0:
        return
    end = time.perf_counter() + seconds
    coarse = seconds - 0.002
    if coarse > 0:
        time.sleep(coarse)
    while time.perf_counter() < end:
        pass


# ═════════════════════════════════════════════════════════════════
#  MACRO ENGINE
# ═════════════════════════════════════════════════════════════════

class MacroEngine:
    """
    Core engine.

    LISTENING  — pynput hooks (detects real user keypresses)
    SIMULATING — raw Win32 SendInput with scan codes (games see it)
    """

    def __init__(self):
        # Public state
        self.active = False
        self.cps = 99
        self.toggle_key_id = "Key.f6"
        self.monitored = {}          # {key_id: display_name}

        # Internal tracking
        self._held = set()           # keys the user is physically holding
        self._firing = {}            # {key_id: Thread}
        self._stop_events = {}       # {key_id: Event}

        # Counters to ignore our own simulated events in the listener
        self._sim_press = {}
        self._sim_release = {}
        self._lock = threading.Lock()

        # pynput listeners (for DETECTION only, not simulation)
        self._kb_listener = None
        self._mouse_listener = None

        # Key capture mode (for UI dialogs)
        self._capture_mode = False
        self._captured = None
        self._capture_event = threading.Event()

        # UI callback
        self.on_toggle = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._kb_listener.daemon = True
        self._mouse_listener.daemon = True
        self._kb_listener.start()
        self._mouse_listener.start()

    def stop(self):
        self._stop_all()
        if self._kb_listener:
            self._kb_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()

    # ── Toggle ───────────────────────────────────────────────────

    def toggle(self):
        self.active = not self.active
        if not self.active:
            self._stop_all()
        if self.on_toggle:
            self.on_toggle(self.active)

    # ── Capture (for UI dialogs) ─────────────────────────────────

    def capture_next_key(self):
        """Block until user presses a key. Returns (key_obj, key_id) or None."""
        self._capture_mode = True
        self._captured = None
        self._capture_event.clear()
        self._capture_event.wait(timeout=10)
        self._capture_mode = False
        return self._captured

    def cancel_capture(self):
        self._capture_mode = False
        self._capture_event.set()

    # ── Keyboard listener callbacks ──────────────────────────────

    def _on_key_press(self, key):
        key_id = key_to_id(key)

        # Capture mode intercepts everything
        if self._capture_mode:
            self._captured = (key, key_id)
            self._capture_event.set()
            self._capture_mode = False
            return

        # Skip our own simulated presses
        with self._lock:
            if self._sim_press.get(key_id, 0) > 0:
                self._sim_press[key_id] -= 1
                return

        # Toggle hotkey (fire only on first press, not auto-repeat)
        if key_id == self.toggle_key_id:
            if key_id not in self._held:
                self._held.add(key_id)
                self.toggle()
            return

        # Ignore auto-repeat
        if key_id in self._held:
            return

        # New user press
        self._held.add(key_id)
        if key_id in self.monitored and self.active:
            self._start_firing(key_id)

    def _on_key_release(self, key):
        key_id = key_to_id(key)

        # Skip our own simulated releases
        with self._lock:
            if self._sim_release.get(key_id, 0) > 0:
                self._sim_release[key_id] -= 1
                return

        # Toggle key release
        if key_id == self.toggle_key_id:
            self._held.discard(key_id)
            return

        # Real user release
        self._held.discard(key_id)
        self._stop_firing(key_id)

    # ── Mouse listener callback ──────────────────────────────────

    def _on_mouse_click(self, x, y, button, pressed):
        key_id = f"Button.{button.name}"

        if pressed:
            with self._lock:
                if self._sim_press.get(key_id, 0) > 0:
                    self._sim_press[key_id] -= 1
                    return

            if key_id in self._held:
                return

            self._held.add(key_id)
            if key_id in self.monitored and self.active:
                self._start_firing(key_id)
        else:
            with self._lock:
                if self._sim_release.get(key_id, 0) > 0:
                    self._sim_release[key_id] -= 1
                    return

            self._held.discard(key_id)
            self._stop_firing(key_id)

    # ── Rapid-fire management ────────────────────────────────────

    def _start_firing(self, key_id):
        if key_id in self._firing:
            return
        stop = threading.Event()
        self._stop_events[key_id] = stop
        t = threading.Thread(target=self._fire_loop, args=(key_id, stop), daemon=True)
        self._firing[key_id] = t
        t.start()

    def _stop_firing(self, key_id):
        evt = self._stop_events.pop(key_id, None)
        if evt:
            evt.set()
        self._firing.pop(key_id, None)

    def _stop_all(self):
        for evt in self._stop_events.values():
            evt.set()
        self._stop_events.clear()
        self._firing.clear()
        self._held.clear()

    def _fire_loop(self, key_id, stop_event):
        """
        Rapid-fire loop using raw Win32 SendInput.
        Sends both VK code + hardware scan code so the input
        is recognized by regular apps AND DirectInput games.
        """
        is_mouse = key_id.startswith("Button.")

        if is_mouse:
            button_name = key_id[7:]   # "left" / "right" / "middle"
            if button_name not in MOUSE_FLAGS:
                return
        else:
            vk = id_to_vk(key_id)
            if vk is None:
                return

        while not stop_event.is_set() and self.active:
            interval = 1.0 / max(self.cps, 1)
            half = interval / 2

            # Tell pynput listener to skip the next simulated press + release
            with self._lock:
                self._sim_press[key_id]   = self._sim_press.get(key_id, 0) + 1
                self._sim_release[key_id] = self._sim_release.get(key_id, 0) + 1

            try:
                if is_mouse:
                    send_mouse_event(button_name, down=True)
                    precise_sleep(half)
                    send_mouse_event(button_name, down=False)
                else:
                    send_key_event(vk, down=True)
                    precise_sleep(half)
                    send_key_event(vk, down=False)
            except Exception:
                break

            precise_sleep(half)


# ═════════════════════════════════════════════════════════════════
#  GUI
# ═════════════════════════════════════════════════════════════════

class HyperClickerApp:
    """Dark-themed tkinter GUI for HyperClicker."""

    def __init__(self):
        self.engine = MacroEngine()
        self.engine.on_toggle = self._on_engine_toggle

        self.root = tk.Tk()
        self.root.title("HyperClicker")
        self.root.geometry("420x620")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Dark title bar (Windows 10/11)
        self._apply_dark_titlebar()

        self._build_ui()
        self._load_settings()
        self.engine.start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Dark title bar helper ────────────────────────────────────

    def _apply_dark_titlebar(self):
        try:
            self.root.update()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int))
        except Exception:
            pass

    # ── Build all widgets ────────────────────────────────────────

    def _build_ui(self):
        # ---- Title bar ----
        title_frame = tk.Frame(self.root, bg=BG)
        title_frame.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(
            title_frame, text="HYPERCLICKER",
            font=("Segoe UI", 24, "bold"), bg=BG, fg=FG,
        ).pack(side="left")

        self.status_badge = tk.Label(
            title_frame, text="  OFF  ",
            font=("Segoe UI", 11, "bold"), bg=BG_BTN, fg=FG_DIM,
        )
        self.status_badge.pack(side="right", pady=8)

        # ---- Status card ----
        card = tk.Frame(self.root, bg=BG_CARD)
        card.pack(fill="x", padx=20, pady=(12, 0))

        self.status_dot = tk.Label(
            card, text="●", font=("Segoe UI", 36), bg=BG_CARD, fg=FG_DIM,
        )
        self.status_dot.pack(pady=(12, 0))

        self.status_text = tk.Label(
            card, text="Press F6 to activate",
            font=("Segoe UI", 12), bg=BG_CARD, fg=FG_DIM,
        )
        self.status_text.pack(pady=(0, 12))

        # ---- Hotkey section ----
        hk_card = tk.Frame(self.root, bg=BG_CARD)
        hk_card.pack(fill="x", padx=20, pady=(8, 0))

        hk_row = tk.Frame(hk_card, bg=BG_CARD)
        hk_row.pack(fill="x", padx=12, pady=10)

        tk.Label(
            hk_row, text="Toggle Hotkey",
            font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=FG,
        ).pack(side="left")

        tk.Button(
            hk_row, text="Change", font=("Segoe UI", 10),
            bg=BG_BTN, fg=FG, relief="flat", cursor="hand2",
            activebackground=ACCENT, activeforeground=BG,
            command=self._change_hotkey,
        ).pack(side="right")

        self.hotkey_label = tk.Label(
            hk_row, text="F6", font=("Segoe UI", 13),
            bg=BG_BTN, fg=ACCENT, padx=14, pady=2,
        )
        self.hotkey_label.pack(side="right", padx=(0, 8))

        # ---- CPS section ----
        sp_card = tk.Frame(self.root, bg=BG_CARD)
        sp_card.pack(fill="x", padx=20, pady=(8, 0))

        sp_header = tk.Frame(sp_card, bg=BG_CARD)
        sp_header.pack(fill="x", padx=12, pady=(10, 2))

        tk.Label(
            sp_header, text="Click Speed",
            font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=FG,
        ).pack(side="left")

        self.cps_label = tk.Label(
            sp_header, text="99 CPS",
            font=("Segoe UI", 12), bg=BG_CARD, fg=ACCENT,
        )
        self.cps_label.pack(side="right")

        self.cps_var = tk.IntVar(value=99)
        self.cps_slider = tk.Scale(
            sp_card, from_=1, to=100, orient="horizontal",
            variable=self.cps_var, showvalue=False,
            bg=BG_CARD, fg=FG, troughcolor=BG_BTN,
            highlightthickness=0, sliderrelief="flat",
            activebackground=ACCENT, length=360,
            command=self._on_cps_change,
        )
        self.cps_slider.pack(padx=12, pady=(0, 10))

        # ---- Key list ----
        tk.Label(
            self.root, text="Rapid-Fire Keys",
            font=("Segoe UI", 12, "bold"), bg=BG, fg=FG,
        ).pack(anchor="w", padx=20, pady=(12, 4))

        self.keys_frame = tk.Frame(self.root, bg=BG_CARD)
        self.keys_frame.pack(fill="x", padx=20)

        # ---- Add buttons ----
        add_row = tk.Frame(self.root, bg=BG)
        add_row.pack(fill="x", padx=20, pady=(6, 0))

        tk.Button(
            add_row, text="+ Add Key", font=("Segoe UI", 11),
            bg=BG_BTN, fg=FG, relief="flat", cursor="hand2",
            activebackground=ACCENT, activeforeground=BG,
            command=self._add_key,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            add_row, text="+ Add Mouse", font=("Segoe UI", 11),
            bg=BG_BTN, fg=FG, relief="flat", cursor="hand2",
            activebackground=ACCENT, activeforeground=BG,
            command=self._add_mouse,
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ---- Activate button ----
        self.activate_btn = tk.Button(
            self.root, text="ACTIVATE",
            font=("Segoe UI", 16, "bold"), relief="flat",
            bg="#2d5a27", fg=GREEN, cursor="hand2",
            activebackground="#3a7a32", activeforeground=GREEN,
            command=self._toggle,
        )
        self.activate_btn.pack(fill="x", padx=20, pady=(14, 18), ipady=8)

    # ── Status updates ───────────────────────────────────────────

    def _on_engine_toggle(self, active):
        self.root.after(0, lambda: self._update_status(active))

    def _update_status(self, active):
        hk = id_to_display(self.engine.toggle_key_id)
        if active:
            self.status_badge.configure(text="  ON  ", bg=GREEN, fg=BG)
            self.status_dot.configure(fg=GREEN)
            self.status_text.configure(text=f"Press {hk} to deactivate", fg=GREEN)
            self.activate_btn.configure(
                text="DEACTIVATE", bg="#5a2727", fg=RED,
                activebackground="#7a3232", activeforeground=RED,
            )
        else:
            self.status_badge.configure(text="  OFF  ", bg=BG_BTN, fg=FG_DIM)
            self.status_dot.configure(fg=FG_DIM)
            self.status_text.configure(text=f"Press {hk} to activate", fg=FG_DIM)
            self.activate_btn.configure(
                text="ACTIVATE", bg="#2d5a27", fg=GREEN,
                activebackground="#3a7a32", activeforeground=GREEN,
            )

    def _toggle(self):
        self.engine.toggle()

    # ── CPS slider ───────────────────────────────────────────────

    def _on_cps_change(self, val):
        cps = int(val)
        self.engine.cps = cps
        self.cps_label.configure(text=f"{cps} CPS")

    # ── Key list ─────────────────────────────────────────────────

    def _refresh_keys(self):
        for w in self.keys_frame.winfo_children():
            w.destroy()

        if not self.engine.monitored:
            tk.Label(
                self.keys_frame, text="No keys bound yet",
                font=("Segoe UI", 11), bg=BG_CARD, fg=FG_DIM, pady=16,
            ).pack()
            return

        for key_id, display in self.engine.monitored.items():
            row = tk.Frame(self.keys_frame, bg=BG_CARD)
            row.pack(fill="x", padx=6, pady=2)

            is_mouse = key_id.startswith("Button.")
            badge = "MS" if is_mouse else "KB"
            badge_fg = YELLOW if is_mouse else ACCENT

            tk.Label(
                row, text=badge, font=("Segoe UI", 9, "bold"),
                bg=BG_BTN, fg=badge_fg, padx=6, pady=1,
            ).pack(side="left", padx=(4, 8), pady=4)

            tk.Label(
                row, text=display, font=("Segoe UI", 12),
                bg=BG_CARD, fg=FG,
            ).pack(side="left", pady=4)

            tk.Button(
                row, text="X", font=("Segoe UI", 10, "bold"),
                bg=BG_CARD, fg=RED, relief="flat", cursor="hand2",
                activebackground=RED, activeforeground=BG,
                command=lambda kid=key_id: self._remove_key(kid),
            ).pack(side="right", padx=4, pady=4)

    def _remove_key(self, key_id):
        self.engine.monitored.pop(key_id, None)
        self.engine._stop_firing(key_id)
        self._refresh_keys()
        self._save_settings()

    # ── Add key dialog ───────────────────────────────────────────

    def _add_key(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Key")
        dlg.geometry("300x130")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(
            dlg, text="Press any key...",
            font=("Segoe UI", 16), bg=BG, fg=FG,
        ).pack(expand=True)

        tk.Button(
            dlg, text="Cancel", font=("Segoe UI", 10),
            bg=BG_BTN, fg=FG, relief="flat",
            command=lambda: (self.engine.cancel_capture(), dlg.destroy()),
        ).pack(pady=(0, 12))

        dlg.protocol("WM_DELETE_WINDOW",
                     lambda: (self.engine.cancel_capture(), dlg.destroy()))

        def _capture():
            result = self.engine.capture_next_key()
            self.root.after(0, lambda: self._on_key_captured(result, dlg))

        threading.Thread(target=_capture, daemon=True).start()

    def _on_key_captured(self, result, dlg):
        try:
            dlg.destroy()
        except Exception:
            pass

        if result is None:
            return

        key_obj, key_id = result

        if key_id in self.engine.monitored:
            messagebox.showinfo("Info", "This key is already bound.")
            return
        if key_id == self.engine.toggle_key_id:
            messagebox.showwarning("Warning",
                                   "Cannot bind the toggle hotkey as a rapid-fire key.")
            return

        self.engine.monitored[key_id] = key_to_display(key_obj)
        self._refresh_keys()
        self._save_settings()

    # ── Add mouse dialog ─────────────────────────────────────────

    def _add_mouse(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Mouse Button")
        dlg.geometry("260x210")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(
            dlg, text="Select Button",
            font=("Segoe UI", 14, "bold"), bg=BG, fg=FG,
        ).pack(pady=(14, 8))

        for label, btn_id in [("Left Click", "Button.left"),
                               ("Right Click", "Button.right"),
                               ("Middle Click", "Button.middle")]:
            already = btn_id in self.engine.monitored
            tk.Button(
                dlg, text=label, font=("Segoe UI", 11),
                bg=BG_BTN, fg=FG if not already else FG_DIM,
                relief="flat", cursor="hand2",
                state="normal" if not already else "disabled",
                activebackground=ACCENT, activeforeground=BG,
                command=lambda b=btn_id, n=label, d=dlg: self._pick_mouse(b, n, d),
            ).pack(fill="x", padx=20, pady=3)

        tk.Button(
            dlg, text="Cancel", font=("Segoe UI", 10),
            bg=BG_BTN, fg=FG, relief="flat", command=dlg.destroy,
        ).pack(pady=(8, 12))

    def _pick_mouse(self, btn_id, name, dlg):
        dlg.destroy()
        self.engine.monitored[btn_id] = name
        self._refresh_keys()
        self._save_settings()

    # ── Change hotkey dialog ─────────────────────────────────────

    def _change_hotkey(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Change Hotkey")
        dlg.geometry("300x130")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(
            dlg, text="Press new toggle key...",
            font=("Segoe UI", 16), bg=BG, fg=FG,
        ).pack(expand=True)

        tk.Button(
            dlg, text="Cancel", font=("Segoe UI", 10),
            bg=BG_BTN, fg=FG, relief="flat",
            command=lambda: (self.engine.cancel_capture(), dlg.destroy()),
        ).pack(pady=(0, 12))

        dlg.protocol("WM_DELETE_WINDOW",
                     lambda: (self.engine.cancel_capture(), dlg.destroy()))

        def _capture():
            result = self.engine.capture_next_key()
            self.root.after(0, lambda: self._on_hotkey_captured(result, dlg))

        threading.Thread(target=_capture, daemon=True).start()

    def _on_hotkey_captured(self, result, dlg):
        try:
            dlg.destroy()
        except Exception:
            pass

        if result is None:
            return

        key_obj, key_id = result

        if key_id.startswith("Button."):
            messagebox.showwarning("Warning", "Toggle hotkey must be a keyboard key.")
            return

        # Remove from monitored list if it was there
        if key_id in self.engine.monitored:
            self.engine.monitored.pop(key_id)
            self._refresh_keys()

        self.engine.toggle_key_id = key_id
        self.hotkey_label.configure(text=key_to_display(key_obj))
        self._update_status(self.engine.active)
        self._save_settings()

    # ── Settings persistence ─────────────────────────────────────

    def _save_settings(self):
        data = {
            "cps": self.engine.cps,
            "toggle_key": self.engine.toggle_key_id,
            "monitored": self.engine.monitored,
        }
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_settings(self):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            self.engine.cps = data.get("cps", 99)
            self.engine.toggle_key_id = data.get("toggle_key", "Key.f6")
            self.engine.monitored = data.get("monitored", {})

            self.cps_var.set(self.engine.cps)
            self.cps_label.configure(text=f"{self.engine.cps} CPS")
            self.hotkey_label.configure(
                text=id_to_display(self.engine.toggle_key_id))
            self._refresh_keys()
            self._update_status(self.engine.active)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self._refresh_keys()

    # ── Cleanup ──────────────────────────────────────────────────

    def _on_close(self):
        self._save_settings()
        self.engine.stop()
        self.root.destroy()

    # ── Run ──────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ═════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = HyperClickerApp()
    app.run()
