"""
Dynamic Commands
This module exposes dynamic PC capabilities using LLM tool calling.
Instead of hardcoded intents, the LLM can decide to run Shell/Windows commands.
"""

import subprocess
import os
import platform

_IS_WINDOWS = platform.system() == "Windows"

def run_shell_command(command: str) -> dict:
    """
    Run an arbitrary shell command (Powershell on Windows, bash on Mac/Linux).
    THIS TOOL IS EXPERIMENTAL AND SHOULD PROMPT THE FRONTEND FOR CONFIRMATION (Future Goal).
    """
    print(f"[DYNAMIC CMD] Executing: {command}")
    try:
        if _IS_WINDOWS:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=15,
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            
        success = result.returncode == 0
        output = result.stdout.strip() if success else result.stderr.strip()
        
        # Truncate extremely long outputs
        if len(output) > 500:
            output = output[:500] + "... (truncated)"
            
        return {
            "success": success,
            "output": output or "Command executed successfully with no output."
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Command timed out after 15 seconds."}
    except Exception as e:
        return {"success": False, "output": f"Execution failed: {e}"}

# List of tools to pass to the LLM (OpenAI/Groq compatible format)
GET_DYNAMIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute an arbitrary shell or OS command. On Windows, this runs in PowerShell. On Mac/Linux, this runs in bash. Use this to open unlisted apps, manipulate files, or run scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact shell command script to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Fetch upcoming events from the user's Google Calendar. Returns a JSON list of events. Provide a brief spoken summary of these events if you call this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "How many events to fetch (default 5, max 10)."
                    }
                }
            }
        }
    }
]
