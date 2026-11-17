"""PC automation tools (Windows). Destructive actions are gated."""
import subprocess
import shutil

_BLOCKED_CONFIRM = {"shutdown", "restart", "logoff"}

_APP_ALIASES = {
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "browser": "start msedge",
    "edge": "start msedge",
    "chrome": "start chrome",
    "spotify": "start spotify:",
    "terminal": "wt",
    "settings": "start ms-settings:",
}


def open_app(name: str) -> str:
    key = name.strip().lower()
    cmd = _APP_ALIASES.get(key, name)
    try:
        subprocess.Popen(cmd, shell=True)
        return f"Opened {name}."
    except Exception as e:
        return f"Could not open {name}: {e}"


def set_volume(action: str) -> str:
    """action: up | down | mute"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        volume = cast(devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                      POINTER(IAudioEndpointVolume))
        if action == "mute":
            volume.SetMute(1, None)
            return "Muted."
        cur = volume.GetMasterVolumeLevelScalar()
        delta = {"up": 0.1, "down": -0.1}.get(action, 0)
        volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, cur + delta)), None)
        return f"Volume {'up' if delta > 0 else 'down'}."
    except Exception:
        # Fallback: media keys via pyautogui
        try:
            import pyautogui
            pyautogui.press({"up": "volumeup", "down": "volumedown", "mute": "volumemute"}[action])
            return f"Volume {action}."
        except Exception as e:
            return f"Volume control unavailable: {e}"


def system_power(action: str, confirmed: bool = False) -> str:
    if action in _BLOCKED_CONFIRM and not confirmed:
        return f"CONFIRM_REQUIRED: {action} the PC? Ask the user to confirm."
    cmds = {"shutdown": "shutdown /s /t 5", "restart": "shutdown /r /t 5", "logoff": "shutdown /l"}
    subprocess.Popen(cmds[action], shell=True)
    return f"{action.capitalize()} initiated."


def screenshot(path: str = "data/screenshot.png") -> str:
    try:
        import pyautogui
        pyautogui.screenshot(path)
        return f"Screenshot saved to {path}."
    except Exception as e:
        return f"Screenshot failed: {e}"


def media_control(action: str) -> str:
    """action: playpause | next | previous | stop"""
    keys = {"playpause": "playpause", "next": "nexttrack", "previous": "prevtrack", "stop": "stop"}
    key = keys.get(action.replace(" ", "").lower())
    if not key:
        return "Unknown media action. Use: playpause, next, previous, stop."
    try:
        import pyautogui
        pyautogui.press(key)
        return f"Media: {action}."
    except Exception as e:
        return f"Media control failed: {e}"


def youtube_play(query: str) -> str:
    import webbrowser, urllib.parse
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"Opened YouTube for '{query}'. Tap the top result to play."


def system_stats() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        return f"CPU {cpu}%, RAM {ram.percent}% ({ram.used // 2**20} MB used of {ram.total // 2**20} MB)."
    except Exception:
        return "System stats unavailable (psutil not installed)."
