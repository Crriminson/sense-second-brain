import os
import subprocess

# All system commands

def execute_system_command(command: str):
    print(f"Executing system command: {command}")
    # Be careful with shell=True
    # subprocess.run(command, shell=True)
    if command == "shutdown":
        # os.system("shutdown /s /t 1")
        print("Shutting down...")
    elif command == "volume_up":
        # System specific volume control
        pass
    return "Command executed"
