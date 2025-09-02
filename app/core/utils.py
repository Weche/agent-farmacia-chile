# app/core/utils.py
import unicodedata
import os
from datetime import datetime, time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_value(key: str, default: str = None) -> str:
    """Get environment variable value with optional default"""
    return os.getenv(key, default)

def strip_accents(s: str) -> str:
    if not s:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def norm_lower(s: str) -> str:
    return strip_accents(s).lower().strip()

def is_open_now_from_times(open_str: str|None, close_str: str|None, now: datetime|None=None) -> bool:
    """
    Maneja horarios que cruzan medianoche (e.g. 21:00–06:00).
    Si no hay datos, retorna True (fail-open) para el MVP.
    """
    try:
        if not open_str or not close_str:
            return True
        fmt = "%H:%M:%S" if len(open_str) > 5 else "%H:%M"
        o = datetime.strptime(open_str, fmt).time()
        c = datetime.strptime(close_str, fmt).time()
        now = now or datetime.now()
        nt = now.time()
        if c >= o:
            # intervalo diurno normal
            return o <= nt <= c
        else:
            # cruza medianoche: abierto si >= apertura o <= cierre
            return nt >= o or nt <= c
    except Exception:
        return True
