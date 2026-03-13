# config.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "second_brain.db"))
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(BASE_DIR, "chroma_data"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
TIMEOUT_INTENT = 60
TIMEOUT_ANSWER = 60
TIMEOUT_RELATION = 60
TIMEOUT_SUMMARIZE = 120
SEARCH_SIMILARITY_MIN = 0.3
EDGE_SIMILARITY_MIN = 0.5
EDGE_TOP_K = 3
CONFIDENCE_MIN = 0.5
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Backward compatibility shim for AI modules
class Settings:
    def __init__(self):
        self.DB_PATH = DB_PATH
        self.CHROMA_PATH = CHROMA_PATH
        self.EMBEDDING_MODEL = EMBEDDING_MODEL
        self.LLM_PROVIDER = LLM_PROVIDER
        self.LLM_URL = LLM_URL
        self.LLM_MODEL = LLM_MODEL
        self.GROQ_API_KEY = GROQ_API_KEY
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
        self.GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
        self.TIMEOUT_INTENT = TIMEOUT_INTENT
        self.TIMEOUT_ANSWER = TIMEOUT_ANSWER
        self.TIMEOUT_RELATION = TIMEOUT_RELATION
        self.TIMEOUT_SUMMARIZE = TIMEOUT_SUMMARIZE
        self.SEARCH_SIMILARITY_MIN = SEARCH_SIMILARITY_MIN
        self.EDGE_SIMILARITY_MIN = EDGE_SIMILARITY_MIN
        self.EDGE_TOP_K = EDGE_TOP_K
        self.CONFIDENCE_MIN = CONFIDENCE_MIN
        self.MQTT_BROKER = MQTT_BROKER
        self.MQTT_PORT = MQTT_PORT

settings = Settings()
