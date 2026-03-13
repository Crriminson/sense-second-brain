"""
LLM abstraction layer.

This is the ONLY file that knows which LLM provider you're using.
Everything else calls provider.ask() and doesn't care if it's
Ollama, Groq, OpenAI, or a potato with a neural network.

Swap guide:
  Change LLM_PROVIDER in config.py. That's it.
  
Testing guide:
  On weak laptop: LLM_MODEL = "phi3:mini" (small, fast)
  On GPU machine: LLM_MODEL = "qwen2.5:7b" (bigger, slower, more accurate)
  Free cloud:     LLM_PROVIDER = "groq" (fast, free tier, needs internet)
"""

import httpx
import json
import re
import asyncio
from config import settings


async def ask(
    prompt: str,
    temperature: float = 0.1,
    json_mode: bool = True,
    timeout: float = 15.0,
    tools: list = None,
    tool_choice: str = "auto",
) -> str:
    try:
        provider = settings.LLM_PROVIDER
        
        if provider == "ollama":
            return await _ask_ollama(prompt, temperature, json_mode, timeout, tools)
        elif provider == "groq":
            return await _ask_groq(prompt, temperature, json_mode, timeout, tools, tool_choice)
        elif provider == "openai":
            return await _ask_openai(prompt, temperature, json_mode, timeout, tools, tool_choice)
        else:
            print(f"[AI] Unknown provider: {provider}")
            return ""
    except asyncio.CancelledError:
        print(f"[AI] Request cancelled (WebSocket disconnect?)")
        return ""
    except httpx.TimeoutException:
        print(f"[AI] Timeout after {timeout}s")
        return ""
    except Exception as e:
        print(f"[AI] Provider error: {e}")
        return ""


async def _ask_ollama(prompt, temperature, json_mode, timeout, tools):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            body = {
                "model": settings.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": temperature,
                    "num_predict": 256,
                    "num_ctx": 2048,
                },
            }
            if json_mode:
                body["format"] = "json"
            if tools:
                body["tools"] = tools

            resp = await client.post(f"{settings.LLM_URL}/api/generate", json=body)
            resp.raise_for_status()
            
            data = resp.json()
            # Ollama returns tool calls differently if it used them
            if "message" in data and "tool_calls" in data["message"]:
                return json.dumps(data["message"]["tool_calls"])
            return data["response"]
    except asyncio.CancelledError:
        raise
    except httpx.HTTPStatusError as e:
        print(f"[AI] Ollama error: {e.response.status_code} {e.response.text[:200]}")
        return ""
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        print(f"[AI] Ollama unavailable: {e}")
        return ""


async def _ask_groq(prompt, temperature, json_mode, timeout, tools, tool_choice):
    async with httpx.AsyncClient(timeout=timeout) as client:
        body = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if json_mode and not tools: # Groq generally dislikes JSON mode combined with tool calling
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice

        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        
        msg = resp.json()["choices"][0]["message"]
        if "tool_calls" in msg and msg["tool_calls"]:
            return json.dumps(msg["tool_calls"])
        return msg.get("content", "")


async def _ask_openai(prompt, temperature, json_mode, timeout, tools, tool_choice):
    async with httpx.AsyncClient(timeout=timeout) as client:
        body = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if json_mode and not tools:
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice

        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        
        msg = resp.json()["choices"][0]["message"]
        if "tool_calls" in msg and msg["tool_calls"]:
            return json.dumps(msg["tool_calls"])
        return msg.get("content", "")


def parse_json(text: str) -> dict | None:
    if not text or not text.strip():
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        json_str = match.group()
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    return None