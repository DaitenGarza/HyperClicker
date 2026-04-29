# HyperClicker

A lightweight, open-source rapid-fire macro tool for Windows. Hold any key or mouse button and it fires at up to **100 clicks per second** instead of registering as a normal hold.

Unlike basic auto-clickers that only spam left click, HyperClicker works with **any keyboard key or mouse button** — and you can bind multiple at the same time.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Any Key or Mouse Button** — Bind keyboard keys (Shift, Space, letters, F-keys, etc.) and mouse buttons (Left, Right, Middle)
- **Multiple Simultaneous Binds** — Hold Left Shift and Left Click at the same time, both rapid-fire independently
- **Adjustable Speed** — Slider from 1 to 100 CPS (clicks per second)
- **Global Toggle Hotkey** — Press F6 (or any key you set) to turn the macro ON/OFF from anywhere
- **Dark Themed UI** — Clean, modern interface
- **Persistent Settings** — Your binds, CPS, and hotkey are saved automatically
- **No Feedback Loops** — Filters its own simulated input so it won't trigger itself
- **High-Precision Timing** — Uses Windows timer APIs and busy-wait for accurate CPS at high speeds

---

## Screenshot

```
┌──────────────────────────────────┐
│  HYPERCLICKER              [OFF] │
│                                  │
│              ●                   │
│      Press F6 to activate        │
│                                  │
│  Toggle Hotkey    [F6]  [Change] │
│                                  │
│  Click Speed             99 CPS  │
│  ═══════════════════════●        │
│                                  │
│  Rapid-Fire Keys                 │
│  ┌──────────────────────────┐    │
│  │ KB  Left Shift        [X]│    │
│  │ MS  Left Click        [X]│    │
│  └──────────────────────────┘    │
│                                  │
│  [+ Add Key]    [+ Add Mouse]    │
│                                  │
│  ┌──────────────────────────┐    │
│  │        ACTIVATE          │    │
│  └──────────────────────────┘    │
└──────────────────────────────────┘
```

---

## Download

### Option 1: Just Run It (no Python needed)

1. Go to the [**Releases**](https://github.com/DaitenGarza/HyperClicker/releases) page
2. Download **HyperClicker.exe**
3. Double-click to run

No install. No Python. No terminal. Just works.

> Windows Defender may flag it since it's unsigned — click **"More info" > "Run anyway"**.

### Option 2: Run From Source

If you have Python installed and want to modify the code:

```bash
git clone https://github.com/DaitenGarza/HyperClicker.git
cd HyperClicker
pip install -r requirements.txt
python hyperclicker.py
```

---

## Usage

| Action | How |
|---|---|
| Turn macro ON/OFF | Press **F6** (or your custom hotkey), or click the **ACTIVATE** button |
| Add a keyboard key | Click **+ Add Key**, then press the key you want |
| Add a mouse button | Click **+ Add Mouse**, then select Left/Right/Middle |
| Remove a bind | Click the red **X** next to the key |
| Change toggle hotkey | Click **Change** next to the hotkey display, then press a new key |
| Adjust speed | Drag the **CPS slider** (1–100) |

### How It Works

1. Set your toggle hotkey (default: F6)
2. Add the keys/mouse buttons you want to rapid-fire
3. Press your toggle hotkey to turn ON
4. Hold any bound key — it fires at your set CPS instead of holding
5. Release the key to stop
6. Press toggle hotkey again to turn OFF

Multiple keys work independently — you can hold Shift and Left Click at the same time and both will rapid-fire.

---

## Configuration

Settings are saved automatically to `settings.json` in the same directory:

```json
{
  "cps": 99,
  "toggle_key": "Key.f6",
  "monitored": {
    "Key.shift": "Left Shift",
    "Button.left": "Left Click"
  }
}
```

---

## Use Cases

- **Gaming** — Rapid-fire attacks, fast building, ability spam
- **Stress Testing** — Simulate rapid input for UI testing
- **Accessibility** — Reduce strain from repetitive key pressing
- **Automation** — Quick repetitive input tasks

---

## Technical Details

- Uses **low-level input hooks** via `pynput` to detect real key presses
- Simulates input with `pynput` controllers (backed by Win32 `SendInput`)
- **Thread-safe counters** filter out simulated events from the listener to prevent feedback loops
- **High-precision timing** via `timeBeginPeriod(1)` + busy-wait tail for accurate CPS
- Each bound key gets its own firing thread for true simultaneous rapid-fire

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

## Disclaimer

This tool is provided for educational and legitimate use cases. Use responsibly and in accordance with the terms of service of any software you use it with. The author is not responsible for misuse.
