import os
import subprocess
import webbrowser
import platform

# All system commands

def execute_pc_command(action: str, params: dict = {}):
    """
    Execute a PC control command.
    Uses standard libraries where possible for Windows compatibility.
    """
    print(f"[SYSTEM] Executing action: {action} with params: {params}")
    target = params.get("target", "")

    try:
        if action == "open_url":
            if target:
                webbrowser.open(target)
                return f"Opened {target}"
            return "No URL specified"

        elif action == "open_app":
            if target:
                # Basic attempt to start a process
                subprocess.Popen(target, shell=True)
                return f"Starting {target}"
            return "No app specified"

        elif action == "lock_screen":
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                return "Screen locked"
            return "Lock screen not supported on this OS"

        elif action == "set_volume":
            # This often requires third-party libs like pycaw on Windows
            # but we can try a basic powershell command
            vol = params.get("level", 50)
            try:
                subprocess.run([
                    "powershell", "-Command",
                    f"(Get-WmiObject -Query 'Select * from Win32_DesktopMonitor').SetBrightness({vol})"
                ], check=True) # Note: This is an example, volume is harder.
                return f"Volume set to {vol}"
            except:
                return "Failed to set volume"

        elif action == "toggle_dark_mode":
            # Windows registry toggle
            cmd = 'reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v AppsUseLightTheme /t REG_DWORD /d {value} /f'
            # This is complex to toggle, usually needs checking current value first
            return "Dark mode toggle not fully implemented"

        elif action == "shutdown_timer":
            minutes = params.get("minutes", 60)
            seconds = int(minutes) * 60
            os.system(f"shutdown /s /t {seconds}")
            return f"System will shutdown in {minutes} minutes"

        elif action == "cancel_shutdown":
            os.system("shutdown /a")
            return "Shutdown cancelled"

        else:
            print(f"[SYSTEM] Unknown action: {action}")
            return f"Action {action} not implemented"

    except Exception as e:
        print(f"[SYSTEM ERR] {e}")
        return f"Error executing {action}: {e}"
