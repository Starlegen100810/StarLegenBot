from pathlib import Path
import os
from dotenv import load_dotenv
import telebot

# ⬇️ ՍՏԵՂԾԱԿԱՆ ՍՈՒՐԲ ՓՈԽՈՒԹՅՈՒՆ՝ ԱՌԱՆՑ "/ project_root"
BASE_DIR = Path(__file__).resolve().parents[2]   # -> C:\StarLegenBot\project_root
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = BASE_DIR.parent / "media"            # -> C:\StarLegenBot\media

def load_config():
    load_dotenv(ENV_PATH)
    cfg = {
        "BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        "DEFAULT_LANG": (os.getenv("DEFAULT_LANG", "hy") or "hy").strip().lower(),
        "ADMIN_ID": int(os.getenv("ADMIN_ID", "0")),
        "MEDIA_DIR": MEDIA_DIR.resolve(),
        "BUNNY_PATH": (MEDIA_DIR / "bunny.jpg").resolve(),
        "COUNTER_FILE": (DATA_DIR / "customer_counter.txt").resolve(),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not cfg["COUNTER_FILE"].exists():
        cfg["COUNTER_FILE"].write_text("1007", encoding="utf-8")
    return cfg

def make_bot(token: str) -> telebot.TeleBot:
    return telebot.TeleBot(token, parse_mode=None)

