"""
Configuration Loader
- Reads settings from config.json
- Allows override via environment variables
- Stores timeout, delay, and filter settings
"""
import json
import os

CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

USER_AGENT = os.getenv("USER_AGENT", CONFIG.get("user_agent"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", CONFIG.get("request_timeout", 30)))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", CONFIG.get("request_delay", 1.5)))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", CONFIG.get("max_concurrency", 3)))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", CONFIG.get("confidence_threshold", 0.5)))
MIN_WORD_COUNT = int(os.getenv("MIN_WORD_COUNT", CONFIG.get("min_word_count", 100)))
SKIP_PATTERNS = CONFIG.get("skip_patterns", [])
SKIP_EXTENSIONS = CONFIG.get("skip_extensions", [])
