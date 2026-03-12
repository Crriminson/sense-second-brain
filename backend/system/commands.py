"""
PC command execution layer.

The ONLY file that touches OS-level operations.
Every action is a pure function: name + params → result string.
Never throws — always returns a status string.

Called by pipeline:
  result = sys_commands.execute("open_app", {"target": "chrome"})

Platform: Windows-first (subprocess + ctypes), with safe fallbacks.
"""

import subprocess
import os
import platform
import time

_IS_WINDOWS = platform.system() == "Windows"


# ═══════════════════════════════════════════════════
#  MAIN DISPATCHER
# ═══════════════════════════════════════════════════

def execute(action: str, params: dict = None) -> str:
    """
    Execute a PC command. Never throws.
    Returns a human-readable status string.
    """
    if params is None:
        params = {}

    handler = _ACTION_MAP.get(action)
    if not handler:
        return f"Unknown action: {action}"

    try:
        return handler(params)
    except Exception as e:
        print(f"[CMD] Error executing {action}: {e}")
        return f"Failed: {e}"


def execute_pc_command(action: str, params: dict = None) -> str:
    """Backward-compatible alias used by older imports."""
    return execute(action, params)


# ═══════════════════════════════════════════════════
#  APP MANAGEMENT
# ═══════════════════════════════════════════════════

# Common app names → executable mappings (Windows)
_APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "brave": "brave",
    "edge": "msedge",
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "notepad": "notepad",
    "terminal": "wt" if _IS_WINDOWS else "x-terminal-emulator",
    "cmd": "cmd",
    "powershell": "powershell",
    "explorer": "explorer",
    "file explorer": "explorer",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "telegram": "telegram",
    "whatsapp": "whatsapp",
    "notion": "notion",
    "obsidian": "obsidian",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "calculator": "calc",
    "paint": "mspaint",
    "snipping tool": "snippingtool",
    "task manager": "taskmgr",
    "settings": "ms-settings:" if _IS_WINDOWS else "gnome-control-center",
}

# Process names for closing — different from launch names for some apps
_CLOSE_ALIASES = {
    "settings": "SystemSettings",
    "ms-settings:": "SystemSettings",
    "calculator": "Calculator",
    "calc": "Calculator",
    "photos": "Microsoft.Photos",
    "store": "WinStore.App",
    "mail": "HxOutlook",
    "calendar": "HxCalendarAppImm",
    "xbox": "XboxApp",
    "maps": "Maps",
    "weather": "Weather",
    "clock": "Time",
    "camera": "WindowsCamera",
    "snipping tool": "SnippingTool",
    "snippingtool": "SnippingTool",
}


def _open_app(params: dict) -> str:
    target = params.get("target", "").strip().lower()
    if not target:
        return "No app specified."

    # Resolve alias
    exe = _APP_ALIASES.get(target, target)

    if _IS_WINDOWS:
        # Try 'start' for Windows Store apps and executables
        try:
            subprocess.Popen(
                f'start "" "{exe}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Opened {target}."
        except Exception:
            pass

        # Fallback: try direct execution
        try:
            subprocess.Popen(
                [exe],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Opened {target}."
        except Exception as e:
            return f"Couldn't open {target}: {e}"
    else:
        # Linux / Mac
        try:
            subprocess.Popen(
                [exe],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Opened {target}."
        except Exception as e:
            return f"Couldn't open {target}: {e}"


def _close_app(params: dict) -> str:
    target = params.get("target", "").strip().lower()
    if not target:
        return "No app specified."

    # Check close-specific aliases first (UWP apps have different process names)
    exe = _CLOSE_ALIASES.get(target)
    if not exe:
        exe = _CLOSE_ALIASES.get(_APP_ALIASES.get(target, ""))
    if not exe:
        exe = _APP_ALIASES.get(target, target)

    if _IS_WINDOWS:
        try:
            # Try exact process name first
            result = subprocess.run(
                f'taskkill /IM "{exe}.exe" /F',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return f"Closed {target}."

            # If that failed, try matching window title
            result = subprocess.run(
                f'taskkill /FI "WINDOWTITLE eq {target}*" /F',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return f"Closed {target}."

            return f"Couldn't find {target} running."
        except Exception as e:
            return f"Couldn't close {target}: {e}"
    else:
        try:
            subprocess.run(["pkill", "-f", exe], capture_output=True, timeout=5)
            return f"Closed {target}."
        except Exception as e:
            return f"Couldn't close {target}: {e}"


# ═══════════════════════════════════════════════════
#  BROWSER / URL
# ═══════════════════════════════════════════════════

# Quick URL shortcuts
_URL_SHORTCUTS = {
    "youtube": "https://youtube.com",
    "github": "https://github.com",
    "google": "https://google.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "reddit": "https://reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "linkedin": "https://linkedin.com",
    "netflix": "https://netflix.com",
    "docs": "https://docs.google.com",
    "drive": "https://drive.google.com",
    "sheets": "https://sheets.google.com",
    "canvas": "https://canvas.instructure.com",
    "whatsapp web": "https://web.whatsapp.com",
}


def _open_url(params: dict) -> str:
    target = params.get("target", "").strip()
    if not target:
        return "No URL specified."

    # Check shortcuts
    url = _URL_SHORTCUTS.get(target.lower(), target)

    # Add https if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    import webbrowser
    try:
        webbrowser.open(url)
        return f"Opened {target}."
    except Exception as e:
        return f"Couldn't open URL: {e}"


# ═══════════════════════════════════════════════════
#  FILE EXPLORER
# ═══════════════════════════════════════════════════

_FOLDER_SHORTCUTS = {
    "documents": os.path.expanduser("~/Documents"),
    "desktop": os.path.expanduser("~/Desktop"),
    "downloads": os.path.expanduser("~/Downloads"),
    "pictures": os.path.expanduser("~/Pictures"),
    "music": os.path.expanduser("~/Music"),
    "videos": os.path.expanduser("~/Videos"),
    "home": os.path.expanduser("~"),
}


def _open_folder(params: dict) -> str:
    target = params.get("target", "").strip().lower()
    if not target:
        return "No folder specified."

    path = _FOLDER_SHORTCUTS.get(target, target)

    if not os.path.exists(path):
        return f"Folder not found: {target}"

    if _IS_WINDOWS:
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

    return f"Opened {target} folder."


# ═══════════════════════════════════════════════════
#  SCREENSHOT
# ═══════════════════════════════════════════════════

def _screenshot(params: dict) -> str:
    save_dir = os.path.expanduser("~/Desktop")
    filename = f"screenshot_{int(time.time())}.png"
    filepath = os.path.join(save_dir, filename)

    if _IS_WINDOWS:
        try:
            # Use PowerShell for screenshotting — no dependencies
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
            $bitmap.Save('{filepath}')
            $graphics.Dispose()
            $bitmap.Dispose()
            """
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                timeout=10,
            )
            return f"Screenshot saved to Desktop."
        except Exception as e:
            return f"Screenshot failed: {e}"
    else:
        try:
            subprocess.run(
                ["scrot", filepath],
                capture_output=True,
                timeout=5,
            )
            return "Screenshot saved to Desktop."
        except Exception:
            return "Screenshot failed. Install scrot: sudo apt install scrot"


# ═══════════════════════════════════════════════════
#  VOLUME CONTROL
# ═══════════════════════════════════════════════════

def _set_volume(params: dict) -> str:
    level = params.get("level", 50)
    try:
        level = int(level)
        level = max(0, min(100, level))
    except (TypeError, ValueError):
        level = 50

    if _IS_WINDOWS:
        # Use nircmd if available, otherwise PowerShell
        try:
            # Map 0-100 to 0-65535 for Windows
            win_level = int(level / 100 * 65535)
            ps_cmd = f"""
            $wshShell = New-Object -ComObject WScript.Shell
            1..50 | ForEach-Object {{ $wshShell.SendKeys([char]174) }}
            $steps = [math]::Round({level} / 2)
            1..$steps | ForEach-Object {{ $wshShell.SendKeys([char]175) }}
            """
            subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                timeout=5,
            )
            return f"Volume set to {level}%."
        except Exception as e:
            return f"Volume control failed: {e}"
    else:
        try:
            subprocess.run(
                ["amixer", "set", "Master", f"{level}%"],
                capture_output=True,
                timeout=5,
            )
            return f"Volume set to {level}%."
        except Exception:
            return "Volume control failed."


def _volume_up(params: dict) -> str:
    if _IS_WINDOWS:
        try:
            ps_cmd = """
            $wshShell = New-Object -ComObject WScript.Shell
            1..5 | ForEach-Object { $wshShell.SendKeys([char]175) }
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
            return "Volume up."
        except Exception:
            return "Volume control failed."
    else:
        try:
            subprocess.run(["amixer", "set", "Master", "10%+"], capture_output=True, timeout=5)
            return "Volume up."
        except Exception:
            return "Volume control failed."


def _volume_down(params: dict) -> str:
    if _IS_WINDOWS:
        try:
            ps_cmd = """
            $wshShell = New-Object -ComObject WScript.Shell
            1..5 | ForEach-Object { $wshShell.SendKeys([char]174) }
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
            return "Volume down."
        except Exception:
            return "Volume control failed."
    else:
        try:
            subprocess.run(["amixer", "set", "Master", "10%-"], capture_output=True, timeout=5)
            return "Volume down."
        except Exception:
            return "Volume control failed."


# ═══════════════════════════════════════════════════
#  MEDIA CONTROL (play/pause/next/prev)
# ═══════════════════════════════════════════════════

def _send_media_key(key_code: str, label: str) -> str:
    """Send a media key press via PowerShell (Windows) or playerctl (Linux)."""
    if _IS_WINDOWS:
        # Virtual key codes for media keys
        vk_map = {
            "play_pause": "0xB3",
            "next": "0xB0",
            "prev": "0xB1",
            "stop": "0xB2",
        }
        vk = vk_map.get(key_code)
        if not vk:
            return f"Unknown media key: {key_code}"

        try:
            ps_cmd = f"""
            $key = {vk}
            $sig = '[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);'
            $type = Add-Type -MemberDefinition $sig -Name KeySend -Namespace Win32 -PassThru
            $type::keybd_event($key, 0, 0, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 50
            $type::keybd_event($key, 0, 2, [UIntPtr]::Zero)
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
            return f"Media: {label}."
        except Exception as e:
            return f"Media control failed: {e}"
    else:
        action_map = {
            "play_pause": "play-pause",
            "next": "next",
            "prev": "previous",
            "stop": "stop",
        }
        playerctl_action = action_map.get(key_code, key_code)
        try:
            subprocess.run(["playerctl", playerctl_action], capture_output=True, timeout=5)
            return f"Media: {label}."
        except Exception:
            return "Media control failed. Install playerctl."


def _media_play(params: dict) -> str:
    return _send_media_key("play_pause", "playing")


def _media_pause(params: dict) -> str:
    return _send_media_key("play_pause", "paused")


def _media_next(params: dict) -> str:
    return _send_media_key("next", "next track")


def _media_prev(params: dict) -> str:
    return _send_media_key("prev", "previous track")


# ═══════════════════════════════════════════════════
#  SYSTEM CONTROLS
# ═══════════════════════════════════════════════════

def _toggle_dark_mode(params: dict) -> str:
    if not _IS_WINDOWS:
        return "Dark mode toggle only supported on Windows."

    try:
        ps_cmd = """
        $path = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
        $current = (Get-ItemProperty -Path $path).AppsUseLightTheme
        $new = if ($current -eq 0) { 1 } else { 0 }
        Set-ItemProperty -Path $path -Name AppsUseLightTheme -Value $new
        Set-ItemProperty -Path $path -Name SystemUsesLightTheme -Value $new
        """
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)
        return "Dark mode toggled."
    except Exception as e:
        return f"Dark mode toggle failed: {e}"


def _lock_screen(params: dict) -> str:
    if _IS_WINDOWS:
        try:
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True, timeout=5)
            return "Screen locked."
        except Exception:
            return "Lock screen failed."
    elif platform.system() == "Darwin":
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to keystroke "q" using {command down, control down}'],
                timeout=5,
            )
            return "Screen locked."
        except Exception:
            return "Lock screen failed."
    else:
        try:
            subprocess.run(["loginctl", "lock-session"], timeout=5)
            return "Screen locked."
        except Exception:
            return "Lock screen failed."


def _focus_mode(params: dict) -> str:
    """Toggle Windows Focus Assist / Do Not Disturb."""
    if not _IS_WINDOWS:
        return "Focus mode only supported on Windows."

    try:
        ps_cmd = """
        $path = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings'
        try {
            $current = (Get-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -ErrorAction SilentlyContinue).NOC_GLOBAL_SETTING_TOASTS_ENABLED
            if ($current -eq 0) {
                Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 1
            } else {
                Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 0
            }
        } catch {
            New-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 0 -PropertyType DWORD
        }
        """
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)
        return "Focus mode toggled."
    except Exception as e:
        return f"Focus mode failed: {e}"


# ═══════════════════════════════════════════════════
#  SHUTDOWN TIMER
# ═══════════════════════════════════════════════════

def _shutdown_timer(params: dict) -> str:
    minutes = params.get("minutes", params.get("level", 30))
    try:
        minutes = int(minutes)
        minutes = max(1, min(480, minutes))  # 1 min to 8 hours
    except (TypeError, ValueError):
        minutes = 30

    seconds = minutes * 60

    if _IS_WINDOWS:
        try:
            subprocess.run(f"shutdown /s /t {seconds}", shell=True, timeout=5)
            return f"Shutdown scheduled in {minutes} minutes."
        except Exception as e:
            return f"Shutdown timer failed: {e}"
    else:
        try:
            subprocess.run(["shutdown", "-h", f"+{minutes}"], timeout=5)
            return f"Shutdown scheduled in {minutes} minutes."
        except Exception as e:
            return f"Shutdown timer failed: {e}"


def _cancel_shutdown(params: dict) -> str:
    if _IS_WINDOWS:
        try:
            subprocess.run("shutdown /a", shell=True, timeout=5)
            return "Shutdown cancelled."
        except Exception:
            return "No shutdown to cancel."
    else:
        try:
            subprocess.run(["shutdown", "-c"], timeout=5)
            return "Shutdown cancelled."
        except Exception:
            return "No shutdown to cancel."


# ═══════════════════════════════════════════════════
#  TYPE TEXT (simulates keyboard input)
# ═══════════════════════════════════════════════════

def _type_text(params: dict) -> str:
    text = params.get("target", params.get("text", ""))
    if not text:
        return "No text to type."

    if _IS_WINDOWS:
        try:
            # Escape single quotes for PowerShell
            safe_text = text.replace("'", "''")
            ps_cmd = f"""
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait('{safe_text}')
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)
            return f"Typed: {text[:30]}"
        except Exception as e:
            return f"Type failed: {e}"
    else:
        try:
            subprocess.run(["xdotool", "type", "--clearmodifiers", text], timeout=10)
            return f"Typed: {text[:30]}"
        except Exception:
            return "Type failed. Install xdotool."


# ═══════════════════════════════════════════════════
#  ACTION MAP
# ═══════════════════════════════════════════════════

_ACTION_MAP = {
    "open_app": _open_app,
    "close_app": _close_app,
    "open_url": _open_url,
    "open_folder": _open_folder,
    "screenshot": _screenshot,
    "set_volume": _set_volume,
    "volume_up": _volume_up,
    "volume_down": _volume_down,
    "media_play": _media_play,
    "media_pause": _media_pause,
    "media_next": _media_next,
    "media_prev": _media_prev,
    "toggle_dark_mode": _toggle_dark_mode,
    "lock_screen": _lock_screen,
    "focus_mode": _focus_mode,
    "shutdown_timer": _shutdown_timer,
    "cancel_shutdown": _cancel_shutdown,
    "type_text": _type_text,
}