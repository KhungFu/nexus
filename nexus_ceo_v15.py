# -*- coding: utf-8 -*-
# NEXUS CEO v15 - QUANT FUND EDITION
# Hibrit AI: Gemini (gemini-3-flash-preview) + Groq (Llama 4) fallback
# Telegram Watchdog: Telegram olmadan trading devam eder
# Trailing SL: Pyramiding pozisyonlari %1.5 trailing stop
# IATA Jet Fuel + Airline Sentiment
# GDACS + NHC Hurricanes + HDD/CDD + EU Gas Storage + ECMWF + NOAA Anomaly
# Global Weather + Disasters + Google Trends + 31 Airlines + 18 Ship Regions
# Alternative Data: Cargo Flüge + Schiffsverkehr + BDI + E-Commerce
# News Cache (RSS + X/Nitter) | 14 Tage Trend-Analyse
# Sentiment-Tracking | Asset-spezifische News pro Kandidat
# 3-Stufen Kara Kugu: -8% Gemini, -12% Auto, -18% Notfall
# Schutz-Thread: alle 5 Min (keine Quota)
# Backtesting 200 Tage (3 Timeframes) | Asset Deep Dive
# Gemini ruft historische Daten selbst ab | /backtest /deepdive
# Stage 1: Python Gate-Keeper (ADX+RSI+MA+Bollinger+Fibonacci)
# Stage 2: Gemini Internet-Suche + Interpretation + Trade
# SQLite Gedaechtnis | Google Search Grounding | Kelly-Kriterium
# Economic Calendar | Wetter-API | Volatilitaets-Regime | Asset-Korrelation
# Source Credibility Engine | Sentiment-Tracking | Seasonal Patterns
import os, time, requests, telebot, re, logging, json, threading, sys
import sqlite3
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from openai import OpenAI  # Groq + Grok icin OpenAI-uyumlu client
from dotenv import load_dotenv

# --- CONFIG IMPORT VERSUCH ---
try:
    from capital_markets_config import MARKET_CONFIG
    logging.info("✅ Externe capital_markets_config.py geladen!")
except ImportError:
    logging.warning("⚠️ capital_markets_config.py bulunamadı. Dahili yedek liste kullanılıyor.")
    MARKET_CONFIG = {
        # Weekend whitelist kriptolar - MUTLAKA olmalı
        "BTC_USD":     {"epic": "BTCUSD",     "min_size": 0.01},
        "ETH_USD":     {"epic": "ETHUSD",     "min_size": 0.001},
        "SOL_USD":     {"epic": "SOLUSD",     "min_size": 0.1},
        "XRP_USD":     {"epic": "XRPUSD",     "min_size": 1.0},
        # Hafta içi assetler
        "GOLD":        {"epic": "GOLD",       "min_size": 0.01},
        "SILVER":      {"epic": "SILVER",     "min_size": 1.0},
        "OIL_BRENT":   {"epic": "OILBRENT",   "min_size": 0.1},
        "NATURAL_GAS": {"epic": "NATURALGAS", "min_size": 1.0},
        "EURUSD":      {"epic": "EURUSD",     "min_size": 100.0},
    }

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# DB sofort beim Start initialisieren (fehlende Tabellen erstellen)
import sqlite3 as _sqlite3_init
try:
    _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_quant.db")
    _conn = _sqlite3_init.connect(_db_path)
    _conn.executescript("""
        CREATE TABLE IF NOT EXISTS news_cache (news_id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, source_type TEXT DEFAULT 'NEWS', asset_tag TEXT DEFAULT 'GENEL', title TEXT, url TEXT DEFAULT '', summary TEXT DEFAULT '', published_at TEXT, fetched_at TEXT, sentiment REAL DEFAULT 0.0, sentiment_label TEXT DEFAULT 'NEUTRAL', importance INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS x_cache (x_id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT, asset_tag TEXT DEFAULT 'GENEL', tweet_text TEXT, tweet_date TEXT, fetched_at TEXT, sentiment REAL DEFAULT 0.0, sentiment_label TEXT DEFAULT 'NEUTRAL', likes INTEGER DEFAULT 0, search_query TEXT DEFAULT '');
    """)
    _conn.commit()
    _conn.close()
    logging.info("DB Tabellen sichergestellt (news_cache, x_cache)")
except Exception as _e:
    logging.warning(f"DB Init Fehler: {_e}")

# ============================================================
# KONFIGURASYON
# ============================================================
TG_TOKEN = os.getenv("TG_TOKEN") or os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
# ============================================================
# AI BACKEND KONFIGURASYONU - Gemini + Groq hibrit sistem
# ============================================================
# Gemini - sadece gemini-3-flash-preview calisiyor
GEMINI_KEYS = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 7)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

# Groq - ultra hizli, Llama modelleri (fallback + hiz gerektiren gorevler)
# Groq key rotasyonu - .env'de istediğin kadar key ekleyebilirsin:
# GROQ_API_KEY=...       (tek key kullanıyorsan)
# GROQ_API_KEY_1=...     (birden fazla key için)
# GROQ_API_KEY_2=...
# GROQ_API_KEY_3=...  vb.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_KEYS    = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 10)]  # max 9 key
if GROQ_API_KEY and GROQ_API_KEY not in GROQ_KEYS:
    GROQ_KEYS.insert(0, GROQ_API_KEY)
GROQ_KEYS = [k for k in GROQ_KEYS if k]  # boş olanları filtrele

# Aktif key index ve rate limit tracker
_groq_key_idx  = 0
_groq_key_lock = threading.Lock()
_groq_rate_limited = {}  # {key: unix_timestamp} - ne zaman serbest kalır
CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW = os.getenv("CAPITAL_PASSWORD")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")  # St. Louis Fed - ucretsiz
# ============================================================
# HESAP SECIMI - .env dosyasinda ayarla
# IS_DEMO=true  -> Demo hesap
# IS_DEMO=false -> Canli (Live) hesap
# CAPITAL_ACCOUNT_ID -> Kullanilacak hesap ID'si (hesap_bul.py ile bul)
# ============================================================
IS_DEMO = os.getenv("IS_DEMO", "true").lower() == "true"
TARGET_ACCOUNT_ID = os.getenv("CAPITAL_ACCOUNT_ID", "")

if IS_DEMO:
    CAPITAL_URL = os.getenv("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"
    logging.info("🧪 MOD: DEMO HESAP")
else:
    CAPITAL_URL = "https://api-capital.backend-capital.com/api/v1"
    logging.info("💰 MOD: CANLI (LIVE) HESAP")

MAX_SPREAD = 0.5

# KARA KUĞU SCHWELLEN
KARA_KUGU_GEMINI_THRESHOLD  = -8.0
KARA_KUGU_AUTO_THRESHOLD    = -12.0
KARA_KUGU_NOTFALL_THRESHOLD = -18.0

# NEWS & X INTELLIGENCE
NEWS_HISTORY_DAYS     = 14
NEWS_COLLECT_INTERVAL = 3600   # Fallback: her saat
X_COLLECT_INTERVAL    = 1800   # X/Twitter: 30 dakika

# Bolgesel haber takvimi - Asya/Avrupa/Amerika sabahları + saatlik
NEWS_REGIONAL_HOURS = {
    "ASYA":    [1, 2, 3],    # UTC 01-03 = Tokyo/Shanghai sabahi
    "AVRUPA":  [6, 7, 8],    # UTC 06-08 = Frankfurt/London acilis
    "AMERIKA": [13, 14, 15], # UTC 13-15 = NY acilis
    "KAPANIS": [20, 21],     # UTC 20-21 = NY kapanis
}
NEWS_PRIORITY_HOURS = [h for hours in NEWS_REGIONAL_HOURS.values() for h in hours]

# TABU ASSETS - kesinlikle trade yapilmaz
TABU_ASSETS = set()  # WHEAT ve CORN kaldirildi - kullanici talimatiyla

# ============================================================
# HARD BLOCK - Kullanici talimatiyla runtime'da engellenen assetler
# Gemini override edemez. Telegram'dan otomatik parse edilir.
# ============================================================
hard_block_lock = threading.Lock()
HARD_BLOCK_ASSETS = {}  # {symbol: {"reason": str, "action": "BUY"|"SELL"|"ALL", "timestamp": str}}

# ============================================================
# ONAY SİSTEMİ - Kullanici mesajina gore Gemini analiz yapar,
# sonucu kullaniciya gonderir, onay beklenir, sonra trade acilir.
# ============================================================
pending_approval_lock = threading.Lock()
PENDING_APPROVAL = {}
# Yapi:
# {
#   "asset": "COFFEE",
#   "side": "BUY",
#   "size": 10.0,
#   "sl": 3.10,
#   "tp": 3.30,
#   "analysis_text": "...",
#   "timestamp": "2026-03-19 09:42:00",
#   "user_request": "Kaufe Kaffee"
# }

# ============================================================
# ASSET KEYWORDS - once tanimla, sonra fonksiyonlar kullanir
# ============================================================
ASSET_KEYWORDS = {
    # Silver
    "silver": "SILVER", "silber": "SILVER", "gumus": "SILVER", "gümüş": "SILVER",
    # Gold
    "gold": "GOLD", "altin": "GOLD", "alton": "GOLD",
    # Oil
    "oil": "OIL_BRENT", "brent": "OIL_BRENT", "petrol": "OIL_BRENT",
    "crude": "OIL_CRUDE", "rohol": "OIL_CRUDE",
    # Natural Gas
    "natural gas": "NATURAL_GAS", "naturalgas": "NATURAL_GAS",
    "dogalgaz": "NATURAL_GAS", "erdgas": "NATURAL_GAS",
    # Gasoline
    "gasoline": "GASOLINE", "benzin": "GASOLINE",
    # Coffee
    "coffee": "COFFEE", "kaffee": "COFFEE", "kahve": "COFFEE",
    # Copper
    "copper": "COPPER", "bakir": "COPPER", "kupfer": "COPPER",
    # Heating Oil
    "heating oil": "HEATING_OIL", "heatingoil": "HEATING_OIL",
    # Crypto
    "btc": "BTC_USD", "bitcoin": "BTC_USD",
    "eth": "ETH_USD", "ethereum": "ETH_USD",
    "solana": "SOL_USD",
    "xrp": "XRP_USD", "ripple": "XRP_USD",
    # Forex
    "eurusd": "EURUSD", "eur/usd": "EURUSD",
}

# Kullanici mesajindan BUY/SELL niyeti parse et
INTENT_BUY_KEYWORDS  = [
    "kauf", "kaufe", "kaufen",          # Almanca al
    "al ", "alim", "satin al",          # Turkce al
    "buy", "long",                      # Ingilizce
    "pozisyon ac", "gir ",
]
INTENT_SELL_KEYWORDS = [
    "verkauf", "verkaufe", "verkaufen", # Almanca sat
    "sat ", "satim",                    # Turkce sat
    "sell", "short",                    # Ingilizce
    "pozisyon kapat",
]
# "long" = BUY, "short" = SELL - bunlar yön belirtir
INTENT_LONG_KEYWORDS  = ["long"]
INTENT_SHORT_KEYWORDS = ["short"]

def parse_user_intent(text):
    """
    Kullanici mesajinda trade niyeti var mi?
    Donus: (asset_sym, side) veya (None, None)

    Ornekler:
      "Kaufe Kaffee"    -> ("COFFEE", "BUY")
      "Gümüş sat"       -> ("SILVER", "SELL")
      "Gümüş short"     -> ("SILVER", "SELL")
      "Gold long"       -> ("GOLD",   "BUY")
      "Gümüş satma"     -> (None, None)  [bu BLOCK, buraya gelmez]
    """
    import re as _re
    t = text.lower().strip()

    # Eger sadece engelleme iceriyorsa (satma/alma/nicht handeln)
    # bu parse_hard_block'un isi - buradan None don
    pure_block = ["satma", "alma", "nicht handeln", "nicht kaufen",
                  "kauf nicht", "engelle", "yasak", "blokla",
                  "stop trading", "buy yapma", "satin alma", "verboten"]
    if any(p in t for p in pure_block):
        return None, None

    # Asset tespit
    detected_asset = None
    for kw in sorted(ASSET_KEYWORDS.keys(), key=len, reverse=True):
        if kw in t:
            if kw == "sol" and any(longer in t for longer in ["solana", "gasoline"]):
                continue
            if kw == "gas" and "natural gas" in t:
                detected_asset = ASSET_KEYWORDS["natural gas"]
                break
            detected_asset = ASSET_KEYWORDS[kw]
            break

    if not detected_asset:
        return None, None

    # Yon tespiti - regex ile kelime siniri
    is_long  = bool(_re.search(r"\blong\b", t))
    is_short = bool(_re.search(r"\bshort\b", t))
    is_buy   = bool(_re.search(r"\b(kauf|kaufe|kaufen|buy|al|alim)\b", t))
    # "sat" kelimesini "satma" ile karismadan yakala
    is_sell  = bool(_re.search(r"\b(verkauf|verkaufe|verkaufen|sell|sat|satim|short)\b", t))
    # "sat" varsa ama "satma" da varsa -> sell degil block
    if "satma" in t and "sat" in t:
        is_sell = False

    if is_long and not is_short:   return detected_asset, "BUY"
    if is_short and not is_long:   return detected_asset, "SELL"
    if is_buy and not is_sell:     return detected_asset, "BUY"
    if is_sell and not is_buy:     return detected_asset, "SELL"
    if is_buy and is_sell:         return detected_asset, "BUY"
    # Sadece asset ismi -> BUY varsayimi
    return detected_asset, "BUY"

# Engelleme / serbest birakma kelimeleri
BLOCK_KEYWORDS     = ["nicht handeln", "alma", "satma", "trade etme", "kauf nicht",
                      "nicht kaufen", "engelle", "blokla", "durdur", "stop trading",
                      "halt", "yasak", "verbot", "verkaufen und heute"]
SELL_KEYWORDS      = ["verkaufen", "sat ", "sell", "kapat", "close", "schliessen"]
BUY_BLOCK_KEYWORDS = ["nicht kaufen", "kauf nicht", "alma", "buy yapma"]
UNBLOCK_KEYWORDS   = ["freigeben", "serbest", "tekrar al", "engeli kaldir",
                      "unblock", "wieder handeln", "izin ver", "artik al", "artik sat"]

def parse_hard_block(text):
    """
    Kullanici mesajindan ENGELLEME niyeti var mi?
    Kural:
      "satma" / "alma" / "nicht handeln" = BLOCK
      "sat" / "al" / "buy" / "sell"      = TRADE (parse_user_intent halleder)
      "serbest" / "freigeben"             = UNBLOCK

    Donus: (asset_sym, action, block_type)
      block_type : "BLOCK" | "UNBLOCK" | None
      action     : "ALL" | "BUY" | "SELL"
    """
    t = text.lower().strip()

    detected_asset = None
    for kw in sorted(ASSET_KEYWORDS.keys(), key=len, reverse=True):
        if kw in t:
            detected_asset = ASSET_KEYWORDS[kw]
            break
    if not detected_asset:
        return None, None, None

    # --- UNBLOCK ---
    for kw in UNBLOCK_KEYWORDS:
        if kw in t:
            return detected_asset, "ALL", "UNBLOCK"

    # --- SADECE ENGELLEME KELIMELERI ---
    # "satma", "alma", "nicht kaufen", "nicht handeln" vb.
    # NOT: "sat " veya "al " tek basina TRADE emirdir, BLOCK degil!
    pure_block_patterns = [
        "satma", "alma", "trade etme",
        "nicht handeln", "nicht kaufen", "kauf nicht",
        "engelle", "blokla", "yasak", "verbot",
        "stop trading", "verkaufen und heute nicht",
        "buy yapma", "satin alma", "verboten",
    ]
    is_pure_block = any(p in t for p in pure_block_patterns)

    if is_pure_block:
        # BUY engeli mi SELL engeli mi?
        buy_block_patterns  = ["alma", "satin alma", "nicht kaufen", "kauf nicht", "buy yapma"]
        sell_block_patterns = ["satma", "nicht verkaufen"]
        if any(p in t for p in buy_block_patterns):
            return detected_asset, "BUY", "BLOCK"
        if any(p in t for p in sell_block_patterns):
            return detected_asset, "SELL", "BLOCK"
        return detected_asset, "ALL", "BLOCK"

    # "sat " veya "al " varsa -> bu TRADE emri, BLOCK degil
    return None, None, None

def apply_hard_block(sym, action, reason):
    with hard_block_lock:
        HARD_BLOCK_ASSETS[sym] = {
            "reason": reason,
            "action": action,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    logging.warning(f"HARD BLOCK aktif: {sym} ({action}) — {reason}")

def remove_hard_block(sym):
    with hard_block_lock:
        removed = HARD_BLOCK_ASSETS.pop(sym, None)
    if removed:
        logging.info(f"HARD BLOCK kaldirildi: {sym}")
    return removed

def check_hard_block(sym, side):
    """Trade yapilmadan once kontrol. Donus: (blocked: bool, reason: str)"""
    with hard_block_lock:
        entry = HARD_BLOCK_ASSETS.get(sym)
    if not entry:
        return False, ""
    action = entry["action"]
    if action == "ALL":
        return True, entry["reason"]
    if action == "BUY" and side == "BUY":
        return True, entry["reason"]
    if action == "SELL" and side == "SELL":
        return True, entry["reason"]
    return False, ""

# HAFTASONU KRIPTO WHITELIST - sadece likit kriptolar izinli
WEEKEND_CRYPTO_WHITELIST = {
    "BTC_USD", "ETH_USD", "SOL_USD", "XRP_USD",
    "BTC_EUR", "ETH_EUR", "SOL_EUR", "XRP_EUR"
}

# SEASONAL PATTERNS - ay bazli guc katsayilari (Ocak=0 ... Aralik=11)
# 1.0=normal | >1.0=guclu sezon | <1.0=zayif sezon
SEASONAL_FACTORS = {
    "GOLD":        [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.1,1.3,1.2,1.1,1.0],
    "SILVER":      [1.0,1.0,1.1,1.1,1.0,1.0,1.0,1.0,1.2,1.2,1.0,1.0],
    "NATURAL_GAS": [1.2,1.1,1.0,1.0,1.0,1.0,1.0,1.1,1.1,1.2,1.3,1.3],
    "HEATING_OIL": [1.2,1.1,1.0,1.0,1.0,1.0,1.0,1.0,1.1,1.2,1.3,1.3],
    "OIL_BRENT":   [1.0,1.0,1.0,1.1,1.1,1.1,1.0,1.0,1.0,1.0,1.0,1.0],
    "BTC_USD":     [1.1,1.0,1.0,1.2,1.0,1.0,1.0,1.0,1.0,1.1,1.2,1.2],
    "ETH_USD":     [1.1,1.0,1.0,1.2,1.0,1.0,1.0,1.0,1.0,1.1,1.2,1.2],
}

# DOSYA YOLLARI
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DB_FILE      = os.path.join(BASE_DIR, "nexus_quant.db")
DAILY_LOSS_FILE = os.path.join(BASE_DIR, "daily_loss_counter.json")
daily_loss_lock = threading.Lock()

# ============================================================
# GEMINI MODELLER UND ROTASYON
# ============================================================
# Gemini: sadece gemini-3-flash-preview calisiyor
GEMINI_MODELS = [
    "gemini-3-flash-preview",   # TEK CALISANMODEL
]

# Groq: ultra hizli Llama modelleri - Gemini quota dolunca devreye girer
# Groq model listesi - SADECE CALISANLAR (26 Mart 2026 itibariyle)
GROQ_MODELS = [
    "moonshotai/kimi-k2-instruct",              # En guclu - 262k context
    "meta-llama/llama-4-scout-17b-16e-instruct",# Llama 4 Scout - hizli
    "qwen/qwen3-32b",                           # Qwen3 - finansal analiz
    "llama-3.3-70b-versatile",                  # Llama 3.3 - fallback
    "llama-3.1-8b-instant",                     # Ultra hizli - kucuk gorevler
]

# Task-based model secimi - hangi is icin hangi model optimal
def get_optimal_groq_model(task_type="analysis"):
    """
    Gorev tipine gore en uygun Groq modelini sec.
    task_type: "complex_analysis" | "quick_signal" | "financial_data" | "emergency"
    """
    task_model_map = {
        "complex_analysis": "moonshotai/kimi-k2-instruct",    # En guclu - tam analiz
        "financial_data":   "qwen/qwen3-32b",                  # Sayi/finans uzmani
        "quick_signal":     "llama-3.1-8b-instant",            # Hiz oncelikli
        "emergency":        "llama-3.1-8b-instant",            # Acil - cok hizli
    }
    return task_model_map.get(task_type, "moonshotai/kimi-k2-instruct")

_model_lock = threading.Lock()
_current_model_idx = 0
_current_ai_backend = "GEMINI"  # "GEMINI" veya "GROQ"
_backend_lock = threading.Lock()

def get_next_model():
    global _current_model_idx
    with _model_lock:
        return GEMINI_MODELS[_current_model_idx % len(GEMINI_MODELS)]

def rotate_model_on_quota():
    """Gemini quota dolunca Groq'a gec, Groq da dolunca bekleme."""
    global _current_model_idx, _current_ai_backend
    with _model_lock:
        with _backend_lock:
            if _current_ai_backend == "GEMINI":
                if GROQ_KEYS:
                    _current_ai_backend = "GROQ"
                    _current_model_idx = 0
                    logging.warning("Gemini quota doldu → Groq'a geciliyor")
                else:
                    _current_model_idx = 0  # Gemini'yi resetle, bekle
            else:
                _current_model_idx = (_current_model_idx + 1) % len(GROQ_MODELS)
                if _current_model_idx == 0:
                    # Tum Groq modelleri de doldu - Gemini'ye don
                    _current_ai_backend = "GEMINI"
                    logging.warning("Groq quota doldu → Gemini'ye donuluyor")
    return get_current_model_and_backend()

def get_current_model_and_backend():
    """Aktif backend ve modeli dondur."""
    with _backend_lock:
        backend = _current_ai_backend
    with _model_lock:
        if backend == "GEMINI":
            return "GEMINI", GEMINI_MODELS[0]
        else:
            return "GROQ", GROQ_MODELS[_current_model_idx % len(GROQ_MODELS)]

# Son kullanılan AI backend bilgisi
_last_ai_backend = {"backend": "GEMINI", "model": "gemini-3-flash-preview"}
_last_ai_lock = threading.Lock()

def _set_last_ai_backend(backend, model):
    with _last_ai_lock:
        _last_ai_backend["backend"] = backend
        _last_ai_backend["model"]   = model

def get_last_ai_info():
    with _last_ai_lock:
        return _last_ai_backend["backend"], _last_ai_backend["model"]

def get_groq_client(force_next=False):
    """
    Groq API client - akıllı key rotasyonu.
    Rate limit gelince otomatik sonraki key'e geçer.
    force_next=True: bir sonraki key'e zorla geç (hata sonrası)
    """
    global _groq_key_idx
    if not GROQ_KEYS:
        logging.warning("GROQ_API_KEY eksik!")
        return None

    with _groq_key_lock:
        now = time.time()

        if force_next:
            _groq_key_idx = (_groq_key_idx + 1) % len(GROQ_KEYS)

        # Rate limit'i geçmiş key'i atla
        attempts = 0
        while attempts < len(GROQ_KEYS):
            key = GROQ_KEYS[_groq_key_idx % len(GROQ_KEYS)]
            wait_until = _groq_rate_limited.get(key, 0)
            if now >= wait_until:
                break  # Bu key kullanılabilir
            # Bu key hâlâ rate limited, bir sonrakine bak
            _groq_key_idx = (_groq_key_idx + 1) % len(GROQ_KEYS)
            attempts += 1
        else:
            # Tüm keyler rate limited
            soonest = min(_groq_rate_limited.values()) if _groq_rate_limited else 0
            wait_sec = max(0, soonest - now)
            logging.warning(f"Tüm Groq keyleri rate limited! En erken {wait_sec:.0f}s sonra serbest.")
            return None

        logging.debug(f"Groq key #{_groq_key_idx + 1}/{len(GROQ_KEYS)} kullanılıyor")
        return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

def groq_mark_rate_limited(wait_seconds=60):
    """Aktif key'i rate limited olarak işaretle, sonraki key'e geç."""
    global _groq_key_idx
    with _groq_key_lock:
        if not GROQ_KEYS: return
        key = GROQ_KEYS[_groq_key_idx % len(GROQ_KEYS)]
        _groq_rate_limited[key] = time.time() + wait_seconds
        _groq_key_idx = (_groq_key_idx + 1) % len(GROQ_KEYS)
        logging.warning(
            f"Groq key #{(_groq_key_idx) % len(GROQ_KEYS) + 1} rate limited "
            f"({wait_seconds}s) → key #{_groq_key_idx + 1} devrede"
        )

# ============================================================
# NEXUS QUANT LAYER v11.0
# ============================================================

# --- SQLite DB ---
db_lock = threading.Lock()

def init_db():
    """Alle Tabellen anlegen."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol       TEXT, direction TEXT, size REAL,
            entry_price  REAL, exit_price REAL,
            sl REAL, tp REAL,
            entry_time   TEXT, exit_time TEXT,
            pnl_eur      REAL, exit_reason TEXT,
            spread_entry REAL, gremium_score TEXT,
            tf_20m TEXT, tf_45m TEXT, tf_2h TEXT,
            adx_value REAL, rsi_value REAL,
            weekday INT, hour INT,
            confidence INT DEFAULT 5,
            macro_regime TEXT DEFAULT 'UNKNOWN',
            fear_greed INT, weather_signal TEXT,
            kelly_pct REAL, sentiment REAL,
            seasonal REAL DEFAULT 1.0,
            status TEXT DEFAULT 'OPEN'
        );
        CREATE TABLE IF NOT EXISTS source_credibility (
            source_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT UNIQUE,
            source_url  TEXT DEFAULT '',
            asset_class TEXT DEFAULT 'ALL',
            total_used  INT DEFAULT 0,
            correct_cnt INT DEFAULT 0,
            score       REAL DEFAULT 0.5,
            blacklisted INT DEFAULT 0,
            last_used   TEXT DEFAULT '',
            notes       TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS gemini_reasoning (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id   INT, timestamp TEXT,
            decision   TEXT, key_factors TEXT,
            sources    TEXT, warnings TEXT,
            confidence INT, macro_regime TEXT,
            fear_greed INT
        );
        CREATE TABLE IF NOT EXISTS asset_learnings (
            symbol              TEXT PRIMARY KEY,
            win_rate_overall    REAL DEFAULT 0.5,
            win_rate_weekend    REAL DEFAULT 0.5,
            win_rate_night      REAL DEFAULT 0.5,
            total_trades        INT  DEFAULT 0,
            total_pnl           REAL DEFAULT 0.0,
            loss_streak_current INT  DEFAULT 0,
            loss_streak_max     INT  DEFAULT 0,
            gemini_notes        TEXT DEFAULT '',
            last_updated        TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS backtest_results (
            bt_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol        TEXT, epic TEXT, run_time TEXT,
            days          INTEGER, resolution TEXT,
            total_trades  INTEGER DEFAULT 0,
            wins          INTEGER DEFAULT 0,
            losses        INTEGER DEFAULT 0,
            win_rate      REAL DEFAULT 0,
            total_pnl     REAL DEFAULT 0,
            avg_win       REAL DEFAULT 0,
            avg_loss      REAL DEFAULT 0,
            max_drawdown  REAL DEFAULT 0,
            details_json  TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS asset_history (
            hist_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT, epic TEXT, resolution TEXT,
            fetched_at TEXT, candle_cnt INTEGER DEFAULT 0,
            data_json  TEXT DEFAULT ''
        );
                CREATE TABLE IF NOT EXISTS gemini_notes (
            note_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            note_type TEXT,
            symbol    TEXT DEFAULT NULL,
            content   TEXT,
            trade_id  INTEGER DEFAULT NULL,
            cycle     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS pattern_learnings (
            pattern_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT,
            symbol       TEXT,
            pattern_desc TEXT,
            success_rate REAL DEFAULT NULL,
            sample_size  INTEGER DEFAULT 1,
            confirmed    INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS cycle_log (
            cycle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            macro_regime TEXT,
            vol_regime  TEXT,
            fear_greed  INTEGER,
            kandidat_cnt INTEGER DEFAULT 0,
            trade_cnt   INTEGER DEFAULT 0,
            gemini_model TEXT DEFAULT '',
            analysis_summary TEXT DEFAULT ''
        );
        """)
        conn.commit()
        conn.close()
    logging.info("SQLite DB hazir: " + DB_FILE)

    # Eski HTML entity'leri DB'de duzelt (&#x27; -> ' gibi)
    try:
        import html as _html_fix
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("SELECT news_id, title FROM news_cache WHERE title LIKE '%&#%'").fetchall()
        for news_id, title in rows:
            clean = _html_fix.unescape(title)
            conn.execute("UPDATE news_cache SET title=? WHERE news_id=?", (clean, news_id))
        if rows:
            logging.info(f"HTML entity duzeltme: {len(rows)} haber temizlendi")
        conn.commit()
        conn.close()
    except Exception as _he:
        logging.debug(f"HTML entity temizleme hatasi: {_he}")

def db_open_trade(symbol, direction, size, entry_price, sl, tp,
                  spread=0, gremium_score="?", tf_20m="?", tf_45m="?", tf_2h="?",
                  adx=0, rsi=50, confidence=5, macro_regime="UNKNOWN",
                  fear_greed=50, weather_signal="", kelly_pct=0.01,
                  sentiment=0.0, seasonal=1.0):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""INSERT INTO trades
            (symbol,direction,size,entry_price,sl,tp,entry_time,
             spread_entry,gremium_score,tf_20m,tf_45m,tf_2h,
             adx_value,rsi_value,weekday,hour,confidence,
             macro_regime,fear_greed,weather_signal,
             kelly_pct,sentiment,seasonal,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'OPEN')""",
            (symbol,direction,size,entry_price,sl,tp,now,
             spread,gremium_score,tf_20m,tf_45m,tf_2h,
             adx,rsi,datetime.now().weekday(),datetime.now().hour,
             confidence,macro_regime,fear_greed,weather_signal,
             kelly_pct,sentiment,seasonal))
        trade_id = c.lastrowid
        conn.commit()
        conn.close()
    logging.info(f"Trade DB: {symbol} {direction} ID={trade_id}")
    return trade_id

def db_close_trade(trade_id, exit_price, pnl_eur, exit_reason):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""UPDATE trades SET exit_price=?,exit_time=?,
            pnl_eur=?,exit_reason=?,status='CLOSED' WHERE trade_id=?""",
            (exit_price, now, pnl_eur, exit_reason, trade_id))
        row = conn.execute("SELECT symbol FROM trades WHERE trade_id=?",
                           (trade_id,)).fetchone()
        conn.commit()
        conn.close()
    if row:
        _update_asset_learnings(row[0])
    logging.info(f"Trade geschlossen: ID={trade_id} PnL={pnl_eur:.2f}EUR ({exit_reason})")

def _update_asset_learnings(symbol):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("""SELECT pnl_eur,weekday,hour FROM trades
            WHERE symbol=? AND status='CLOSED'""", (symbol,)).fetchall()
        conn.close()
    if not rows: return
    total = len(rows)
    wins  = sum(1 for r in rows if r[0] and r[0] > 0)
    pnl   = sum(r[0] for r in rows if r[0])
    wr    = wins/total
    we    = [r for r in rows if r[1] in (5,6)]
    we_wr = sum(1 for r in we if r[0]>0)/len(we) if we else 0.5
    ni    = [r for r in rows if r[2]>=23 or r[2]<6]
    ni_wr = sum(1 for r in ni if r[0]>0)/len(ni) if ni else 0.5
    # Loss streak
    cur = max_s = tmp = 0
    for r in reversed(rows):
        if r[0] and r[0] < 0:
            tmp += 1; max_s = max(max_s, tmp)
        else:
            cur = cur or tmp; tmp = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO asset_learnings
            (symbol,win_rate_overall,win_rate_weekend,win_rate_night,
             total_trades,total_pnl,loss_streak_current,loss_streak_max,last_updated)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(symbol) DO UPDATE SET
            win_rate_overall=excluded.win_rate_overall,
            win_rate_weekend=excluded.win_rate_weekend,
            win_rate_night=excluded.win_rate_night,
            total_trades=excluded.total_trades,
            total_pnl=excluded.total_pnl,
            loss_streak_current=excluded.loss_streak_current,
            loss_streak_max=excluded.loss_streak_max,
            last_updated=excluded.last_updated""",
            (symbol,wr,we_wr,ni_wr,total,pnl,cur,max_s,now))
        conn.commit()
        conn.close()

def db_get_memory_context(limit=25):
    """Letzte N Trades als Kontext fuer Gemini."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("""SELECT symbol,direction,pnl_eur,entry_time,
            gremium_score,macro_regime,status,exit_reason
            FROM trades ORDER BY entry_time DESC LIMIT ?""", (limit,)).fetchall()
        conn.close()
    if not rows:
        return "Henuz trade gecmisi yok."
    lines = []
    for sym,dr,pnl,et,gs,mr,st,er in rows:
        if st == 'OPEN':
            lines.append(f"  ACIK {sym} {dr} | {et[:16]} | Gremium:{gs}")
        elif pnl and pnl > 0:
            lines.append(f"  KAZANC {sym} {dr} | +{pnl:.2f}EUR | {et[:16]} | {mr}")
        else:
            p = f"{pnl:.2f}" if pnl else "?"
            lines.append(f"  KAYIP {sym} {dr} | {p}EUR | {et[:16]} | {mr} | {er}")
    return "\n".join(lines)

def db_get_asset_summary():
    """Asset-Performance fuer Gemini - best_tf dahil."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("""SELECT symbol,win_rate_overall,win_rate_weekend,
            total_trades,total_pnl,loss_streak_current,gemini_notes,
            best_tf,best_tf_wr,best_tf_updated
            FROM asset_learnings ORDER BY total_pnl DESC""").fetchall()
        conn.close()
    if not rows:
        return "Henuz asset istatistigi yok."
    lines = []
    for row in rows:
        sym,wr,wer,tot,pnl,ls,notes = row[0],row[1],row[2],row[3],row[4],row[5],row[6]
        best_tf     = row[7] if len(row) > 7 else ""
        best_tf_wr  = row[8] if len(row) > 8 else 0.0
        best_tf_upd = row[9] if len(row) > 9 else ""
        warn = " KAYIP SERISI!" if (ls and ls >= 2) else ""
        tf_str = f" | BestTF={best_tf}(WR={best_tf_wr:.0%})" if best_tf else ""
        lines.append(
            f"  {sym}: Win%={wr:.0%} WE:{wer:.0%} ({tot}t) PnL:{pnl:.2f}EUR{tf_str}{warn}"
        )
        if notes:
            lines.append(f"    NOT: {notes}")
    return "\n".join(lines)

def db_get_source_scores():
    """Source Scores fuer Gemini."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("""SELECT source_name,score,total_used,blacklisted
            FROM source_credibility ORDER BY score DESC""").fetchall()
        conn.close()
    if not rows:
        return "Henuz kaynak degerlendirmesi yok."
    lines = []
    for name,score,total,bl in rows:
        status = "BLOKLU" if bl else ("COK_IYI" if score>=0.7 else ("IYI" if score>=0.5 else "ZAYIF"))
        lines.append(f"  [{status}] {name}: {score:.2f} ({total} kullanim)")
    return "\n".join(lines)

def db_update_source_score(source_name, was_correct):
    alpha = 0.3
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT score,total_used FROM source_credibility WHERE source_name=?",
                           (source_name,)).fetchone()
        if row:
            new_score = alpha*(1.0 if was_correct else 0.0) + (1-alpha)*row[0]
            new_total = row[1]+1
            bl = 1 if (new_score < 0.3 and new_total >= 8) else 0
            conn.execute("""UPDATE source_credibility SET score=?,total_used=?,
                correct_cnt=correct_cnt+?,blacklisted=?,last_used=?
                WHERE source_name=?""",
                (new_score,new_total,1 if was_correct else 0,bl,now,source_name))
        else:
            s = 0.6 if was_correct else 0.4
            conn.execute("""INSERT INTO source_credibility
                (source_name,score,total_used,correct_cnt,last_used)
                VALUES (?,?,1,?,?)""", (source_name,s,1 if was_correct else 0,now))
        conn.commit()
        conn.close()

def db_save_reasoning(trade_id, decision, key_factors, sources,
                      warnings, confidence, macro_regime, fear_greed):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO gemini_reasoning
            (trade_id,timestamp,decision,key_factors,sources,
             warnings,confidence,macro_regime,fear_greed)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (trade_id,now,decision,
             json.dumps(key_factors, ensure_ascii=False),
             json.dumps(sources, ensure_ascii=False),
             json.dumps(warnings, ensure_ascii=False),
             confidence,macro_regime,fear_greed))
        conn.commit()
        conn.close()

def db_get_full_memory():
    """Vollstaendiges Gedaechtnis fuer Gemini vor jeder Analyse."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        trades   = conn.execute("""SELECT symbol,direction,pnl_eur,entry_time,
            gremium_score,macro_regime,exit_reason,status,confidence,fear_greed
            FROM trades ORDER BY entry_time DESC LIMIT 30""").fetchall()
        assets   = conn.execute("""SELECT symbol,win_rate_overall,win_rate_weekend,
            win_rate_night,total_trades,total_pnl,loss_streak_current,gemini_notes
            FROM asset_learnings ORDER BY total_trades DESC""").fetchall()
        # USER_INFO notlari 48 saat sonra otomatik silinir
        conn.execute("""DELETE FROM gemini_notes
            WHERE note_type='USER_INFO'
            AND timestamp < datetime('now', '-48 hours')""")
        conn.commit()
        notes    = conn.execute("""SELECT timestamp,note_type,symbol,content
            FROM gemini_notes ORDER BY timestamp DESC LIMIT 20""").fetchall()
        patterns = conn.execute("""SELECT symbol,pattern_desc,success_rate,sample_size
            FROM pattern_learnings ORDER BY timestamp DESC LIMIT 15""").fetchall()
        sources  = conn.execute("""SELECT source_name,score,total_used,correct_cnt,blacklisted
            FROM source_credibility ORDER BY score DESC LIMIT 20""").fetchall()
        cycles   = conn.execute("""SELECT timestamp,macro_regime,fear_greed,
            kandidat_cnt,trade_cnt,analysis_summary
            FROM cycle_log ORDER BY timestamp DESC LIMIT 3""").fetchall()
        conn.close()

    L = []
    L.append("=" * 50)
    L.append("NEXUS QUANT FUND - TAM HAFIZA RAPORU")
    L.append("=" * 50)

    L.append("\n[TRADE GECMISI - Son 30]")
    if not trades:
        L.append("  Henuz trade yok.")
    else:
        wins  = sum(1 for t in trades if t[2] and t[2]>0 and t[7]=='CLOSED')
        total = sum(1 for t in trades if t[7]=='CLOSED')
        pnl   = sum(t[2] for t in trades if t[2] and t[7]=='CLOSED')
        L.append(f"  Genel: {wins}/{total} kazanc | Toplam PnL: {pnl:.2f}EUR")
        for t in trades[:10]:
            sym,dr,p,et,gs,mr,er,st,conf,fg = t
            if st=='OPEN':
                L.append(f"  ACIK   {sym:12s} {dr:4s} | {et[:16]} | Conf:{conf}")
            elif p and p>0:
                L.append(f"  KAZANC {sym:12s} {dr:4s} | +{p:.2f}EUR | {et[:16]} | {mr}")
            else:
                L.append(f"  KAYIP  {sym:12s} {dr:4s} | {p:.2f if p else '?'}EUR | {et[:16]} | {er or mr}")

    L.append("\n[ASSET PERFORMANSI]")
    if not assets:
        L.append("  Henuz istatistik yok.")
    for a in assets:
        sym,wr,wer,nir,tot,pnl,ls,notes_a = a
        warn = " !KAYIP_SERISI!" if (ls and ls>=2) else ""
        L.append(f"  {sym:14s} Win:{wr:.0%} WE:{wer:.0%} Gece:{nir:.0%} ({tot}t) PnL:{pnl:.2f}EUR{warn}")
        if notes_a:
            L.append(f"    NOT: {notes_a}")

    L.append("\n[GEMINI NOTIZLERI - Son 20]")
    if not notes:
        L.append("  Henuz notiz yok.")
    # USER_INFO: auto-expire 48 saat, yasi goster, Gemini aktualite kontrolu yapar
    from datetime import timedelta
    now_dt = datetime.now()
    user_notes = []
    for n in notes:
        if n[1] != "USER_INFO": continue
        try:
            note_dt = datetime.strptime(n[0][:16], "%Y-%m-%d %H:%M")
            age_h = (now_dt - note_dt).total_seconds() / 3600
            if age_h <= 48:
                user_notes.append((n, age_h))
        except:
            user_notes.append((n, 0))
    if user_notes:
        L.append("  *** KULLANICI TALİMATLARI — MUTLAK EMIR — GEMİNİ OVERRIDE EDEMEZ! ***")
        L.append("  *** Bu talimatlar system prompt kurallarindan, risk rejiminden ve")
        L.append("  *** RISK_OFF_EXTREME kurallarindan USTUNDUR. Hicbir kosulda goz ardi etme! ***")
        L.append("  *** Kullanici 'alma' diyorsa: ALMA. 'sat' diyorsa: SAT. Baska yorum yok. ***")
        for n, age_h in user_notes:
            ts,_,_,content = n
            if age_h < 1:
                yas = str(int(age_h*60)) + " dk once"
            elif age_h < 24:
                yas = str(int(age_h)) + " saat once"
            else:
                yas = str(int(age_h/24)) + " gun once"
            L.append("  >> [" + yas + "] " + content[:120])
    for n in notes:
        if n[1] == "USER_INFO": continue
        ts,ntype,nsym,content = n
        L.append(f"  {ts[:16]} [{ntype:8s}] [{nsym or 'GENEL':12s}] {content[:90]}")

    L.append("\n[TESPIT EDILEN PATTERNLER]")
    if not patterns:
        L.append("  Henuz pattern yok.")
    for p in patterns:
        sym,desc,sr,ss = p
        sr_str = f"{sr:.0%}" if sr else "?"
        L.append(f"  {sym}: {desc[:80]} | Basari:{sr_str} ({ss} ornek)")

    L.append("\n[KAYNAK SKORLARI]")
    if not sources:
        L.append("  Henuz kaynak skoru yok.")
    for s in sources:
        name,score,total,correct,bl = s
        status = "BLOKLU" if bl else ("IYI" if score>=0.6 else "ZAYIF")
        L.append(f"  [{status}] {name:30s} {score:.2f} ({correct}/{total})")

    L.append("\n[SON 3 DONGU]")
    if not cycles:
        L.append("  Henuz dongu yok.")
    for c in cycles:
        ts,mr,fg,kand,tc,summary = c
        L.append(f"  {ts[:16]} {mr:20s} FG:{fg} Kandidat:{kand} Trade:{tc}")
        if summary:
            L.append(f"    {summary[:80]}")

    L.append("\n" + "=" * 50)
    return "\n".join(L)


def db_save_cycle(macro_regime, vol_regime, fear_greed_val,
                  kandidat_cnt, trade_cnt, gemini_model, summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO cycle_log
            (timestamp,macro_regime,vol_regime,fear_greed,
             kandidat_cnt,trade_cnt,gemini_model,analysis_summary)
            VALUES (?,?,?,?,?,?,?,?)""",
            (now,macro_regime,vol_regime,fear_greed_val,
             kandidat_cnt,trade_cnt,gemini_model,summary[:500]))
        conn.commit()
        conn.close()


def db_gemini_write(note_type, content, symbol=None, trade_id=None, cycle=0):
    """Gemini'nin serbest not yazmasi."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO gemini_notes
            (timestamp,note_type,symbol,content,trade_id,cycle)
            VALUES (?,?,?,?,?,?)""",
            (now,note_type,symbol,content[:1000],trade_id,cycle))
        conn.commit()
        conn.close()
    logging.info(f"Gemini DB: {note_type}|{symbol or 'GENEL'}|{content[:50]}")


def db_gemini_pattern(symbol, pattern_desc, success_rate=None, sample_size=1):
    """Pattern kaydet veya guncelle."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        ex = conn.execute("""SELECT pattern_id,sample_size FROM pattern_learnings
            WHERE symbol=? AND pattern_desc=?""",
            (symbol,pattern_desc[:200])).fetchone()
        if ex:
            conn.execute("""UPDATE pattern_learnings SET
                sample_size=?,success_rate=?,timestamp=? WHERE pattern_id=?""",
                (ex[1]+sample_size,success_rate,now,ex[0]))
        else:
            conn.execute("""INSERT INTO pattern_learnings
                (timestamp,symbol,pattern_desc,success_rate,sample_size)
                VALUES (?,?,?,?,?)""",
                (now,symbol,pattern_desc[:500],success_rate,sample_size))
        conn.commit()
        conn.close()
    logging.info(f"Gemini PATTERN: {symbol}|{pattern_desc[:50]}")


def db_update_asset_note(symbol, note):
    """Asset notu guncelle."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO asset_learnings (symbol,gemini_notes,last_updated)
            VALUES (?,?,?)
            ON CONFLICT(symbol) DO UPDATE SET
            gemini_notes=excluded.gemini_notes,
            last_updated=excluded.last_updated""",
            (symbol,note[:500],now))
        conn.commit()
        conn.close()


def parse_and_execute_db_commands(analysis_text, cycle_counter=0):
    """
    Gemini analysis metnindeki DB komutlarini bulup calistirir.
    DB_NOTE | DB_WARN | DB_PATTERN | DB_SOURCE | DB_ASSET_NOTE | DB_WRITE
    """
    import json as _json
    commands_executed = 0
    pattern = re.compile(
        r'(DB_WRITE|DB_NOTE|DB_LEARN|DB_WARN|DB_SOURCE|DB_PATTERN|DB_ASSET_NOTE)'
        r'\s*:\s*(\{[^}]+\})',
        re.DOTALL
    )
    for match in pattern.finditer(analysis_text):
        cmd = match.group(1)
        raw = match.group(2)
        try:
            data = _json.loads(raw)
        except Exception:
            data = {}
            for field in ['symbol','content','note','pattern','source',
                          'correct','rate','warning']:
                fm = re.search(rf'"{field}"\s*:\s*"([^"]*)"', raw)
                if fm: data[field] = fm.group(1)
                else:
                    fm2 = re.search(rf'"{field}"\s*:\s*([^\s,}}]+)', raw)
                    if fm2: data[field] = fm2.group(1)
        try:
            if cmd in ('DB_NOTE', 'DB_WARN'):
                sym = data.get('symbol')
                cnt = data.get('content') or data.get('warning','')
                if cnt:
                    db_gemini_write('WARN' if cmd=='DB_WARN' else 'NOTE',
                                    cnt, sym, cycle=cycle_counter)
                    commands_executed += 1
            elif cmd in ('DB_LEARN', 'DB_PATTERN'):
                sym  = data.get('symbol','GENEL')
                patt = data.get('pattern', data.get('content',''))
                rate = float(data.get('rate',0)) if data.get('rate') else None
                if patt:
                    db_gemini_pattern(sym, patt, rate)
                    commands_executed += 1
            elif cmd == 'DB_SOURCE':
                src_name = data.get('source','')
                correct  = str(data.get('correct','true')).lower() in ('true','1','yes')
                if src_name:
                    db_update_source_score(src_name, correct)
                    commands_executed += 1
            elif cmd == 'DB_ASSET_NOTE':
                sym  = data.get('symbol','')
                note = data.get('note', data.get('content',''))
                if sym and note:
                    db_update_asset_note(sym, note)
                    commands_executed += 1
            elif cmd == 'DB_WRITE':
                cnt = data.get('content', data.get('decision',''))
                sym = data.get('symbol')
                ntp = data.get('type','WRITE')
                if cnt:
                    db_gemini_write(ntp, cnt, sym, cycle=cycle_counter)
                    commands_executed += 1
        except Exception as e:
            logging.warning(f"DB Cmd Hatasi [{cmd}]: {e}")
    if commands_executed > 0:
        logging.info(f"Gemini {commands_executed} DB komutu yazdirdi")
    return commands_executed

def fetch_asset_history(symbol, epic, resolution="HOUR_4", days=30):
    """Historische Kerzen von Capital.com holen und in DB speichern."""
    cpd = {"MINUTE_30":48,"HOUR":24,"HOUR_4":6,"DAY":1}.get(resolution,6)
    max_c = min(days * cpd, 999)
    h = capital_session.get_headers()
    if not h: return None
    try:
        url = f"{CAPITAL_URL}/prices/{epic}?resolution={resolution}&max={max_c}"
        r = requests.get(url, headers=h, timeout=30)
        if r.status_code != 200: return None
        candles = []
        for p in r.json().get('prices', []):
            c  = p.get('closePrice',{}).get('bid')
            hv = p.get('highPrice', {}).get('bid')
            lv = p.get('lowPrice',  {}).get('bid')
            ov = p.get('openPrice', {}).get('bid')
            if c and hv and lv:
                candles.append({
                    "t": p.get('snapshotTimeUTC',''),
                    "o": float(ov) if ov else float(c),
                    "h": float(hv), "l": float(lv), "c": float(c)
                })
        if not candles: return None
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("""INSERT INTO asset_history
                (symbol,epic,resolution,fetched_at,candle_cnt,data_json)
                VALUES (?,?,?,?,?,?)""",
                (symbol,epic,resolution,now,len(candles),
                 json.dumps(candles[-200:])))
            conn.commit()
            conn.close()
        logging.info(f"History: {symbol} {resolution} {len(candles)} mum")
        return candles
    except Exception as e:
        logging.warning(f"History hatasi {symbol}: {e}")
        return None


def get_asset_history_summary(symbol, resolution="HOUR_4"):
    """DB'den kaydedilmis history ozetini don."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("""SELECT data_json,fetched_at,candle_cnt
            FROM asset_history WHERE symbol=? AND resolution=?
            ORDER BY fetched_at DESC LIMIT 1""",
            (symbol, resolution)).fetchone()
        conn.close()
    if not row or not row[0]: return None
    try:
        candles = json.loads(row[0])
    except:
        return None
    if len(candles) < 10: return None
    closes = [c['c'] for c in candles]
    highs  = [c['h'] for c in candles]
    lows   = [c['l'] for c in candles]
    price  = closes[-1]
    ref    = closes[-30] if len(closes)>=30 else closes[0]
    chg    = (price-ref)/ref*100 if ref else 0
    ma20   = sum(closes[-20:])/20 if len(closes)>=20 else None
    ma50   = sum(closes[-50:])/50 if len(closes)>=50 else None
    boll   = berechne_bollinger(closes, 20)
    fib    = berechne_fibonacci(highs, lows, closes, 50)
    L = [
        f"Asset:{symbol} Res:{resolution} Guncelleme:{row[1][:16]} ({row[2]} mum)",
        f"Fiyat:{price:.5f} | 30-Mum Degisim:{chg:+.2f}%",
        f"MA20:{ma20:.5f}" if ma20 else "MA20:-",
        f"MA50:{ma50:.5f}" if ma50 else "MA50:-",
    ]
    if boll:
        L.append(f"BB: Alt={boll['lower']:.5f} Orta={boll['middle']:.5f} "
                 f"Ust={boll['upper']:.5f} Poz={boll['position']}")
    if fib:
        L.append(f"FIB: 38.2%={fib['levels']['38.2%']:.5f} "
                 f"61.8%={fib['levels']['61.8%']:.5f} "
                 f"YakinSev={fib['nearest_level']}@{fib['distance_pct']:.1f}%")
    return "\n".join(L)


def run_backtest(symbol, epic, days=200):
    """200 gun geriye giderek 3 timeframe'de backtest calistir."""
    logging.info(f"Backtest: {symbol} {days} gun")
    results = {}
    for resolution, cpd, label in [
        ("MINUTE_30",48,"30dk"), ("HOUR",24,"1sa"), ("HOUR_4",6,"4sa")
    ]:
        candles = fetch_asset_history(symbol, epic, resolution, days)
        if not candles or len(candles) < 50:
            results[label] = {"error":"Veri yetersiz"}
            continue
        closes = [c['c'] for c in candles]
        highs  = [c['h'] for c in candles]
        lows   = [c['l'] for c in candles]
        times  = [c['t'] for c in candles]
        trades = []
        i = 55
        while i < len(closes)-5:
            cs = closes[:i]; hs = highs[:i]; ls = lows[:i]
            ma9  = sum(cs[-9:])/9   if len(cs)>=9  else None
            ma26 = sum(cs[-26:])/26 if len(cs)>=26 else None
            if not ma9 or not ma26: i+=1; continue
            ma_sig = "BUY" if ma9>ma26 else "SELL"
            adx = berechne_adx(hs[-15:],ls[-15:],cs[-15:])
            rsi = berechne_rsi(cs[-15:])
            score = (1 if ma_sig!="NOTR" else 0)
            score += (1 if adx>20 else 0)
            score += (1 if (ma_sig=="BUY" and rsi<70) or (ma_sig=="SELL" and rsi>30) else 0)
            boll = berechne_bollinger(cs,20)
            if boll:
                if ma_sig=="BUY" and boll["position"] in ("NEAR_LOWER","SQUEEZE"): score+=1
                if ma_sig=="SELL" and boll["position"] in ("NEAR_UPPER","SQUEEZE"): score+=1
            fib = berechne_fibonacci(hs,ls,cs,50)
            if fib and fib["nearest_level"] in ("38.2%","50.0%","61.8%") and fib["distance_pct"]<=1.5: score+=1
            if score>=3:
                future = closes[i:i+5]
                if len(future)<3: i+=1; continue
                ep = closes[i]; xp = future[-1]
                pnl = (xp-ep)/ep*100 if ma_sig=="BUY" else (ep-xp)/ep*100
                trades.append({"time":times[i][:16] if i<len(times) else str(i),
                               "signal":ma_sig,"score":score,
                               "entry":round(ep,5),"exit":round(xp,5),
                               "pnl":round(pnl,3),"win":pnl>0})
                i+=5
            else: i+=1
        if not trades: results[label]={"error":"Sinyal yok"}; continue
        wins = sum(1 for t in trades if t['win'])
        losses = len(trades)-wins
        wr = wins/len(trades)
        aw = sum(t['pnl'] for t in trades if t['win'])/(wins or 1)
        al = sum(t['pnl'] for t in trades if not t['win'])/(losses or 1)
        tpnl = sum(t['pnl'] for t in trades)
        cu=pk=dd=0
        for t in trades:
            cu+=t['pnl']
            if cu>pk: pk=cu
            if pk-cu>dd: dd=pk-cu
        results[label]={"total":len(trades),"wins":wins,"losses":losses,
                        "win_rate":round(wr,3),"avg_win":round(aw,3),
                        "avg_loss":round(al,3),"total_pnl":round(tpnl,3),
                        "max_dd":round(dd,3)}
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("""INSERT INTO backtest_results
                (symbol,epic,run_time,days,resolution,total_trades,wins,losses,
                 win_rate,total_pnl,avg_win,avg_loss,max_drawdown,details_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (symbol,epic,now,days,resolution,len(trades),wins,losses,
                 wr,tpnl,aw,al,dd,json.dumps(trades[-10:])))
            conn.commit()
            conn.close()
    return results


def format_backtest_report(symbol, results, days):
    L = [f"NEXUS BACKTEST: {symbol} | {days} gün","="*40]
    for tf,r in results.items():
        L.append(f"\n[{tf}]")
        if "error" in r: L.append(f"  Hata: {r['error']}"); continue
        L.append(f"  Sinyal:{r['total']} | K/Z:{r['wins']}/{r['losses']}")
        L.append(f"  WinRate:{r['win_rate']:.1%} | AvgKazanc:{r['avg_win']:+.2f}% | AvgKayip:{r['avg_loss']:+.2f}%")
        L.append(f"  ToplamPnL:{r['total_pnl']:+.2f}% | MaxDD:-{r['max_dd']:.2f}%")
        if r['win_rate']>=0.55 and r['avg_win']>abs(r['avg_loss']):
            L.append("  >> GÜÇLÜ STRATEJİ")
        elif r['win_rate']>=0.45:
            L.append("  >> ORTA - iyileştirme gerekli")
        else:
            L.append("  >> ZAYIF - bu zaman dilimi dikkat!")
    L.append("\nDetaylar veritabanına kaydedildi.")
    return "\n".join(L)


def parse_db_fetch_commands(analysis_text):
    """DB_FETCH komutlarini isle ve history cek."""
    import json as _j
    fetched = []
    for match in re.finditer(r'DB_FETCH\s*:\s*(\{[^}]+\})', analysis_text, re.DOTALL):
        raw = match.group(1)
        try: data = _j.loads(raw)
        except:
            data = {}
            for f in ['symbol','resolution','days']:
                fm = re.search(rf'"{f}"\s*:\s*"?([^",}}]+)"?', raw)
                if fm: data[f] = fm.group(1).strip()
        sym  = data.get('symbol','').upper()
        res  = data.get('resolution','HOUR_4')
        days = int(data.get('days',30))
        if sym and sym in MARKET_CONFIG:
            epic = MARKET_CONFIG[sym]['epic']
            c = fetch_asset_history(sym, epic, res, days)
            if c: fetched.append({"symbol":sym,"resolution":res,"candles":len(c)})
    return fetched


def _format_deep_dive(kandidaten):
    """Kandidat assetler icin mevcut history ozeti."""
    if not kandidaten: return "Kandidat yok."
    lines = []
    for sym in list(kandidaten.keys())[:3]:
        s4h = get_asset_history_summary(sym,"HOUR_4")
        s1h = get_asset_history_summary(sym,"HOUR")
        if s4h or s1h:
            lines.append(f"[{sym}] Kayitli History:")
            if s4h: lines.append("  "+s4h.replace("\n","\n  "))
            if s1h: lines.append("  "+s1h.replace("\n","\n  "))
        else:
            lines.append(f'[{sym}] History yok. Almak icin:\nDB_FETCH: {{"symbol": "{sym}", "resolution": "HOUR_4", "days": 30}}')
    return "\n".join(lines) if lines else "Deep Dive yok."





# --- Data APIs ---
_api_cache = {}
_api_cache_lock = threading.Lock()

def _cached(key, ttl_min, fn):
    with _api_cache_lock:
        if key in _api_cache:
            v, ts = _api_cache[key]
            if (datetime.now()-ts).seconds < ttl_min*60:
                return v
    try:
        v = fn()
        with _api_cache_lock:
            _api_cache[key] = (v, datetime.now())
        return v
    except Exception as e:
        logging.warning(f"API [{key}] hatasi: {e}")
        return None

def get_fear_greed():
    def fetch():
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8)
        if r.status_code == 200:
            d = r.json()["data"][0]
            return {"value": int(d["value"]), "label": d["value_classification"]}
        return None
    return _cached("fg", 60, fetch) or {"value": 50, "label": "Neutral"}

def get_weather_signal(asset_class="AGRAR"):
    def fetch_agrar():
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=39.1&longitude=-94.6"
            "&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max"
            "&forecast_days=3&timezone=America/Chicago", timeout=8)
        if r.status_code == 200:
            d = r.json()["daily"]
            t = sum(d["temperature_2m_max"][:3])/3
            rain = sum(d["precipitation_sum"][:3])
            wind = max(d["wind_speed_10m_max"][:3])
            sig = "NORMAL"; notes = []
            if t > 38:    sig="HITZE_STRESS"; notes.append(f"Sicaklik:{t:.0f}C")
            elif t < -5:  sig="DON_STRESS";   notes.append(f"Don:{t:.0f}C")
            if rain < 5:  notes.append("Kuraklik")
            elif rain>50: sig="YAGMUR_STRESS"; notes.append(f"Yagis:{rain:.0f}mm")
            if wind > 60: notes.append(f"Firtina:{wind:.0f}km/h")
            return {"signal": sig, "notes": " | ".join(notes) or "Normal"}
        return {"signal": "UNKNOWN", "notes": ""}
    def fetch_energy():
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=57.0&longitude=2.0"
            "&daily=temperature_2m_max,wind_speed_10m_max"
            "&forecast_days=3&timezone=Europe/London", timeout=8)
        if r.status_code == 200:
            d = r.json()["daily"]
            t = sum(d["temperature_2m_max"][:3])/3
            wind = max(d["wind_speed_10m_max"][:3])
            sig = "NORMAL"; notes = []
            if wind > 80: sig="STORM"; notes.append(f"Firtina:{wind:.0f}km/h")
            if t < 0:     notes.append(f"Soguk:{t:.0f}C-talep_artar")
            return {"signal": sig, "notes": " | ".join(notes) or "Normal"}
        return {"signal": "UNKNOWN", "notes": ""}
    fn = fetch_agrar if asset_class == "AGRAR" else fetch_energy
    return _cached(f"wx_{asset_class}", 180, fn) or {"signal": "UNKNOWN", "notes": ""}

def get_economic_calendar():
    def fetch():
        now = datetime.now()
        first = datetime(now.year, now.month, 1)
        fri_off = (4 - first.weekday()) % 7
        nfp = first + timedelta(days=fri_off)
        if nfp < now: nfp += timedelta(days=7)
        tue_off = (1 - first.weekday()) % 7 + 7
        cpi = first + timedelta(days=tue_off)
        if cpi < now: cpi += timedelta(days=28)
        events = [
            {"event":"NFP",  "days":(nfp-now).days, "impact":"HIGH"},
            {"event":"CPI",  "days":(cpi-now).days, "impact":"HIGH"},
        ]
        events.sort(key=lambda x: x["days"])
        n = events[0]
        return {"next_event": n["event"], "days_until": n["days"], "all": events}
    return _cached("econ", 360, fetch) or {"next_event":"UNKNOWN","days_until":99}



# ============================================================
# ALTERNATIVE DATA SIGNALS
# ============================================================

# --- Cargo Airlines ICAO Prefixes ---
CARGO_AIRLINES = {
    # Amerika
    "UPS":  ["UPS", "N"],        # UPS Airlines
    "FDX":  ["FDX", "N"],        # FedEx
    "ABX":  ["ABX"],             # ABX Air
    "GTI":  ["GTI"],             # Atlas Air
    # Europa
    "DHL":  ["DHK","DHL","BCS"], # DHL Air
    "CLX":  ["CLX"],             # Cargolux
    "MSC":  ["MSC"],             # Air Belgium Cargo
    "LCI":  ["LCI"],             # Lufthansa Cargo
    # Asya / Çin
    "CCA":  ["CCA","B-"],        # Air China Cargo
    "CSN":  ["CSN"],             # China Southern Cargo
    "SF":   ["CSS","B-"],        # SF Airlines (JD.com/Cainiao)
    "YTO":  ["YTO"],             # YTO Cargo (Alibaba)
    "ZTO":  ["ZTO"],             # ZTO Express
    # Japonya
    "NCA":  ["NCA","JA"],        # Nippon Cargo Airlines
    # Hindistan
    "BLU":  ["BLU","VT"],        # Blue Dart (Amazon India/Flipkart)
    # Güney Kore
    "KAL":  ["KAL","HL"],        # Korean Air Cargo (Coupang)
}

# Önemli liman bölgeleri koordinatları (enlem/boylam kutusu)
SHIP_REGIONS = {
    "PERSIAN_GULF": {  # OIL_BRENT
        "min_lat": 23.0, "max_lat": 30.5,
        "min_lon": 48.0, "max_lon": 60.0,
        "signal": "OIL_BRENT", "type": "TANKER"
    },
    "STRAIT_MALACCA": {  # Asya ticaret yolu
        "min_lat": 1.0, "max_lat": 6.5,
        "min_lon": 98.0, "max_lon": 105.0,
        "signal": "RISK_ON", "type": "CONTAINER"
    },
    "SOUTH_CHINA_SEA": {  # Çin ihracatı
        "min_lat": 15.0, "max_lat": 25.0,
        "min_lon": 110.0, "max_lon": 122.0,
        "signal": "RISK_ON", "type": "CONTAINER"
    },
    "NORTH_SEA": {  # Kuzey Denizi Brent
        "min_lat": 55.0, "max_lat": 62.0,
        "min_lon": 0.0,  "max_lon": 8.0,
        "signal": "NATURAL_GAS", "type": "TANKER"
    },
    "GULF_OF_MEXICO": {  # ABD petrolu
        "min_lat": 22.0, "max_lat": 30.0,
        "min_lon": -97.0,"max_lon": -82.0,
        "signal": "OIL_BRENT", "type": "TANKER"
    },
    "ROTTERDAM": {  # Avrupa liman
        "min_lat": 51.5, "max_lat": 52.5,
        "min_lon": 3.5,  "max_lon": 5.5,
        "signal": "COPPER", "type": "BULK"
    },
    "SHANGHAI": {  # Çin ihracat merkezi
        "min_lat": 30.0, "max_lat": 32.0,
        "min_lon": 121.0,"max_lon": 123.0,
        "signal": "RISK_ON", "type": "CONTAINER"
    },
}


def get_cargo_flight_signal():
    """
    OpenSky Network API - ücretsiz cargo uçuş sayacı.
    UPS/FedEx/DHL/Cainiao/SF Express uçuşlarını sayar.
    
    Yorum:
    - Çok uçuş = ekonomi aktif = RISK_ON
    - Az uçuş = durgunluk = RISK_OFF
    
    ENV: OPENSKY_USER, OPENSKY_PASS (opensky-network.org)
    """
    def fetch():
        try:
            # Tüm aktif uçuşları çek (anonim de çalışır ama sınırlı)
            auth = None
            if OPENSKY_USER and OPENSKY_PASS:
                auth = (OPENSKY_USER, OPENSKY_PASS)

            r = requests.get(
                "https://opensky-network.org/api/states/all",
                auth=auth,
                timeout=15,
                headers={"User-Agent": "NEXUS-CEO-Bot/1.0"}
            )

            if r.status_code != 200:
                return {"signal": "UNKNOWN", "total": 0,
                        "cargo_count": 0, "notes": f"API {r.status_code}"}

            states = r.json().get("states", []) or []

            # Cargo uçuş sayısı
            cargo_count = 0
            by_airline   = {}
            for s in states:
                if not s or len(s) < 2: continue
                callsign = str(s[1] or "").strip().upper()
                for airline, prefixes in CARGO_AIRLINES.items():
                    if any(callsign.startswith(p) for p in prefixes):
                        cargo_count += 1
                        by_airline[airline] = by_airline.get(airline, 0) + 1
                        break

            total = len(states)

            # Sinyal yorumu
            # Normal cargo oranı ~%8-12 toplam uçuşlar içinde
            cargo_pct = cargo_count / total * 100 if total > 0 else 0

            if cargo_pct > 15:
                signal = "CARGO_SURGE"    # Olağandışı yüksek = ekonomi patlıyor
                trend  = "RISK_ON"
            elif cargo_pct > 10:
                signal = "CARGO_HIGH"     # Yüksek aktivite
                trend  = "RISK_ON"
            elif cargo_pct > 6:
                signal = "CARGO_NORMAL"   # Normal
                trend  = "NEUTRAL"
            elif cargo_pct > 3:
                signal = "CARGO_LOW"      # Düşük aktivite
                trend  = "RISK_OFF"
            else:
                signal = "CARGO_MINIMAL"  # Çok düşük = durgunluk
                trend  = "RISK_OFF"

            # En aktif havayolları
            top3 = sorted(by_airline.items(), key=lambda x: -x[1])[:3]
            top3_str = " | ".join([f"{k}:{v}" for k,v in top3])

            return {
                "signal":      signal,
                "trend":       trend,
                "total":       total,
                "cargo_count": cargo_count,
                "cargo_pct":   round(cargo_pct, 1),
                "top_airlines": top3_str,
                "notes":       f"Toplam:{total} | Cargo:{cargo_count} (%{cargo_pct:.1f}) | {top3_str}"
            }

        except Exception as e:
            logging.debug(f"Cargo flight signal: {e}")
            return {"signal": "UNKNOWN", "trend": "NEUTRAL",
                    "total": 0, "cargo_count": 0, "cargo_pct": 0,
                    "top_airlines": "", "notes": f"Hata: {e}"}

    return _cached("cargo_flight", 60, fetch) or {
        "signal": "UNKNOWN", "trend": "NEUTRAL",
        "cargo_count": 0, "notes": "Veri yok"
    }


def get_ship_traffic_signal():
    """
    AISHub.net API - ücretsiz gemi takip.
    Tanker, konteyner, bulk carrier sayar.
    
    ENV: AISHUB_USER, AISHUB_PASS (aishub.net)
    Hesap yoksa: kısmi veri döner (genel toplam)
    """
    def fetch():
        results = {}

        for region_name, region in SHIP_REGIONS.items():
            try:
                if AISHUB_USER and AISHUB_PASS:
                    # AISHub JSON API
                    url = (
                        f"https://data.aishub.net/ws.php"
                        f"?username={AISHUB_USER}"
                        f"&format=1&output=json"
                        f"&latmin={region['min_lat']}&latmax={region['max_lat']}"
                        f"&lonmin={region['min_lon']}&lonmax={region['max_lon']}"
                    )
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        ships = data[1] if len(data) > 1 else []

                        # Gemi tipi filtrele
                        # AIS Ship Type: 80-89=Tanker, 70-79=Cargo, 71=Bulk
                        tankers    = sum(1 for s in ships
                                        if 80 <= int(s.get("SHIPTYPE",0) or 0) <= 89)
                        containers = sum(1 for s in ships
                                        if 70 <= int(s.get("SHIPTYPE",0) or 0) <= 79)
                        total      = len(ships)

                        results[region_name] = {
                            "total":      total,
                            "tankers":    tankers,
                            "containers": containers,
                            "signal":     region["signal"],
                            "type":       region["type"]
                        }
                else:
                    # AISHub hesabı yoksa VesselFinder public endpoint dene
                    results[region_name] = {
                        "total": 0, "tankers": 0, "containers": 0,
                        "signal": region["signal"],
                        "notes": "AISHUB_USER gerekli"
                    }

            except Exception as e:
                logging.debug(f"Ship traffic {region_name}: {e}")
                results[region_name] = {
                    "total": 0, "signal": region["signal"],
                    "notes": str(e)[:50]
                }

        # Genel sinyal yorumu
        persian_gulf = results.get("PERSIAN_GULF", {})
        malacca      = results.get("STRAIT_MALACCA", {})
        shanghai     = results.get("SHANGHAI", {})

        oil_signal   = "BULLISH" if persian_gulf.get("tankers", 0) > 20 else "NEUTRAL"
        trade_signal = "RISK_ON" if (malacca.get("total", 0) > 50 or
                                      shanghai.get("total", 0) > 30) else "NEUTRAL"

        return {
            "regions":     results,
            "oil_signal":  oil_signal,
            "trade_signal": trade_signal,
            "notes":       (
                f"PersKörf:{persian_gulf.get('tankers',0)} tanker | "
                f"Malakka:{malacca.get('total',0)} gemi | "
                f"Şangay:{shanghai.get('total',0)} gemi"
            )
        }

    return _cached("ship_traffic", 120, fetch) or {
        "regions": {}, "oil_signal": "UNKNOWN",
        "trade_signal": "NEUTRAL", "notes": "Veri yok"
    }


def get_baltic_dry_index():
    """
    Baltic Dry Index - küresel deniz taşımacılığı maliyet endeksi.
    Stooq.com'dan ücretsiz veri çeker (kısmi).
    
    BDI Yorumu:
    > 2000: Güçlü küresel talep = RISK_ON / COPPER/ALUMINUM BUY
    1000-2000: Normal
    < 1000: Zayıf talep = RISK_OFF
    """
    def fetch():
        try:
            # Stooq.com BDI verisi
            r = requests.get(
                "https://stooq.com/q/d/l/?s=bdi&i=d",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if r.status_code == 200:
                lines = r.text.strip().splitlines()
                if len(lines) >= 2:
                    last = lines[-1].split(",")
                    if len(last) >= 5:
                        bdi_val = float(last[4])  # Close price

                        if bdi_val > 2500:
                            signal = "VERY_BULLISH"
                            trend  = "RISK_ON"
                            note   = "Küresel talep çok güçlü"
                        elif bdi_val > 2000:
                            signal = "BULLISH"
                            trend  = "RISK_ON"
                            note   = "Küresel talep güçlü"
                        elif bdi_val > 1500:
                            signal = "NEUTRAL_HIGH"
                            trend  = "NEUTRAL"
                            note   = "Normal - üst bant"
                        elif bdi_val > 1000:
                            signal = "NEUTRAL"
                            trend  = "NEUTRAL"
                            note   = "Normal"
                        elif bdi_val > 600:
                            signal = "BEARISH"
                            trend  = "RISK_OFF"
                            note   = "Zayıf küresel talep"
                        else:
                            signal = "VERY_BEARISH"
                            trend  = "RISK_OFF"
                            note   = "Küresel talep çok zayıf"

                        return {
                            "value":  int(bdi_val),
                            "signal": signal,
                            "trend":  trend,
                            "notes":  f"BDI:{int(bdi_val)} - {note}"
                        }

            # Fallback: Investing.com RSS
            r2 = requests.get(
                "https://www.investing.com/rss/news_69.rss",
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            return {
                "value":  0,
                "signal": "UNKNOWN",
                "trend":  "NEUTRAL",
                "notes":  "BDI verisi alınamadı"
            }

        except Exception as e:
            logging.debug(f"Baltic Dry Index: {e}")
            return {"value": 0, "signal": "UNKNOWN",
                    "trend": "NEUTRAL", "notes": f"Hata: {e}"}

    return _cached("bdi", 240, fetch) or {
        "value": 0, "signal": "UNKNOWN",
        "trend": "NEUTRAL", "notes": "Veri yok"
    }


def get_ecommerce_signal():
    """
    E-Ticaret sinyal endeksi.
    Alibaba, JD.com, Amazon, Flipkart, Coupang, Lazada haberlerini
    news_cache DB'den çeker ve cargo/lojistik sinyalleriyle birleştirir.
    """
    try:
        ecom_keywords = [
            "alibaba", "jd.com", "jingdong", "amazon",
            "flipkart", "coupang", "lazada", "shopee",
            "tokopedia", "rakuten", "zalando", "otto",
            "logistics", "shipping", "delivery", "cargo",
            "supply chain", "tedarik zinciri", "lojistik"
        ]

        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            cutoff = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            try:
                news = conn.execute("""
                    SELECT title, sentiment, sentiment_label
                    FROM news_cache
                    WHERE published_at >= ?
                    LIMIT 100
                """, (cutoff,)).fetchall()
            except:
                news = []
            conn.close()

        # E-ticaret haberlerini filtrele
        ecom_news = [
            n for n in news
            if any(kw in n[0].lower() for kw in ecom_keywords)
        ]

        if not ecom_news:
            return {
                "signal": "NO_DATA",
                "trend":  "NEUTRAL",
                "notes":  "E-ticaret haberi yok (news_cache boş olabilir)"
            }

        avg_sent  = sum(n[1] for n in ecom_news) / len(ecom_news)
        bull_cnt  = sum(1 for n in ecom_news if n[1] > 0.2)
        bear_cnt  = sum(1 for n in ecom_news if n[1] < -0.2)

        if avg_sent > 0.3:
            signal = "ECOM_BULLISH"
            trend  = "RISK_ON"
        elif avg_sent > 0:
            signal = "ECOM_POSITIVE"
            trend  = "NEUTRAL"
        elif avg_sent > -0.3:
            signal = "ECOM_NEGATIVE"
            trend  = "NEUTRAL"
        else:
            signal = "ECOM_BEARISH"
            trend  = "RISK_OFF"

        return {
            "signal":    signal,
            "trend":     trend,
            "avg_sent":  round(avg_sent, 2),
            "bull_cnt":  bull_cnt,
            "bear_cnt":  bear_cnt,
            "news_cnt":  len(ecom_news),
            "notes":     (f"E-ticaret:{len(ecom_news)} haber | "
                         f"Bullish:{bull_cnt} Bearish:{bear_cnt} | "
                         f"Ort.Sentiment:{avg_sent:+.2f}")
        }

    except Exception as e:
        logging.debug(f"Ecommerce signal: {e}")
        return {"signal": "UNKNOWN", "trend": "NEUTRAL", "notes": str(e)}




# ============================================================
# KÜRESEL HAVA + DOĞAL AFET + GOOGLE TRENDS
# ============================================================

COMMODITY_WEATHER_ZONES = {
    "WHEAT":       {"lat": 51.0,  "lon": 55.0,  "label": "Rusya/Ukrayna bugday"},
    "CORN":        {"lat": 41.5,  "lon": -93.0, "label": "ABD misir kusagi"},
    "SOYBEANS":    {"lat": -15.0, "lon": -54.0, "label": "Brezilya soya"},
    "COFFEE":      {"lat": -21.0, "lon": -45.0, "label": "Brezilya kahve"},
    "SUGAR":       {"lat": -22.0, "lon": -47.5, "label": "Brezilya sekerkami"},
    "COTTON":      {"lat": 33.0,  "lon": -90.0, "label": "ABD pamuk kusagi"},
    "COCOA":       {"lat": 7.0,   "lon": -5.0,  "label": "Fildisi Sahili kakao"},
    "NATURAL_GAS": {"lat": 57.0,  "lon": 2.0,   "label": "Kuzey Denizi"},
    "OIL_BRENT":   {"lat": 29.0,  "lon": 48.0,  "label": "Korfez bolge"},
    "COPPER":      {"lat": -33.0, "lon": -71.0, "label": "Sili bakir madenleri"},
    "GOLD":        {"lat": 26.5,  "lon": 30.5,  "label": "Misir-Etiyopya"},
}


def get_global_commodity_weather():
    """Tum emtia bolgeleri icin hava durumu sinyali."""
    def fetch():
        results = {}
        alerts  = []
        for commodity, zone in COMMODITY_WEATHER_ZONES.items():
            try:
                r = requests.get(
                    "https://api.open-meteo.com/v1/forecast"
                    f"?latitude={zone['lat']}&longitude={zone['lon']}"
                    "&daily=temperature_2m_max,temperature_2m_min,"
                    "precipitation_sum,wind_speed_10m_max"
                    "&forecast_days=7&timezone=auto",
                    timeout=8
                )
                if r.status_code != 200: continue
                d = r.json()["daily"]
                t_max = sum(d.get("temperature_2m_max",[35])[:7])/7
                t_min = sum(d.get("temperature_2m_min",[10])[:7])/7
                rain  = sum(d.get("precipitation_sum",[10])[:7])
                wind  = max(d.get("wind_speed_10m_max",[20])[:7])
                signal = "NORMAL"; impact = "NEUTRAL"; reasons = []
                if commodity in ["WHEAT","CORN","SOYBEANS","COFFEE","SUGAR","COTTON","COCOA"]:
                    if t_max > 38:   signal="HEAT_STRESS";  impact="BULLISH"; reasons.append(f"Sicak:{t_max:.0f}C")
                    elif t_min < -5: signal="FROST_RISK";   impact="BULLISH"; reasons.append(f"Don:{t_min:.0f}C")
                    if rain < 5:     signal="DROUGHT";      impact="BULLISH"; reasons.append(f"Kuraklik:{rain:.0f}mm")
                    elif rain > 100: signal="FLOOD_RISK";   impact="BEARISH"; reasons.append(f"Sel:{rain:.0f}mm")
                    if wind > 80:    reasons.append(f"Firtina:{wind:.0f}km/h")
                elif commodity in ["NATURAL_GAS","OIL_BRENT"]:
                    if t_min < -10:  signal="COLD_DEMAND";  impact="BULLISH"; reasons.append(f"Soguk:{t_min:.0f}C")
                    elif t_max > 38: signal="HEAT_DEMAND";  impact="BULLISH"; reasons.append(f"Sicak:{t_max:.0f}C")
                    if wind > 70:    signal="STORM_RISK";   impact="BULLISH"; reasons.append(f"Firtina:{wind:.0f}km/h")
                elif commodity in ["COPPER","GOLD"]:
                    if wind > 100 or rain > 200:
                        signal="MINE_DISRUPTION"; impact="BULLISH"; reasons.append("Maden aksamasi riski")
                results[commodity] = {
                    "signal": signal, "impact": impact,
                    "zone": zone["label"],
                    "reasons": " | ".join(reasons) if reasons else "Normal",
                }
                if impact == "BULLISH" and signal != "NORMAL":
                    alerts.append(f"{commodity}: {signal} ({zone['label']})")
            except Exception as e:
                logging.debug(f"Weather {commodity}: {e}")
        return {"data": results, "alerts": alerts}
    return _cached("global_weather", 180, fetch) or {"data": {}, "alerts": []}


def get_natural_disaster_signal():
    """USGS deprem + ReliefWeb afet sinyali."""
    def fetch():
        disasters = []
        try:
            r = requests.get(
                "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
                timeout=10)
            if r.status_code == 200:
                for eq in r.json().get("features", [])[:5]:
                    props = eq.get("properties", {})
                    mag   = props.get("mag", 0)
                    place = props.get("place", "")
                    pl    = place.lower()
                    assets = []
                    if any(k in pl for k in ["chile","peru"]): assets.append("COPPER")
                    if any(k in pl for k in ["japan","tokyo"]): assets.append("NATURAL_GAS")
                    if any(k in pl for k in ["iran","iraq","saudi"]): assets.append("OIL_BRENT")
                    if any(k in pl for k in ["indonesia","papua"]): assets.append("COPPER")
                    disasters.append({"type":"EARTHQUAKE","mag":mag,"place":place,
                                      "assets":assets,
                                      "impact":"HIGH" if mag>=7.0 else "MEDIUM" if mag>=6.0 else "LOW"})
        except Exception as e:
            logging.debug(f"USGS: {e}")
        try:
            r2 = requests.get("https://api.reliefweb.int/v1/disasters?appname=nexus&limit=3&status=alert",timeout=8)
            if r2.status_code == 200:
                for item in r2.json().get("data",[])[:3]:
                    f = item.get("fields",{}); disasters.append({"type":"DISASTER","place":f.get("name",""),"impact":"MEDIUM","assets":[]})
        except: pass
        high = [d for d in disasters if d.get("impact")=="HIGH"]
        affected = {}
        for d in disasters:
            for a in d.get("assets",[]): affected[a] = affected.get(a,0)+1
        return {
            "signal": "DISASTER_HIGH" if high else ("DISASTER_WATCH" if disasters else "CLEAR"),
            "trend":  "RISK_OFF" if high else "NEUTRAL",
            "disasters": disasters, "affected_assets": affected,
            "notes": f"{len(disasters)} olay | Yuksek:{len(high)} | Etkilenen:{list(affected.keys())}"
        }
    return _cached("disasters", 120, fetch) or {"signal":"UNKNOWN","disasters":[],"affected_assets":{},"notes":"Veri yok"}




# ============================================================
# GDACS - KÜRESEL AFET UYARI SİSTEMİ
# ============================================================
def get_gdacs_alerts():
    """
    GDACS (Global Disaster Alert and Coordination System)
    Tamamen ücretsiz, kein Key.
    Magnitude > 6.0 veya Kategori 3+ hurrikan → Telegram alarm.
    """
    def fetch():
        alerts = []
        try:
            r = requests.get(
                "https://www.gdacs.org/xml/rss.xml",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if r.status_code != 200:
                return {"alerts": [], "critical": [], "notes": f"GDACS HTTP {r.status_code}"}

            import re as _re
            # GDACS RSS parsa
            titles = _re.findall(r'<title>(.*?)</title>', r.text)[1:]
            descs  = _re.findall(r'<description>(.*?)</description>', r.text)
            geos   = _re.findall(r'<geo:Point>.*?<geo:lat>(.*?)</geo:lat>.*?<geo:long>(.*?)</geo:long>.*?</geo:Point>', r.text, _re.DOTALL)

            for i, title in enumerate(titles[:10]):
                title = title.strip()
                desc  = descs[i].strip() if i < len(descs) else ""

                # Olay tipi tespit
                event_type = "UNKNOWN"
                if "earthquake" in title.lower(): event_type = "EARTHQUAKE"
                elif "cyclone" in title.lower() or "hurricane" in title.lower() or "typhoon" in title.lower(): event_type = "CYCLONE"
                elif "flood" in title.lower(): event_type = "FLOOD"
                elif "volcano" in title.lower(): event_type = "VOLCANO"
                elif "drought" in title.lower(): event_type = "DROUGHT"
                elif "tsunami" in title.lower(): event_type = "TSUNAMI"

                # Büyüklük / kategori tespit
                mag_match = _re.search(r'M\s*([\d.]+)', title + desc)
                cat_match = _re.search(r'[Cc]at(?:egory)?\s*(\d)', title + desc)
                magnitude = float(mag_match.group(1)) if mag_match else 0
                category  = int(cat_match.group(1)) if cat_match else 0

                # Konum
                lat = float(geos[i][0]) if i < len(geos) else 0
                lon = float(geos[i][1]) if i < len(geos) else 0

                # Asset etki analizi
                assets_affected = []
                loc_lower = (title + desc).lower()

                if event_type == "EARTHQUAKE":
                    if any(k in loc_lower for k in ["chile","peru","andes"]): assets_affected += ["COPPER","SILVER"]
                    if any(k in loc_lower for k in ["japan","honshu","fukushima","tokyo"]): assets_affected += ["NATURAL_GAS","JPY"]
                    if any(k in loc_lower for k in ["taiwan"]): assets_affected += ["SEMICONDUCTOR","TECH"]
                    if any(k in loc_lower for k in ["iran","iraq"]): assets_affected += ["OIL_BRENT"]
                    if any(k in loc_lower for k in ["indonesia","sumatra"]): assets_affected += ["COPPER","COAL"]
                    if any(k in loc_lower for k in ["turkey","greece","italy"]): assets_affected += ["EURUSD"]
                    if any(k in loc_lower for k in ["new zealand","australia"]): assets_affected += ["GOLD"]

                elif event_type == "CYCLONE":
                    if -100 < lon < -60 and 15 < lat < 35:  # Golf von Mexiko
                        assets_affected += ["OIL_BRENT","NATURAL_GAS","HEATING_OIL"]
                    if 60 < lon < 100 and 5 < lat < 25:     # Hint Okyanusu
                        assets_affected += ["OIL_BRENT"]
                    if 120 < lon < 180 and 15 < lat < 40:   # Pasifik (Japonya/Filipinler)
                        assets_affected += ["NATURAL_GAS"]

                elif event_type == "FLOOD":
                    if any(k in loc_lower for k in ["thailand","bangkok"]): assets_affected += ["TECH","HDD"]
                    if any(k in loc_lower for k in ["china","yangtze"]): assets_affected += ["COPPER","ALUMINUM"]
                    if any(k in loc_lower for k in ["india","bangladesh"]): assets_affected += ["COTTON","SUGAR"]
                    if any(k in loc_lower for k in ["pakistan"]): assets_affected += ["COTTON"]
                    if any(k in loc_lower for k in ["mississippi","midwest"]): assets_affected += ["CORN","SOYBEANS"]

                elif event_type == "DROUGHT":
                    if any(k in loc_lower for k in ["brazil","sao paulo"]): assets_affected += ["COFFEE","SUGAR","SOYBEANS"]
                    if any(k in loc_lower for k in ["ukraine","russia"]): assets_affected += ["WHEAT"]
                    if any(k in loc_lower for k in ["australia"]): assets_affected += ["WHEAT","COAL"]

                elif event_type == "VOLCANO":
                    if any(k in loc_lower for k in ["indonesia","krakatau"]): assets_affected += ["COPPER","NICKEL"]
                    if any(k in loc_lower for k in ["iceland"]): assets_affected += ["EURUSD","NATURAL_GAS"]

                # Kritiklik değerlendirme
                is_critical = (
                    (event_type == "EARTHQUAKE" and magnitude >= 6.5) or
                    (event_type == "CYCLONE"    and category >= 3) or
                    (event_type == "TSUNAMI") or
                    (event_type == "VOLCANO"    and "eruption" in loc_lower)
                )

                alert = {
                    "type":     event_type,
                    "title":    title[:100],
                    "mag":      magnitude,
                    "category": category,
                    "lat": lat, "lon": lon,
                    "assets":   assets_affected,
                    "critical": is_critical,
                }
                alerts.append(alert)

        except Exception as e:
            logging.warning(f"GDACS: {e}")
            return {"alerts": [], "critical": [], "notes": f"GDACS hatasi: {e}"}

        critical = [a for a in alerts if a["critical"]]
        all_affected = {}
        for a in alerts:
            for asset in a["assets"]:
                all_affected[asset] = all_affected.get(asset, 0) + 1

        return {
            "alerts":       alerts,
            "critical":     critical,
            "all_affected": all_affected,
            "notes": (f"GDACS: {len(alerts)} olay | "
                      f"Kritik:{len(critical)} | "
                      f"Etkilenen:{list(all_affected.keys())[:5]}")
        }

    result = _cached("gdacs", 60, fetch) or {"alerts":[],"critical":[],"all_affected":{},"notes":"Veri yok"}

    # Kritik uyarı → Telegram push
    if result.get("critical"):
        for alert in result["critical"]:
            cache_key = f"gdacs_sent_{alert['title'][:30]}"
            if not _cache.get(cache_key):
                try:
                    msg = (f"GDACS KRİTİK UYARI!\n"
                           f"Tip: {alert['type']} | Büyüklük:{alert['mag']}\n"
                           f"Konum: {alert['title']}\n"
                           f"Etkilenen Assetler: {', '.join(alert['assets']) or 'Belirsiz'}")
                    bot.send_message(MY_CHAT_ID, msg)
                    _cache[cache_key] = (time.time(), True)
                except: pass

    return result


# ============================================================
# NHC - ULUSAL KASIRGA MERKEZİ (Hurrikan Tracking)
# ============================================================
def get_hurricane_signal():
    """
    NOAA NHC (National Hurricane Center) RSS beslemesi.
    Tamamen ücretsiz, kein Key.
    
    Kategori 3+ kasırga → OIL/GAS acil sinyal.
    """
    def fetch():
        storms = []
        try:
            # Atlantik havzası (Golf von Mexiko dahil)
            feeds = [
                ("ATLANTIC", "https://www.nhc.noaa.gov/index-at.xml"),
                ("PACIFIC",  "https://www.nhc.noaa.gov/index-ep.xml"),
            ]
            import re as _re

            for basin, url in feeds:
                try:
                    r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code != 200: continue

                    items = _re.findall(r'<item>(.*?)</item>', r.text, _re.DOTALL)
                    for item in items[:5]:
                        title = _re.search(r'<title>(.*?)</title>', item)
                        desc  = _re.search(r'<description>(.*?)</description>', item)
                        if not title: continue

                        t = title.group(1).strip()
                        d = desc.group(1).strip() if desc else ""

                        # Fırtına kategorisi
                        cat_m  = _re.search(r'[Cc]ategory\s*(\d)', t + d)
                        wind_m = _re.search(r'(\d+)\s*mph', t + d)
                        cat    = int(cat_m.group(1)) if cat_m else 0
                        wind   = int(wind_m.group(1)) if wind_m else 0

                        # Kategori rüzgar hızından tahmin (mph)
                        if cat == 0 and wind > 0:
                            if wind >= 157: cat = 5
                            elif wind >= 130: cat = 4
                            elif wind >= 111: cat = 3
                            elif wind >= 96:  cat = 2
                            elif wind >= 74:  cat = 1

                        # Gulf pozisyonu tespit
                        in_gulf = "gulf" in (t + d).lower() or "mexico" in (t + d).lower()
                        in_carib = "caribbean" in (t + d).lower() or "florida" in (t + d).lower()

                        # Asset etki
                        assets = []
                        if in_gulf:
                            assets += ["OIL_BRENT","NATURAL_GAS","HEATING_OIL","GASOLINE"]
                        if in_carib or in_gulf:
                            assets += ["SUGAR"]  # Karayip şeker kamışı
                        if cat >= 3:
                            assets += ["GOLD"]   # Panik alımı

                        storms.append({
                            "basin":    basin,
                            "name":     t[:60],
                            "category": cat,
                            "wind_mph": wind,
                            "in_gulf":  in_gulf,
                            "assets":   assets,
                            "critical": cat >= 3 and in_gulf
                        })
                except: continue

        except Exception as e:
            logging.debug(f"NHC: {e}")

        gulf_storms = [s for s in storms if s.get("in_gulf")]
        cat3_plus   = [s for s in storms if s.get("category", 0) >= 3]

        if cat3_plus:
            signal = "HURRICANE_CRITICAL"
            trend  = "OIL_BULLISH"
        elif gulf_storms:
            signal = "HURRICANE_WATCH"
            trend  = "OIL_ALERT"
        elif storms:
            signal = "TROPICAL_ACTIVITY"
            trend  = "NEUTRAL"
        else:
            signal = "CLEAR"
            trend  = "NEUTRAL"

        return {
            "signal":  signal,
            "trend":   trend,
            "storms":  storms,
            "notes":   (f"NHC: {len(storms)} firtina | "
                        f"Kat3+:{len(cat3_plus)} | "
                        f"Gulf:{len(gulf_storms)}")
        }

    return _cached("hurricane", 60, fetch) or {
        "signal": "UNKNOWN", "storms": [], "notes": "Veri yok"
    }


# ============================================================
# HDD/CDD - HEATING/COOLING DEGREE DAYS
# Enerji Talebi Modeli
# ============================================================
def get_hdd_cdd_signal():
    """
    Heating Degree Days (HDD) ve Cooling Degree Days (CDD).
    Enerji talebiyle doğrudan korelasyon.
    
    HDD = max(0, 18 - T_avg)  → Isınma talebi (Gaz/Petrol)
    CDD = max(0, T_avg - 18)  → Soğutma talebi (Elektrik)
    
    Bölgeler: Merkez Avrupa, Kuzeydoğu ABD, Kuzey Asya
    """
    def fetch():
        zones = {
            "EU_CENTRAL": {"lat": 50.0, "lon": 10.0, "label": "Orta Avrupa",
                           "asset": "NATURAL_GAS"},
            "US_NORTHEAST":{"lat": 42.0, "lon": -74.0,"label": "Kuzey Doğu ABD",
                            "asset": "HEATING_OIL"},
            "RUSSIA_WEST": {"lat": 55.0, "lon": 37.0, "label": "Batı Rusya",
                            "asset": "NATURAL_GAS"},
            "CHINA_NORTH": {"lat": 40.0, "lon": 116.0,"label": "Kuzey Çin",
                            "asset": "COAL"},
            "JAPAN":       {"lat": 35.6, "lon": 139.7,"label": "Japonya",
                            "asset": "LNG"},
        }

        results = {}
        for zone_name, zone in zones.items():
            try:
                r = requests.get(
                    "https://api.open-meteo.com/v1/forecast"
                    f"?latitude={zone['lat']}&longitude={zone['lon']}"
                    "&daily=temperature_2m_max,temperature_2m_min"
                    "&forecast_days=7&timezone=auto",
                    timeout=8
                )
                if r.status_code != 200: continue

                d      = r.json()["daily"]
                t_max  = d.get("temperature_2m_max", [])
                t_min  = d.get("temperature_2m_min", [])
                if not t_max or not t_min: continue

                # 7 günlük HDD/CDD hesapla
                total_hdd = 0
                total_cdd = 0
                for i in range(min(7, len(t_max))):
                    t_avg = (t_max[i] + t_min[i]) / 2
                    total_hdd += max(0, 18 - t_avg)
                    total_cdd += max(0, t_avg - 18)

                # Sinyal yorumu
                if total_hdd > 70:
                    signal = "EXTREME_HEATING"
                    impact = "VERY_BULLISH"
                elif total_hdd > 42:
                    signal = "HIGH_HEATING"
                    impact = "BULLISH"
                elif total_cdd > 70:
                    signal = "EXTREME_COOLING"
                    impact = "BULLISH"
                elif total_cdd > 42:
                    signal = "HIGH_COOLING"
                    impact = "BULLISH"
                else:
                    signal = "MODERATE"
                    impact = "NEUTRAL"

                results[zone_name] = {
                    "label":  zone["label"],
                    "asset":  zone["asset"],
                    "hdd":    round(total_hdd, 1),
                    "cdd":    round(total_cdd, 1),
                    "signal": signal,
                    "impact": impact,
                }

            except Exception as e:
                logging.debug(f"HDD/CDD {zone_name}: {e}")

        # Genel enerji sinyali
        bullish_zones = [z for z in results.values() if z.get("impact") in ("BULLISH","VERY_BULLISH")]
        if len(bullish_zones) >= 3:
            overall = "ENERGY_DEMAND_HIGH"
        elif len(bullish_zones) >= 1:
            overall = "ENERGY_DEMAND_ELEVATED"
        else:
            overall = "ENERGY_DEMAND_NORMAL"

        # En yüksek HDD/CDD bölgesi
        top_zone = max(results.items(), key=lambda x: x[1].get("hdd",0) + x[1].get("cdd",0)) if results else None
        top_str  = f"{top_zone[1]['label']}: HDD={top_zone[1]['hdd']} CDD={top_zone[1]['cdd']}" if top_zone else "Veri yok"

        return {
            "zones":   results,
            "overall": overall,
            "notes":   f"HDD/CDD: {overall} | En yüksek: {top_str}"
        }

    return _cached("hdd_cdd", 180, fetch) or {
        "zones": {}, "overall": "UNKNOWN", "notes": "Veri yok"
    }


# ============================================================
# EU GAZ DEPOLARI - GIE AGSI+
# ============================================================
def get_eu_gas_storage():
    """
    Avrupa Gaz Depolama Doluluğu.
    GIE (Gas Infrastructure Europe) AGSI+ API - ücretsiz, kein Key.
    
    < 30% dolu → NATURAL_GAS BULLISH (kış yaklaşırsa kritik)
    > 90% dolu → BEARISH
    """
    def fetch():
        try:
            r = requests.get(
                "https://agsi.gie.eu/api/data/eu",
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json"
                }
            )
            if r.status_code == 200:
                data = r.json()
                # AGSI API yanıt formatı
                if isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                elif isinstance(data, dict):
                    latest = data.get("data", [{}])[0] if data.get("data") else data
                else:
                    latest = {}

                # Doluluk yüzdesi
                full_pct = float(latest.get("full", latest.get("gas_day_start", 0)) or 0)
                # Değişim
                change   = float(latest.get("change", latest.get("injection", 0)) or 0)

                if full_pct == 0:
                    return {"pct": 0, "signal": "UNKNOWN", "notes": "GIE API format degisti"}

                if full_pct < 20:
                    signal = "CRITICALLY_LOW"; trend = "VERY_BULLISH"
                elif full_pct < 35:
                    signal = "LOW";            trend = "BULLISH"
                elif full_pct < 60:
                    signal = "MODERATE";       trend = "NEUTRAL"
                elif full_pct < 80:
                    signal = "COMFORTABLE";    trend = "NEUTRAL"
                elif full_pct < 90:
                    signal = "HIGH";           trend = "BEARISH"
                else:
                    signal = "FULL";           trend = "VERY_BEARISH"

                # Mevsim etkisi
                month = datetime.now().month
                winter_approaching = month in [8, 9, 10, 11]  # Sonbahar = dolum sezonu
                if winter_approaching and full_pct < 70:
                    trend = "BULLISH"  # Kış öncesi düşük stok = fiyat artar

                return {
                    "pct":    round(full_pct, 1),
                    "change": round(change, 2),
                    "signal": signal,
                    "trend":  trend,
                    "notes":  (f"AB Gaz Deposu: %{full_pct:.1f} dolu "
                               f"(değişim: {change:+.1f}%) | {signal}")
                }

        except Exception as e:
            logging.debug(f"EU Gas Storage: {e}")

        # Fallback: Investing.com natural gas news
        return {
            "pct": 0, "signal": "UNKNOWN", "trend": "NEUTRAL",
            "notes": "GIE API erisilemedi (AGSI+ key gerekebilir)"
        }

    return _cached("eu_gas", 240, fetch) or {
        "pct": 0, "signal": "UNKNOWN", "trend": "NEUTRAL", "notes": "Veri yok"
    }


# ============================================================
# ECMWF 14-GÜN TAHMİN (Open-Meteo ECMWF Modeli)
# ============================================================
def get_ecmwf_outlook():
    """
    ECMWF (Avrupa Orta Vadeli Hava Tahminleri) modeli.
    Open-Meteo üzerinden ücretsiz erişim.
    14 günlük tahmin - tarım ve enerji için kritik.
    """
    def fetch():
        # Kritik bölgeler için 14 günlük tahmin
        targets = [
            {"name": "Kansas_Bugday", "lat": 39.1, "lon": -94.6, "asset": "WHEAT"},
            {"name": "Brezilya_Kahve","lat": -21.0, "lon": -45.0, "asset": "COFFEE"},
            {"name": "Orta_Avrupa",   "lat": 50.0, "lon": 10.0,  "asset": "NATURAL_GAS"},
            {"name": "Kuzey_Rusya",   "lat": 60.0, "lon": 60.0,  "asset": "WHEAT"},
            {"name": "Sili_Bakir",    "lat": -33.0,"lon": -71.0, "asset": "COPPER"},
        ]

        results = {}
        anomalies = []

        for t in targets:
            try:
                r = requests.get(
                    "https://api.open-meteo.com/v1/forecast"
                    f"?latitude={t['lat']}&longitude={t['lon']}"
                    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                    "&forecast_days=14&models=ecmwf_ifs04&timezone=auto",
                    timeout=10
                )
                if r.status_code != 200: continue

                d       = r.json()["daily"]
                t_max   = d.get("temperature_2m_max", [])
                t_min   = d.get("temperature_2m_min", [])
                rain    = d.get("precipitation_sum",  [])

                if not t_max: continue

                # İlk 7 gün vs sonraki 7 gün karşılaştırma
                week1_t = sum(t_max[:7]) / 7 if len(t_max) >= 7 else sum(t_max)/len(t_max)
                week2_t = sum(t_max[7:14]) / 7 if len(t_max) >= 14 else week1_t
                week1_r = sum(rain[:7]) if len(rain) >= 7 else sum(rain)
                week2_r = sum(rain[7:14]) if len(rain) >= 14 else week1_r

                trend_str = ""
                anomaly   = False

                # Anomali tespit
                if week2_t - week1_t > 8:
                    trend_str = f"Hızlı ısınma (+{week2_t-week1_t:.0f}°C)"
                    anomaly = True
                elif week1_t - week2_t > 8:
                    trend_str = f"Hızlı soğuma (-{week1_t-week2_t:.0f}°C)"
                    anomaly = True
                elif week1_r < 5 and week2_r < 5:
                    trend_str = "Süregelen kuraklık"
                    anomaly = True
                elif week1_r + week2_r > 150:
                    trend_str = f"Aşırı yağış ({week1_r+week2_r:.0f}mm)"
                    anomaly = True
                else:
                    trend_str = "Normal"

                results[t["name"]] = {
                    "asset":    t["asset"],
                    "w1_temp":  round(week1_t, 1),
                    "w2_temp":  round(week2_t, 1),
                    "w1_rain":  round(week1_r, 1),
                    "w2_rain":  round(week2_r, 1),
                    "trend":    trend_str,
                    "anomaly":  anomaly,
                }

                if anomaly:
                    anomalies.append(f"{t['name']} ({t['asset']}): {trend_str}")

            except Exception as e:
                logging.debug(f"ECMWF {t['name']}: {e}")

        return {
            "forecasts": results,
            "anomalies": anomalies,
            "notes": (f"ECMWF 14-gun: {len(anomalies)} anomali | "
                      + " | ".join(anomalies[:3]) if anomalies else "ECMWF 14-gun: Normal")
        }

    return _cached("ecmwf", 360, fetch) or {
        "forecasts": {}, "anomalies": [], "notes": "ECMWF verisi yok"
    }


# ============================================================
# NOAA GHCN - TARİHSEL KARŞILAŞTIRMA
# (Şu anki hava tarihsel ortalamadan ne kadar sapıyor?)
# ============================================================
def get_historical_weather_anomaly():
    """
    Şu anki hava koşullarını tarihsel ortalamalarla karşılaştır.
    Anomali ne kadar büyük → piyasa sürprizi o kadar büyük.
    
    Open-Meteo ERA5 verisi kullanır (NOAA GHCN eşdeğeri, ücretsiz).
    """
    def fetch():
        targets = [
            {"name": "US_CORN_BELT", "lat": 41.5, "lon": -93.0, "asset": "CORN"},
            {"name": "BRAZIL_SOY",   "lat": -15.0,"lon": -54.0, "asset": "SOYBEANS"},
            {"name": "EU_GAS",       "lat": 50.0, "lon": 10.0,  "asset": "NATURAL_GAS"},
            {"name": "UKRAINE_WHEAT","lat": 49.0, "lon": 32.0,  "asset": "WHEAT"},
        ]

        anomalies = {}
        now = datetime.now()
        # 30 günlük tarihsel karşılaştırma
        start_hist = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        end_hist   = now.strftime("%Y-%m-%d")
        # Geçen yıl aynı dönem
        start_prev = (now - timedelta(days=395)).strftime("%Y-%m-%d")
        end_prev   = (now - timedelta(days=365)).strftime("%Y-%m-%d")

        for t in targets:
            try:
                # Bu yılki veri
                r1 = requests.get(
                    "https://archive-api.open-meteo.com/v1/archive"
                    f"?latitude={t['lat']}&longitude={t['lon']}"
                    f"&start_date={start_hist}&end_date={end_hist}"
                    "&daily=temperature_2m_max,precipitation_sum"
                    "&timezone=auto", timeout=10
                )
                # Geçen yıl verisi
                r2 = requests.get(
                    "https://archive-api.open-meteo.com/v1/archive"
                    f"?latitude={t['lat']}&longitude={t['lon']}"
                    f"&start_date={start_prev}&end_date={end_prev}"
                    "&daily=temperature_2m_max,precipitation_sum"
                    "&timezone=auto", timeout=10
                )

                if r1.status_code != 200 or r2.status_code != 200: continue

                d1 = r1.json()["daily"]
                d2 = r2.json()["daily"]

                t_now  = sum(d1.get("temperature_2m_max",[]))/max(len(d1.get("temperature_2m_max",[1])),1)
                t_prev = sum(d2.get("temperature_2m_max",[]))/max(len(d2.get("temperature_2m_max",[1])),1)
                r_now  = sum(d1.get("precipitation_sum",[]))
                r_prev = sum(d2.get("precipitation_sum",[]))

                temp_anomaly = t_now - t_prev
                rain_anomaly = r_now - r_prev
                rain_pct     = (r_now - r_prev)/max(r_prev,1) * 100

                signal = "NORMAL"
                if abs(temp_anomaly) > 3:
                    signal = f"TEMP_ANOMALY_{'+' if temp_anomaly>0 else ''}{temp_anomaly:.1f}C"
                if abs(rain_pct) > 30:
                    signal = f"RAIN_ANOMALY_{'+' if rain_pct>0 else ''}{rain_pct:.0f}PCT"

                anomalies[t["name"]] = {
                    "asset":        t["asset"],
                    "temp_now":     round(t_now, 1),
                    "temp_prev":    round(t_prev, 1),
                    "temp_anomaly": round(temp_anomaly, 1),
                    "rain_now":     round(r_now, 1),
                    "rain_prev":    round(r_prev, 1),
                    "rain_pct":     round(rain_pct, 1),
                    "signal":       signal,
                }

            except Exception as e:
                logging.debug(f"GHCN {t['name']}: {e}")

        significant = {k: v for k, v in anomalies.items() if v["signal"] != "NORMAL"}

        return {
            "anomalies":   anomalies,
            "significant": significant,
            "notes": (f"Hava Anomalisi: {len(significant)} kritik bölge | " +
                      " | ".join([f"{k}:{v['signal']}" for k,v in significant.items()])
                      if significant else "Hava Anomalisi: Normal")
        }

    return _cached("wx_anomaly", 360, fetch) or {
        "anomalies": {}, "significant": {}, "notes": "Anomali verisi yok"
    }


def get_iata_signals():
    """IATA Jet Fuel + Airline Sentiment sinyali."""
    def fetch():
        jet_price = 0
        jet_chg   = 0
        try:
            r = requests.get(
                "https://api.eia.gov/v2/petroleum/pri/spt/data/"
                "?frequency=weekly&data[0]=value&facets[product][]=EPD2DXL0",
                timeout=10, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code == 200:
                entries = r.json().get("response",{}).get("data",[])
                if entries:
                    jet_price = float(entries[0].get("value",0))
                    prev_p    = float(entries[1].get("value",jet_price)) if len(entries)>1 else jet_price
                    jet_chg   = (jet_price-prev_p)/prev_p*100 if prev_p else 0
        except Exception as e:
            logging.debug(f"EIA jet fuel: {e}")

        airline_sentiment = "NEUTRAL"
        try:
            import re as _re
            r2 = requests.get("https://simpleflying.com/feed/",timeout=8,headers={"User-Agent":"Mozilla/5.0"})
            if r2.status_code == 200:
                titles   = _re.findall(r"<title>(.*?)</title>", r2.text)[1:10]
                text_all = " ".join(titles).lower()
                bull = sum(1 for k in ["record","surge","growth","profit","full"] if k in text_all)
                bear = sum(1 for k in ["cancel","loss","bankrupt","cut","crisis"] if k in text_all)
                if bull > bear+1:   airline_sentiment = "BULLISH"
                elif bear > bull+1: airline_sentiment = "BEARISH"
        except Exception as e:
            logging.debug(f"Airline RSS: {e}")

        if jet_price > 3.5:   fuel_sig="FUEL_HIGH";   oil_imp="BULLISH"
        elif jet_price > 2.5: fuel_sig="FUEL_NORMAL";  oil_imp="NEUTRAL"
        elif jet_price > 0:   fuel_sig="FUEL_LOW";     oil_imp="BEARISH"
        else:                 fuel_sig="UNKNOWN";      oil_imp="NEUTRAL"

        return {
            "jet_fuel_price":    round(jet_price,3),
            "jet_fuel_chg":      round(jet_chg,2),
            "jet_fuel_signal":   fuel_sig,
            "oil_impact":        oil_imp,
            "airline_sentiment": airline_sentiment,
            "notes": (f"Jet Fuel:${jet_price:.2f}/gal ({jet_chg:+.1f}%) "
                      f"{fuel_sig} | Airline:{airline_sentiment}")
        }
    return _cached("iata",240,fetch) or {
        "jet_fuel_price":0,"jet_fuel_signal":"UNKNOWN",
        "oil_impact":"NEUTRAL","airline_sentiment":"NEUTRAL",
        "notes":"IATA veri yok"
    }

def get_google_trends_proxy():
    """Trends24 RSS ile global arama trendi."""
    def fetch():
        try:
            r = requests.get("https://trends24.in/worldwide/rss.xml",timeout=8,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code == 200:
                import re as _re
                items = _re.findall(r'<title>(.*?)</title>', r.text)[1:21]
                trend_text = " ".join(items).lower()
                signals = {
                    "recession": {"active": any(k in trend_text for k in ["recession","crisis","layoff"])},
                    "shopping":  {"active": any(k in trend_text for k in ["sale","deals","shopping"])},
                    "inflation": {"active": any(k in trend_text for k in ["inflation","price","cost"])},
                }
                return {"trends": trend_text[:200],"signals": signals,"notes": f"Trendler: {', '.join(items[:5])}"}
        except Exception as e:
            logging.debug(f"Trends: {e}")
        return {"trends":"","signals":{},"notes":"Trend verisi yok"}
    return _cached("gtrends", 120, fetch) or {"trends":"","signals":{},"notes":"Veri yok"}

def get_alternative_data_summary():
    """
    Renaissance Technologies / Two Sigma seviyesinde non-traditional data.
    Tum alternatif veri sinyallerini birlestirir.
    """
    cargo    = get_cargo_flight_signal()
    ships    = get_ship_traffic_signal()
    bdi      = get_baltic_dry_index()
    ecom     = get_ecommerce_signal()
    wx_glob  = get_global_commodity_weather()
    disaster = get_natural_disaster_signal()
    gdacs    = get_gdacs_alerts()
    hurr     = get_hurricane_signal()
    hdd      = get_hdd_cdd_signal()
    eu_gas   = get_eu_gas_storage()
    ecmwf    = get_ecmwf_outlook()
    wx_anom  = get_historical_weather_anomaly()
    gtrends  = get_google_trends_proxy()

    L = ["=== ALTERNATIF VERI SINYALLERI (QUANT ALPHA) ===", ""]

    # 1. Cargo + Gemi + BDI
    L += [
        f"CARGO UCUSLARI: {cargo.get('signal','?')} | {cargo.get('notes','?')}",
        f"GEMI TRAFIGI: Petrol={ships.get('oil_signal','?')} Ticaret={ships.get('trade_signal','?')} | {ships.get('notes','?')}",
        f"BALTIK KURU: {bdi.get('value',0)} - {bdi.get('signal','?')} | {bdi.get('notes','?')}",
        f"IATA JET FUEL: {get_iata_signals().get('notes','?')}",
        "",
    ]
    L += [
        f"E-TICARET: {ecom.get('signal','?')} | {ecom.get('notes','?')}",
        "",
    ]

    # 2. Afet Sistemi (GDACS + NHC + USGS)
    critical_gdacs = gdacs.get("critical", [])
    L += [f"GDACS AFET SISTEMI: {gdacs.get('notes','?')}"]
    for c in critical_gdacs[:3]:
        L.append(f"  KRITIK: {c['type']} M{c['mag']} - {c['title'][:60]} | Etkilenen:{c['assets']}")

    L += [f"NHC KASIRGA: {hurr.get('signal','?')} | {hurr.get('notes','?')}"]
    for s in [st for st in hurr.get("storms",[]) if st.get("category",0) >= 3][:2]:
        L.append(f"  KAT{s['category']}: {s['name']} | Etkilenen:{s['assets']}")
    L.append("")

    # 3. Enerji Talep Modeli
    L += [
        f"HDD/CDD ENERJI TALEP: {hdd.get('overall','?')} | {hdd.get('notes','?')}",
        f"AB GAZ DEPOSU: {eu_gas.get('pct',0):.1f}% dolu - {eu_gas.get('signal','?')} | {eu_gas.get('notes','?')}",
        "",
    ]

    # 4. Hava Anomalisi
    wx_data   = wx_glob.get("data", {})
    wx_alerts = wx_glob.get("alerts", [])
    L += [f"KURESEL EMTIA HAVA: {len(wx_alerts)} uyari"]
    for alert in wx_alerts[:4]:
        L.append(f"  {alert}")

    # ECMWF 14-gun anomaliler
    ecmwf_anom = ecmwf.get("anomalies", [])
    if ecmwf_anom:
        L.append(f"ECMWF 14-GUN ANOMALI: {' | '.join(ecmwf_anom[:3])}")
    else:
        L.append(f"ECMWF 14-GUN: {ecmwf.get('notes','?')}")

    # Tarihsel karsilastirma
    sig_anom = wx_anom.get("significant", {})
    if sig_anom:
        L.append(f"TARIHSEL HAVA ANOMALISI: {len(sig_anom)} kritik bolge")
        for k, v in list(sig_anom.items())[:3]:
            L.append(f"  {k} ({v['asset']}): {v['signal']}")
    L.append("")

    # 5. Google Trends
    gtrend_sigs = gtrends.get("signals", {})
    if gtrend_sigs.get("recession", {}).get("active"): L.append("GOOGLE TRENDS: Resesyon aramalari YUKSELIYOR - RISK_OFF")
    elif gtrend_sigs.get("shopping", {}).get("active"): L.append("GOOGLE TRENDS: Alisveris aramalari YUKSELIYOR - RISK_ON")
    L.append(f"  {gtrends.get('notes','?')}")
    L.append("")

    # Sinyal ozeti
    L += [
        "SINYAL REHBERI:",
        "  CARGO_SURGE + BDI>2000 = Kuresel buyume = RISK_ON + COPPER BUY",
        "  GDACS M7+ Sili/Peru = Bakir maden durur = COPPER BUY",
        "  GDACS M7+ Japonya = LNG talebi artar = NATURAL_GAS BUY",
        "  NHC Kat3+ Gulf = Petrol uretimi durur = OIL BUY",
        "  AB Gaz<%30 + Kis yaklasıyor = NATURAL_GAS VERY_BULLISH",
        "  HDD>70 Avrupa = Gaz talebi zirve = NATURAL_GAS BUY",
        "  DROUGHT Brezilya = Kahve/Soya arz azalir = COFFEE/SOY BUY",
        "  FROST Kansas = Bugday hasat riski = WHEAT BUY",
        "  CARGO_LOW + BDI<1000 = Resesyon = RISK_OFF + GOLD BUY",
    ]

    return "\n".join(L)
def get_volatility_regime(market_intel):
    spreads = [v.get("spread",0) for v in (market_intel or {}).values()
               if v.get("spread",0) < 999]
    if not spreads: return "UNKNOWN"
    avg = sum(spreads)/len(spreads)
    if avg < 0.1:    return "LOW"
    elif avg < 0.25: return "NORMAL"
    elif avg < 0.45: return "HIGH"
    else:            return "EXTREME"


# ============================================================
# FRED API - St. Louis Federal Reserve (v14.2)
# Ucretsiz, API key gerekli, gunluk veriler cache'lenir
# Endpoint: https://api.stlouisfed.org/fred/series/observations
# ============================================================
def get_fred_macro_data():
    """
    FRED API'den makro ekonomik veri ceker.
    Gunluk veriler: 240 dk cache | Aylik veriler: 720 dk cache
    Donus: dict ile yield curve, DXY, VIX, M2, CPI, faiz
    """
    if not FRED_API_KEY:
        return {
            "yield_curve": None, "dxy": None, "vix": None,
            "m2_growth": None, "cpi": None, "fed_rate": None,
            "signal": "FRED_KEY_YOK", "notes": "FRED_API_KEY .env dosyasinda tanimli degil"
        }

    BASE = "https://api.stlouisfed.org/fred/series/observations"

    def fred_get(series_id, limit=2):
        """Bir FRED serisinin son N degerini cek."""
        try:
            r = requests.get(BASE, params={
                "series_id":  series_id,
                "api_key":    FRED_API_KEY,
                "limit":      limit,
                "sort_order": "desc",
                "file_type":  "json"
            }, timeout=10)
            if r.status_code == 200:
                obs = r.json().get("observations", [])
                # "." = veri yok (FRED bunu bos deger icin kullanir)
                vals = [float(o["value"]) for o in obs if o["value"] not in (".", "")]
                return vals[0] if vals else None
            else:
                logging.warning(f"FRED {series_id} HTTP {r.status_code}")
                return None
        except Exception as e:
            logging.warning(f"FRED {series_id} hatasi: {e}")
            return None

    def fetch():
        result = {}

        # --- Gunluk veriler ---
        # Yield Curve: 10Y - 2Y (negatif = resesyon sinyali)
        t10y2y = fred_get("T10Y2Y")
        result["yield_curve"] = t10y2y

        # DXY - Dolar Endeksi (FRED DTWEXBGS serisi trade-weighted dollar)
        dxy = fred_get("DTWEXBGS")
        result["dxy"] = dxy

        # VIX - Volatilite endeksi
        vix = fred_get("VIXCLS")
        result["vix"] = vix

        # 10Y Tahvil faizi
        t10y = fred_get("DGS10")
        result["t10y"] = t10y

        # --- Aylik veriler (son 2 deger - buyume hesabi icin) ---
        # M2 Para Arzi - son 2 ay (buyume yuzdesini hesapla)
        try:
            r_m2 = requests.get(BASE, params={
                "series_id":  "M2SL",
                "api_key":    FRED_API_KEY,
                "limit":      2,
                "sort_order": "desc",
                "file_type":  "json"
            }, timeout=10)
            if r_m2.status_code == 200:
                obs = r_m2.json().get("observations", [])
                vals = [float(o["value"]) for o in obs if o["value"] not in (".", "")]
                if len(vals) >= 2:
                    # Aylik buyume yuzdesi
                    result["m2_growth"] = round((vals[0] - vals[1]) / vals[1] * 100, 3)
                    result["m2_level"]  = vals[0]
                else:
                    result["m2_growth"] = None
                    result["m2_level"]  = vals[0] if vals else None
        except Exception as e:
            logging.warning(f"FRED M2 hatasi: {e}")
            result["m2_growth"] = None

        # CPI - Enflasyon
        result["cpi"] = fred_get("CPIAUCSL")

        # Fed Funds Rate - mevcut faiz
        result["fed_rate"] = fred_get("FEDFUNDS")

        # --- Sinyal uret ---
        signals = []
        notes   = []

        # Yield Curve yorumu
        if t10y2y is not None:
            if t10y2y < -0.5:
                signals.append("RESESYON_RISKI")
                notes.append(f"Yield Curve: {t10y2y:.2f}% (inversiyon - resesyon sinyali!)")
            elif t10y2y < 0:
                signals.append("DIKKAT")
                notes.append(f"Yield Curve: {t10y2y:.2f}% (hafif inversiyon)")
            else:
                notes.append(f"Yield Curve: +{t10y2y:.2f}% (normal)")

        # VIX yorumu
        if vix is not None:
            if vix > 30:
                signals.append("RISK_OFF")
                notes.append(f"VIX: {vix:.1f} (YUKSEK - piyasa korkusu)")
            elif vix > 20:
                notes.append(f"VIX: {vix:.1f} (yukseldi - dikkat)")
            else:
                notes.append(f"VIX: {vix:.1f} (normal)")

        # DXY yorumu
        if dxy is not None:
            notes.append(f"DXY: {dxy:.2f}")
            if dxy > 106:
                signals.append("DXY_GUCLU")
                notes.append("(Guclu dolar - emtia baski altinda)")
            elif dxy < 100:
                signals.append("DXY_ZAYIF")
                notes.append("(Zayif dolar - emtia/kripto pozitif)")

        # M2 yorumu
        if result.get("m2_growth") is not None:
            mg = result["m2_growth"]
            if mg > 0.5:
                signals.append("M2_GENISLIYOR")
                notes.append(f"M2 buyume: +{mg:.3f}% (likidite artiyor)")
            elif mg < -0.3:
                signals.append("M2_DARALIYOR")
                notes.append(f"M2 buyume: {mg:.3f}% (likidite azaliyor)")

        result["signal"] = " | ".join(signals) if signals else "NEUTRAL"
        result["notes"]  = " | ".join(notes)
        return result

    return _cached("fred_macro", 240, fetch) or {
        "yield_curve": None, "dxy": None, "vix": None,
        "m2_growth": None, "cpi": None, "fed_rate": None,
        "signal": "FRED_HATA", "notes": "FRED verisi alinamadi"
    }

def get_macro_regime(fg_val, vol_regime, fred_data=None):
    """
    Makro rejim tespiti - v14.2: FRED verisi entegre edildi.
    Fear/Greed + Volatilite + Yield Curve + VIX + DXY + M2
    """
    # FRED risk sinyalleri
    fred_risk_off = False
    fred_risk_on  = False
    if fred_data:
        yc  = fred_data.get("yield_curve")
        vix = fred_data.get("vix")
        dxy = fred_data.get("dxy")
        m2g = fred_data.get("m2_growth")
        # Resesyon + Yuksek VIX = guclu RISK_OFF sinyali
        if (yc is not None and yc < -0.3) or (vix is not None and vix > 30):
            fred_risk_off = True
        # Zayif dolar + M2 genisliyor = RISK_ON (emtia/kripto pozitif)
        if (dxy is not None and dxy < 100) and (m2g is not None and m2g > 0.3):
            fred_risk_on = True

    # EXTREME Spreads + Extreme Fear = RISK_OFF_EXTREME
    if vol_regime == "EXTREME" and fg_val < 25:
        return "RISK_OFF_EXTREME"
    # Yüksek spread + FRED RISK_OFF = RISK_OFF_EXTREME'e yukselt
    if vol_regime == "EXTREME" and fred_risk_off:
        return "RISK_OFF_EXTREME"
    # Sadece yüksek spread
    if vol_regime == "EXTREME":
        return "RISK_OFF_SPREAD"
    # FRED resesyon sinyali fear ile birlesirse
    if fred_risk_off and fg_val < 35:
        return "RISK_OFF_FEAR"
    # Normal Fear/Greed bazli rejim - FRED ile nüanslı
    if fg_val >= 75:
        return "RISK_ON_GREEDY"
    elif fg_val >= 55:
        return "RISK_ON" if not fred_risk_off else "NEUTRAL"
    elif fg_val >= 45:
        return "RISK_ON" if fred_risk_on else "NEUTRAL"
    elif fg_val >= 25:
        return "RISK_OFF_FEAR" if fred_risk_off else "RISK_OFF"
    else:
        return "RISK_OFF_EXTREME" if fred_risk_off else "RISK_OFF_FEAR"

def get_seasonal_factor(symbol):
    m = datetime.now().month - 1
    f = SEASONAL_FACTORS.get(symbol)
    return f[m] if f else 1.0

# --- Kelly Kriterium ---
def berechne_kelly(symbol, confidence=5):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("""SELECT win_rate_overall,total_trades
            FROM asset_learnings WHERE symbol=?""", (symbol,)).fetchone()
        conn.close()
    wr = row[0] if (row and row[1] >= 10) else 0.5
    R = 2.0
    f = max(0.001, min((wr*R-(1-wr))/R, 0.5)) * 0.5 * (confidence/10.0)
    return round(max(0.001, min(f, 0.05)), 4)

# Sichere Häfen bei Panik/Extreme Regime
SAFE_HAVEN_ASSETS = {"GOLD", "SILVER", "BTC_USD", "ETH_USD",
                     "GOLD_EUR", "SILVER_EUR"}

def berechne_position_size(symbol, balance, confidence=5,
                           vol_regime="NORMAL", macro_regime="NEUTRAL"):
    k = berechne_kelly(symbol, confidence)
    is_safe_haven = symbol.upper() in SAFE_HAVEN_ASSETS

    if macro_regime == "RISK_OFF_EXTREME":
        # Echte Krise: nur sichere Häfen mit sehr kleiner Position
        if is_safe_haven:
            k *= 0.3
        else:
            k *= 0.1   # Sehr kleine Position für andere Assets
    elif macro_regime == "RISK_OFF_SPREAD":
        # Nur hohe Spreads: spread-basierte Reduktion
        if is_safe_haven:
            k *= 0.5
        else:
            k *= 0.25
    elif macro_regime == "RISK_OFF_FEAR":
        # Nur Panik (Fear<25): sichere Häfen bevorzugen
        if is_safe_haven:
            k *= 0.6   # Sichere Häfen bei Panik: gute Gelegenheit
        else:
            k *= 0.2
    elif vol_regime == "HIGH" or macro_regime == "RISK_OFF":
        k *= 0.5
    elif "GREEDY" in macro_regime:
        k *= 0.7
    return round(balance * k, 2)
# ============================================================
# BOLLINGER BANDS
# ============================================================
def berechne_bollinger(closes, period=20):
    """
    Bollinger Bands hesapla.
    Doner: dict mit upper, middle, lower, price, bandwidth, position
    position: NEAR_LOWER / NEAR_UPPER / MIDDLE / SQUEEZE
    """
    if len(closes) < period:
        return None
    closes = closes[-period:]
    middle = sum(closes) / period
    variance = sum((c - middle)**2 for c in closes) / period
    std = variance ** 0.5
    upper  = middle + 2 * std
    lower  = middle - 2 * std
    price  = closes[-1]
    bandwidth = (upper - lower) / middle if middle != 0 else 0

    # Pozisyon belirleme
    band_range = upper - lower
    if band_range == 0:
        position = "SQUEEZE"
    else:
        pct = (price - lower) / band_range  # 0.0=alt band, 1.0=ust band
        if pct <= 0.15:
            position = "NEAR_LOWER"   # BUY kandidati
        elif pct >= 0.85:
            position = "NEAR_UPPER"   # SELL kandidati
        elif 0.4 <= pct <= 0.6:
            position = "MIDDLE"       # Belirsiz
        else:
            position = "BETWEEN"

    # Squeeze: bantlar cok dar = patlama bekleniyor
    if bandwidth < 0.02:
        position = "SQUEEZE"

    return {
        "upper":     round(upper, 5),
        "middle":    round(middle, 5),
        "lower":     round(lower, 5),
        "price":     round(price, 5),
        "bandwidth": round(bandwidth, 4),
        "position":  position,
        "pct_pos":   round(pct if band_range != 0 else 0.5, 3)
    }


# ============================================================
# FIBONACCI RETRACEMENT
# ============================================================
def berechne_fibonacci(highs, lows, closes, lookback=50):
    """
    Fibonacci Retracement Levels hesapla.
    Son N mumdaki Swing High ve Swing Low bul,
    oradan Fib seviyelerini hesapla.
    Doner: dict mit levels, nearest_level, price, trend
    """
    if len(closes) < lookback:
        lookback = len(closes)
    if lookback < 10:
        return None

    recent_highs  = highs[-lookback:]
    recent_lows   = lows[-lookback:]
    recent_closes = closes[-lookback:]

    swing_high = max(recent_highs)
    swing_low  = min(recent_lows)
    price      = recent_closes[-1]
    diff       = swing_high - swing_low

    if diff == 0:
        return None

    # Fibonacci seviyeleri (retracement)
    levels = {
        "0.0%":   round(swing_high, 5),
        "23.6%":  round(swing_high - 0.236 * diff, 5),
        "38.2%":  round(swing_high - 0.382 * diff, 5),
        "50.0%":  round(swing_high - 0.500 * diff, 5),
        "61.8%":  round(swing_high - 0.618 * diff, 5),
        "78.6%":  round(swing_high - 0.786 * diff, 5),
        "100%":   round(swing_low, 5),
    }

    # Hangi seviyeye en yakin?
    nearest = min(levels.items(), key=lambda x: abs(x[1] - price))
    dist_pct = abs(nearest[1] - price) / price * 100

    # Trend yonu (basit: son kapanis ortalamanin neresinde?)
    avg_close = sum(recent_closes) / len(recent_closes)
    trend = "UP" if price > avg_close else "DOWN"

    # Support mu Resistance mi?
    # Trend UP + fib level altta = SUPPORT
    # Trend DOWN + fib level ustte = RESISTANCE
    sr = "SUPPORT" if trend == "UP" else "RESISTANCE"

    return {
        "swing_high":    round(swing_high, 5),
        "swing_low":     round(swing_low, 5),
        "price":         round(price, 5),
        "levels":        levels,
        "nearest_level": nearest[0],
        "nearest_price": nearest[1],
        "distance_pct":  round(dist_pct, 2),
        "trend":         trend,
        "sr_type":       sr,
    }


# ============================================================
# KOMPLE SINYAL SKORU (Gate-Keeper)
# ============================================================
def berechne_signal_score(sym, epic):
    """
    Tum teknik indikatörleri hesaplar ve bir toplam skor verir.
    Doner: dict mit score, max_score, signal, details, bollinger, fibonacci
    Bu skor Gemini'nin cagrilip cagrilmayacagini belirler.

    Skor Sistemi (max 5):
      1. MA Cross          → +1
      2. ADX > 20          → +1
      3. RSI uygun         → +1
      4. Bollinger uyumu   → +1
      5. Fibonacci uyumu   → +1
    """
    # Kripto icin HOUR_2, Forex/Emtia icin HOUR_4
    resolution = "HOUR_2" if is_crypto(epic) else "HOUR_4"
    data = get_candles(epic, resolution, 55)  # 55 mum: Fib icin yeterli

    closes = data.get('close', [])
    highs  = data.get('high', [])
    lows   = data.get('low', [])

    min_len = min(len(closes), len(highs), len(lows))
    if min_len < 26:
        return {
            "score": 0, "max_score": 5, "signal": "NOTR",
            "details": f"Veri yetersiz ({min_len} mum)",
            "bollinger": None, "fibonacci": None,
            "passed": False
        }

    closes = closes[-min_len:]
    highs  = highs[-min_len:]
    lows   = lows[-min_len:]

    score   = 0
    details = []
    signal  = "NOTR"

    # --- 1. MA Cross ---
    ma9  = hesapla_ma(closes, 9)
    ma26 = hesapla_ma(closes, 26)
    if ma9 and ma26:
        ma_sig = "BUY" if ma9 > ma26 else "SELL"
        score += 1
        details.append(f"MA:{ma_sig}(+1)")
        signal = ma_sig
    else:
        details.append("MA:NOTR(0)")

    # --- 2. ADX ---
    adx    = berechne_adx(highs, lows, closes)
    adx_ok = adx > 20
    if adx_ok:
        score += 1
        details.append(f"ADX:{adx:.1f}(+1)")
    else:
        details.append(f"ADX:{adx:.1f}(0)")

    # --- 3. RSI ---
    rsi    = berechne_rsi(closes)
    rsi_ok = (signal == "BUY" and rsi < 70) or (signal == "SELL" and rsi > 30)
    if rsi_ok:
        score += 1
        details.append(f"RSI:{rsi:.1f}(+1)")
    else:
        details.append(f"RSI:{rsi:.1f}(0)")

    # --- 4. Bollinger Bands ---
    boll = berechne_bollinger(closes, period=20)
    boll_ok = False
    if boll:
        if signal == "BUY"  and boll["position"] in ("NEAR_LOWER", "SQUEEZE"):
            boll_ok = True
        elif signal == "SELL" and boll["position"] in ("NEAR_UPPER", "SQUEEZE"):
            boll_ok = True
        if boll_ok:
            score += 1
            details.append(f"BB:{boll['position']}(+1)")
        else:
            details.append(f"BB:{boll['position']}(0)")
    else:
        details.append("BB:NODATA(0)")

    # --- 5. Fibonacci ---
    fib = berechne_fibonacci(highs, lows, closes, lookback=50)
    fib_ok = False
    if fib:
        # Uyum: Fiyat 38.2% veya 61.8% seviyesine yakin mi?
        key_levels = ["38.2%", "50.0%", "61.8%"]
        if fib["nearest_level"] in key_levels and fib["distance_pct"] <= 1.5:
            fib_ok = True
        if fib_ok:
            score += 1
            details.append(f"FIB:{fib['nearest_level']}@{fib['distance_pct']:.1f}%(+1)")
        else:
            details.append(f"FIB:{fib['nearest_level']}@{fib['distance_pct']:.1f}%(0)")
    else:
        details.append("FIB:NODATA(0)")

    # --- Gate-Keeper Esigi ---
    # Normal: 3/5 | Krypto Haftasonu/Gece: 4/5
    saat = datetime.now().hour
    gece = saat >= 23 or saat < 6
    if is_crypto(epic) and (is_weekend() or gece):
        threshold = 4
    else:
        threshold = 3

    passed = (score >= threshold) and (signal != "NOTR")

    return {
        "score":     score,
        "max_score": 5,
        "signal":    signal,
        "threshold": threshold,
        "passed":    passed,
        "details":   " | ".join(details),
        "adx":       adx,
        "rsi":       rsi,
        "bollinger": boll,
        "fibonacci": fib,
    }



# --- Taglicher Verlust Zaehler ---
def _load_daily_losses():
    try:
        if os.path.exists(DAILY_LOSS_FILE):
            with open(DAILY_LOSS_FILE, 'r') as f:
                d = json.load(f)
            if d.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return d
    except: pass
    return {"date": datetime.now().strftime("%Y-%m-%d"), "losses": {}}

def _save_daily_losses(d):
    try:
        with open(DAILY_LOSS_FILE, 'w') as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        logging.error(f"DailyLoss Fehler: {e}")

def kayip_ekle(sym):
    with daily_loss_lock:
        d = _load_daily_losses()
        d["losses"][sym] = d["losses"].get(sym, 0) + 1
        _save_daily_losses(d)
        logging.info(f"Gunluk kayip: {sym} -> {d['losses'][sym]}x")

def gunluk_kayip_sayisi(sym):
    with daily_loss_lock:
        return _load_daily_losses()["losses"].get(sym, 0)

# ============================================================
# DEPOT DRAWDOWN TRACKER
# ============================================================
DEPOT_DD_FILE  = os.path.join(BASE_DIR, "depot_dd_tracker.json")
DEPOT_DD_LIMIT = -15.0   # % - Demo hesap icin daha genis limit
MAX_DAILY_LOSS_EUR = -80.0  # Demo hesap icin daha genis EUR limiti
depot_dd_lock  = threading.Lock()

def _load_dd_tracker():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(DEPOT_DD_FILE):
            with open(DEPOT_DD_FILE, 'r') as f:
                data = json.load(f)
            # Ayni gun ise yukle
            if data.get("date") == today:
                return data
            # Yeni gun - trading_halt sifirla, peak koru
            # (peak yeni gunun basinda ilk bakiye ile guncellenir)
            logging.info(f"DD Tracker: Yeni gun ({today}), halt sifirlanıyor")
            return {"date": today, "peak_value": 0.0, "trading_halt": False, "halt_reason": ""}
    except: pass
    return {"date": today, "peak_value": 0.0, "trading_halt": False, "halt_reason": ""}

def _save_dd_tracker(data):
    try:
        with open(DEPOT_DD_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"DD Tracker hatasi: {e}")

def update_depot_peak(current_value):
    """Günlük en yüksek değeri güncelle."""
    if current_value <= 0: return
    with depot_dd_lock:
        data = _load_dd_tracker()
        if current_value > data["peak_value"]:
            data["peak_value"] = current_value
            if data["trading_halt"]:
                data["trading_halt"] = False
                data["halt_reason"]  = ""
            _save_dd_tracker(data)

def check_depot_dd(current_value):
    """
    Gunluk DD limitini kontrol et - tum assetler icin gecerli.
    Limit 1: -%10 depot degeri dustu (yuzde bazli)
    Limit 2: -50 EUR mutlak kayip (kucuk hesaplar icin guvenli sinir)
    Geri doner: (halt:bool, sebep:str)
    """
    if current_value <= 0: return False, ""
    with depot_dd_lock:
        data = _load_dd_tracker()
        peak = data["peak_value"]
        if peak <= 0:
            data["peak_value"] = current_value
            _save_dd_tracker(data)
            return False, ""

        dd_pct = (current_value - peak) / peak * 100
        dd_eur = current_value - peak  # Negatif = kayip

        # Limit 1: Yuzde bazli -%5 (kucuk hesaplar icin guncellendi)
        # Limit 2: Mutlak EUR kayip - sabit MAX_DAILY_LOSS_EUR (-40 EUR)
        halt = dd_pct <= DEPOT_DD_LIMIT or dd_eur <= MAX_DAILY_LOSS_EUR

        if halt:
            if not data["trading_halt"]:
                if dd_pct <= DEPOT_DD_LIMIT:
                    reason = (
                        "GUNLUK KAYIP ALARMI: "
                        "Depo degeri %" + str(abs(DEPOT_DD_LIMIT)) + " dustu! "
                        "Peak: " + str(round(peak,2)) + "EUR "
                        "Simdi: " + str(round(current_value,2)) + "EUR "
                        "Kayip: " + str(round(dd_eur,2)) + "EUR ("
                        + str(round(dd_pct,1)) + "%) "
                        "BUGUN YENİ TRADE YOK!"
                    )
                else:
                    reason = (
                        "GUNLUK KAYIP ALARMI: "
                        "EUR kayip limiti asildi! "
                        "Peak: " + str(round(peak,2)) + "EUR "
                        "Simdi: " + str(round(current_value,2)) + "EUR "
                        "Kayip: " + str(round(dd_eur,2)) + "EUR "
                        "BUGUN YENİ TRADE YOK!"
                    )
                data["trading_halt"] = True
                data["halt_reason"]  = reason
                _save_dd_tracker(data)
                logging.warning("DD HALT: " + reason)
                try:
                    bot.send_message(MY_CHAT_ID, reason)
                except: pass
            return True, data["halt_reason"]
        return False, ""

def get_dd_status():
    """DD durumunu döndür."""
    with depot_dd_lock:
        data = _load_dd_tracker()
    return {"peak":  data.get("peak_value", 0),
            "halt":  data.get("trading_halt", False),
            "reason": data.get("halt_reason", ""),
            "date":  data.get("date", "?")}




bot = telebot.TeleBot(TG_TOKEN)

# ============================================================
# TELEGRAM SAFE SEND - Telegram çökünce sadece log'a yazar
# Bot Telegram olmadan da trading yapmaya devam eder
# ============================================================
_tg_disabled = False
_tg_lock = threading.Lock()

# ============================================================
# DEPOT PREFIX - Her mesajda hangi bot/hesap olduğu görünsün
# Birden fazla bot çalıştırırken hangisi olduğunu anlamak için
# ============================================================
_depot_prefix = ""   # Örnek: "[CEo7 | DEMO]" - başlangıçta set edilir
_depot_lock = threading.Lock()

def set_depot_prefix(hesap_adi, hesap_id, is_demo):
    """Bot başlangıcında depot etiketini ayarla."""
    global _depot_prefix
    mod = "DEMO" if is_demo else "LIVE"
    # Hesap adı varsa kullan, yoksa ID'nin son 6 hanesi
    name = hesap_adi if hesap_adi else f"ID:{str(hesap_id)[-6:]}"
    with _depot_lock:
        _depot_prefix = f"[{name} | {mod}]"
    logging.info(f"Depot prefix ayarlandi: {_depot_prefix}")

def get_depot_prefix():
    with _depot_lock:
        return _depot_prefix

def tg_safe_send(msg, reply_markup=None):
    """
    Telegram mesajı güvenli gönder.
    Her mesajın başına depot etiketi eklenir (hangi bot olduğu belli olsun).
    Telegram çalışmıyorsa log'a yazar, bot trading'e devam eder.
    """
    global _tg_disabled
    with _tg_lock:
        disabled = _tg_disabled

    if disabled:
        logging.info(f"[TG_DISABLED] {msg[:100]}")
        return False

    # Depot prefix ekle - başlangıç mesajı hariç (zaten orada var)
    prefix = get_depot_prefix()
    if prefix and not msg.startswith("NEXUS CEO"):
        full_msg = f"{prefix}\n{msg}"
    else:
        full_msg = msg

    try:
        if reply_markup:
            bot.send_message(MY_CHAT_ID, full_msg[:4000], reply_markup=reply_markup)
        else:
            bot.send_message(MY_CHAT_ID, full_msg[:4000])
        return True
    except Exception as e:
        err = str(e).lower()
        logging.warning(f"Telegram hatasi: {e}")
        if any(x in err for x in ["unauthorized", "forbidden", "blocked", "chat not found"]):
            with _tg_lock:
                _tg_disabled = True
            logging.error("Telegram kalıcı hata - bildirimler devre dışı, trading devam ediyor")
        return False

# ============================================================
# REPLY KEYBOARD MENU - Her zaman ekranda gorunur
# ============================================================
from telebot.types import (ReplyKeyboardMarkup, KeyboardButton,
                            InlineKeyboardMarkup, InlineKeyboardButton)

def get_nexus_reply_menu():
    """
    ReplyKeyboard — her zaman ekranin altinda gorunur.
    Giris alaninin solundaki buton gibi calisir.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        KeyboardButton("📊 Status"),
        KeyboardButton("📍 Pozisyon"),
        KeyboardButton("📈 Sinyaller"),
    )
    markup.add(
        KeyboardButton("📰 Haberler"),
        KeyboardButton("💸 Kayip"),
        KeyboardButton("🔒 Bloklar"),
    )
    markup.add(
        KeyboardButton("📋 Menü"),
        KeyboardButton("❓ Yardım"),
        KeyboardButton("🧮 Stats"),
    )
    return markup

def get_nexus_inline_menu():
    """
    Inline Keyboard — /menu yazinca gelen detayli buton paneli.
    """
    kb = InlineKeyboardMarkup(row_width=3)

    kb.add(
        InlineKeyboardButton("📊 Status",     callback_data="cmd_status"),
        InlineKeyboardButton("📍 Pozisyon",   callback_data="cmd_pozisyon"),
        InlineKeyboardButton("📈 MA/ADX/RSI", callback_data="cmd_ma"),
    )
    kb.add(
        InlineKeyboardButton("🧮 Stats",      callback_data="cmd_stats"),
        InlineKeyboardButton("📰 Haberler",   callback_data="cmd_news"),
        InlineKeyboardButton("📡 Haber Topla",callback_data="cmd_newscollect"),
    )
    kb.add(
        InlineKeyboardButton("⚡ Volatilite", callback_data="cmd_volatilite"),
        InlineKeyboardButton("📏 Spread",     callback_data="cmd_spread"),
        InlineKeyboardButton("💸 Kayip",      callback_data="cmd_kayip"),
    )
    kb.add(
        InlineKeyboardButton("🔬 Backtest",   callback_data="cmd_backtest"),
        InlineKeyboardButton("🔭 DeepDive",   callback_data="cmd_deepdive"),
        InlineKeyboardButton("🌐 Kaynaklar",  callback_data="cmd_sources"),
    )
    kb.add(
        InlineKeyboardButton("🔒 Bloklar",    callback_data="cmd_bloklar"),
        InlineKeyboardButton("🗑️ Unut",       callback_data="cmd_unut"),
        InlineKeyboardButton("❓ Yardım",     callback_data="cmd_help"),
    )
    return kb

NEXUS_MENU        = get_nexus_reply_menu()
NEXUS_INLINE_MENU = get_nexus_inline_menu()

# ============================================================
# PYRAMIDING TAKIP - JSON-Datei (bleibt nach Neustart erhalten)
# ============================================================
PYRAMIDING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyramiding_state.json")
pyramiding_lock = threading.Lock()

def _load_pyramiding():
    try:
        if os.path.exists(PYRAMIDING_FILE):
            with open(PYRAMIDING_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.warning(f"Pyramiding-Datei Lesefehler: {e}")
    return {}

def _save_pyramiding(data):
    try:
        with open(PYRAMIDING_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Pyramiding-Datei Schreibfehler: {e}")

def get_pyramiding_stufe(epic):
    with pyramiding_lock:
        return _load_pyramiding().get(epic, 0)

def set_pyramiding_stufe(epic, stufe):
    with pyramiding_lock:
        data = _load_pyramiding()
        data[epic] = stufe
        _save_pyramiding(data)

def reset_pyramiding_stufe(epic):
    with pyramiding_lock:
        data = _load_pyramiding()
        if epic in data:
            del data[epic]
        _save_pyramiding(data)

def sync_pyramiding_from_capital():
    try:
        h = capital_session.get_headers()
    except Exception as e:
        return f"Pyramiding-Sync: Session nicht bereit ({e})"
    if not h: return "Piramiding-Senkron: API bağlantısı yok"
    try:
        pozisyonlar = get_positions(h)
    except Exception as e:
        return f"Pyramiding-Sync Fehler: {e}"
    epic_count = {}
    for p in pozisyonlar:
        epic = p['market']['epic']
        epic_count[epic] = epic_count.get(epic, 0) + 1
    with pyramiding_lock:
        alte_daten = _load_pyramiding()
        korrekturen = []
        for epic, anzahl in epic_count.items():
            if alte_daten.get(epic, 0) != anzahl:
                korrekturen.append(f"  {epic}: {alte_daten.get(epic,0)} -> {anzahl} (düzeltildi)")
        for epic in alte_daten:
            if epic not in epic_count:
                korrekturen.append(f"  {epic}: {alte_daten[epic]} -> 0 (kapatıldı)")
        _save_pyramiding(epic_count)
    if korrekturen:
        return "Pyramiding-Sync korrigiert:\n" + "\n".join(korrekturen)
    return f"Pyramiding-Sync: {len(epic_count)} Epics korrekt"

# ============================================================
# CAPITAL.COM HELPERS (SESSION CACHING)
# ============================================================
class CapitalSession:
    """
    Capital.com session yoneticisi.
    v13.2 ile ayni sade sistem - calistigini bildigimiz yontem.
    Login sirasinda accountId veriliyor, X-CAP-ACCOUNT-ID her istekte gidiyor.
    """
    def __init__(self):
        self.cst     = None
        self.token   = None
        self.expires = 0
        self.lock    = threading.Lock()

    def get_headers(self):
        with self.lock:
            if time.time() < self.expires and self.cst:
                return {
                    "X-CAP-API-KEY":    CAP_KEY,
                    "CST":              self.cst,
                    "X-SECURITY-TOKEN": self.token,
                    "Content-Type":     "application/json",
                    **( {"X-CAP-ACCOUNT-ID": str(TARGET_ACCOUNT_ID)} if TARGET_ACCOUNT_ID else {} )
                }
            try:
                login_payload = {"identifier": CAP_ID, "password": CAP_PW}
                if TARGET_ACCOUNT_ID:
                    login_payload["accountId"] = TARGET_ACCOUNT_ID
                r = requests.post(
                    f"{CAPITAL_URL}/session",
                    json=login_payload,
                    headers={"X-CAP-API-KEY": CAP_KEY},
                    timeout=15
                )
                if r.status_code == 200:
                    self.cst     = r.headers.get("CST")
                    self.token   = r.headers.get("X-SECURITY-TOKEN")
                    self.expires = time.time() + 1200
                    mod_info     = "DEMO" if IS_DEMO else "CANLI"
                    acc_info     = f"(ID: {TARGET_ACCOUNT_ID})" if TARGET_ACCOUNT_ID else "(ilk hesap)"
                    logging.info(f"✅ Session olusturuldu - {mod_info} {acc_info}")
                    return {
                        "X-CAP-API-KEY":    CAP_KEY,
                        "CST":              self.cst,
                        "X-SECURITY-TOKEN": self.token,
                        "Content-Type":     "application/json",
                        **( {"X-CAP-ACCOUNT-ID": str(TARGET_ACCOUNT_ID)} if TARGET_ACCOUNT_ID else {} )
                    }
            except Exception as e:
                logging.error(f"Session hatasi: {e}")
            return None


capital_session = CapitalSession()

def get_positions(h):
    try:
        return requests.get(f"{CAPITAL_URL}/positions", headers=h, timeout=10).json().get('positions', [])
    except:
        return []

def get_account_info(h):
    try:
        acc_req = requests.get(f"{CAPITAL_URL}/accounts", headers=h, timeout=10).json()
        if not acc_req.get('accounts'):
            logging.error("Hesap listesi bos - Capital.com session hatasi")
            return None
        # TARGET_ACCOUNT_ID varsa o hesabi sec, yoksa ilk hesabi kullan
        accounts = acc_req['accounts']
        acc = None
        if TARGET_ACCOUNT_ID:
            for a in accounts:
                if str(a.get('accountId','')) == str(TARGET_ACCOUNT_ID):
                    acc = a
                    break
        if not acc:
            acc = accounts[0]
            if TARGET_ACCOUNT_ID:
                logging.warning(f"Hesap ID {TARGET_ACCOUNT_ID} bulunamadi - ilk hesap kullaniliyor")
        return {
            "nakit": acc['balance'].get('balance', 0),
            "toplam": acc['balance'].get('deposit', 0),
            "upl": acc['balance'].get('profitLoss', 0),
            "marjin": 0,
            "musait": acc['balance'].get('available', 0),
            "hesap_id": acc.get('accountId', ''),
            "hesap_adi": acc.get('accountName', '')
        }
    except:
        return {"nakit": 0, "toplam": 0, "upl": 0, "marjin": 0, "musait": 0}

# ============================================================
# INDIKATOREN (ADX, RSI, MA)
# ============================================================
def berechne_adx(highs, lows, closes, period=14):
    if len(closes) < period + 1: return 0
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
        up = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
    avg_tr = sum(tr_list[-period:]) / period
    avg_plus = sum(plus_dm[-period:]) / period
    avg_minus = sum(minus_dm[-period:]) / period
    if avg_tr == 0: return 0
    plus_di = (avg_plus / avg_tr) * 100
    minus_di = (avg_minus / avg_tr) * 100
    if (plus_di + minus_di) == 0: return 0
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    return dx

def berechne_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = 0, 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0: gains += diff
        else: losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def hesapla_ma(prices, period):
    if len(prices) < period: return None
    return sum(prices[-period:]) / period

def get_candles(epic, resolution, max_candles=30):
    h = capital_session.get_headers()
    if not h: return {'close': [], 'high': [], 'low': []}
    try:
        url = f"{CAPITAL_URL}/prices/{epic}?resolution={resolution}&max={max_candles}"
        r = requests.get(url, headers=h, timeout=15)
        if r.status_code == 200:
            prices_data = r.json().get('prices', [])
            closes, highs, lows = [], [], []
            for p in prices_data:
                c = p.get('closePrice', {}).get('bid', None)
                h_val = p.get('highPrice', {}).get('bid', None)  # FIX: highPrice statt high
                l_val = p.get('lowPrice', {}).get('bid', None)   # FIX: lowPrice statt low
                if c is not None: closes.append(float(c))
                if h_val is not None: highs.append(float(h_val))
                if l_val is not None: lows.append(float(l_val))
            return {'close': closes, 'high': highs, 'low': lows}
    except Exception as e:
        logging.warning(f"Mum verisi alinamadi {epic}/{resolution}: {e}")
    return {'close': [], 'high': [], 'low': []}

# ============================================================
# 2-of-3 TEKNİK KONTROL (MA + ADX + RSI) - BUGFIX
# ============================================================
def _analyse_timeframe(epic, resolution, max_candles=30):
    """Tek bir timeframe için MA/ADX/RSI analizi. (sinyal, guc, detay) döner."""
    data = get_candles(epic, resolution, max_candles)
    closes = data.get('close', [])
    highs  = data.get('high', [])
    lows   = data.get('low', [])

    min_len = min(len(closes), len(highs), len(lows))
    if min_len < 26:
        return "NOTR", 0, f"Veri yetersiz ({min_len} mum)"

    closes = closes[-min_len:]
    highs  = highs[-min_len:]
    lows   = lows[-min_len:]

    ma9  = hesapla_ma(closes, 9)
    ma26 = hesapla_ma(closes, 26)
    if ma9 is None or ma26 is None:
        return "NOTR", 0, "MA hesaplanamadı"
    ma_signal = "BUY" if ma9 > ma26 else "SELL" if ma9 < ma26 else "NOTR"

    adx    = berechne_adx(highs, lows, closes)
    adx_ok = adx > 20

    rsi    = berechne_rsi(closes)
    rsi_ok = (ma_signal == "BUY" and rsi < 70) or (ma_signal == "SELL" and rsi > 30)

    score = (1 if ma_signal != "NOTR" else 0) + (1 if adx_ok else 0) + (1 if rsi_ok else 0)
    details = f"MA:{ma_signal} ADX:{adx:.1f} RSI:{rsi:.1f}"
    return ma_signal, score, details


def technical_confluence(epic):
    """
    Kripto: 3 timeframe analizi (20min + 45min + 2h).
      - Giriş:      MINUTE_20
      - Ara trend:  MINUTE_45
      - Üst trend:  HOUR_2
      Tüm 3 timeframe aynı yönü gösterirse puan artar.
      En az 2/3 timeframe + her birinde min 2/3 indikatör uyumu gerekir.

    Forex/Emtia: Mevcut HOUR_4 analizi (değişmedi).
    """
    if is_crypto(epic):
        # --- KRİPTO: ÇOK ZAMANLI ANALİZ ---
        s20,  g20,  d20  = _analyse_timeframe(epic, "MINUTE_20",  35)
        s45,  g45,  d45  = _analyse_timeframe(epic, "MINUTE_45",  35)
        s2h,  g2h,  d2h  = _analyse_timeframe(epic, "HOUR_2",     30)

        signals = [s20, s45, s2h]
        scores  = [g20, g45, g2h]

        # Kaç timeframe net yön gösteriyor?
        buy_tf  = signals.count("BUY")
        sell_tf = signals.count("SELL")

        if buy_tf >= 2:
            master_signal = "BUY"
            tf_count = buy_tf
        elif sell_tf >= 2:
            master_signal = "SELL"
            tf_count = sell_tf
        else:
            details = f"20m:{s20}({g20}) 45m:{s45}({g45}) 2h:{s2h}({g2h})"
            return "NOTR", 0, f"TF uyumsuz | {details}"

        # Ortalama indikatör skoru (sadece uyumlu TF'ler)
        uyumlu_scores = [scores[i] for i, s in enumerate(signals) if s == master_signal]
        avg_score = sum(uyumlu_scores) / len(uyumlu_scores) if uyumlu_scores else 0

        # Nihai güç: TF sayısı (2 veya 3) * ortalama indikatör skoru
        # Normalize: max = 3*3=9, biz 0-3 aralığına map edelim
        raw_power = tf_count * avg_score          # max 9
        guc = 3 if raw_power >= 6 else 2 if raw_power >= 3 else 1

        details = (f"20m:{s20}({g20}/3) 45m:{s45}({g45}/3) 2h:{s2h}({g2h}/3) "
                   f"→ {tf_count}/3 TF uyumlu")

        if guc >= 2:
            return master_signal, guc, details
        else:
            return "NOTR", guc, f"Sinyal zayıf | {details}"

    else:
        # --- FOREX / EMTİA: Mevcut HOUR_4 analizi ---
        sinyal, guc, details = _analyse_timeframe(epic, "HOUR_4", 30)
        if guc >= 2:
            return sinyal, guc, details
        return "NOTR", guc, details

# ============================================================
# SPREAD IN capital_markets_config.py SCHREIBEN
# ============================================================
def update_spreads_in_config(spread_data: dict):
    """
    Schreibt aktuelle Spreads in capital_markets_config.py.
    spread_data = {"EURUSD": 0.00012, "BTCUSD": 15.3, ...}
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capital_markets_config.py")
    if not os.path.exists(config_path):
        logging.warning("capital_markets_config.py nicht gefunden - Spread-Update übersprungen")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        for symbol, spread in spread_data.items():
            # Suche nach "SYMBOL": { ... } und füge/ersetze "spread": X ein
            # Pattern: Eintrag für dieses Symbol finden
            pattern = rf'("{symbol}"\s*:\s*\{{[^}}]*?)(\}})'
            def replacer(m, sym=symbol, sp=spread):
                block = m.group(1)
                closing = m.group(2)
                if '"spread"' in block:
                    # Ersetze bestehenden spread-Wert
                    block = re.sub(r'"spread"\s*:\s*[\d\.]+', f'"spread": {sp:.6f}', block)
                else:
                    # Füge spread am Ende des Blocks hinzu
                    block = block.rstrip() + f',\n        "spread": {sp:.6f}\n    '
                return block + closing

            new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
            content = new_content

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"✅ Spreads in capital_markets_config.py aktualisiert ({len(spread_data)} Assets)")
    except Exception as e:
        logging.error(f"Spread-Schreibfehler: {e}")


def scan_and_write_spreads():
    """Liest aktuelle Spreads von Capital.com und schreibt sie in die Config."""
    h = capital_session.get_headers()
    if not h:
        return {}

    spread_data = {}
    for sym, cfg in MARKET_CONFIG.items():
        try:
            epic = cfg["epic"]
            r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=10)
            if r.status_code == 200:
                snapshot = r.json().get('snapshot', {})
                bid = snapshot.get('bid', 0)
                offer = snapshot.get('offer', 0)
                if bid and offer:
                    spread = round(abs(offer - bid), 6)
                    spread_data[sym] = spread
        except Exception as e:
            logging.warning(f"Spread-Scan Fehler {sym}: {e}")

    if spread_data:
        update_spreads_in_config(spread_data)

    return spread_data

# ============================================================
# SPREAD & WEEKEND KONTROL
# ============================================================
def check_spread_ok(epic, spread):
    if spread > MAX_SPREAD: return False, f"Spread çok yüksek: {spread}"
    return True, "OK"

def is_weekend():
    return datetime.now().weekday() >= 5

def is_crypto(sym_key):
    # EXAKTE Pruefung - kein Teilstring-Match!
    # Verhindert: "SOL" in "GASOLINE" = True
    crypto_config_keys = {
        "ETH_USD", "ETH_EUR", "SOL_USD", "SOL_EUR",
        "XRP_USD", "XRP_EUR", "ADA_USD", "ADA_EUR",
        "LTC_USD", "LTC_EUR", "BTC_USD", "BTC_EUR",
        "DOT_USD", "DOT_EUR", "AVAX_USD", "AVAX_EUR",
        "LINK_USD", "LINK_EUR", "UNI_USD", "UNI_EUR",
        "AAVE_USD", "AAVE_EUR", "ATOM_USD", "ATOM_EUR",
        "ALGO_USD", "ALGO_EUR", "VET_USD", "VET_EUR",
        "HBAR_USD", "HBAR_EUR", "IOTA_USD", "IOTA_EUR",
        "EOS_USD", "EOS_EUR", "TRX_USD", "TRX_EUR",
        "XTZ_USD", "XTZ_EUR", "XLM_USD", "XLM_EUR",
        "MATIC_USD", "MATIC_EUR", "POL_USD", "POL_EUR",
    }
    crypto_epics = {
        "ETHUSD", "ETHEUR", "SOLUSD", "SOLEUR",
        "XRPUSD", "XRPEUR", "ADAUSD", "ADAEUR",
        "LTCUSD", "LTCEUR", "BTCUSD", "BTCEUR",
        "DOTUSD", "DOTEUR", "AVAXUSD", "AVAXEUR",
        "LINKUSD", "LINKEUR", "UNIUSD", "UNIEUR",
        "AAVEUSD", "AAVEEUR", "ATOMUSD", "ATOMEUR",
        "ALGOUSD", "ALGOEUR", "VETUSD", "VETEUR",
        "HBARUSD", "HBAREUR", "IOTAUSD", "IOTAEUR",
        "EOSUSD", "EOSEUR", "TRXUSD", "TRXEUR",
        "XTZUSD", "XTZEUR", "XLMUSD", "XLMEUR",
        "MATICUSD", "MATICEUR", "POLUSD", "POLEUR",
    }
    if sym_key.upper() in crypto_config_keys:
        return True
    if sym_key in MARKET_CONFIG:
        epic = MARKET_CONFIG[sym_key].get("epic", "").upper()
        if epic in crypto_epics:
            return True
    return False

def check_weekend_allowed(sym_key):
    if is_weekend():
        if not is_crypto(sym_key): return False, "Haftasonu: Sadece kripto!"
        if sym_key.upper() not in WEEKEND_CRYPTO_WHITELIST:
            return False, f"Haftasonu: {sym_key} yasak (sadece BTC/ETH/SOL/XRP)"
        return True, "Kripto haftasonu acik"
    return True, "Hafta ici"

# ============================================================
# VOLATILITE KORUMA (KARA KUĞU)
# ============================================================

def gemini_emergency_call(instrument, sym, direction, degisim_pct, upl, entry_price, current_price):
    """Kurzer Gemini-Call bei -8%% bis -12%%. Gibt KAPAT/HEDGE/TUT zurueck."""
    fg = get_fear_greed()
    prompt = (
        f"KARA KUGU ACIL KARAR!\n\n"
        f"Asset:{instrument} Yon:{direction}\n"
        f"Degisim:{degisim_pct:.1f}%% Zarar:{upl:.2f}EUR\n"
        f"Fear&Greed:{fg['value']}/100\n\n"
        f"SADECE BIR SECENEK YAZ:\n"
        f"KAPAT - Kapat\nHEDGE - Karsı pozisyon\nTUT - Bekle (max 1 kez)\n\n"
        f"Sonra 1 cumle gerekcE."
    )
    sys_msg = "Acil kriz. Hizli karar. Sadece KAPAT, HEDGE veya TUT yaz."

    # Once Gemini dene
    if GEMINI_KEYS:
        try:
            key = GEMINI_KEYS[0]
            response = genai.Client(api_key=key).models.generate_content(
                model="gemini-3-flash-preview", contents=prompt,
                config=types.GenerateContentConfig(system_instruction=sys_msg)
            )
            text = response.text.strip().upper()
            karar = "KAPAT" if "KAPAT" in text[:20] else ("HEDGE" if "HEDGE" in text[:20] else ("TUT" if "TUT" in text[:20] else "KAPAT"))
            try: db_gemini_write("EMERGENCY", f"{sym} {degisim_pct:.1f}%% karar:{karar}", sym)
            except: pass
            logging.info(f"Emergency Gemini: {sym} → {karar}")
            return karar, text[:150]
        except Exception as e:
            logging.warning(f"Emergency Gemini hatasi: {e}")

    # Groq fallback
    groq_client = get_groq_client()
    if groq_client:
        # Emergency icin en hizli model
        emergency_models = [get_optimal_groq_model("emergency")] + [m for m in GROQ_MODELS if m != get_optimal_groq_model("emergency")][:2]
        for model in emergency_models:
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user",   "content": prompt[:2000]}  # Emergency kisa tut
                    ],
                    max_tokens=100, temperature=0.1,
                )
                text = resp.choices[0].message.content.strip().upper()
                karar = "KAPAT" if "KAPAT" in text[:20] else ("HEDGE" if "HEDGE" in text[:20] else ("TUT" if "TUT" in text[:20] else "KAPAT"))
                logging.info(f"Emergency Groq ({model}): {sym} → {karar}")
                return karar, text[:150]
            except Exception as e:
                logging.warning(f"Emergency Groq {model}: {e}")

    return "KAPAT", "Tum AI modelleri basarisiz - guvenli: KAPAT"


_tut_tracker = {}
_tut_lock    = threading.Lock()
def tut_kullanildi_mi(deal_id):
    with _tut_lock: return _tut_tracker.get(deal_id, False)
def tut_olarak_isaretle(deal_id):
    with _tut_lock: _tut_tracker[deal_id] = True

def volatilite_kontrol(h):
    """
    3 Katmanli Black Swan Korumasi:
    -8%  bis -12%: Gemini Emergency Call
    -12% bis -18%: Otomatik kapat
    >-18%:         NOTFALL - tum pozisyonlari kapat
    """
    pozisyonlar = get_positions(h)
    kapatilanlar = []

    # NOTFALL KONTROL ONCE: Herhangi biri >-18% mi?
    notfall_mode = False
    for p in pozisyonlar:
        try:
            level       = float(p['position']['level'])
            current_bid = float(p['market'].get('bid', level))
            direction   = p['position']['direction']
            if level > 0:
                chg = (current_bid-level)/level*100 if direction=="BUY" else (level-current_bid)/level*100
                if chg <= KARA_KUGU_NOTFALL_THRESHOLD:
                    notfall_mode = True
                    break
        except: pass

    if notfall_mode:
        logging.error("NOTFALL MODU! Tum pozisyonlar kapatiliyor!")
        try:
            bot.send_message(MY_CHAT_ID,
                f"KARA KUĞU ACİL!\n>%{abs(KARA_KUGU_NOTFALL_THRESHOLD):.0f} kayıp!\nTÜM POZİSYONLAR KAPATILIYOR!")
        except: pass
        for p in pozisyonlar:
            try:
                deal_id    = p['position']['dealId']
                epic       = p['market']['epic']
                instrument = p['market']['instrumentName']
                upl        = float(p['position']['upl'])
                bid        = float(p['market'].get('bid', 0))
                r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                if r.status_code == 200:
                    kapatilanlar.append(f"NOTFALL-KAPAT {instrument}: {upl:.2f}EUR")
                    reset_pyramiding_stufe(epic)
                    sym = next((_s for _s,_c in MARKET_CONFIG.items() if _c.get("epic")==epic), None)
                    if sym:
                        kayip_ekle(sym)
                        try:
                            with db_lock:
                                conn = sqlite3.connect(DB_FILE)
                                ot = conn.execute("SELECT trade_id FROM trades WHERE symbol=? AND status='OPEN' ORDER BY entry_time DESC LIMIT 1",(sym,)).fetchone()
                                conn.close()
                            if ot: db_close_trade(ot[0], bid, upl, 'NOTFALL')
                        except: pass
                        db_gemini_write("NOTFALL", f"NOTFALL {instrument} {upl:.2f}EUR", sym)
            except Exception as e:
                logging.error(f"Notfall kapat: {e}")
        if kapatilanlar:
            try: bot.send_message(MY_CHAT_ID, "ACİL KAPATMA TAMAMLANDI:\n"+"\n".join(kapatilanlar))
            except: pass
        return kapatilanlar

    # NORMAL: Pozisyon bazli 3-stufen kontrol
    for p in pozisyonlar:
        try:
            epic        = p['market']['epic']
            upl         = float(p['position']['upl'])
            level       = float(p['position']['level'])
            current_bid = float(p['market'].get('bid', level))
            direction   = p['position']['direction']
            deal_id     = p['position']['dealId']
            instrument  = p['market']['instrumentName']
            if level <= 0: continue

            if direction == "BUY":
                degisim_pct = (current_bid - level) / level * 100
            else:
                degisim_pct = (level - current_bid) / level * 100

            sym = next((_s for _s,_c in MARKET_CONFIG.items() if _c.get("epic")==epic), None)

            # STUFE 1: -8% bis -12% -> Gemini Emergency
            if KARA_KUGU_GEMINI_THRESHOLD >= degisim_pct > KARA_KUGU_AUTO_THRESHOLD:
                logging.warning(f"KARA KUGU UYARI [{degisim_pct:.1f}%]: {instrument}")
                if tut_kullanildi_mi(deal_id):
                    karar, gerekce = "KAPAT", "TUT hakki bitti"
                else:
                    karar, gerekce = gemini_emergency_call(
                        instrument, sym or epic, direction,
                        degisim_pct, upl, level, current_bid)
                try:
                    bot.send_message(MY_CHAT_ID,
                        f"KARA KUGU ({degisim_pct:.1f}%)\n"
                        f"Asset: {instrument} | UPL:{upl:.2f}EUR\n"
                        f"Gemini: {karar} - {gerekce[:80]}")
                except: pass

                if karar == "KAPAT":
                    r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                    if r.status_code == 200:
                        kapatilanlar.append(f"KARA_KUGU(Gemini→KAPAT) {instrument}: {degisim_pct:.1f}%")
                        reset_pyramiding_stufe(epic)
                        if sym:
                            kayip_ekle(sym)
                            try:
                                with db_lock:
                                    conn = sqlite3.connect(DB_FILE)
                                    ot = conn.execute("SELECT trade_id FROM trades WHERE symbol=? AND status='OPEN' ORDER BY entry_time DESC LIMIT 1",(sym,)).fetchone()
                                    conn.close()
                                if ot: db_close_trade(ot[0], current_bid, upl, 'KARA_KUGU_GEMINI')
                            except: pass
                elif karar == "HEDGE":
                    hedge_side = "SELL" if direction=="BUY" else "BUY"
                    r = requests.post(f"{CAPITAL_URL}/positions",
                        json={"epic":epic,"direction":hedge_side,
                              "size":float(p['position']['size']),"type":"MARKET"},
                        headers=h, timeout=10)
                    if r.status_code == 200:
                        kapatilanlar.append(f"KARA_KUGU(Gemini→HEDGE) {instrument}: {hedge_side}")
                        if sym: db_gemini_write("HEDGE", f"Emergency hedge {instrument}", sym)
                    else:
                        requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                        kapatilanlar.append(f"KARA_KUGU(Hedge→KAPAT) {instrument}: hedge basarisiz")
                elif karar == "TUT":
                    tut_olarak_isaretle(deal_id)
                    kapatilanlar.append(f"KARA_KUGU(Gemini→TUT) {instrument}: 1x TUT kullanildi")

            # STUFE 2: -12% bis -18% -> Otomatik kapat
            elif KARA_KUGU_AUTO_THRESHOLD >= degisim_pct > KARA_KUGU_NOTFALL_THRESHOLD:
                logging.warning(f"KARA KUGU AUTO [{degisim_pct:.1f}%]: {instrument}")
                r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                if r.status_code == 200:
                    kapatilanlar.append(f"KARA_KUGU(AUTO) {instrument}: {degisim_pct:.1f}% | {upl:.2f}EUR")
                    reset_pyramiding_stufe(epic)
                    if sym:
                        kayip_ekle(sym)
                        try:
                            with db_lock:
                                conn = sqlite3.connect(DB_FILE)
                                ot = conn.execute("SELECT trade_id FROM trades WHERE symbol=? AND status='OPEN' ORDER BY entry_time DESC LIMIT 1",(sym,)).fetchone()
                                conn.close()
                            if ot: db_close_trade(ot[0], current_bid, upl, 'AUTO_CLOSE')
                        except: pass
                        db_gemini_write("AUTO_CLOSE", f"Auto-close {instrument} {degisim_pct:.1f}%", sym)

        except Exception as e:
            logging.error(f"Volatilite hatasi: {e}")

    if kapatilanlar:
        try: bot.send_message(MY_CHAT_ID, "KARA KUĞU ALARMI!\n"+"\n".join(kapatilanlar))
        except: pass
    return kapatilanlar

# ============================================================
# PYRAMIDING & DOKTRIN
# ============================================================
def pyramiding_kontrol(h, epic, instrument):
    stufe = get_pyramiding_stufe(epic)
    # Pyramiding limit kaldirildi - Gemini veya Trailing SL karar verir
    pozisyonlar = get_positions(h)
    epic_pozisyonlar = [p for p in pozisyonlar if p['market']['epic'] == epic]
    if not epic_pozisyonlar: return True, "Ilk giris"
    for p in epic_pozisyonlar:
        upl = float(p['position']['upl'])
        level = float(p['position']['level'])
        size = float(p['position']['size'])
        if level > 0 and size > 0:
            maliyet = level * size
            if maliyet > 0:
                kar_pct = (upl / maliyet) * 100
                if kar_pct >= 2.0: return True, f"Pozisyon %{kar_pct:.1f} karda - Pyramiding izinli"
                else: return False, f"Pozisyon sadece %{kar_pct:.1f} karda - Min %2 gerekli"
    return False, "Pyramiding icin yeterli kar yok"



# ============================================================
# TRAILING STOP LOSS - Pyramiding pozisyonlari icin
# ============================================================
TRAILING_SL_FILE = os.path.join(BASE_DIR, "trailing_sl_state.json")
trailing_sl_lock = threading.Lock()

def _load_trailing_state():
    try:
        if os.path.exists(TRAILING_SL_FILE):
            with open(TRAILING_SL_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def _save_trailing_state(state):
    try:
        with open(TRAILING_SL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Trailing SL kayit: {e}")

def update_trailing_sl(h):
    """
    PYRAMIDING TRAILING SL - %5 sabit, tum seviyelerden bastan.

    Stufe 1: Pos1 SL = guncel * 0.95
    Stufe 2: Pos1 + Pos2 SL = ayni seviye (yeni peak * 0.95)
    Stufe 3: Pos1 + Pos2 + Pos3 SL = ayni seviye
    Stufe N: Hepsi ayni SL (sinir yok)
    SL asla geri gitmez.
    """
    TRAIL_PCT = 0.05

    try:
        pozisyonlar = get_positions(h)
        if not pozisyonlar:
            return 0

        state   = _load_trailing_state()
        updated = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        epic_groups = {}
        for p in pozisyonlar:
            epic = p["market"]["epic"]
            if epic not in epic_groups:
                epic_groups[epic] = []
            epic_groups[epic].append(p)

        for epic, positions in epic_groups.items():
            try:
                # Hafta sonu: sadece kripto pozisyonlari icin Trailing SL
                # Diger assetler kapali - gereksiz API cagrisi ve mesaj yok
                if is_weekend() and not is_crypto(epic):
                    logging.debug(f"Trailing SL hafta sonu atlandi: {epic}")
                    continue

                direction  = positions[0]["position"]["direction"]
                instrument = positions[0]["market"].get("instrumentName", epic)
                stufe      = get_pyramiding_stufe(epic)
                current    = float(positions[0]["market"].get("bid", 0))
                if current <= 0:
                    continue

                peak_key = "peak_" + epic + "_" + direction
                old_peak = state.get(peak_key, {}).get("value", 0)
                peak = old_peak if old_peak > 0 else current

                if direction == "BUY":
                    peak = max(peak, current)
                    target_sl = round(peak * (1 - TRAIL_PCT), 5)
                else:
                    if peak == 0 or current < peak:
                        peak = current
                    target_sl = round(peak * (1 + TRAIL_PCT), 5)

                # Peak degismediyse hic islem yapma - mesaj gonderme
                peak_changed = abs(peak - old_peak) > 0.00001
                if not peak_changed:
                    logging.debug(f"Trailing SL: {instrument} peak degismedi ({peak}) - atlanıyor")
                    continue

                # Peak degisti - SL guncelle
                any_updated = False
                for p in positions:
                    deal_id = p["position"]["dealId"]
                    cur_sl  = float(p["position"].get("stopLevel", 0) or 0)
                    entry   = float(p["position"]["level"])

                    if direction == "BUY":
                        if cur_sl > 0 and target_sl <= cur_sl:
                            continue
                        final_sl = max(target_sl, round(entry * 0.90, 5))
                    else:
                        if cur_sl > 0 and target_sl >= cur_sl:
                            continue
                        final_sl = min(target_sl, round(entry * 1.10, 5))

                    r = requests.put(
                        CAPITAL_URL + "/positions/" + deal_id,
                        json={"stopLevel": final_sl},
                        headers=h, timeout=10
                    )
                    if r.status_code == 200:
                        updated += 1
                        any_updated = True
                        logging.info(
                            "Trailing SL guncellendi: " + instrument + " " + direction +
                            " Peak:" + str(round(peak, 5)) +
                            " SL:" + str(round(cur_sl, 5)) +
                            "->" + str(final_sl)
                        )
                    else:
                        logging.warning(
                            "Trailing SL basarisiz " + instrument +
                            ": " + str(r.status_code)
                        )

                state[peak_key] = {"value": peak, "updated": now_str}

                # Mesaj SADECE peak yukseldiginde (SL gercekten guncellendi)
                if any_updated:
                    n_pos = len(positions)
                    msg = (
                        "📈 Trailing SL: " + instrument + " " + direction +
                        " Sv." + str(stufe) + "\n" +
                        str(n_pos) + " poz | Yeni Peak:" + str(round(peak, 5)) + "\n" +
                        "SL yukseltildi: " + str(final_sl) + " (-%" + str(int(TRAIL_PCT*100)) + ")"
                    )
                    try:
                        bot.send_message(MY_CHAT_ID, msg)
                    except:
                        pass

            except Exception as e:
                logging.warning("Trailing SL epic " + str(epic) + ": " + str(e))

        if updated > 0:
            _save_trailing_state(state)
        return updated

    except Exception as e:
        logging.error("Trailing SL: " + str(e))
        return 0


def load_sources():
    """
    toplam_egitim.txt dosyasini GitHub'dan okur.
    X hesaplari ve haber linklerini ayirir.
    Blacklisted kaynaklari (source_credibility DB) filtreler.
    Doner: {"x_accounts": [...], "news_sites": [...], "all": [...]}
    """
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/KhungFu/nexus/refs/heads/main/toplam_egitim.txt",
            timeout=10
        )
        if r.status_code != 200:
            return {"x_accounts": [], "news_sites": [], "all": []}

        lines = r.text.splitlines()
        x_accounts = []
        news_sites  = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # X / Twitter hesaplari
            if 'x.com/' in line.lower() or 'twitter.com/' in line.lower():
                handle = line.split('x.com/')[-1].split('/')[0].strip()
                if handle:
                    x_accounts.append({"handle": f"@{handle}", "url": line})
            # Haber siteleri (youtube haric)
            elif line.startswith('http') and 'youtube.com' not in line.lower():
                news_sites.append(line)

        # Blacklisted kaynaklari filtrele
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            blacklisted = set(row[0] for row in conn.execute(
                "SELECT source_name FROM source_credibility WHERE blacklisted=1"
            ).fetchall())
            conn.close()

        x_accounts = [x for x in x_accounts if x["handle"] not in blacklisted]
        news_sites  = [s for s in news_sites  if s not in blacklisted]

        all_sources = [x["handle"] for x in x_accounts] + news_sites
        logging.info(f"Kaynaklar yuklendi: {len(x_accounts)} X hesabi, {len(news_sites)} haber sitesi")
        return {"x_accounts": x_accounts, "news_sites": news_sites, "all": all_sources}

    except Exception as e:
        logging.warning(f"Kaynak yuklenemedi: {e}")
        return {"x_accounts": [], "news_sites": [], "all": []}


# ============================================================
# NEWS & X INTELLIGENCE - 14 Tage Cache
# ============================================================

# Asset-Tag Mapping: Welches Keyword gehört zu welchem Asset
NEWS_ASSET_KEYWORDS = {
    "SILVER":      ["silver","gümüş","xag","silber"],
    "GOLD":        ["gold","altın","xau","federal reserve","fed","inflation"],
    "BTC_USD":     ["bitcoin","btc","crypto","kripto"],
    "ETH_USD":     ["ethereum","eth"],
    "SOL_USD":     ["solana"],
    "XRP_USD":     ["ripple","xrp"],
    "OIL_BRENT":   ["oil","brent","crude","petrol","opec"],
    "NATURAL_GAS": ["natural gas","natgas","doğalgaz","lng"],
    "COPPER":      ["copper","bakır","chile","maden"],
    "COFFEE":      ["coffee","kahve","arabica"],
    "EURUSD":      ["euro","eur/usd","dolar","dollar","dxy","ecb","fed"],
}

def detect_asset_tag(text):
    """Metinden asset tag tespit et - haber kategorilendirme icin."""
    text_lower = text.lower()
    for asset, keywords in NEWS_ASSET_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return asset
    return "GENEL"

def quick_sentiment(text):
    """
    Basit kural bazli sentiment analizi.
    Gercek NLP yerine anahtar kelime bazli.
    -1.0 (cok bearish) ... +1.0 (cok bullish)
    """
    text_lower = text.lower()
    bullish_words = [
        "surge","rally","soar","rise","gain","bullish","buy","long",
        "breakout","support","strong","growth","positive","up","higher",
        "yükseliş","artış","güçlü","al","alım","pozitif","yükseldi"
    ]
    bearish_words = [
        "crash","fall","drop","decline","bearish","sell","short",
        "breakdown","resistance","weak","negative","down","lower",
        "düşüş","kayıp","zayıf","sat","satım","negatif","düştü"
    ]
    neutral_words = [
        "stable","sideways","range","mixed","uncertain","wait",
        "yatay","karışık","belirsiz","bekle"
    ]
    bull_score = sum(1 for w in bullish_words if w in text_lower)
    bear_score = sum(1 for w in bearish_words if w in text_lower)
    total = bull_score + bear_score
    if total == 0:
        return 0.0, "NEUTRAL"
    score = (bull_score - bear_score) / total
    if score > 0.3:   label = "BULLISH"
    elif score < -0.3: label = "BEARISH"
    else:              label = "NEUTRAL"
    return round(score, 2), label


def collect_news_rss(sources_data):
    # Tabellen sicherstellen (falls DB neu)
    try: init_db()
    except: pass
    """
    RSS feed'lerden haber topla.
    toplam_egitim.txt'deki haber sitelerini kullanir.
    """
    rss_urls = {
        "wallstreet-online.de":  "https://www.wallstreet-online.de/rss/nachrichten.xml",
        "bloomberght.com":       "https://www.bloomberght.com/rss",
        "n-tv.de/wirtschaft":    "https://www.n-tv.de/wirtschaft/rss",
        "finanzen.net":          "https://www.finanzen.net/rss/news",
        "investing.com/news":    "https://www.investing.com/rss/news.rss",
        "marketwatch":           "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    }

    collected = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cutoff   = (datetime.now() - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")

    for source_name, rss_url in rss_urls.items():
        try:
            r = requests.get(rss_url, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue

            # Einfacher XML-Parser ohne externe Bibliothek
            content = r.text
            # Titel und Links extrahieren
            import re as _re
            titles = _re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>',
                                  content, _re.DOTALL)
            links  = _re.findall(r'<link>(https?://[^<]+)</link>', content)
            dates  = _re.findall(r'<pubDate>(.*?)</pubDate>', content)

            import html as _html
            for i, title in enumerate(titles[1:11], 0):  # Max 10 pro Quelle, skip feed-title
                title = _html.unescape(title.strip())  # &#x27; -> ' gibi HTML entity'leri coz
                if not title or len(title) < 10:
                    continue

                url   = links[i] if i < len(links) else ''
                date  = dates[i][:10] if i < len(dates) else now_str[:10]

                if date < cutoff:
                    continue

                asset_tag       = detect_asset_tag(title)
                sentiment, label = quick_sentiment(title)

                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    # Duplikat check
                    exists = conn.execute(
                        "SELECT 1 FROM news_cache WHERE title=? AND source=?",
                        (title[:200], source_name)).fetchone()
                    if not exists:
                        conn.execute("""INSERT INTO news_cache
                            (source,source_type,asset_tag,title,url,
                             published_at,fetched_at,sentiment,sentiment_label)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (source_name,'RSS',asset_tag,title[:500],
                             url[:300],date,now_str,sentiment,label))
                        collected += 1
                    conn.commit()
                    conn.close()

        except Exception as e:
            logging.warning(f"RSS {source_name}: {e}")

    # Eski haberleri temizle (>14 gun)
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("DELETE FROM news_cache WHERE published_at < ?", (cutoff,))
            conn.commit()
            conn.close()
    except: pass

    if collected > 0:
        logging.info(f"RSS: {collected} yeni haber toplandi")
    return collected


def collect_x_via_search(sources_data):
    # Tabellen sicherstellen
    try: init_db()
    except: pass
    """
    X/Twitter postlarini Google Search Grounding ile topla.
    Nitter mirror'u RSS olarak kullan.
    toplam_egitim.txt'deki X hesaplarini kullanir.
    """
    x_accounts = sources_data.get("x_accounts", [])
    if not x_accounts:
        logging.warning("X hesap listesi bos")
        return 0

    collected  = 0
    now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cutoff     = (datetime.now() - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")

    # Nitter instance'lari (public X mirror)
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]

    # Her hesap icin dene
    for acc_data in x_accounts[:20]:  # Max 20 hesap
        handle = acc_data["handle"].lstrip("@")

        for nitter_base in nitter_instances:
            try:
                rss_url = f"{nitter_base}/{handle}/rss"
                r = requests.get(rss_url, timeout=8,
                                  headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    continue

                import re as _re
                titles = _re.findall(
                    r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>',
                    r.text, _re.DOTALL)
                dates  = _re.findall(r'<pubDate>(.*?)</pubDate>', r.text)

                for i, tweet in enumerate(titles[1:8], 0):  # Max 7 tweet
                    tweet = tweet.strip()
                    if not tweet or len(tweet) < 15:
                        continue

                    date = dates[i][:10] if i < len(dates) else now_str[:10]
                    if date < cutoff:
                        continue

                    asset_tag        = detect_asset_tag(tweet)
                    sentiment, label = quick_sentiment(tweet)

                    with db_lock:
                        conn = sqlite3.connect(DB_FILE)
                        exists = conn.execute(
                            "SELECT 1 FROM x_cache WHERE tweet_text=? AND account=? AND tweet_date=?",
                            (tweet[:300], handle, date)).fetchone()
                        # Ayni metin farkli gunlerde de eklenmesin (RT spam)
                        if not exists:
                            exists = conn.execute(
                                "SELECT 1 FROM x_cache WHERE tweet_text=? AND account=?",
                                (tweet[:200], handle)).fetchone()
                        if not exists:
                            conn.execute("""INSERT INTO x_cache
                                (account,asset_tag,tweet_text,tweet_date,
                                 fetched_at,sentiment,sentiment_label)
                                VALUES (?,?,?,?,?,?,?)""",
                                (handle,asset_tag,tweet[:500],
                                 date,now_str,sentiment,label))
                            collected += 1
                        conn.commit()
                        conn.close()

                break  # Erfolgreich → nächster Account

            except Exception as e:
                logging.debug(f"Nitter {nitter_base}/{handle}: {e}")
                continue

    # Eski X postlarini temizle
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("DELETE FROM x_cache WHERE tweet_date < ?", (cutoff,))
            conn.commit()
            conn.close()
    except: pass

    if collected > 0:
        logging.info(f"X Cache: {collected} yeni post toplandi")
    return collected


def get_news_summary_for_asset(asset_tag, days=14):
    """
    Bir asset icin son N gun haber ozeti.
    Gemini'ye verilecek format.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            news = conn.execute("""
                SELECT source, title, published_at, sentiment, sentiment_label
                FROM news_cache
                WHERE (asset_tag=? OR asset_tag='GENEL')
                AND published_at >= ?
                ORDER BY published_at DESC
                LIMIT 20
            """, (asset_tag, cutoff)).fetchall()

            x_posts = conn.execute("""
                SELECT account, tweet_text, tweet_date, sentiment, sentiment_label
                FROM x_cache
                WHERE (asset_tag=? OR asset_tag='GENEL')
                AND tweet_date >= ?
                ORDER BY tweet_date DESC
                LIMIT 15
            """, (asset_tag, cutoff)).fetchall()

            conn.close()
    except Exception as e:
        logging.warning(f"News summary DB hatasi ({asset_tag}): {e}")
        return f"[{asset_tag}] Haber DB henuz hazir degil (/newscollect ile doldurun)"

    if not news and not x_posts:
        return f"[{asset_tag}] Son {days} gun icin haber/X verisi yok."

    lines = [f"=== {asset_tag} - Son {days} Gun Haber & X Analizi ==="]

    # Sentiment ozeti
    all_sentiments = [n[3] for n in news] + [x[3] for x in x_posts]
    if all_sentiments:
        avg_sent = sum(all_sentiments) / len(all_sentiments)
        bull_cnt = sum(1 for s in all_sentiments if s > 0.2)
        bear_cnt = sum(1 for s in all_sentiments if s < -0.2)
        neut_cnt = len(all_sentiments) - bull_cnt - bear_cnt
        sent_label = "BULLISH" if avg_sent > 0.2 else ("BEARISH" if avg_sent < -0.2 else "NEUTRAL")
        lines.append(
            f"GENEL SENTIMENT: {sent_label} ({avg_sent:+.2f}) | "
            f"Bullish:{bull_cnt} Bearish:{bear_cnt} Neutral:{neut_cnt} haber"
        )

    # Son haberler
    if news:
        lines.append(f"\nSON HABERLER ({len(news)} adet):")
        for src, title, date, sent, label in news[:10]:
            emoji = "+" if sent > 0.2 else ("-" if sent < -0.2 else "~")
            lines.append(f"  [{emoji}{label[:4]}] {date[:10]} | {src[:20]}: {title[:80]}")

    # X posts
    if x_posts:
        lines.append(f"\nX/TWİTTER ({len(x_posts)} post):")
        for acc, tweet, date, sent, label in x_posts[:8]:
            emoji = "+" if sent > 0.2 else ("-" if sent < -0.2 else "~")
            lines.append(f"  [{emoji}{label[:4]}] {date[:10]} @{acc}: {tweet[:80]}")

    return "\n".join(lines)


def get_global_news_summary(days=3):
    """
    Genel makro haber ozeti (asset'ten bagimsiz).
    Son 3 gun en onemli haberler.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            news = conn.execute("""
                SELECT source, title, published_at, sentiment_label
                FROM news_cache
                WHERE published_at >= ?
                ORDER BY published_at DESC LIMIT 15
            """, (cutoff,)).fetchall()
            x_top = conn.execute("""
                SELECT account, tweet_text, tweet_date, sentiment_label
                FROM x_cache
                WHERE tweet_date >= ?
                AND sentiment != 0
                ORDER BY ABS(sentiment) DESC LIMIT 10
            """, (cutoff,)).fetchall()
            conn.close()
    except Exception as e:
        logging.warning(f"Global news DB hatasi: {e}")
        return "Haber DB henuz hazir degil - /newscollect ile doldurun"

    if not news and not x_top:
        return "Son 3 gun icin genel haber yok."

    lines = [f"=== GENEL MAKRO HABERLER (Son {days} Gun) ==="]
    if news:
        for src, title, date, label in news[:8]:
            lines.append(f"  [{label[:4]}] {date[:10]} {src[:15]}: {title[:80]}")
    if x_top:
        lines.append("\nONE CIKAN X POSTLARI:")
        for acc, tweet, date, label in x_top[:5]:
            lines.append(f"  [{label[:4]}] @{acc}: {tweet[:80]}")
    return "\n".join(lines)


# ============================================================
# NEWS COLLECTOR THREAD
# ============================================================
_news_collector_running = False

def news_collector_loop():
    """
    Arkaplanda calisir, her saatte haber + X toplar.
    Tamamen ayri thread, Gemini quota kullanmaz.
    """
    global _news_collector_running
    _news_collector_running = True
    logging.info("Haber Toplama Thread baslatildi (v14.2: bolgesel saat bazli)")
    time.sleep(60)  # Baslangicta bekle

    _last_news_hour = -1   # Son haber toplama saati
    _last_x_time   = 0    # Son X toplama zamani

    while True:
        try:
            now_utc  = datetime.utcnow()
            saat_utc = now_utc.hour
            sources  = load_sources()

            # --- RSS HABER TOPLAMA ---
            # Her saat basinda VEYA oncelikli bolgesel saatlerde topla
            if saat_utc != _last_news_hour:
                _last_news_hour = saat_utc
                if sources["all"]:
                    bolge = None
                    for b, saatler in NEWS_REGIONAL_HOURS.items():
                        if saat_utc in saatler:
                            bolge = b
                            break
                    if bolge:
                        logging.info(f"Haber Toplayici: {bolge} bolge saati ({saat_utc}:00 UTC) - oncelikli toplama")
                    else:
                        logging.info(f"Haber Toplayici: Saat basi rutin toplama ({saat_utc}:00 UTC)")
                    n_news = collect_news_rss(sources)
                    logging.info(f"Haber Toplayici: {n_news} yeni haber toplandi")
                else:
                    logging.warning("Haber Toplayici: kaynak listesi bos")

            # --- X/TWITTER TOPLAMA ---
            # Her 30 dakikada bir
            if time.time() - _last_x_time >= X_COLLECT_INTERVAL:
                _last_x_time = time.time()
                if sources["all"]:
                    n_x = collect_x_via_search(sources)
                    if n_x > 0:
                        logging.info(f"X Toplayici: {n_x} yeni post toplandi")

        except Exception as e:
            logging.error(f"Haber Toplayici hatasi: {e}")

        # Her 5 dakikada bir dongu kontrol et (saat degisimini yakala)
        time.sleep(300)

def load_doctrine():
    """
    Doktrin yukle - oncelik sirasi:
    1. Botun bulundugu klasordeki doktrin.txt (lokal)
    2. GitHub mentor_name.txt + moonshot_doktrin.txt
    Hangi doktrinin kullanildigini bildir.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lokal_path = os.path.join(base_dir, "doktrin.txt")

    # 1. Lokal doktrin.txt var mi?
    if os.path.exists(lokal_path):
        try:
            with open(lokal_path, "r", encoding="utf-8") as f:
                lokal_text = f.read().strip()
            if lokal_text:
                logging.info(f"✅ Lokal doktrin yuklendi: {lokal_path}")
                global _aktif_doktrin_kaynagi
                _aktif_doktrin_kaynagi = f"Lokal: doktrin.txt"
                return lokal_text[:4000]
        except Exception as e:
            logging.warning(f"Lokal doktrin okunamadi: {e}")

    # 2. GitHub'dan cek
    base_gh = "https://raw.githubusercontent.com/KhungFu/nexus/main"
    parts = []
    for fname in ["mentor_name.txt", "moonshot_doktrin.txt"]:
        try:
            r = requests.get(f"{base_gh}/{fname}", timeout=10)
            if r.status_code == 200 and r.text.strip():
                parts.append(r.text[:2000])
                logging.info(f"✅ GitHub doktrin yuklendi: {fname}")
        except: pass

    if parts:
        _aktif_doktrin_kaynagi = "GitHub: mentor_name.txt"
        return "\n\n".join(parts)

    _aktif_doktrin_kaynagi = "Yok (standart kurallar)"
    return "Standart kurallar uygulanir."

_aktif_doktrin_kaynagi = "Henuz yuklenmedi"

# ============================================================
# GREMIUM OYLAMA
# ============================================================
def gremium_oylama(sinyal, guc, sym_key, instrument, upl_toplam, saat):
    oylar = {}
    is_krypto = is_crypto(sym_key)
    is_gece = 23 <= saat or saat < 6
    is_haftasonu = is_weekend()

    if sinyal in ["BUY", "SELL"] and guc >= 2: oylar["Cihat"] = "JA"
    else: oylar["Cihat"] = "NEIN"

    if guc >= 2 and not (is_krypto and is_gece and guc < 3): oylar["Dalio"] = "JA"
    else: oylar["Dalio"] = "NEIN"

    oylar["Kiyosaki"] = "JA" if sinyal != "NOTR" else "NEIN"
    oylar["Graham"] = "JA" if guc == 3 else "NEIN"
    oylar["Buffett"] = "JA" if guc >= 2 else "NEIN"

    if upl_toplam < -30: oylar["Sander"] = "NEIN"
    else: oylar["Sander"] = "JA" if sinyal != "NOTR" else "NEIN"

    if is_krypto and is_gece: oylar["Kostolany"] = "NEIN"
    else: oylar["Kostolany"] = "JA" if guc >= 2 else "NEIN"

    oylar["Lynch"] = "JA" if sinyal != "NOTR" else "NEIN"
    if guc < 2 or (is_krypto and is_gece): oylar["Taleb"] = "NEIN"
    else: oylar["Taleb"] = "JA"
    oylar["Munger"] = "JA" if guc >= 2 else "NEIN"
    oylar["Druckenmiller"] = "JA" if guc == 3 else ("NEIN" if guc < 2 else "JA")

    ja_sayisi = sum(1 for v in oylar.values() if v == "JA")
    if is_haftasonu and is_krypto: karar = ja_sayisi >= 5
    else: karar = ja_sayisi >= 6
    return karar, ja_sayisi, len(oylar) - ja_sayisi, oylar

# ============================================================
# GEMINI ANALIZ (AUTONOMOUS)
# ============================================================

def _format_kandidaten(kandidaten):
    """Bollinger + Fibonacci Rohdaten fuer Gemini formatieren."""
    if not kandidaten:
        return "HIC KANDIDAT YOK - Bu dongude teknik filtre hicbir asset icin gecmedi."

    lines = [f"{len(kandidaten)} KANDIDAT BULUNDU - Bunlari analiz et:\n"]
    for sym, skor in kandidaten.items():
        boll = skor.get("bollinger")
        fib  = skor.get("fibonacci")
        lines.append(f"{'='*40}")
        lines.append(f"KANDIDAT: {sym}")
        lines.append(f"  Gate-Keeper Skoru: {skor['score']}/{skor['max_score']}")
        lines.append(f"  Teknik Sinyal:     {skor['signal']}")
        lines.append(f"  Detaylar:          {skor['details']}")

        if boll:
            lines.append(f"  BOLLINGER BANDS (Yorumla!):")
            lines.append(f"    Fiyat:        {boll['price']}")
            lines.append(f"    Ust Band:     {boll['upper']}")
            lines.append(f"    Orta (MA20):  {boll['middle']}")
            lines.append(f"    Alt Band:     {boll['lower']}")
            lines.append(f"    Bant Genisligi: {boll['bandwidth']:.4f}")
            lines.append(f"    Pozisyon:     {boll['position']} "
                         f"(Yuzde:{boll['pct_pos']:.1%})")
        else:
            lines.append("  BOLLINGER: Veri yok")

        if fib:
            lines.append(f"  FIBONACCI RETRACEMENT (Yorumla!):")
            lines.append(f"    Swing High:   {fib['swing_high']}")
            lines.append(f"    Swing Low:    {fib['swing_low']}")
            lines.append(f"    Guncel Fiyat: {fib['price']}")
            lines.append(f"    Trend:        {fib['trend']}")
            lines.append(f"    En Yakin Sev: {fib['nearest_level']} "
                         f"({fib['nearest_price']}) "
                         f"[{fib['distance_pct']:.1f}% uzakta]")
            lines.append(f"    Tur:          {fib['sr_type']}")
            lines.append(f"    Tum Seviyeler:")
            for lvl, price in fib['levels'].items():
                marker = " <-- FIYAT BURAYA YAKIN" if lvl == fib['nearest_level'] else ""
                lines.append(f"      {lvl:6s}: {price}{marker}")
        else:
            lines.append("  FIBONACCI: Veri yok")

        # Asset sinifina gore kaynak oneri
        if any(c in sym.upper() for c in ["BTC","ETH","SOL","XRP","CRYPTO"]):
            asset_sources = "@zerohedge, @Danny_Crypton, @unusual_whales, alternative.me/fng"
            search_terms  = f'"{sym} price outlook today", "bitcoin market sentiment today"'
        elif any(c in sym.upper() for c in ["GOLD","SILVER","XAU","XAG"]):
            asset_sources = "@SchiffGold, @PeterSchiff, @KobeissiLetter, @MakeGoldGreat"
            search_terms  = f'"{sym} price forecast today", "gold silver outlook fundamentals"'
        elif any(c in sym.upper() for c in ["OIL","BRENT","CRUDE","GAS","ENERGY"]):
            asset_sources = "@KobeissiLetter, @zerohedge, Reuters Energy, EIA.gov"
            search_terms  = f'"{sym} supply demand today", "crude oil inventory today"'
        elif any(c in sym.upper() for c in ["EUR","USD","GBP","JPY","FOREX"]):
            asset_sources = "@NickTimiraos, @robin_j_brooks, @steve_hanke, @BloombergHT"
            search_terms  = f'"DXY dollar index today", "{sym} forex outlook"'
        else:
            asset_sources = "@KobeissiLetter, @zerohedge, Bloomberg, Reuters"
            search_terms  = f'"{sym} outlook today", "{sym} market analysis"'

        # Asset icin 14 gunluk haber ozeti
        asset_news = get_news_summary_for_asset(sym, days=14)
        lines.append(f"  SON 14 GUN HABER & X ANALİZİ:")
        for nl in asset_news.split("\n")[1:12]:  # Max 11 satir
            lines.append(f"    {nl}")
        lines.append(f"  INTERNET GOREVI (MAKALE TAM OKU!):")
        lines.append(f"    Arama terimleri: {search_terms}")
        lines.append(f"    Oncelikli kaynaklar: {asset_sources}")
        lines.append(f"    KURAL: Haberleri oku, trend gör, karar ver!")
        lines.append(f"    DB'deki haber trendini Google ile dogrula.")
        lines.append("")

    return "\n".join(lines)

def fetch_strategic_response(prompt_type="AUTONOMOUS", extra_data=None):
    h = capital_session.get_headers()
    if not h: return "API Baglanti Hatasi"
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)

    # === QUANT DATEN SAMMELN ===
    fear_greed   = get_fear_greed()
    econ_cal     = get_economic_calendar()
    wx_agrar     = get_weather_signal("AGRAR")
    wx_energy    = get_weather_signal("ENERGY")

    # === ALTERNATİF VERİ SİNYALLERİ ===
    alt_data_summary = get_alternative_data_summary()
    disaster_data    = get_natural_disaster_signal()
    wx_commodity     = get_global_commodity_weather()

    # === FRED MAKRO VERİSİ (v14.2) ===
    fred_data = get_fred_macro_data()
    if fred_data.get("signal") not in ("FRED_KEY_YOK", "FRED_HATA"):
        logging.info(f"FRED: {fred_data.get('signal')} | {fred_data.get('notes','')[:80]}")
    portfolio = []
    for p in pozisyonlar:
        stufe = get_pyramiding_stufe(p['market']['epic'])
        portfolio.append({
            "asset": p['market']['instrumentName'], "epic": p['market']['epic'],
            "upl": p['position']['upl'], "size": p['position']['size'],
            "dir": p['position']['direction'], "level": p['position'].get('level', 0),
            "pyramiding_stufe": stufe
        })

    # ============================================================
    # STAGE 1: PYTHON TEKNIK FILTRE
    # ADX + RSI + MA + Bollinger + Fibonacci → Signal-Score
    # Sadece yeterli skoru olan assetler Gemini'ye gider
    # ============================================================
    tech_sinyaller   = {}   # tum assetler (heartbeat icin)
    gemini_kandidaten = {}  # sadece filtreyi gecenler
    count = 0

    for k, v in MARKET_CONFIG.items():
        if k in TABU_ASSETS:
            continue
        if is_weekend() and not is_crypto(k):
            continue
        if not is_weekend() and count >= 15:
            break

        # Hizli MA/ADX/RSI kontrolu (mevcut logic)
        sinyal, guc, aciklama = technical_confluence(v['epic'])
        tech_sinyaller[k] = {"sinyal": sinyal, "guc": guc, "aciklama": aciklama}
        count += 1

        # Sadece NOTR olmayan assetler icin tam skor hesapla
        if sinyal != "NOTR" and guc >= 2:
            skor = berechne_signal_score(k, v['epic'])
            if skor["passed"]:
                gemini_kandidaten[k] = skor
                logging.info(
                    f"GATE-KEEPER GECTI: {k} | "
                    f"Skor:{skor['score']}/{skor['max_score']} | "
                    f"Sinyal:{skor['signal']} | {skor['details']}"
                )
            else:
                logging.info(
                    f"GATE-KEEPER BLOK: {k} | "
                    f"Skor:{skor['score']}/{skor['max_score']} < "
                    f"Esik:{skor['threshold']} | {skor['details']}"
                )

    market_intel = {}
    for k, v in MARKET_CONFIG.items():
        # FIX3
        if is_weekend() and not is_crypto(k):
            continue
        try:
            p_res = requests.get(f"{CAPITAL_URL}/markets/{v['epic']}", headers=h, timeout=10).json()
            snapshot = p_res.get('snapshot', {})
            bid = snapshot.get('bid', 0)
            offer = snapshot.get('offer', 0)
            spread = round(abs(offer - bid), 5) if offer and bid else 999
            market_intel[k] = {"price": bid, "spread": spread}
        except: market_intel[k] = {"price": 0, "spread": 999}

    # === REGIME BERECHNUNG (v14.2: FRED entegre) ===
    vol_regime   = get_volatility_regime(market_intel)
    macro_regime = get_macro_regime(fear_greed["value"], vol_regime, fred_data)

    # === VOLLSTAENDIGES GEDAECHTNIS (VOR Gemini-Analyse) ===
    full_memory = db_get_full_memory()

    current_model = get_next_model()
    saat = datetime.now().hour
    dynamic_doctrine = load_doctrine()
    sources_data     = load_sources()

    # Hard block listesini prompt için hazırla - AI bu assetler için trade üretmeyecek
    with hard_block_lock:
        _blk = dict(HARD_BLOCK_ASSETS)
    if _blk:
        hard_block_ozet = "\n".join(
            f"  ⛔ {sym}: {info.get('action','ALL')} YASAK — {info.get('reason','')[:50]}"
            for sym, info in _blk.items()
        )
    else:
        hard_block_ozet = "  (Yok - tüm assetler serbest)"

    # Kaynaklar: ilk 15 X hesabi + ilk 10 haber sitesi (token tasarrufu)
    x_list    = [x["handle"] for x in sources_data["x_accounts"][:15]]
    news_list = sources_data["news_sites"][:10]

    # === 14 GUN HABER & X INTELLIGENCE ===
    global_news  = get_global_news_summary(days=3)
    # Kandidat assetler icin ozel haber ozeti (henuz bilinmiyor,
    # sonradan _format_kandidaten icinde ekleniyor)

    # Gemini bekommt die exakte Symbol-Liste damit er keine Namen erfindet
    symbol_liste  = "\n".join([f"  {k}" for k in MARKET_CONFIG.keys()])
    x_kaynak_str  = ", ".join(x_list) if x_list else "Yukleniyor..."
    haber_str     = "\n   ".join(news_list) if news_list else "Yukleniyor..."

    system_prompt = f"""Sen NEXUS CEO v14.1 - KI-Quant-Fonds modundasin.
Kimlik: Renaissance Technologies / Two Sigma seviyesinde veri odakli karar alici.
Cihat E. Cicek tarzi: direkt, ogretici, Turkce, piyasayi seven bir mentor.
Fiat para = "kagit para" | Enflasyon = "sistematik hirsizlik"

CFD KALDIRAÇ SİSTEMİ - SIZE HESAPLAMA (ZORUNLU):

Capital.com CFD hesabında kaldıraç aktiftir.
Doktrin'deki kaldıraç oranlarını kullan. Doktrin yoksa varsayılan değerleri kullan.

VARSAYILAN KALDIRAÇ ORANLARI (Doktrin'de belirtilmemişse):
  Döviz (EURUSD, GBPUSD...): 1:30
  Endeks (DE40, US500...):   1:20
  Emtia (GOLD, SILVER...):   1:10
  Ham Petrol, Doğalgaz:      1:10
  Hisse Senedi:              1:5
  Kripto (BTC, ETH...):      1:2

SIZE HESAPLAMA FORMÜLÜ:
  Marjin = Musait_EUR × Kelly%
  Pozisyon_Değeri = Marjin × Kaldıraç
  SIZE = Pozisyon_Değeri ÷ Güncel_Fiyat

  Örnek GOLD (fiyat 3300, kaldıraç 1:10, musait 200 EUR, Kelly %5):
    Marjin = 200 × 0.05 = 10 EUR
    Pozisyon = 10 × 10 = 100 EUR
    SIZE = 100 ÷ 3300 = 0.030 lot

  Örnek BTC (fiyat 85000, kaldıraç 1:2, musait 200 EUR, Kelly %5):
    Marjin = 200 × 0.05 = 10 EUR
    Pozisyon = 10 × 2 = 20 EUR
    SIZE = 20 ÷ 85000 = 0.00024 BTC

  Örnek EURUSD (kaldıraç 1:30, musait 200 EUR, Kelly %5):
    Marjin = 200 × 0.05 = 10 EUR
    Pozisyon = 10 × 30 = 300 EUR
    SIZE = 300 ÷ 1.08 = 277.7 → min_size kontrolü yap

TRADE satırında LEVERAGE alanını da yaz:
  TRADE: GOLD | SIDE: BUY | SIZE: 0.030 | SL: 3250.0 | TP: 3400.0 | LEVERAGE: 10
  TRADE: BTC_USD | SIDE: BUY | SIZE: 0.00024 | SL: 82000 | TP: 90000 | LEVERAGE: 2

KURAL: Marjin (SIZE × Fiyat ÷ Kaldıraç) <= Musait_EUR × Kelly%
Risk yönetimi: SL, marjinin maksimum %50'sini kaybettirecek seviyeye koy.
Mevcut Model: {current_model} | Backend: Gemini (gemini-3-flash-preview) + Groq (Llama4) fallback

QUANT PROTOKOLÜ - SEN STAGE 2'SIN:

Python Stage 1 tamamladi:
  ADX + RSI + MA + Bollinger Bands + Fibonacci → Hepsi hesaplandi
  Sadece filtreyi gecen assetler sana geldi (asagida KANDATLAR bolumu)

SENIN GOREVLERIN (Stage 2):
1. Her kandidat icin Google Search ile internette ara:
   - "[Asset] price outlook today"
   - "[Asset] news sentiment" veya "[Asset] fundamental today"
   - DXY, Fear&Greed, makro haberleri

   KAYNAK LiSTESi (toplam_egitim.txt - dinamik):
   X Hesaplari: {x_kaynak_str}
   Haber Siteleri:
   {haber_str}

   14 GUN HABER TREND KURALI:
   - Asagida her kandidat icin son 14 gunun haber + X ozeti verilir
   - Sadece bugunun haberlerine bakma! TREND'i gör
   - "5 gun once bearish + 2 gun once neutral + bugun bullish = TREND DÖNÜŞÜ"
   - Google Search ile DB'deki haberleri DOGRULA + yeni haberleri ekle
   - Cakisan bilgi varsa: Google > DB (Google daha güncel olabilir)

   MAKALE OKUMA KURALI (cok onemli!):
   - Sadece baslik okuma! Linke gir, tam icerige bak.
   - Her makaleden en az 3 somut bilgi cikart:
     * Fiyat tahmini varsa not al
     * Hacim/akis bilgisi varsa not al
     * Risk faktoru varsa not al
   - "Basliga gore..." deme, icerigi oku ve ozetle.
   - Kaynak guvenilirlik skorunu kontrol et (asagida verilir).
   - Blacklisted kaynaklar: KULLANMA.

2. Bollinger + Fibonacci verilerini YORUMLA (Python sadece sayilari verdi):
   - Bollinger: Fiyat hangi bantta? Squeeze var mi? Ne anlama gelir?
   - Fibonacci: Hangi seviyeye yakin? Support mu Resistance mi?
   - Bu iki indikatoru diger sinyallerle birlestir

3. Her kandidat icin karar ver:
   - Fundamental internet arastirmasi teknik sinyali destekliyor mu?
   - Ne kadar gidebilir? (TP hedefi)
   - Simdi mi girmeli, yoksa retest beklemeli mi?
   - Hangi riskler teknik sinyali gecersiz kilar?

4. KAYNAKLAR satirini yazmayi unutma:
   KAYNAKLAR: [Kaynak1: BUY/SELL] [Kaynak2: CAUTION]
   GUVEN: [1-10]
   UYARILAR: [gordugün riskler]

5. Gremium oylamasi yap, Kelly boyutunu kullan, trade uret.

KELLY POZISYON BOYUTU: Python hesapladi (asagida)
MAKRO REJIM: asagida - buna gore agirlik ver

RISK PROTOKOLÜ (DINAMIK):

RISK_OFF_EXTREME (Yuksek Spread + Fear<25 = Gercek kriz):
  → GOLD, SILVER, BTC, ETH IZINLI: Score 4/5+ gerekli, Kelly×0.3
  → Diger assetler: Score 5/5 gerekli, Kelly×0.1 (cok kucuk)
  → Mantik: Krizde "guvenli liman" asset'leri YUKSELIR (ters korelasyon)

RISK_OFF_SPREAD (Sadece spread yuksek, Fear normal):
  → Spread < 0.3 olan her asset izinli: Score 3/5+, Kelly×0.5
  → Spread > 0.3: KAPAT veya bekle
  → Mantik: Spread sorunu gecici, iyi asset'lerde firsat var

RISK_OFF_FEAR (Fear<25, spread normal):
  → GOLD, SILVER, BTC, ETH: Score 3/5+, Kelly×0.6 (FIRSAT!)
  → Diger: Score 4/5+, Kelly×0.2
  → Mantik: Extreme Fear = potansiyel dip, guvenli limanlar al

RISK_OFF / HIGH volatilite:
  → Her asset izinli: Score 3/5+, Kelly×0.5

NEUTRAL: Normal kural, Kelly×1.0
RISK_ON: Kelly×1.0, biraz daha agresif
RISK_ON_GREEDY: Dikkat! Asiri aci = donus yakindır, Kelly×0.7

ONEMLI: RISK_OFF_EXTREME'de GOLD/SILVER/BTC/ETH icin TRADE YAZ!
Bu assetler krizde deger KAZANIR. "TRADE YOK" yazma!

AMA: Kullanici 'alma', 'sat', 'nicht handeln' gibi bir talimat vermisse
bu kural GECERSIZDIR. Kullanici talimati her zaman kazanir. Sorgulama, uygula!

HABER KARAR KURALI:
- FED/CPI/NFP 0-1 gun icinde: Sadece GOLD/SILVER izinli (hedge varliglar)
  Diger assetler: Yeni pozisyon ACMA
- 2-3 gun: Score 4/5+ gerekli, boyutu %50 azalt
- 4-7 gun: Score 3/5+, normal boyutun %75i
- 7+ gun: Normal
NOT: NFP yakinda diye hic trade yapma = yanlis! GOLD haberlere gore hareket eder.

KAYNAK DEGERLENDIRME:
Her kullandigin kaynaği degerlendir.
Format: KAYNAKLAR: [kaynak1: BUY/SELL/NEUTRAL] [kaynak2: ...]
GUVEN: [1-10] UYARILAR: [gordugün riskler]

VERITABANI YAZMA YETKISI - SEN DB'YE YAZABILIRSIN:
Her analiz sonunda EN AZ 1 DB komutu yaz. Python otomatik kaydeder.

DB_NOTE: {{"symbol": "SILVER", "content": "DXY dusus + lower BB = guclu BUY"}}
DB_SOURCE: {{"source": "@KobeissiLetter", "correct": true}}
DB_PATTERN: {{"symbol": "ATOM_USD", "pattern": "Haftasonu gece BUY basarisiz", "rate": 0.2}}
DB_ASSET_NOTE: {{"symbol": "SILVER", "note": "38.2% Fib + lower BB en iyi giris noktasi"}}
DB_WARN: {{"symbol": null, "warning": "NFP 2 gun sonra - pozisyon kucult"}}
DB_WRITE: {{"type": "OZET", "content": "RISK_OFF, 0 trade acildi"}}

KURAL: Her analizde en az 1 DB komutu yaz. Ogrenmek icin kaydet!

TARIHSEL VERi (Deep Dive) - bir asset icin tarihsel veri iste:
DB_FETCH: {{"symbol": "SILVER", "resolution": "HOUR_4", "days": 30}}
DB_FETCH: {{"symbol": "BTC_USD", "resolution": "MINUTE_30", "days": 7}}
Python Capital.com'dan cekip DB'ye kaydeder. Sonraki dongude ozet gelir.

KRITIK - SYMBOL LISTE (NUR DIESE NAMEN VERWENDEN - EXAKT SO):
{symbol_liste}

TRADE FORMAT REGEL (KESİNLİKLE UYULACAK):
1. Sadece yukarıdaki SYMBOL LİSTESİNDEN isim kullan
2. SIDE: sadece BUY veya SELL - HOLD YAZMA, trade etmeyeceksen satır yazma
3. SIZE, SL, TP gerçek sayı olmalı - asla "X" veya placeholder yazma
4. Format tam olarak şöyle olmalı:
   TRADE: GOLD | SIDE: BUY | SIZE: 0.01 | SL: 3150.0 | TP: 3250.0

YANLIŞ örnekler (YAZMA):
  TRADE: GOLD | SIDE: HOLD | SIZE: 0 | SL: 0 | TP: 0
  TRADE: HEATINGOIL | SIDE: BUY | SIZE: X | SL: X | TP: X
  **TRADE:** GOLD | SIDE: BUY (markdown işareti ekleme!)

DOĞRU örnek:
  TRADE: GOLD | SIDE: BUY | SIZE: 0.01 | SL: 3150.00 | TP: 3300.00

KRITİK KURALLAR:
1. TEKNİK FİLTRE:
   KRİPTO: 3 timeframe analizi → 20dk (giriş) + 45dk (ara trend) + 2sa (üst trend)
   En az 2/3 timeframe aynı yönü göstermeli + her TF'de min 2/3 indikatör (MA+ADX+RSI)
   FOREX/EMTİA: HOUR_4 tek timeframe, min 2/3 indikatör onayı
2. SPREAD: Maksimum 0.5 spread - yüksek spread'te işlem YOK
3. Pyramiding: Sinir yok - her seviye min %2 karda. EXIT: Gemini karar verir veya Trailing SL (%5) tetiklenir
4. Volatilite: Tek mumda -%10 = HEMEN KAP
5. Gece (23-06): Kripto sadece 3/3 sinyal uyumunda
6. Haftasonu: SADECE kripto! ALTIN/GUMUS/ENERJI/TARIM YASAK!
   YASAK: GOLD, SILVER, OIL_BRENT, OIL_CRUDE, NATURAL_GAS, HEATING_OIL, GASOLINE, COPPER, WHEAT, CORN, VIX
   HAFTASONU İZİNLİ KRİPTO LİSTESİ (SADECE BUNLAR - başkası KESİNLİKLE YOK):
     BTC_USD, ETH_USD, SOL_USD, XRP_USD
   DOT_USD, ADA_USD, LINK_USD veya başka altcoin YASAK - Python zaten bloklar ama zaman kaybetme!
   HAFTASONU KRIPTO KURALI: Yukarıdaki 4 kripto arasından karşılaştır.
   EN GÜÇLÜ 1 (bir) kripto seç - sadece ona trade yap! Birden fazla kripto pozisyonu YASAK!
   Seçim kriteri: En yüksek guc skoru (3>2>1), eşitse spread en düşük olanı seç.
7. HER KARAR 11 mentordan 6+ JA oy almalı (haftasonu kripto 5+)
8. KAPATMA EMRİ: Teknik sinyal bozuldu veya zarar büyüyorsa, mevcut pozisyonu KAPAT (SIDE: SELL bei BUY).
   NOT: Kaldıraç KAPALI (1:1). Sadece teknik/fundamental bozulursa kapat.
   BEST_TF KURALI: Asset performans tablosunda BestTF bilgisi varsa (örn. SILVER: BestTF=1sa),
   o asset için ANALİZİ O TF'DE YAP. Python Stage 1 o timeframe'i öncelikli kullanır.
   BestTF yoksa normal 3-TF analizine devam et.
9. POZİSYON BOYUTU: Kaldıraç YOK (1:1). Kelly formülü kullan.
   Formül: SIZE = (Musait_EUR × Kelly%) ÷ Güncel_Fiyat
   Örnek: 200 EUR musait, %5 Kelly, Gold 3300 USD → SIZE = (200×0.05)÷3300 = 0.003 → min_size=0.01 kullan
   Örnek: 200 EUR musait, %5 Kelly, Silver 33 USD → SIZE = (200×0.05)÷33 = 0.30
   ASLA bakiyeden büyük pozisyon açma!
10. KAPITAL-ASSET KURALI → DEVREdışı (Kaldıraç kapalı = Margin Call yok)
    €0-199 depo = max 1 | €200-399 = max 2 | ... → Bu kural şu an UYGULANMIYOR.
    Kaldıraç tekrar açılırsa Python otomatik aktifleştirir.
    Şu an: Gremium ve Kelly yeterli risk kontrolü sağlıyor.
10. SEN YINEDE KENDI DÜSÜNCENE GÖRE KONTROL ETTIKTEN SONRA ALIM SATIM YAP

GREMİUM (11 Mentor):
Cihat Cicek | Ray Dalio | Kiyosaki | Graham | Buffett
Beate Sander | Kostolany | Lynch | Taleb | Munger | Druckenmiller

DİNAMİK DOKTRİN:
{dynamic_doctrine}

FORMAT (KESİNLİKLE KORU):
NEXUS HESAP DURUMU
Nakit: [EUR]
Toplam Deger: [EUR]
Acik Kar/Zarar: [+/- EUR]

GREMİUM KARAR: [JA/NEIN] ([X]/11 oy)
Mentorlarin gorusleri: [kisa ozet]

[Cihat Cicek tarzinda stratejik analiz - makroekonomi, DXY, M1/M2/M3 dahil]

TRADE: [SYMBOL] | SIDE: [BUY/SELL] | SIZE: [Miktar] | SL: [Fiyat] | TP: [Fiyat] | PYRAMIDING: [Seviye]

PYRAMIDING KURALLARI:
- PYRAMIDING: 0 = ilk giris (henuz acik pozisyon yok)
- PYRAMIDING: 1,2,3 = mevcut pozisyona EK yeni seviye ac (min %2 karda)
- TRAILING SL: Pyramiding pozisyonlarinda SL otomatik yukari tasir (%1.5 trail)
  Python halleder - sen sadece SL fiyati yaz, sistem otomatik gunceller
- Yon degisikligi (BUY->SELL veya SELL->BUY) = otomatik EXIT + karsit pozisyon
- Acik pozisyon varken ayni yonde sinyal: PYRAMIDING seviyesini artir

Robot Model: {current_model}"""

    # Kelly boyutlari hesapla
    # Kaynak listesi icin tam format
    x_tam_liste   = "\n".join([f"  {x}" for x in x_list]) if x_list else "  (Yukleniyor...)"
    news_tam_liste= "\n".join([f"  {n}" for n in news_list]) if news_list else "  (Yukleniyor...)"
    x_adet        = len(x_list)
    news_adet     = len(news_list)

    kelly_sizes = {}
    toplam_val = float(acc.get("toplam", 100))
    for k in list(tech_sinyaller.keys())[:5]:
        s = get_seasonal_factor(k)
        ks = berechne_position_size(k, toplam_val, 5, vol_regime, macro_regime)
        kelly_sizes[k] = {"kelly_eur": ks, "seasonal": s}

    # Seasonal uyarilar
    seasonal_warns = []
    for k, v in kelly_sizes.items():
        if v["seasonal"] >= 1.2:
            seasonal_warns.append(f"{k} GUCLU SEZON ({v['seasonal']}x)")
        elif v["seasonal"] <= 0.8:
            seasonal_warns.append(f"{k} ZAYIF SEZON ({v['seasonal']}x)")

    full_prompt = f"""=== QUANT VERI PAKETI ===
ZAMAN: {saat}:00 | HAFTASONU: {"EVET" if is_weekend() else "HAYIR"}

⛔⛔ HARD BLOCK - KESİN YASAK ⛔⛔
Aşağıdaki assetler için TRADE satırı YAZMA. Analiz bile yapma. Atla!
{hard_block_ozet}
Bu liste sistem hafızasından gelir. Kullanıcı açıkça "serbest" demeden geçersiz sayma!
MAKRO REJiM: {macro_regime} | VOLATiLiTE: {vol_regime}
KORKU/ACGOZLULUK: {fear_greed["value"]}/100 ({fear_greed["label"]})
EKONOMIK TAKVIM: Sonraki olay={econ_cal["next_event"]} ({econ_cal["days_until"]} gun sonra)
HAVA (AGRAR/Kansas): {wx_agrar["signal"]} - {wx_agrar["notes"]}
HAVA (ENERJi/KuzeyDenizi): {wx_energy["signal"]} - {wx_energy["notes"]}

{alt_data_summary}

=== ACIL UYARILAR ===
Deprem/Afet: {disaster_data["signal"]} | {disaster_data["notes"]}
Emtia Hava: {len(wx_commodity.get("alerts",[]))} aktif uyari
SEZONSAL UYARILAR: {", ".join(seasonal_warns) if seasonal_warns else "Yok"}

=== FRED MAKRO VERİSİ (St. Louis Fed - Resmi ABD verisi) ===
Yield Curve (10Y-2Y): {fred_data.get("yield_curve", "N/A")}% | VIX: {fred_data.get("vix", "N/A")} | DXY: {fred_data.get("dxy", "N/A")}
10Y Tahvil: {fred_data.get("t10y", "N/A")}% | Fed Faiz: {fred_data.get("fed_rate", "N/A")}% | M2 Buyume: {fred_data.get("m2_growth", "N/A")}%
FRED Sinyali: {fred_data.get("signal", "N/A")} | {fred_data.get("notes", "")}

=== HESAP ===
Nakit={acc["nakit"]}, Toplam={acc["toplam"]}, UPL={acc["upl"]}, Musait={acc["musait"]} [KALDIRAÇ KAPALI - 1:1]

=== PORTFOY ===
{json.dumps(portfolio, ensure_ascii=False)}

=== TUM TEKNIK TARAMA (Bilgi icin) ===
{json.dumps(tech_sinyaller, ensure_ascii=False)}

=== STAGE 1 GATE-KEEPER SONUCLARI ===
{_format_kandidaten(gemini_kandidaten)}

=== MARKET (Fiyat/Spread) ===
{json.dumps(market_intel)}

=== ASSET DEEP DIVE (Tarihsel Veri) ===
{_format_deep_dive(gemini_kandidaten)}

=== GENEL MAKRO HABERLER (Son 3 Gun) ===
{global_news}

=== KELLY POZiSYON BOYUTLARI ===
{json.dumps(kelly_sizes, ensure_ascii=False)}

{full_memory}

=== AKTIF KAYNAK LiSTESi (toplam_egitim.txt - sen degistir) ===
X HESAPLARI ({x_adet} hesap):
{x_tam_liste}

HABER SiTELERi ({news_adet} site):
{news_tam_liste}

NOT: Bu listeyi degistirmek icin GitHub'daki toplam_egitim.txt dosyasini guncelle.
Blacklisted kaynaklar otomatik filtrelenmistir.

EXTRA: {json.dumps(extra_data) if extra_data else "Yok"}

KOMUT: Google Search ile interneti tara, quant verileri degerlendir,
2-of-3 teknik filtre + spread kontrol + Gremium oylama yap, uygun ise trade ureT.
Her trade icin: KAYNAKLAR, GUVEN, UYARILAR satirlarini yaz."""

    if not GEMINI_KEYS and not GROQ_KEYS:
        tg_safe_send("❌ KRITIK: Gemini ve Groq API key eksik! Bot analiz yapamıyor.")
        return "AI_KEY_EKSIK"

    # ============================================================
    # GROQ ICIN OPTIMIZE PROMPT (v14.2)
    # Gemini'den farkli: internet yok ama DB haberleri tam dahil
    # Gate-keeper verileri + hesap + DB haberleri = tam analiz
    # Alt veri (gemi/kargo/BDI) kisaltilmis - token tasarrufu
    # ============================================================

    # Kandidatlar icin DB haberlerini topla
    kandidat_haberler = ""
    for sym in list(gemini_kandidaten.keys())[:5]:
        h_ozet = get_news_summary_for_asset(sym, days=3)  # Son 3 gun - guncel
        kandidat_haberler += h_ozet + "\n\n"

    global_news_groq = get_global_news_summary(days=2)  # Son 2 gun makro

    groq_prompt = f"""=== NEXUS QUANT ANALIZ PAKETI ===
ZAMAN: {saat}:00 UTC | HAFTASONU: {"EVET" if is_weekend() else "HAYIR"}
MAKRO REJIM: {macro_regime} | VOLATiLiTE: {vol_regime}
KORKU/ACGOZLULUK: {fear_greed["value"]}/100 ({fear_greed["label"]})
EKONOMIK TAKVIM: Sonraki olay={econ_cal["next_event"]} ({econ_cal["days_until"]} gun sonra)

=== FRED MAKRO VERİSİ (St. Louis Fed - Resmi ABD verisi) ===
Yield Curve (10Y-2Y): {fred_data.get("yield_curve", "N/A")}% | VIX: {fred_data.get("vix", "N/A")} | DXY: {fred_data.get("dxy", "N/A")}
10Y Tahvil: {fred_data.get("t10y", "N/A")}% | Fed Faiz: {fred_data.get("fed_rate", "N/A")}% | M2 Buyume: {fred_data.get("m2_growth", "N/A")}%
FRED Sinyali: {fred_data.get("signal", "N/A")} | {fred_data.get("notes", "")}

=== HESAP ===
Nakit={acc["nakit"]}, Toplam={acc["toplam"]}, UPL={acc["upl"]}, Musait={acc["musait"]} [KALDIRAÇ KAPALI - 1:1]

=== PORTFOY ===
{json.dumps(portfolio, ensure_ascii=False)}

=== STAGE 1 GATE-KEEPER SONUCLARI ===
{_format_kandidaten(gemini_kandidaten)}

=== MARKET (Fiyat/Spread) ===
{json.dumps(market_intel)}

=== GUNCEL DB HABERLER (Son 2-3 Gun, RSS ile toplandi) ===
{global_news_groq}

=== KANDIDAT VARLIK HABERLERI ===
{kandidat_haberler if kandidat_haberler else "Kandidat yok veya haber bulunamadi."}

=== KELLY POZiSYON BOYUTLARI ===
{json.dumps(kelly_sizes, ensure_ascii=False)}

=== ACIL UYARILAR ===
Deprem/Afet: {disaster_data["signal"]} | {disaster_data["notes"]}
NHC Kasirga: {alt_data_summary[:300] if alt_data_summary else "Veri yok"}

{full_memory}

KOMUT: Quant verilerini ve DB haberlerini degerlendир.
Gate-keeper filtresini gecen varliklar icin teknik + haber analizi yap.
Gremium oylama, Kelly boyutu hesapla, uygun ise trade uret.
NOT: Internet erisimin yok - DB haberleri (saat basi RSS) en guncel verilerdir.
Her trade icin: KAYNAKLAR, GUVEN, UYARILAR satirlarini yaz.
EXTRA: {json.dumps(extra_data) if extra_data else "Yok"}"""

    groq_system = f"""Sen NEXUS CEO v14.2 - KI-Quant-Fonds modundasin.
Kimlik: Renaissance Technologies / Two Sigma seviyesinde veri odakli karar alici.
Cihat E. Cicek tarzi: direkt, ogretici, Turkce, piyasayi seven bir mentor.

ONEMLI: Google Search erisimin YOK. Ama sana verilen DB haberleri
her saat saat basi RSS ile toplaniyor (Asya/Avrupa/Amerika bolgelerine gore).
Bu haberler guncel ve guvenilir - onlari kullan.

KALDIRAÇ KAPALI (1:1): SIZE = (Musait_EUR x Kelly%) / Guncel_Fiyat

TRADE FORMAT (KESINLIKLE UYUL):
TRADE: [SYMBOL] | SIDE: [BUY/SELL] | SIZE: [Sayi] | SL: [Fiyat] | TP: [Fiyat]
HOLD veya placeholder yazma. Sinyal yoksa hic TRADE satiri yazma.

SEMBOL LISTESI (SADECE BUNLARI KULLAN):
{symbol_liste}

GREMIUM (11 Mentor - 6+ JA gerekli):
Cihat Cicek | Ray Dalio | Kiyosaki | Graham | Buffett
Beate Sander | Kostolany | Lynch | Taleb | Munger | Druckenmiller

DINAMIK DOKTRIN:
{dynamic_doctrine}

Robot Model: {{model}}"""

    def _call_gemini(system_p, user_p):
        """Gemini API cagrisi - tum keyleri dene, quota dolunca siradakine gec."""
        if not GEMINI_KEYS: return None
        for i, key in enumerate(GEMINI_KEYS):
            try:
                client = genai.Client(api_key=key)
                cfg_kwargs = {
                    "system_instruction": system_p,
                    "tools": [types.Tool(google_search=types.GoogleSearch())]
                }
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=user_p,
                    config=types.GenerateContentConfig(**cfg_kwargs)
                )
                logging.info(f"AI: Gemini key #{i+1}/{len(GEMINI_KEYS)} - gemini-3-flash-preview (Google Search aktif)")
                _set_last_ai_backend("GEMINI", "gemini-3-flash-preview")
                return "🟢 [GEMİNİ - gemini-3-flash-preview]\n" + response.text
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                    logging.warning(f"Gemini key #{i+1} quota doldu, sonraki deneniyor...")
                    continue
                else:
                    logging.warning(f"Gemini key #{i+1} hatasi: {e}")
                    return None
        logging.warning(f"Tum {len(GEMINI_KEYS)} Gemini key quota dolu!")
        return None

    def _call_groq(system_p, user_p, model=None, task_type="complex_analysis"):
        """
        Groq API cagrisi - OpenAI-uyumlu.
        Model bazli token limit - buyuk modeller tam prompt alir.
        """
        client = get_groq_client()
        if not client: return None
        if not model:
            model = get_optimal_groq_model(task_type)

        # Model bazli token limiti
        # Kimi-k2: 262k context - sinir yok
        # Llama-4-Scout: 131k context - sinir yok
        # Qwen3-32b: 32k context - orta
        # Llama-3.3-70b: 12k TPM limiti - dikkatli
        # Llama-3.1-8b: kucuk, hizli - kisalt
        MODEL_CHAR_LIMITS = {
            "moonshotai/kimi-k2-instruct":               200000,  # 262k context
            "meta-llama/llama-4-scout-17b-16e-instruct": 100000,  # 131k context
            "qwen/qwen3-32b":                             24000,  # 32k context
            "llama-3.3-70b-versatile":                    8000,   # 12k TPM - dikkat
            "llama-3.1-8b-instant":                       4000,   # Kucuk model
        }
        MAX_PROMPT_CHARS = MODEL_CHAR_LIMITS.get(model, 8000)
        user_p_safe = user_p[:MAX_PROMPT_CHARS] + "\n[...prompt truncated for token limit...]" if len(user_p) > MAX_PROMPT_CHARS else user_p

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_p},
                    {"role": "user",   "content": user_p_safe}
                ],
                max_tokens=2048,
                temperature=0.7,
            )
            logging.info(f"AI: Groq {model} (task:{task_type})")
            _set_last_ai_backend("GROQ", model)
            return f"🟡 [GROQ - {model}]\n" + response.choices[0].message.content
        except Exception as e:
            err = str(e)
            # 413 = prompt cok buyuk -> daha kucuk kes ve tekrar dene
            if "413" in err or "too large" in err.lower():
                logging.warning(f"Groq {model} 413 - prompt kucultulyor...")
                try:
                    user_p_tiny = user_p[:3000] + "\n[prompt shortened - token limit]"
                    resp2 = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_p[:1000]},
                            {"role": "user",   "content": user_p_tiny}
                        ],
                        max_tokens=1024, temperature=0.7,
                    )
                    _set_last_ai_backend("GROQ", model)
                    return f"🟡 [GROQ - {model} (kisa)]\n" + resp2.choices[0].message.content
                except Exception as e2:
                    logging.warning(f"Groq {model} kisa prompt da basarisiz: {e2}")
            # 429 = rate limit → key'i işaretle, sonraki key'e geç
            elif "429" in err:
                # Bekleme süresini parse et (retry-after varsa)
                wait = 60
                try:
                    import re as _re2
                    m = _re2.search(r"try again in ([\d\.]+)s", err)
                    if m: wait = min(int(float(m.group(1))) + 5, 3600)
                except: pass
                groq_mark_rate_limited(wait)
                logging.warning(f"Groq {model} rate limit → {wait}s sonra serbest, sonraki key devrede")
            elif "404" in err or "not exist" in err.lower():
                logging.warning(f"Groq {model} mevcut degil - listeden cikar")
                if model in GROQ_MODELS:
                    GROQ_MODELS.remove(model)
            elif "decommission" in err.lower():
                logging.warning(f"Groq {model} kaldirilmis - listeden cikar")
                if model in GROQ_MODELS:
                    GROQ_MODELS.remove(model)
            else:
                logging.warning(f"Groq {model} hatasi: {e}")
            return None

    # --- 1. DENEMEK: Gemini (Google Search ile) ---
    resp_text = _call_gemini(system_prompt, full_prompt)
    if resp_text:
        try:
            parse_and_execute_db_commands(resp_text, 0)
            parse_db_fetch_commands(resp_text)
        except Exception as pe:
            logging.warning(f"DB parse hatasi: {pe}")
        return resp_text

    # --- 2. FALLBACK: Groq (Gemini cevap vermedi/quota doldu) ---
    logging.warning("Gemini basarisiz → Groq fallback devreye giriyor")
    groq_model_info = GROQ_MODELS[0] if GROQ_MODELS else "?"
    tg_safe_send(f"⚠️ Gemini quota/hata\n🟡 GROQ fallback: {groq_model_info} devreye girdi\nTrading devam ediyor.")

    # Task-based model sirasi: once en guclu (tam prompt), sonra yedekler
    groq_attempts = [
        ("complex_analysis", get_optimal_groq_model("complex_analysis")),  # kimi-k2 - tam prompt
        ("financial_data",   get_optimal_groq_model("financial_data")),    # qwen3 - sayi uzmani
        ("quick_signal",     get_optimal_groq_model("quick_signal")),      # llama-8b - hizli
    ]
    used = {m for _, m in groq_attempts}
    for m in GROQ_MODELS:
        if m not in used:
            groq_attempts.append(("analysis", m))

    for task_type, model in groq_attempts:
        if model not in GROQ_MODELS and model not in [m for _, m in groq_attempts]:
            continue
        # v14.2: Groq icin optimize edilmis prompt kullan
        # Model ismini system prompt'a yaz
        groq_sys_final = groq_system.replace("{model}", model)
        resp_text = _call_groq(groq_sys_final, groq_prompt, model, task_type)
        if resp_text:
            try:
                parse_and_execute_db_commands(resp_text, 0)
                parse_db_fetch_commands(resp_text)
            except: pass
            tg_safe_send(f"🟡 Groq ({model}) analiz tamamladi — DB haberleri dahil, Gemini quota doluydu")
            return resp_text
        time.sleep(2)

    logging.error("Tum AI modelleri basarisiz (Gemini + Groq)!")
    tg_safe_send("❌ Gemini + Groq: Tüm modeller başarısız! 60dk bekleniyor.")
    return "QUOTA_FULL_ALL"


# ============================================================
# FREIE CHAT-ANTWORT (ohne /) - Gemini antwortet auf Fragen
# ============================================================
def fetch_chat_response(user_message: str) -> str:
    """
    Beantwortet freie Textnachrichten über den Bot mit Gemini.
    Bezieht Portfolio + Kontostatus mit ein für Kontextfragen.
    """
    h = capital_session.get_headers()
    acc = get_account_info(h) if h else {"nakit": "?", "toplam": "?", "upl": "?", "marjin": "?", "musait": "?"}
    pozisyonlar = get_positions(h) if h else []

    portfolio_ozet = []
    for p in pozisyonlar:
        epic = p['market']['epic']
        stufe = get_pyramiding_stufe(epic)
        portfolio_ozet.append(
            f"{p['market']['instrumentName']} | {p['position']['direction']} | "
            f"UPL:{p['position']['upl']:.2f} | Pyr:Sv.{stufe}"
        )

    symbol_liste_chat = ", ".join(MARKET_CONFIG.keys())
    system_prompt = f"""Sen NEXUS CEO v14.0 yapay zeka asistanısın.
Kullanıcı seninle Telegram üzerinden konuşuyor.
Cihat E. Cicek tarzında cevap ver - direkt, öğretici, güvenilir.
Yatırım kararlarını açıkla, sorulara detaylı yanıt ver.
Türkçe konuş. Kısa ve net ol.
Mevcut semboller: {symbol_liste_chat}"""

    portfolio_str = "\n".join(portfolio_ozet) if portfolio_ozet else "Açık pozisyon yok"
    full_prompt = f"""AKTİF PORTFÖY:
{portfolio_str}

HESAP: Nakit={acc['nakit']}, UPL={acc['upl']}, Musait={acc['musait']} [1:1 - kaldiracsiz]

KULLANICI SORUSU: {user_message}"""

    # 1. Gemini dene
    # 1. Gemini - key_1'den başla, quota dolunca sıradakine geç
    if GEMINI_KEYS:
        for i, key in enumerate(GEMINI_KEYS):
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=full_prompt,
                    config=types.GenerateContentConfig(system_instruction=system_prompt)
                )
                logging.info(f"Chat: Gemini key #{i+1}/{len(GEMINI_KEYS)}")
                return response.text
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                    logging.warning(f"Chat Gemini key #{i+1} quota dolu, sonraki deneniyor...")
                    continue
                else:
                    logging.warning(f"Chat Gemini key #{i+1} hatasi: {e}")
                    break
        logging.warning("Tum Gemini keyleri bitti → Groq fallback")

    # 2. Groq fallback
    groq_client = get_groq_client()
    if groq_client:
        for model in GROQ_MODELS[:3]:
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": full_prompt}
                    ],
                    max_tokens=1024, temperature=0.7,
                )
                return resp.choices[0].message.content
            except Exception as e:
                logging.warning(f"Chat Groq {model}: {e}")
                time.sleep(1)

    return "⚠️ Şu anda yanıt veremiyorum (Gemini + Groq quota/hata). Daha sonra tekrar dene."

# ============================================================
# TRADE EXECUTION
# ============================================================
# ============================================================
# KAPITAL-ASSET-LIMIT (€200 Regel)
# ============================================================
def max_erlaubte_assets(h):
    """
    Depo değerine göre max eş zamanlı asset sayısı (€1000 altında):
    €0-199   → max 1 asset
    €200-399 → max 2 asset
    €400-599 → max 3 asset
    €600-799 → max 4 asset
    €800-999 → max 5 asset
    €1000+   → sınırsız (normal Gremium mantığı)
    Haftasonu: +1 ek asset (pozisyonlar kapatılamadığı için)

    !! DEVREdışı: Kaldıraç kapalı = Margin Call yok = Bu kural gerekli değil.
    !! Yeniden aktifleştirmek için: KAPITAL_ASSET_LIMIT_AKTIF = True yap
    """
    # KAPITAL_ASSET_LIMIT_AKTIF = False  ← Kaldıraç kapalı olduğu için devre dışı
    return 999  # Sınır yok

    # --- Aşağıdaki kod devre dışı (kaldıraç aktifleşirse geri aç) ---
    # try:
    #     acc = get_account_info(h)
    #     toplam = float(acc.get("toplam", 0))
    #     if toplam >= 1000:
    #         return 999
    #     limit = int(toplam / 200) + 1
    #     limit = min(limit, 5)
    #     if is_weekend():
    #         limit += 1
    #     return limit
    # except:
    #     return 999

def aktuelle_asset_anzahl(positions):
    """Zählt einzigartige Epics (Assets) in offenen Positionen."""
    epics = set()
    for p in positions:
        epics.add(p['market']['epic'])
    return len(epics)


# ============================================================
# PRE-TRADE SCHNELL-BACKTEST
# ============================================================
def pre_trade_backtest(symbol, epic, signal_side):
    """
    Trade acmadan once hizli backtest yapar (90 gun).
    En iyi timeframe'i secip geri doner.
    Geri doner: {
      "best_tf": "HOUR",
      "best_resolution": "HOUR",
      "win_rate": 0.61,
      "max_dd": 2.1,
      "score": 0.58,   # Win_rate / max_dd (Sharpe benzeri)
      "all_results": {...}
      "ok": True/False  # Trade yapilmali mi?
    }
    """
    logging.info(f"Pre-Trade Backtest: {symbol} {signal_side} (90 gun)")

    timeframes = [
        ("MINUTE_30", 48, "30dk"),
        ("HOUR",      24, "1sa"),
        ("HOUR_4",     6, "4sa"),
    ]

    results = {}
    best_tf  = None
    best_res = "HOUR_4"
    best_score = -999

    for resolution, cpd, label in timeframes:
        max_c = min(90 * cpd, 999)
        try:
            h = capital_session.get_headers()
            if not h: continue
            url  = f"{CAPITAL_URL}/prices/{epic}?resolution={resolution}&max={max_c}"
            r    = requests.get(url, headers=h, timeout=20)
            if r.status_code != 200: continue
            candles = []
            for p in r.json().get('prices',[]):
                c  = p.get('closePrice',{}).get('bid')
                hv = p.get('highPrice', {}).get('bid')
                lv = p.get('lowPrice',  {}).get('bid')
                if c and hv and lv:
                    candles.append({"c":float(c),"h":float(hv),"l":float(lv)})
        except Exception as e:
            logging.debug(f"Pre-BT {symbol} {resolution}: {e}")
            continue

        if not candles or len(candles) < 50:
            results[label] = {"error": "Yetersiz veri"}
            continue

        closes = [c['c'] for c in candles]
        highs  = [c['h'] for c in candles]
        lows   = [c['l'] for c in candles]

        # Sadece signal_side yonunde trade simule et
        trades = []
        i = 55
        while i < len(closes) - 5:
            cs = closes[:i]; hs = highs[:i]; ls = lows[:i]
            ma9  = sum(cs[-9:])/9   if len(cs)>=9  else None
            ma26 = sum(cs[-26:])/26 if len(cs)>=26 else None
            if not ma9 or not ma26: i+=1; continue
            ma_sig = "BUY" if ma9>ma26 else "SELL"

            # Sadece ayni yon
            if ma_sig != signal_side: i+=1; continue

            adx   = berechne_adx(hs[-15:],ls[-15:],cs[-15:])
            rsi   = berechne_rsi(cs[-15:])
            score = ((1 if adx>20 else 0) +
                     (1 if (ma_sig=="BUY" and rsi<70) or
                           (ma_sig=="SELL" and rsi>30) else 0))

            boll = berechne_bollinger(cs,20)
            if boll:
                if ma_sig=="BUY"  and boll["position"] in ("NEAR_LOWER","SQUEEZE"): score+=1
                if ma_sig=="SELL" and boll["position"] in ("NEAR_UPPER","SQUEEZE"): score+=1

            if score >= 2:
                future = closes[i:i+5]
                if len(future)<3: i+=1; continue
                ep = closes[i]; xp = future[-1]
                pnl = (xp-ep)/ep*100 if ma_sig=="BUY" else (ep-xp)/ep*100
                trades.append({"pnl": round(pnl,3), "win": pnl>0})
                i += 5
            else:
                i += 1

        if not trades:
            results[label] = {"error": "Sinyal yok", "resolution": resolution}
            continue

        wins   = sum(1 for t in trades if t['win'])
        wr     = wins / len(trades)
        avg_w  = sum(t['pnl'] for t in trades if t['win'])  / (wins or 1)
        avg_l  = sum(t['pnl'] for t in trades if not t['win']) / (len(trades)-wins or 1)

        # Max DD
        cu=pk=dd=0
        for t in trades:
            cu+=t['pnl']
            if cu>pk: pk=cu
            if pk-cu>dd: dd=pk-cu

        # Skor: WinRate × AvgWin / max(DD,0.1)  — Sharpe benzeri
        tf_score = (wr * abs(avg_w)) / max(dd, 0.1) if dd > 0 else wr * abs(avg_w)

        results[label] = {
            "resolution":  resolution,
            "total":       len(trades),
            "win_rate":    round(wr, 3),
            "avg_win":     round(avg_w, 3),
            "avg_loss":    round(avg_l, 3),
            "max_dd":      round(dd, 3),
            "score":       round(tf_score, 4),
        }

        if tf_score > best_score:
            best_score = tf_score
            best_tf    = label
            best_res   = resolution

    # Trade yapilmali mi? (min 30% win rate ve en az 5 trade)
    ok = False
    if best_tf and "error" not in results.get(best_tf, {}):
        best_r = results[best_tf]
        ok = (best_r.get("win_rate", 0) >= 0.35 and
              best_r.get("total", 0) >= 5)

    # Log
    summary = " | ".join([
        f"{lbl}: WR={r.get('win_rate','?')} DD={r.get('max_dd','?')}"
        for lbl,r in results.items() if "error" not in r
    ])
    logging.info(f"Pre-BT {symbol}: Best={best_tf} Score={best_score:.3f} | {summary}")

    return {
        "best_tf":         best_tf or "4sa",
        "best_resolution": best_res,
        "score":           best_score,
        "all_results":     results,
        "ok":              ok,
    }

def execute_nexus_trade(analysis):
    # LEVERAGE opsiyonel - AI doktrine göre verir
    pattern = r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*(BUY|SELL)\s*\|\s*SIZE:\s*([\d\.]+)\s*\|\s*SL:\s*([\d\.]+)\s*\|\s*TP:\s*([\d\.]+)(?:\s*\|\s*LEVERAGE:\s*([\d\.]+))?"
    matches = re.findall(pattern, analysis)

    if not matches:
        # HOLD veya yanlış format tespiti - log'a yaz
        hold_pat = re.search(r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*HOLD", analysis, re.IGNORECASE)
        if hold_pat:
            logging.info(f"AI HOLD sinyali verdi: {hold_pat.group(1)} - trade açılmıyor")
        elif "TRADE:" in analysis.upper():
            # TRADE var ama format yanlış - log
            idx = analysis.upper().find("TRADE:")
            logging.warning(f"Yanlış TRADE format: {analysis[idx:idx+80]}")
        return None

    h = capital_session.get_headers()
    if not h: return "❌ API bağlantı hatası"

    # DEPOT DD KONTROLU - Trade baslamadan once
    acc_now = get_account_info(h)
    if acc_now:
        toplam_now = float(acc_now.get("toplam", 0))
        dd_halt, dd_reason = check_depot_dd(toplam_now)
        if dd_halt:
            msg = "DEPOT DD ALARMI: " + dd_reason + " - Yeni trade ACILMIYOR"
            logging.warning(msg)
            return msg

    current_positions = get_positions(h)
    results = []

    for match_tuple in matches:
        sym, side, size, sl, tp = match_tuple[0], match_tuple[1], match_tuple[2], match_tuple[3], match_tuple[4]
        leverage_ai = int(float(match_tuple[5])) if len(match_tuple) > 5 and match_tuple[5] else None
        sym = sym.upper().strip()

        # --- FUZZY SYMBOL MATCHING ---
        # Gemini schreibt manchmal HEATINGOIL statt HEATING_OIL etc.
        def normalize(s):
            return re.sub(r'[\s_\-]', '', s.upper())

        matched_sym = None
        if sym in MARKET_CONFIG:
            matched_sym = sym
        else:
            sym_norm = normalize(sym)
            for config_key in MARKET_CONFIG:
                if normalize(config_key) == sym_norm:
                    matched_sym = config_key
                    logging.info(f"Fuzzy Match: '{sym}' -> '{config_key}'")
                    break

        if matched_sym is None:
            logging.warning(f"Symbol '{sym}' nicht in MARKET_CONFIG - uebersprungen")
            results.append(f"\u26a0\ufe0f {sym} config'de bulunamadı (eşleşme başarısız)")
            continue

        sym = matched_sym

        cfg = MARKET_CONFIG[sym]
        epic = cfg["epic"]

        # --- HAFTASONU WHITELIST ---
        if is_weekend() and is_crypto(sym):
            if sym.upper() not in WEEKEND_CRYPTO_WHITELIST:
                msg = f"BLOK {sym}: Haftasonu yasak (sadece BTC/ETH/SOL/XRP)"
                results.append(msg); logging.warning(msg); continue

        # --- TABU CHECK ---
        if sym in TABU_ASSETS:
            msg = f"TABU {sym}: Kesinlikle trade yapilmaz"
            results.append(msg); logging.warning(msg); continue

        # --- HARD BLOCK CHECK (Kullanici talimati - Gemini override edemez!) ---
        hb, hb_reason = check_hard_block(sym, side)
        if hb:
            logging.info(f"HARD BLOCK aktif: {sym} {side} → atlandı ({hb_reason})")
        if hb:
            msg = f"⛔ HARD BLOCK {sym} ({side}): Kullanici talimati aktif — {hb_reason}"
            results.append(msg); logging.warning(msg); continue

        # --- PIYASA ACIK MI? (Capital.com market status) ---
        try:
            mkt_r = requests.get(f"{CAPITAL_URL}/markets/{cfg['epic']}",
                                 headers=h, timeout=8)
            if mkt_r.status_code == 200:
                mkt_data  = mkt_r.json()
                tradeable = mkt_data.get("dealingEnabled", True)
                mkt_status = mkt_data.get("snapshot", {}).get("marketStatus", "TRADEABLE")
                if not tradeable or mkt_status not in ("TRADEABLE", "OPEN"):
                    msg = f"KAPALI {sym}: Piyasa su an kapali ({mkt_status}) - trade atlaniyor"
                    results.append(msg); logging.warning(msg); continue
        except Exception as me:
            logging.debug(f"Market status check {sym}: {me}")

        # --- GUNLUK KAYIP KONTROLU ---
        kayip = gunluk_kayip_sayisi(sym)
        if kayip >= 3:
            msg = f"BLOK {sym}: Bugun {kayip}x kayip (limit: 3) - yeni trade yok"
            results.append(msg); logging.warning(msg); continue

        # --- AFFORDABILITY CHECK - Bakiye yeterliligi ---
        # 1:1 kaldiracsiz sistemde: size * guncel_fiyat <= musait bakiye
        # min_size config'den alinir (Gold=0.01, Silver=1, BTC=0.01 vb.)
        try:
            acc_aff = get_account_info(h)
            musait = float(acc_aff.get("musait", 0)) if acc_aff else 0
            mkt_snap = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=8)
            if mkt_snap.status_code == 200:
                snap = mkt_snap.json().get("snapshot", {})
                guncel_fiyat = float(snap.get("offer", snap.get("bid", 0)) or 0)
                if guncel_fiyat > 0:
                    min_size_cfg = float(cfg.get("min_size", 1))

                    # Gemini'den gelen size'i onayla - min_size ile kiyasla
                    gemini_size = float(size)
                    # Eger Gemini cok buyuk size verdiyse min_size'a duşür
                    if gemini_size > musait / guncel_fiyat:
                        gemini_size = min_size_cfg

                    gercek_size = max(gemini_size, min_size_cfg)
                    gerekli_teminat = guncel_fiyat * gercek_size

                    # Bakiye yeterli mi? %10 tampon ekle
                    if musait < gerekli_teminat * 1.10:
                        logging.warning(
                            f"{sym}: Bakiye yetersiz! "
                            f"Gerekli teminat={gerekli_teminat:.2f} EUR, "
                            f"Musait={musait:.2f} EUR"
                        )
                        # Bakiyeye gore max karsilanabilir size hesapla
                        max_karsilanabilir = (musait * 0.90) / guncel_fiyat
                        # min_size'in kati olarak yuvarla (asagi)
                        import math as _math
                        max_karsilanabilir = _math.floor(max_karsilanabilir / min_size_cfg) * min_size_cfg
                        max_karsilanabilir = round(max_karsilanabilir, 8)

                        if max_karsilanabilir < min_size_cfg:
                            msg = (
                                f"⛔ YETERSIZ BAKIYE {sym}: "
                                f"Min pozisyon: {min_size_cfg} x {guncel_fiyat:.2f} = "
                                f"{min_size_cfg * guncel_fiyat:.2f}EUR | "
                                f"Musait: {musait:.2f}EUR | Trade atlanıyor."
                            )
                            results.append(msg); logging.warning(msg); continue
                        else:
                            logging.warning(
                                f"AFFORDABILITY: {sym} size {gercek_size} -> {max_karsilanabilir} "
                                f"(fiyat:{guncel_fiyat:.2f} musait:{musait:.2f}EUR)"
                            )
                            size = str(max_karsilanabilir)
                            results.append(
                                f"⚠️ {sym}: Boyut bakiyeye gore ayarlandi: "
                                f"{gercek_size} → {max_karsilanabilir} "
                                f"(Fiyat: {guncel_fiyat:.2f} | Musait: {musait:.2f}EUR)"
                            )
        except Exception as aff_e:
            logging.debug(f"Affordability check hatasi {sym}: {aff_e}")

        # FIX6: Alle Positionen dieses Epics (Long + Short)
        epic_positions = [p for p in current_positions if p['market']['epic'] == epic]

        if epic_positions:
            curr_direction = epic_positions[0]['position']['direction']
            is_gegenrichtung = (side == "SELL" and curr_direction == "BUY") or \
                               (side == "BUY" and curr_direction == "SELL")

            # Gegenrichtung = EXIT alle Positionen + sofort Gegenposition
            # (egal welcher PYRAMIDING Wert - Richtungswechsel ist immer EXIT)
            if is_gegenrichtung:
                logging.warning(f"EXIT: {sym} {curr_direction}->{side}, {len(epic_positions)} Pos")
                geschlossen = 0
                for pos in epic_positions:
                    try:
                        r = requests.delete(f"{CAPITAL_URL}/positions/{pos['position']['dealId']}", headers=h, timeout=10)
                        if r.status_code == 200: geschlossen += 1
                    except Exception as e:
                        logging.error(f"Exit Fehler: {e}")
                reset_pyramiding_stufe(epic)
                results.append(f"{sym}: {geschlossen}/{len(epic_positions)} kapatıldı (ÇIKIŞ)")
                # Kayip mi kar mi? UPL kontrolu
                for pos in epic_positions:
                    try:
                        upl_val = float(pos["position"].get("upl", 0) or 0)
                        if upl_val < 0:
                            kayip_ekle(sym)
                            logging.warning(f"EXIT kayip: {sym} UPL={upl_val:.2f}")
                    except: pass
                # Sofort Gegenposition eroeffnen
                r2 = requests.post(f"{CAPITAL_URL}/positions", json={
                    "epic": epic, "direction": side.upper(),
                    "size": max(float(size), cfg["min_size"]),
                    "type": "MARKET", "stopLevel": float(sl), "profitLevel": float(tp)
                }, headers=h, timeout=10)
                if r2.status_code == 200:
                    set_pyramiding_stufe(epic, 1)
                    results.append(f"{sym} karşı pozisyon açıldı ({side}) Stufe 1/4")
                else:
                    results.append(f"{sym} karşı pozisyon BAŞARISIZ: {r2.text[:100]}")
                continue

            # Gleiche Richtung + PYRAMIDING: 0 = erste Position bereits offen,
            # Gemini meint 'neue Erstposition' -> als Pyramiding behandeln
            # (pyramiding_kontrol prueft ob genug Profit fuer neue Stufe)

        if is_weekend() and not is_crypto(sym):
            results.append(f"{sym} engellendi: Haftasonu - sadece kripto!")
            continue

        if is_weekend() and is_crypto(sym):
            alle_pos = get_positions(h)
            krypto_pos = [p for p in alle_pos if is_crypto(p['market']['epic'])]
            if len(krypto_pos) >= 3:
                results.append(f"{sym} engellendi: Haftasonu kripto limiti 3/3")
                continue

        izinli, neden = pyramiding_kontrol(h, epic, sym)
        if not izinli:
            results.append(f"{sym} Pyramiding atlandı: {neden}")
            continue

        # ============================================================
        # KAPITAL-ASSET-LIMIT (€200 Regel) - DEVREdışı
        # Kaldıraç kapalı = Margin Call yok = Bu kontrol gerekli değil
        # Kaldıraç tekrar açılırsa aşağıdaki bloğu aktifleştir:
        # ============================================================
        # if not epic_positions:
        #     limit = max_erlaubte_assets(h)
        #     acik_asset_sayisi = aktuelle_asset_anzahl(current_positions)
        #     if acik_asset_sayisi >= limit:
        #         acc_check = get_account_info(h)
        #         toplam_val = float(acc_check.get("toplam", 0)) if acc_check else 0
        #         if toplam_val < 1000:
        #             msg = (f"⛔ {sym} KAPITAL LİMİTİ: {acik_asset_sayisi} asset açık, "
        #                    f"max {limit} izinli (€200 kural)")
        #             results.append(msg); logging.warning(msg); continue

        # PRE-TRADE BACKTEST: En iyi timeframe sec
        try:
            bt = pre_trade_backtest(sym, epic, side.upper())
            best_tf  = bt["best_tf"]
            bt_ok    = bt["ok"]
            bt_all   = bt["all_results"]

            # Backtest ozeti log + Telegram
            bt_lines = []
            for lbl, br in bt_all.items():
                if "error" not in br:
                    marker = " ← SECILDI" if lbl == best_tf else ""
                    bt_lines.append(
                        f"  {lbl}: WR={br['win_rate']:.0%} "
                        f"DD={br['max_dd']:.1f}% "
                        f"({br['total']} islem){marker}"
                    )
            bt_msg = f"PRE-TRADE BACKTEST: {sym} {side}\n" + "\n".join(bt_lines) + f"\nSeçilen TF: {best_tf}"
            logging.info(bt_msg.replace("\n"," | "))
            try: bot.send_message(MY_CHAT_ID, bt_msg)
            except: pass

            # Backtest cok kotu ise uyari
            if not bt_ok:
                msg = (f"⚠️ {sym} backtest zayif "
                       f"(WR<35% veya yetersiz veri) - "
                       f"trade devam ediyor ama dikkat!")
                results.append(msg)
                logging.warning(msg)

            # DB'ye kaydet - hem gemini_notes hem asset_learnings
            try:
                db_gemini_write(
                    "PRE_BACKTEST",
                    f"{sym} {side}: Best={best_tf} | " +
                    " | ".join([f"{l}:WR={r.get('win_rate','?')}"
                                for l,r in bt_all.items() if "error" not in r]),
                    sym
                )
                # asset_learnings'e best_tf kaydet (kalici hafiza)
                best_wr = bt_all.get(best_tf, {}).get("win_rate", 0.0)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    try:
                        conn.execute(
                            "ALTER TABLE asset_learnings ADD COLUMN best_tf TEXT DEFAULT \'\'"
                        )
                    except: pass
                    try:
                        conn.execute(
                            "ALTER TABLE asset_learnings ADD COLUMN best_tf_wr REAL DEFAULT 0.0"
                        )
                    except: pass
                    try:
                        conn.execute(
                            "ALTER TABLE asset_learnings ADD COLUMN best_tf_updated TEXT DEFAULT \'\'"
                        )
                    except: pass
                    conn.execute("""
                        INSERT INTO asset_learnings (symbol, best_tf, best_tf_wr, best_tf_updated)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(symbol) DO UPDATE SET
                        best_tf=excluded.best_tf,
                        best_tf_wr=excluded.best_tf_wr,
                        best_tf_updated=excluded.best_tf_updated
                    """, (sym, best_tf, best_wr, now_str))
                    conn.commit()
                    conn.close()
            except Exception as db_bt_e:
                logging.debug(f"Best TF DB kayit hatasi: {db_bt_e}")

        except Exception as bt_e:
            logging.warning(f"Pre-BT hatasi {sym}: {bt_e}")
            best_tf = "4sa"  # Varsayilan

        # SL-minimum mesafe pruefen und korrigieren
        sl_float = float(sl)
        tp_float = float(tp)
        try:
            # Aktuellen Preis von Capital.com holen
            price_r = requests.get(
                f"{CAPITAL_URL}/markets/{epic}",
                headers=h, timeout=10
            )
            if price_r.status_code == 200:
                pdata = price_r.json()
                bid = float(pdata.get('snapshot', {}).get('bid', 0) or
                            pdata.get('bid', 0) or 0)
                ask = float(pdata.get('snapshot', {}).get('offer', 0) or
                            pdata.get('offer', 0) or 0)
                current_price = ask if side.upper() == 'BUY' else bid
                min_stop_pct = cfg.get('min_stop_pct', 0.002)  # 0.2% default
                if is_weekend() and is_crypto(sym):
                    min_stop_pct *= 2.5  # Haftasonu kripto: daha genis SL
                min_dist = current_price * min_stop_pct
                if side.upper() == 'BUY':
                    min_sl = current_price - min_dist
                    if sl_float > min_sl:
                        old_sl = sl_float
                        sl_float = round(min_sl, 5)
                        logging.warning(f"{sym} SL düzeltildi: {old_sl} -> {sl_float} (minimum mesafe)")
                        results.append(f"{sym} SL güncellendi: {old_sl} -> {sl_float}")
                else:  # SELL
                    max_sl = current_price + min_dist
                    if sl_float < max_sl:
                        old_sl = sl_float
                        sl_float = round(max_sl, 5)
                        logging.warning(f"{sym} SL düzeltildi: {old_sl} -> {sl_float} (minimum mesafe)")
                        results.append(f"{sym} SL güncellendi: {old_sl} -> {sl_float}")
        except Exception as e:
            logging.warning(f"{sym} fiyat kontrolü başarısız: {e}")

        # Kaldıraç bilgisini logla
        if leverage_ai:
            logging.info(f"{sym} LEVERAGE: 1:{leverage_ai} (AI doktrine göre belirledi)")
        else:
            logging.info(f"{sym} LEVERAGE: AI belirtmedi (hesap ayarları geçerli)")

        payload = {
            "epic":        epic,
            "direction":   side.upper(),
            "size":        max(float(size), cfg["min_size"]),
            "type":        "MARKET",
            "stopLevel":   sl_float,
            "profitLevel": tp_float
        }
        r = requests.post(f"{CAPITAL_URL}/positions", json=payload, headers=h, timeout=10)
        if r.status_code == 200:
            stufe = get_pyramiding_stufe(epic) + 1
            set_pyramiding_stufe(epic, stufe)
            results.append(f"{sym} yeni pozisyon açıldı ({side}) Seviye {stufe}")
            # DB'ye kaydet
            try:
                db_open_trade(
                    symbol=sym, direction=side, size=max(float(size), cfg["min_size"]),
                    entry_price=sl_float, sl=sl_float, tp=tp_float,
                    spread=market_intel.get(sym, {}).get("spread", 0) if "market_intel" in dir() else 0,
                    gremium_score="?",
                    macro_regime=macro_regime if "macro_regime" in dir() else "UNKNOWN",
                    fear_greed=fear_greed["value"] if "fear_greed" in dir() else 50,
                )
            except Exception as db_e:
                logging.warning(f"DB Trade kayit hatasi: {db_e}")
            sync_ok = 0
            alle_pos_aktuell = get_positions(h)
            for pos in [p for p in alle_pos_aktuell if p['market']['epic'] == epic]:
                try:
                    r_upd = requests.put(
                        f"{CAPITAL_URL}/positions/{pos['position']['dealId']}",
                        json={"stopLevel": float(sl), "profitLevel": float(tp)},
                        headers=h, timeout=10)
                    if r_upd.status_code == 200: sync_ok += 1
                except Exception as e:
                    logging.error(f"SL/TP Sync Fehler: {e}")
            if sync_ok > 0:
                results.append(f"{sym} SL/TP senkron: {sync_ok} Pos -> SL:{sl} TP:{tp}")
            # Trailing SL peak state - hemen initialize et (5 dk bekleme)
            try:
                trail_state = _load_trailing_state()
                peak_key = "peak_" + epic + "_" + side.upper()
                if peak_key not in trail_state:
                    if side.upper() == "BUY":
                        initial_peak = sl_float / (1 - 0.05) if sl_float > 0 else float(tp)
                    else:
                        initial_peak = sl_float / (1 + 0.05) if sl_float > 0 else float(tp)
                    trail_state[peak_key] = {
                        "value": round(initial_peak, 5),
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    _save_trailing_state(trail_state)
                    results.append(f"{sym} Trailing SL aktif: -%5 ({round(initial_peak,3)} peak)")
            except Exception as te:
                logging.warning("Trailing init: " + str(te))
        else:
            error_text = r.text[:150]
            results.append(f"{sym} açılış hatası: {error_text}")
            logging.error(f"Trade Fehler {sym}: {error_text}")

    return "\n".join(results) if results else None

# ============================================================
# TELEGRAM KOMMANDOS (/ Befehle)
# ============================================================
@bot.message_handler(commands=['status'])
def handle_status(message):
    sync_bericht = sync_pyramiding_from_capital()
    bot.send_message(MY_CHAT_ID, f"Piramiding Senkron: {sync_bericht}")
    bot.send_message(MY_CHAT_ID, "🔍 NEXUS CEO v14.1 - Analiz yapılıyor...")
    analysis = fetch_strategic_response("STATUS_REQUEST")
    bot.send_message(MY_CHAT_ID, analysis[:4000])

@bot.message_handler(commands=['pozisyon'])
def handle_pozisyon(message):
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı")
        return
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)
    mesaj = f"📊 NEXUS POZİSYON RAPORU\n"
    mesaj += f"Nakit: {acc['nakit']:.2f} EUR\n"
    mesaj += f"UPL: {acc['upl']:.2f} EUR\n"
    # Marjin: Kaldıraç yok - gösterilmiyor
    if pozisyonlar:
        for p in pozisyonlar:
            epic = p['market']['epic']
            stufe = get_pyramiding_stufe(epic)
            mesaj += f"• {p['market']['instrumentName']}: {p['position']['direction']} "
            mesaj += f"UPL:{p['position']['upl']:.2f} Pyr:Sv.{stufe}\n"
    else:
        mesaj += "Açık pozisyon yok."
    bot.send_message(MY_CHAT_ID, mesaj, reply_markup=NEXUS_MENU)

@bot.message_handler(commands=['ma'])
def handle_ma(message):
    mesaj = "📈 MA 9/26 SİNYALLERİ\n"
    # Hafta sonu: sadece whitelist kriptolar taransin
    if is_weekend():
        scan_keys = [k for k in MARKET_CONFIG if k in WEEKEND_CRYPTO_WHITELIST]
    else:
        scan_keys = list(MARKET_CONFIG.keys())
    for k in scan_keys[:20]:
        v = MARKET_CONFIG[k]
        sinyal, guc, aciklama = technical_confluence(v['epic'])
        emoji = "🟢" if sinyal == "BUY" else "🔴" if sinyal == "SELL" else "⚪"
        mesaj += f"{emoji} {k}: {sinyal} ({guc}/3) - {aciklama}\n"
        count += 1
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['volatilite'])
def handle_volatilite(message):
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı")
        return
    bot.send_message(MY_CHAT_ID, "🔍 Volatilite kontrolü yapılıyor...")
    kapatilanlar = volatilite_kontrol(h)
    if not kapatilanlar:
        bot.send_message(MY_CHAT_ID, "✅ Tüm pozisyonlar normal aralıkta")

@bot.message_handler(commands=['spread'])
def handle_spread(message):
    """Scannt alle Spreads und schreibt sie in die Config."""
    bot.send_message(MY_CHAT_ID, "📡 Spread tarama başlatılıyor...")
    spread_data = scan_and_write_spreads()
    if spread_data:
        lines = [f"• {sym}: {sp:.5f}" for sym, sp in list(spread_data.items())[:20]]
        mesaj = "✅ Spread'ler güncellendi:\n" + "\n".join(lines)
        if len(spread_data) > 20:
            mesaj += f"\n... ve {len(spread_data)-20} daha"
    else:
        mesaj = "⚠️ Spread verisi alınamadı."
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['backtest'])
def handle_backtest(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.send_message(MY_CHAT_ID,
            "Kullanim: /backtest SYMBOL [GUN]\n"
            "Ornek: /backtest SILVER 200\n"
            "Semboller: " + ", ".join(list(MARKET_CONFIG.keys())[:10]))
        return
    sym  = parts[1].upper().strip()
    days = int(parts[2]) if len(parts)>2 else 90
    if sym not in MARKET_CONFIG:
        bot.send_message(MY_CHAT_ID, f"{sym} bulunamadi."); return
    days = min(days, 200)
    epic = MARKET_CONFIG[sym]['epic']
    bot.send_message(MY_CHAT_ID, f"Backtest: {sym} {days} gün - 3 zaman dilimi test ediliyor...")
    try:
        results = run_backtest(sym, epic, days)
        report  = format_backtest_report(sym, results, days)
        bot.send_message(MY_CHAT_ID, report[:4000])
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"Backtest hatası: {e}")


@bot.message_handler(commands=['deepdive'])
def handle_deepdive(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.send_message(MY_CHAT_ID,
            "Kullanim: /deepdive SYMBOL [RESOLUTION] [GUN]\n"
            "Ornek: /deepdive SILVER HOUR_4 30"); return
    sym  = parts[1].upper().strip()
    res  = parts[2].upper() if len(parts)>2 else "HOUR_4"
    days = int(parts[3]) if len(parts)>3 else 30
    if sym not in MARKET_CONFIG:
        bot.send_message(MY_CHAT_ID, f"{sym} bulunamadi."); return
    epic = MARKET_CONFIG[sym]['epic']
    bot.send_message(MY_CHAT_ID, f"{sym} {res} {days} gun cekiliyor...")
    candles = fetch_asset_history(sym, epic, res, days)
    if not candles:
        bot.send_message(MY_CHAT_ID, f"Veri alinamadi: {sym}"); return
    summary = get_asset_history_summary(sym, res)
    bot.send_message(MY_CHAT_ID,
        f"DEEP DIVE: {sym}\n{'='*30}\n{summary or 'Ozet yok'}")


@bot.message_handler(commands=['stats'])
def handle_stats(message):
    """Trade istatistiklerini goster."""
    asset_sum = db_get_asset_summary()
    history   = db_get_memory_context(10)
    fg        = get_fear_greed()
    econ      = get_economic_calendar()
    dd_status = get_dd_status()
    dd_line = (f"\n⛔ DEPOT DD HALT: {dd_status['reason']}"
               if dd_status["halt"]
               else f"\n✅ Depot DD Normal | Peak: {dd_status['peak']:.2f}EUR")
    msg = (
        f"NEXUS QUANT STATS\n"
        f"Korku/Açgözlülük: {fg['value']}/100 ({fg['label']})\n"
        f"Sonraki Olay: {econ['next_event']} ({econ['days_until']} gün)"
        f"{dd_line}\n\n"
        f"ASSET PERFORMANSI:\n{asset_sum}\n\n"
        f"SON 10 TRADE:\n{history}"
    )
    bot.send_message(MY_CHAT_ID, msg[:4000])

@bot.message_handler(commands=['sources'])
def handle_sources(message):
    """Kaynak guvenilirlik skorlarini goster."""
    scores = db_get_source_scores()
    bot.send_message(MY_CHAT_ID, f"KAYNAK GUVENILIRLIK:\n{scores}")

@bot.message_handler(commands=['kayip'])
def handle_kayip(message):
    """Bugunun kayip sayacini goster."""
    data = _load_daily_losses()
    losses = data.get("losses", {})
    if not losses:
        bot.send_message(MY_CHAT_ID, "Bugun kayip yok.", reply_markup=NEXUS_MENU)
        return
    tarih = data.get("date","?")
    lines = [f"BUGUNUN KAYIP SAYACI ({tarih}):"]
    for sym, cnt in sorted(losses.items(), key=lambda x: -x[1]):
        lines.append(f"  BLOKLU {sym}: {cnt}x kayip")
    bot.send_message(MY_CHAT_ID, "\n".join(lines), reply_markup=NEXUS_MENU)

@bot.message_handler(commands=['news'])
def handle_news(message):
    """
    /news [SYMBOL] [DAYS]
    Ornek: /news SILVER 14
           /news BTC_USD 7
           /news (genel makro)
    """
    parts = message.text.strip().split()
    if len(parts) >= 2:
        sym  = parts[1].upper().strip()
        days = int(parts[2]) if len(parts) > 2 else 14
        summary = get_news_summary_for_asset(sym, days)
        bot.send_message(MY_CHAT_ID, summary[:4000])
    else:
        # Genel makro ozet
        summary = get_global_news_summary(days=3)
        bot.send_message(MY_CHAT_ID, summary[:4000])


@bot.message_handler(commands=['newscollect'])
def handle_newscollect(message):
    """Manuel news collection tetikle."""
    bot.send_message(MY_CHAT_ID, "Haber toplama baslatiliyor...\nOnce eski haberler temizleniyor...")
    try:
        # Eski haberleri temizle - taze baslangic
        try:
            with db_lock:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM news_cache")
                conn.execute("DELETE FROM x_cache")
                conn.commit()
                conn.close()
            logging.info("Haber DB temizlendi - yeni toplama basliyor")
        except Exception as db_e:
            logging.warning(f"DB temizleme hatasi: {db_e}")

        sources = load_sources()
        n_news = collect_news_rss(sources)
        n_x    = collect_x_via_search(sources)
        bot.send_message(MY_CHAT_ID,
            f"✅ Toplama tamamlandi:\n"
            f"RSS: {n_news} haber\n"
            f"X: {n_x} post\n"
            f"Eski haberler temizlendi, yeni kaynaklar aktif.")
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"Hata: {e}")


@bot.message_handler(commands=['help'])
def handle_help(message):
    mesaj = (
        "NEXUS CEO - Komut Rehberi\n"
        "------------------------------\n\n"
        "ANALIZ & DURUM:\n"
        "/status      - Tam Gemini analizi + Gremium oylama\n"
        "/pozisyon    - Acik pozisyonlar, PnL, Pyramiding\n"
        "/ma          - MA9/26 + ADX + RSI sinyalleri\n"
        "/stats       - Trade istatistikleri + asset performansi\n\n"
        "ARASTIRMA:\n"
        "/backtest [SEMBOL] [GUN] - Ornek: /backtest GOLD 200\n"
        "/deepdive [SEMBOL] [TF] [GUN] - Ornek: /deepdive GOLD HOUR_4 30\n"
        "/news [SEMBOL] [GUN] - Ornek: /news OIL 7\n"
        "/newscollect - Manuel haber toplama (otomatik 60 dk)\n"
        "/sources     - Kaynak guvenilirlik skorlari\n\n"
        "RISK & KONTROL:\n"
        "/volatilite  - Volatilite + Kara Kugu kontrolu\n"
        "/spread      - Spread tarama + config guncelleme\n"
        "/kayip       - Bugunun kayip/zarar sayaci\n\n"
        "HAFIZA:\n"
        "/unut        - Kaydedilen kullanici notlarini sil\n\n"
        "BILGI GONDERME (quota YOK):\n"
        "Komut olmadan yaz = NOT olarak kaydedilir\n"
        "Gemini 30 dk icinde kullanir (48 saat gecerli)\n"
        "Ornek: Iran rafinerileri kapaniyor, Brent yukselir\n\n"
        "HARD BLOCK (aninda Python seviyesinde - Gemini override EDEMEZ!):\n"
        "/bloklar     - Aktif bloklar listesi\n"
        "Ornekler:\n"
        "  'Silver satma'  → SILVER blok + acik pozisyon kapatilir\n"
        "  'Silver alma'   → SILVER BUY blok\n"
        "  'Gold nicht handeln' → GOLD tam blok\n"
        "  'Silver serbest'     → SILVER blok kaldirilir\n\n"
        "ONAY SİSTEMİ:\n"
        "'Kaufe Kaffee' gibi mesaj yaz\n"
        "  → Gemini analiz yapar + sana rapor gönderir\n"
        "/onayla  → Trade açılır\n"
        "/iptal   → Trade iptal edilir\n"
        "Onay süresi: 15 dakika"
    )
    bot.send_message(MY_CHAT_ID, mesaj, reply_markup=NEXUS_MENU)

# ============================================================
# FREIE TEXTNACHRICHTEN (ohne /) - NEU
# ============================================================
@bot.message_handler(commands=['aidurum'])
def handle_aidurum(message):
    """AI backend durumunu göster - Gemini ve Groq."""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    backend, model = get_last_ai_info()
    cfg_backend, cfg_model = get_current_model_and_backend()
    gemini_status = f"✅ {len(GEMINI_KEYS)} key" if GEMINI_KEYS else "❌ Key yok"
    # Rate limited key var mı?
    now_ts = time.time()
    limited = sum(1 for t in _groq_rate_limited.values() if t > now_ts)
    free    = len(GROQ_KEYS) - limited
    groq_status = f"✅ {len(GROQ_KEYS)} key ({free} aktif, {limited} rate limited)" if GROQ_KEYS else "❌ Key yok"
    tg_status     = "❌ DEVRE DIŞI" if _tg_disabled else "✅ Aktif"

    msg = (
        f"🤖 NEXUS v14.1 AI BACKEND DURUMU\n"
        f"{'='*35}\n"
        f"Gemini : {gemini_status} | Model: gemini-3-flash-preview\n"
        f"Groq   : {groq_status}\n"
        f"  Modeller: {', '.join(GROQ_MODELS[:3])}...\n\n"
        f"Aktif backend : {backend}\n"
        f"Aktif model   : {model}\n\n"
        f"Telegram : {tg_status}\n"
        f"{'='*35}\n"
        f"NOT: Gemini quota dolunca Groq otomatik devreye girer."
    )
    tg_safe_send(msg)

@bot.message_handler(commands=['sifirla'])
def handle_sifirla(message):
    """
    DD Halt ve gunluk kayip sayacini sifirla.
    Bot ticaret yapmadiginda kullan.
    """
    if str(message.chat.id) != str(MY_CHAT_ID): return
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        # DD tracker sifirla
        with depot_dd_lock:
            data = {"date": today, "peak_value": 0.0,
                    "trading_halt": False, "halt_reason": ""}
            _save_dd_tracker(data)
        # Gunluk kayip sayaci sifirla
        with daily_loss_lock:
            _save_daily_losses({"date": today, "losses": {}})
        msg = (
            "✅ SIFIRLAMA TAMAM:\n"
            "• DD Halt: KALDIRILDI\n"
            "• Gunluk kayip sayaci: SIFIRLANDI\n"
            "• Peak deger: SIFIRLANDI (ilk trade'de guncellenir)\n"
            "Bot artik trade yapabilir."
        )
        bot.send_message(MY_CHAT_ID, msg, reply_markup=NEXUS_MENU)
        logging.info("Manuel sifirlama yapildi")
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"Sifirlama hatasi: {e}")

@bot.message_handler(commands=['bloklar'])
def handle_bloklar(message):
    """Aktif HARD BLOCK listesini goster."""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    with hard_block_lock:
        aktif = dict(HARD_BLOCK_ASSETS)
    if not aktif:
        bot.send_message(MY_CHAT_ID, "✅ Aktif HARD BLOCK yok. Tum assetler serbest.", reply_markup=NEXUS_MENU)
        return
    lines = ["🔒 AKTİF HARD BLOKLAR:"]
    for sym, info in aktif.items():
        lines.append(f"  ⛔ {sym} ({info['action']}) — {info['timestamp'][:16]}")
        lines.append(f"     Sebep: {info['reason'][:80]}")
    lines.append("\nKaldirmak icin: '<asset> serbest' veya '<asset> freigeben'")
    bot.send_message(MY_CHAT_ID, "\n".join(lines))

@bot.message_handler(commands=['menu'])
def handle_menu(message):
    """Inline menü panelini gönder."""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    bot.send_message(MY_CHAT_ID,
        "🤖 NEXUS CEO — Komut Paneli:",
        reply_markup=NEXUS_INLINE_MENU)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
def handle_inline_callback(call):
    """Inline buton tiklandi - ilgili komutu calistir."""
    if str(call.message.chat.id) != str(MY_CHAT_ID): return
    cmd = call.data.replace("cmd_", "")
    handler_map = {
        "status":      handle_status,
        "pozisyon":    handle_pozisyon,
        "ma":          handle_ma,
        "stats":       handle_stats,
        "news":        handle_news,
        "newscollect": handle_newscollect,
        "volatilite":  handle_volatilite,
        "spread":      handle_spread,
        "kayip":       handle_kayip,
        "backtest":    handle_backtest,
        "deepdive":    handle_deepdive,
        "sources":     handle_sources,
        "bloklar":     handle_bloklar,
        "unut":        handle_unut,
        "help":        handle_help,
    }
    fn = handler_map.get(cmd)
    try:
        bot.answer_callback_query(call.id)  # Loading spinner kapat
        if fn:
            fn(call.message)
        else:
            bot.send_message(MY_CHAT_ID, f"Komut bulunamadi: {cmd}")
    except Exception as e:
        logging.error(f"Inline callback hatasi: {e}")

@bot.message_handler(commands=['unut'])
def handle_unut(message):
    if str(message.chat.id) != str(MY_CHAT_ID):
        return
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            cnt = conn.execute(
                "SELECT COUNT(*) FROM gemini_notes WHERE note_type='USER_INFO'"
            ).fetchone()[0]
            conn.execute("DELETE FROM gemini_notes WHERE note_type='USER_INFO'")
            conn.commit()
            conn.close()
        msg = str(cnt) + " adet kullanici notu silindi. Gemini artik bunlari gormeyecek."
        bot.send_message(MY_CHAT_ID, msg)
    except Exception as e:
        bot.send_message(MY_CHAT_ID, "Silme hatasi: " + str(e))

REPLY_BUTTON_MAP = {
    "📊 Status":     "status",
    "📍 Pozisyon":   "pozisyon",
    "📈 Sinyaller":  "ma",
    "📰 Haberler":   "news",
    "💸 Kayip":      "kayip",
    "🔒 Bloklar":    "bloklar",
    "📋 Menü":       "menu",
    "❓ Yardım":     "help",
    "🧮 Stats":      "stats",
    # Alternatif yazımlar (emoji farklılığı için)
    "📊 status":     "status",
    "📍 pozisyon":   "pozisyon",
    "📈 sinyaller":  "ma",
    "Sinyaller":     "ma",
    "sinyaller":     "ma",
}

def _normalize_button_text(text):
    """Butondaki emoji + boşluk farklılıklarını normalize et."""
    import unicodedata
    # Unicode normalize
    t = unicodedata.normalize('NFC', text.strip())
    return t

@bot.message_handler(func=lambda msg: msg.text and msg.text.strip() in REPLY_BUTTON_MAP)
def handle_menu_button(message):
    """ReplyKeyboard butonlarindan gelen mesajlari ilgili komutlara yonlendir."""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    raw = message.text.strip()
    cmd = REPLY_BUTTON_MAP.get(raw) or REPLY_BUTTON_MAP.get(_normalize_button_text(raw))
    # Son çare: içinde "sinyal" geçiyorsa ma komutu
    if not cmd and "sinyal" in raw.lower():
        cmd = "ma"
    handler_map = {
        "status":      handle_status,
        "pozisyon":    handle_pozisyon,
        "ma":          handle_ma,
        "stats":       handle_stats,
        "news":        handle_news,
        "newscollect": handle_newscollect,
        "volatilite":  handle_volatilite,
        "spread":      handle_spread,
        "kayip":       handle_kayip,
        "backtest":    handle_backtest,
        "deepdive":    handle_deepdive,
        "sources":     handle_sources,
        "bloklar":     handle_bloklar,
        "unut":        handle_unut,
        "help":        handle_help,
        "menu":        handle_menu,
    }
    fn = handler_map.get(cmd)
    if fn:
        fn(message)


@bot.message_handler(content_types=['web_app_data'])
def handle_webapp_data(message):
    """
    Telegram Web App'ten gelen komutlari isle.
    sendData() ile gonderilen mesajlar buraya gelir.
    """
    if str(message.chat.id) != str(MY_CHAT_ID): return
    try:
        data = message.web_app_data.data.strip()
        logging.info(f"Web App komutu: {data}")
        # Komut mu mesaj mi?
        if data.startswith('/'):
            # Komut - ilgili handler'i cagir
            fake_msg = message
            fake_msg.text = data
            cmd = data.lstrip('/').split()[0]
            handler_map = {
                'status': handle_status, 'pozisyon': handle_pozisyon,
                'ma': handle_ma, 'stats': handle_stats,
                'news': handle_news, 'newscollect': handle_newscollect,
                'volatilite': handle_volatilite, 'spread': handle_spread,
                'kayip': handle_kayip, 'backtest': handle_backtest,
                'deepdive': handle_deepdive, 'sources': handle_sources,
                'bloklar': handle_bloklar, 'unut': handle_unut,
                'help': handle_help, 'menu': handle_menu,
            }
            fn = handler_map.get(cmd)
            if fn: fn(fake_msg)
            else: bot.send_message(MY_CHAT_ID, f"Komut bulunamadi: {cmd}")
        else:
            # Serbest metin - handle_free_text'e yonlendir
            message.text = data
            handle_free_text(message)
    except Exception as e:
        logging.error(f"Web App data hatasi: {e}")
        bot.send_message(MY_CHAT_ID, f"⚠️ Web App hatasi: {e}")


@bot.message_handler(func=lambda message: True)
def handle_free_text(message):
    """
    Serbest metin handler - v14 mantigi:

    1. HARD BLOCK / UNBLOCK
       "Gümüş satma" -> BLOCK (trade engellenir)
       "Gümüş serbest" -> UNBLOCK

    2. KAPAT komutu (asset + kapat/sat/al)
       Long pozisyon varsa: "sat/verkaufen/kapat" ile kapat
       Short pozisyon varsa: "al/kaufen/kapat" ile kapat
       "kapat" her iki yone de calisir

    3. YENİ POZİSYON (asset + long/short)
       "Gümüş long" -> Gemini SL/TP/SIZE hesaplar, direkt acar
       "Gümüş short" -> Gemini SL/TP/SIZE hesaplar, direkt acar

    4. Sadece bilgi -> Gemini hafizasina kaydet
    """
    user_text = message.text.strip()
    if not user_text:
        return
    if str(message.chat.id) != str(MY_CHAT_ID):
        bot.send_message(message.chat.id, "⛔ Yetkisiz erişim.")
        return
    try:
        t = user_text.lower().strip()

        # ---- 0. URL TESPİTİ - Link gönderildi mi? ----
        import re as _re_url
        urls_in_msg = _re_url.findall(
            r'https?://[^\s<>"{}|\^`\[\]]+', user_text
        )
        if urls_in_msg:
            def _fetch_user_links(urls, original_text):
                """Kullanıcının gönderdiği linkleri çek ve DB'ye kaydet."""
                kaydedilen = []
                for url in urls[:3]:  # max 3 link
                    try:
                        bot.send_chat_action(MY_CHAT_ID, "typing")

                        # X / Twitter linki mi?
                        if "x.com/" in url or "twitter.com/" in url:
                            # Nitter üzerinden oku
                            nitter_bases = [
                                "https://nitter.net",
                                "https://nitter.privacydev.net",
                                "https://nitter.poast.org",
                            ]
                            tweet_text = None
                            for nb in nitter_bases:
                                try:
                                    # x.com/user/status/ID → nitter/user/status/ID
                                    nitter_url = url.replace("x.com", nb.replace("https://","")).replace("twitter.com", nb.replace("https://",""))
                                    nitter_url = nb + "/" + url.split("x.com/")[-1].split("twitter.com/")[-1]
                                    r = requests.get(nitter_url, timeout=10,
                                        headers={"User-Agent": "Mozilla/5.0"})
                                    if r.status_code == 200:
                                        # Tweet metnini parse et
                                        import re as _rp
                                        m = _rp.search(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>', r.text, _rp.DOTALL)
                                        if m:
                                            import html as _html
                                            tweet_text = _html.unescape(_rp.sub(r'<[^>]+>', '', m.group(1))).strip()
                                            break
                                except: continue

                            if tweet_text and len(tweet_text) > 10:
                                asset_tag = detect_asset_tag(tweet_text)
                                sentiment, label = quick_sentiment(tweet_text)
                                with db_lock:
                                    conn = sqlite3.connect(DB_FILE)
                                    conn.execute("""INSERT OR IGNORE INTO x_cache
                                        (account, asset_tag, tweet_text, tweet_date, fetched_at, sentiment, sentiment_label)
                                        VALUES (?,?,?,?,?,?,?)""",
                                        ("USER_LINK", asset_tag,
                                         tweet_text[:500], datetime.now().strftime("%Y-%m-%d"),
                                         datetime.now().strftime("%Y-%m-%d %H:%M"),
                                         sentiment, label))
                                    conn.commit(); conn.close()
                                kaydedilen.append(f"🐦 Tweet kaydedildi ({asset_tag}): {tweet_text[:80]}...")
                            else:
                                kaydedilen.append(f"⚠️ Tweet okunamadı: {url[:50]}")

                        else:
                            # Haber / Web linki
                            r = requests.get(url, timeout=15,
                                headers={"User-Agent": "Mozilla/5.0"})
                            if r.status_code == 200:
                                import html as _html2
                                import re as _rp2
                                # Title
                                t_m = _rp2.search(r'<title[^>]*>(.*?)</title>', r.text, _rp2.IGNORECASE | _rp2.DOTALL)
                                title = _html2.unescape(t_m.group(1).strip()) if t_m else url
                                title = _rp2.sub(r'\s+', ' ', title)[:150]
                                # İçerik - paragrafları al
                                paras = _rp2.findall(r'<p[^>]*>(.*?)</p>', r.text, _rp2.DOTALL)
                                body_parts = []
                                for p in paras[:15]:
                                    text = _html2.unescape(_rp2.sub(r'<[^>]+>', '', p)).strip()
                                    if len(text) > 50:
                                        body_parts.append(text)
                                body = " ".join(body_parts)[:1000]
                                full_content = f"{title}. {body}"
                                asset_tag = detect_asset_tag(full_content)
                                sentiment, label = quick_sentiment(full_content)
                                with db_lock:
                                    conn = sqlite3.connect(DB_FILE)
                                    conn.execute("""INSERT OR IGNORE INTO news_cache
                                        (source, source_type, asset_tag, title, url, summary,
                                         published_at, fetched_at, sentiment, sentiment_label, importance)
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                        ("USER_LINK", "USER", asset_tag,
                                         title[:200], url, body[:500],
                                         datetime.now().strftime("%Y-%m-%d %H:%M"),
                                         datetime.now().strftime("%Y-%m-%d %H:%M"),
                                         sentiment, label, 3))  # importance=3 (yüksek)
                                    conn.commit(); conn.close()
                                kaydedilen.append(f"📰 Haber kaydedildi ({asset_tag}): {title[:80]}")
                            else:
                                kaydedilen.append(f"⚠️ Link açılamadı (HTTP {r.status_code}): {url[:50]}")

                    except Exception as le:
                        logging.warning(f"Link fetch hatası {url}: {le}")
                        kaydedilen.append(f"⚠️ Hata: {url[:50]}")

                ozet = "\n".join(kaydedilen)
                tg_safe_send(
                    f"🔗 {len(kaydedilen)} link işlendi:\n{ozet}\n\n"
                    f"✅ Bir sonraki analizde AI bu içeriği kullanacak.\n"
                    f"Hemen analiz için /status yazabilirsin."
                )

            threading.Thread(
                target=_fetch_user_links,
                args=(urls_in_msg, user_text),
                daemon=True
            ).start()
            return

        # ---- 1. HARD BLOCK / UNBLOCK ----
        asset_sym_blk, action_blk, block_type = parse_hard_block(user_text)
        if asset_sym_blk and block_type == "UNBLOCK":
            removed = remove_hard_block(asset_sym_blk)
            msg = (f"✅ HARD BLOCK kaldirildi: {asset_sym_blk} artik serbest."
                   if removed else f"ℹ️ {asset_sym_blk} zaten bloklu degildi.")
            db_gemini_write("USER_INFO", user_text[:500], symbol=asset_sym_blk, cycle=0)
            bot.send_message(MY_CHAT_ID, msg)
            return

        if asset_sym_blk and block_type == "BLOCK":
            apply_hard_block(asset_sym_blk, action_blk, user_text[:120])
            db_gemini_write("USER_INFO", user_text[:500], symbol=asset_sym_blk, cycle=0)
            bot.send_message(MY_CHAT_ID,
                f"⛔ HARD BLOCK aktif: {asset_sym_blk} ({action_blk}) — Gemini override EDEMEZ!")
            return

        # ---- 2. KAPAT KOMUTU ----
        # Asset tespit
        detected_asset = None
        for kw in sorted(ASSET_KEYWORDS.keys(), key=len, reverse=True):
            if kw in t:
                detected_asset = ASSET_KEYWORDS[kw]
                break

        close_keywords = ["kapat", "close", "schliessen", "schließen"]
        sell_keywords  = ["sat ", "sat$", "verkauf", "verkaufe", "verkaufen", "sell"]
        buy_keywords   = ["al ", "al$", "kauf", "kaufe", "kaufen", "buy"]

        import re as _re
        is_close = any(kw in t for kw in close_keywords)
        is_sell  = bool(_re.search(r"\b(sat|verkauf|verkaufe|verkaufen|sell)\b", t)) and "satma" not in t
        is_buy   = bool(_re.search(r"\b(al|kauf|kaufe|kaufen|buy)\b", t)) and "alma" not in t and "satin alma" not in t
        is_long  = bool(_re.search(r"\blong\b", t))
        is_short = bool(_re.search(r"\bshort\b", t))

        # Kapat komutu: asset + (kapat VEYA sat VEYA al) ama long/short YOK
        if detected_asset and (is_close or is_sell or is_buy) and not is_long and not is_short:
            try:
                h = capital_session.get_headers()
                if not h:
                    bot.send_message(MY_CHAT_ID, "❌ API bağlantı hatası"); return
                positions = get_positions(h)
                cfg = next((v for k, v in MARKET_CONFIG.items() if k == detected_asset), None)
                if not cfg:
                    bot.send_message(MY_CHAT_ID, f"⚠️ {detected_asset} config bulunamadi."); return

                epic_target = cfg["epic"]
                asset_positions = [p for p in positions if p["market"]["epic"] == epic_target]

                if not asset_positions:
                    bot.send_message(MY_CHAT_ID,
                        f"ℹ️ {detected_asset} için açık pozisyon yok."); return

                # Hangi pozisyonlari kapat?
                to_close = []
                for pos in asset_positions:
                    pos_dir = pos["position"]["direction"]  # BUY veya SELL
                    # "kapat" -> her ikisini de kapat
                    if is_close:
                        to_close.append(pos)
                    # "sat/verkaufen" -> sadece LONG (BUY) pozisyonlari kapat
                    elif is_sell and pos_dir == "BUY":
                        to_close.append(pos)
                    # "al/kaufen" -> sadece SHORT (SELL) pozisyonlari kapat
                    elif is_buy and pos_dir == "SELL":
                        to_close.append(pos)

                if not to_close:
                    dir_info = " | ".join([p["position"]["direction"] for p in asset_positions])
                    bot.send_message(MY_CHAT_ID,
                        f"ℹ️ {detected_asset}: Kapatilacak uygun pozisyon yok.\n"
                        f"Mevcut pozisyon yonleri: {dir_info}\n"
                        f"(sat = LONG kapat | al = SHORT kapat | kapat = hepsini kapat)")
                    return

                closed_cnt = 0
                total_pnl  = 0.0
                for pos in to_close:
                    deal_id = (pos["position"].get("dealId") or
                               pos["position"].get("deal_id", ""))
                    upl = float(pos["position"].get("upl", 0) or 0)
                    if deal_id:
                        r = requests.delete(
                            f"{CAPITAL_URL}/positions/{deal_id}",
                            headers=h, timeout=10)
                        if r.status_code in (200, 201, 204):
                            closed_cnt += 1
                            total_pnl  += upl
                            if upl < 0:
                                kayip_ekle(detected_asset)

                pnl_str = f"+{total_pnl:.2f}" if total_pnl >= 0 else f"{total_pnl:.2f}"
                bot.send_message(MY_CHAT_ID,
                    f"✅ {detected_asset}: {closed_cnt}/{len(to_close)} pozisyon kapatildi\n"
                    f"Tahmini PnL: {pnl_str} EUR")
                db_gemini_write("USER_INFO", user_text[:500], symbol=detected_asset, cycle=0)
            except Exception as ce:
                logging.error(f"Kapat hatasi: {ce}")
                bot.send_message(MY_CHAT_ID, f"⚠️ Kapatma hatasi: {ce}")
            return

        # ---- 3. YENİ POZİSYON (asset + long/short) ----
        if (is_long or is_short):
            if not detected_asset:
                # Bilinmeyen asset - hata ver, Gemini'ye gonderme
                known = ", ".join(sorted(set(ASSET_KEYWORDS.values())))
                bot.send_message(MY_CHAT_ID,
                    f"❓ Asset tanınamadı: '{user_text}'\n"
                    f"Bilinen assetler: {known}\n"
                    f"Örnek: 'Gold long', 'Silver short', 'BTC long'")
                return
            side = "BUY" if is_long else "SELL"
            db_gemini_write("USER_INFO", user_text[:500], symbol=detected_asset, cycle=0)
            threading.Thread(
                target=_execute_user_trade_request,
                args=(detected_asset, side, user_text),
                daemon=True
            ).start()
            return

        # ---- 4. SORU / SERBEST METIN → AI cevap versin ----
        # Not olarak da kaydet
        db_gemini_write("USER_INFO", user_text[:500], symbol=None, cycle=0)

        # Soru işareti var mı veya bilgi sorusu mu?
        soru_kelimeleri = ["?", "ne ", "neden", "nasıl", "nedir", "kaç", "hangi",
                           "düşün", "analiz", "görüş", "tavsiye", "öner",
                           "was ", "wie ", "warum", "was ist", "meinst", "denkst",
                           "think", "what", "how", "why", "analyze", "opinion"]
        is_question = any(kw in user_text.lower() for kw in soru_kelimeleri)

        if is_question or len(user_text) > 10:
            # AI ile konuş - thread'de çalıştır
            def _ai_chat():
                try:
                    bot.send_chat_action(MY_CHAT_ID, "typing")
                    cevap = fetch_chat_response(user_text)
                    tg_safe_send(f"🤖 {cevap[:4000]}")
                except Exception as ce:
                    logging.error(f"AI chat hatasi: {ce}")
                    tg_safe_send("⚠️ AI şu an cevap veremedi.")
            threading.Thread(target=_ai_chat, daemon=True).start()
        else:
            tg_safe_send("📝 Not kaydedildi. Bir sonraki analizde kullanılacak.")

    except Exception as e:
        logging.error("handle_free_text: " + str(e))
        bot.send_message(MY_CHAT_ID, f"Kayit hatasi: {e}")


def _execute_user_trade_request(asset_sym, side, user_text):
    """
    Kullanici 'Gold long' veya 'Silver short' gibi bir komut verdi.
    1. Gemini'den SL/TP/SIZE hesaplamasini iste
    2. Affordability check
    3. Direkt trade ac - onay yok
    """
    try:
        bot.send_message(MY_CHAT_ID,
            f"📊 {asset_sym} {side} — Gemini SL/TP/SIZE hesaplıyor...")

        extra = (
            f"\n\n=== KULLANICI DOĞRUDAN EMRİ ===\n"
            f"Kullanici komutu: '{user_text}'\n"
            f"GÖREV: {asset_sym} icin {side} pozisyon ac.\n"
            f"1. {asset_sym} su anki fiyatini kontrol et\n"
            f"2. {side} icin uygun SL ve TP hesapla\n"
            f"3. Mevcut bakiyeye gore uygun SIZE belirle\n"
            f"4. ASAGIDAKI FORMAT ile yaz - baska hicbir format KABUL EDILMEZ:\n"
            f"TRADE: {asset_sym} | SIDE: {side} | SIZE: [sayi] | SL: [fiyat] | TP: [fiyat]\n"
            f"ÖNEMLI: SIZE/SL/TP degerlerini gercek sayi olarak yaz, X veya placeholder kullanma!\n"
            f"=== SON ==="
        )
        analysis = fetch_strategic_response("AUTONOMOUS", extra_data=extra)

        import re as _re
        pattern = r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*(BUY|SELL)\s*\|\s*SIZE:\s*([\d\.]+)\s*\|\s*SL:\s*([\d\.]+)\s*\|\s*TP:\s*([\d\.]+)"
        matches = _re.findall(pattern, analysis)

        if not matches:
            ozet = analysis[:800] if analysis else "Analiz alinamadi."
            bot.send_message(MY_CHAT_ID,
                f"⚠️ {asset_sym} {side}: Gemini TRADE satiri uretmedi.\n"
                f"Analiz: {ozet}")
            return

        # execute_nexus_trade ile direkt ac (affordability check icinde)
        result = execute_nexus_trade(analysis)
        if result:
            bot.send_message(MY_CHAT_ID, f"🔔 {asset_sym} {side}:\n{result}")
        else:
            bot.send_message(MY_CHAT_ID, f"⚠️ {asset_sym} {side}: Trade acilamadi.")

    except Exception as e:
        logging.error(f"_execute_user_trade_request hatasi: {e}")
        bot.send_message(MY_CHAT_ID, f"⚠️ Hata: {e}")

# ============================================================
# ANA DONGU (HEARTBEAT + SPREAD WRITER)
# ============================================================
def schutz_loop():
    """
    5-Min koruma thread:
    1. Kara Kugu volatilite kontrolu
    2. Trailing SL guncelleme (Pyramiding pozisyonlari)
    """
    logging.info("Koruma-Thread baslatildi (5 Dak: KaraKugu + Trailing SL)")
    time.sleep(30)
    while True:
        try:
            h = capital_session.get_headers()
            if h:
                kapatilanlar = volatilite_kontrol(h)
                if kapatilanlar:
                    logging.warning(f"KaraKugu: {len(kapatilanlar)} pozisyon kapatildi")
                n_trail = update_trailing_sl(h)
                if n_trail > 0:
                    logging.info(f"Trailing SL: {n_trail} pozisyon guncellendi")
        except Exception as e:
            logging.error(f"Schutz-Thread hatasi: {e}")
        time.sleep(300)




def main_loop():
    dongu_sayaci = 0
    spread_scan_counter = 0

    while True:
        try:
            dongu_sayaci += 1
            spread_scan_counter += 1
            h = capital_session.get_headers()

            if not h:
                logging.error("API bağlantısı yok, 60s bekleniyor")
                tg_safe_send(f"⚠️ NEXUS v14.0: Capital.com API hatası! Döngü #{dongu_sayaci}")
                time.sleep(60)
                continue

            # Volatilite kontrol: Schutz-Thread (alle 5 Min)
            # Hier nicht mehr nötig - läuft separat ohne Quota

            # Spread alle 3 Zyklen (alle 90 Minuten) in Config schreiben
            if spread_scan_counter >= 3:
                spread_scan_counter = 0
                logging.info("🔄 Automatischer Spread-Scan...")
                scan_and_write_spreads()

            # Pyramiding-JSON VOR jeder KI-Analyse abgleichen
            sync_result = sync_pyramiding_from_capital()
            if "korrigiert" in sync_result:
                logging.warning(f"Pyramiding-Sync: {sync_result}")
                tg_safe_send(f"Piramiding Senkron:\n{sync_result}")

            # ============================================================
            # DEPOT DRAWDOWN KONTROLU - Her dongu basinda
            # ============================================================
            acc_dd = get_account_info(h)
            if acc_dd:
                toplam = float(acc_dd.get("toplam", 0))
                update_depot_peak(toplam)
                dd_halt, dd_reason = check_depot_dd(toplam)
                if dd_halt:
                    msg = ("DEPOT DD ALARMI! Bugun yeni trade YOK.\n" + dd_reason)
                    logging.warning(msg)
                    tg_safe_send(msg)
                    time.sleep(1800)
                    continue

            # Strategische Analyse
            analysis = fetch_strategic_response("AUTONOMOUS")

            if "QUOTA_FULL_ALL" in analysis:
                logging.warning("TÜM AI modelleri (Gemini+Groq) quota dolu! 60dk bekleniyor")
                tg_safe_send("⚠️ NEXUS v14.0: Gemini + Groq quota doldu. 60dk bekleniyor...")
                time.sleep(3600)
                continue

            if "API Bağlantı" in analysis:
                time.sleep(60)
                continue

            # HEARTBEAT
            if "TRADE:" not in analysis:
                if is_weekend():
                    we_info = "🔵 HAFTASONU: Sadece kripto izleniyor (BTC/ETH/SOL/XRP)"
                else:
                    we_info = "🟢 HAFTA İÇİ: Tüm assetler aktif"
                backend, model = get_current_model_and_backend()
                ai_icon = "🟢" if backend == "GEMINI" else "🟡"
                status_msg = (
                    f"NEXUS v14.1 Tarama #{dongu_sayaci}\n"
                    f"{we_info}\n"
                    f"{ai_icon} AI: {backend} ({model})\n"
                    f"Trade sinyali yok."
                )
                tg_safe_send(status_msg)
            else:
                backend, model = get_last_ai_info()
                ai_icon = "🟢" if backend == "GEMINI" else "🟡"
                tg_safe_send(f"{ai_icon} AI: {backend} ({model}) analizi:\n{analysis[:3800]}")

            # Wochenende: max 3 Krypto-Positionen
            if is_weekend():
                h_check = capital_session.get_headers()
                if h_check:
                    alle_pos = get_positions(h_check)
                    krypto_pos = [p for p in alle_pos if is_crypto(p['market']['epic'])]
                    if len(krypto_pos) >= 3:
                        try: bot.send_message(MY_CHAT_ID, f"⚠️ Haftasonu kripto limiti: {len(krypto_pos)}/3 kripto pozisyon açık")
                        except: pass
            res = execute_nexus_trade(analysis)
            if res:
                backend, model = get_current_model_and_backend()
                ai_icon = "🟢" if backend == "GEMINI" else "🟡"
                tg_safe_send(f"🔔 İşlem Bildirimi [{ai_icon}{backend}]:\n{res}")
                # Nach Trade: echten Depot-Stand per Telegram senden
                try:
                    h_after = capital_session.get_headers()
                    if h_after:
                        sync_pyramiding_from_capital()
                        pos_after = get_positions(h_after)
                        acc_after = get_account_info(h_after)
                        pos_liste = ""
                        for p in pos_after:
                            sn = p["market"].get("instrumentName", p["market"]["epic"])
                            dr = p["position"]["direction"]
                            up = float(p["position"].get("upl", 0))
                            st = get_pyramiding_stufe(p["market"]["epic"])
                            pos_liste += f"  {sn} {dr} UPL:{up:.2f} Seviye:{st}\n"
                        rp = acc_after["musait"]/acc_after["toplam"]*100 if acc_after.get("toplam",0)>0 else 0
                        nakit_val = acc_after["nakit"]
                        musait_val = acc_after["musait"]
                        upl_val = acc_after["upl"]
                        dm = (
                            "TRADE SONRASI DEPO:\n"
                            f"Nakit: {nakit_val:.2f} EUR | "
                            f"Musait: {musait_val:.2f} EUR ({rp:.1f}%) | "
                            f"UPL: {upl_val:.2f} EUR\n"
                            f"Pozisyonlar ({len(pos_after)}):\n"
                            f"{pos_liste or '  Yok'}"
                        )
                        bot.send_message(MY_CHAT_ID, dm)
                except Exception as e:
                    logging.error(f"Post-Trade Status Fehler: {e}")

            # Alle 6 Zyklen Pyramiding-Zusammenfassung
            if dongu_sayaci % 6 == 0:
                ozet = "📊 Pyramiding Özet:\n"
                for k, v in MARKET_CONFIG.items():
                    stufe = get_pyramiding_stufe(v['epic'])
                    if stufe > 0:
                        ozet += f"• {k}: Seviye {stufe} (aktif)\n"
                if "Seviye" in ozet:
                    try: bot.send_message(MY_CHAT_ID, ozet)
                    except: pass

            time.sleep(1800)  # 30 Minuten

        except Exception as e:
            logging.error(f"Ana döngü hatası: {e}")
            time.sleep(60)

# ============================================================
# BAŞLANGIÇ
# ============================================================
if __name__ == "__main__":
    # ============================================================
    # 409 SCHUTZ: Andere Instanzen automatisch beenden
    # ============================================================
    import subprocess, signal
    current_pid = os.getpid()
    try:
        result = subprocess.run(
            ["pgrep", "-f", "nexus_ceo.py"],
            capture_output=True, text=True
        )
        pids = [int(p) for p in result.stdout.strip().split("\n") if p and int(p) != current_pid]
        if pids:
            logging.info(f"🔴 Andere Instanzen gefunden: {pids} - werden beendet...")
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass
            time.sleep(3)
            # Notfalls SIGKILL
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
            time.sleep(2)
            logging.info("✅ Alte Instanzen beendet.")
    except Exception as e:
        logging.warning(f"PID-Check Fehler: {e}")

    init_db()  # SQLite DB initialisieren

    # Hafta sonu / hafta ici modu belirle
    if is_weekend():
        mod_bilgisi = "🔵 HAFTASONU MODU: SADECE KRİPTO (BTC/ETH/SOL/XRP)"
    else:
        mod_bilgisi = "🟢 HAFTA İÇİ MODU: Tüm assetler aktif"

    hesap_mod = "🧪 DEMO" if IS_DEMO else "💰 CANLI (LIVE)"

    # Capital.com'dan hesap ADINI cek - birden fazla deneme
    _depot_hesap_adi = ""
    _depot_hesap_id  = TARGET_ACCOUNT_ID

    for _attempt in range(3):
        try:
            h_init = capital_session.get_headers()
            if not h_init:
                time.sleep(3)
                continue
            # Direkt /accounts endpoint'inden tam liste cek
            _acc_r = requests.get(
                f"{CAPITAL_URL}/accounts",
                headers=h_init, timeout=10
            )
            if _acc_r.status_code == 200:
                _accounts = _acc_r.json().get("accounts", [])
                # TARGET_ACCOUNT_ID ile eslesen hesabi bul
                _found = None
                if TARGET_ACCOUNT_ID:
                    for _a in _accounts:
                        if str(_a.get("accountId","")) == str(TARGET_ACCOUNT_ID):
                            _found = _a
                            break
                if not _found and _accounts:
                    _found = _accounts[0]
                if _found:
                    _depot_hesap_adi = _found.get("accountName", "")
                    _depot_hesap_id  = _found.get("accountId", TARGET_ACCOUNT_ID)
                    logging.info(f"Hesap adi: '{_depot_hesap_adi}' (ID: {_depot_hesap_id})")
                    break
        except Exception as _e:
            logging.warning(f"Hesap adi cekilemedi (deneme {_attempt+1}): {_e}")
            time.sleep(3)

    # Depot prefix ayarla - TUM mesajlarda gorunecek
    set_depot_prefix(_depot_hesap_adi, _depot_hesap_id, IS_DEMO)

    # Baslangic mesaji icin hesap bilgisi - ISIM goster, ID degil
    if _depot_hesap_adi:
        hesap_id_info = f"Konto: {_depot_hesap_adi}"
    elif TARGET_ACCOUNT_ID:
        hesap_id_info = f"Konto-ID: {str(TARGET_ACCOUNT_ID)[-8:]}"
    else:
        hesap_id_info = "Konto: (ilk hesap)"

    # AI backend durumu
    gemini_ok = "✅" if GEMINI_KEYS else "❌"
    groq_ok   = "✅" if GROQ_KEYS   else "❌"
    ai_info   = f"Gemini:{gemini_ok} gemini-3-flash-preview | Groq:{groq_ok} Llama4"

    # Doktrin yukle ve kaynagini al
    load_doctrine()  # _aktif_doktrin_kaynagi'ni gunceller
    doktrin_info = _aktif_doktrin_kaynagi

    baslanis_mesaji = f"""NEXUS CEO v14.2 - QUANT FUND Baslatildi
{hesap_mod} | {hesap_id_info}
{mod_bilgisi}
🤖 AI: {ai_info}
📜 Doktrin: {doktrin_info}

Mod: Hibrit Gremium + MA 9/26 + ADX + RSI
Interval: 30 dakika
Kara Kuğu Koruması (3 Seviye):
  -%8  Gemini Acil Karar
  -%12 Otomatik Kapat
  -%18 ACIL TUM POZİSYONLARI KAPAT
Koruma-Thread: 5 Dakika (Quota yok)
Haber-Thread: Saat basi RSS (Asya/Avrupa/Amerika) | X: 30 Dak | Groq DB haberler okur
Alternatif Veri: 31 Cargo Airline + 18 Gemi Bolgesi + BDI
  GDACS + NHC Kasirga + HDD/CDD + AB Gaz Deposu + ECMWF + NOAA
Haber Geçmişi: 14 Gün
Pyramiding: Sinir yok (min %2 kar per seviye) | EXIT: Gemini veya Trailing SL %5
Gremium: 11 Mentor (6+ JA gerekli)
Spread Filter: Max 0.5 | Auto-Config: AKTİF
Haftasonu: Kripto AKTIF (sadece BTC/ETH/SOL/XRP)\nAşama 1 Filtre (Bollinger+Fib): AKTİF
Google Search Grounding: AKTIF\nSQLite Hafıza: AKTİF\nKelly-Kriteri: AKTİF\nEconomic Calendar: AKTIF\nHava Durumu API: AKTİF\nKaynak Güvenilirliği: AKTİF

Komutlar: /help"""

    try: bot.send_message(MY_CHAT_ID, baslanis_mesaji, reply_markup=NEXUS_MENU)
    except Exception as e: logging.error(f"Başlangıç mesajı hatası: {e}")

    sync_bericht = sync_pyramiding_from_capital()
    logging.info(sync_bericht)
    try: bot.send_message(MY_CHAT_ID, f"Başlangıç Senkronu:\n{sync_bericht}")
    except: pass

    # BotFather menu - "/" yazinca komutlar gorunsun
    try:
        from telebot.types import BotCommand, BotCommandScopeDefault
        # Once mevcut komutlari sil - Telegram cache'ini temizle
        try:
            bot.delete_my_commands(scope=BotCommandScopeDefault())
        except:
            pass
        bot.set_my_commands([
            BotCommand("status",      "Tam quant analiz (Gemini)"),
            BotCommand("pozisyon",    "Acik pozisyonlar ve PnL"),
            BotCommand("ma",          "Teknik sinyaller (MA/ADX/RSI)"),
            BotCommand("stats",       "Trade istatistikleri"),
            BotCommand("backtest",    "Backtest - ornek: /backtest GOLD 200"),
            BotCommand("deepdive",    "Tarihsel analiz"),
            BotCommand("news",        "Haber ozeti - ornek: /news OIL 7"),
            BotCommand("newscollect", "Manuel haber toplama"),
            BotCommand("sources",     "Kaynak guvenilirlik skorlari"),
            BotCommand("kayip",       "Bugunun kayip sayaci"),
            BotCommand("sifirla",    "DD halt ve kayip sayacini sifirla"),
            BotCommand("aidurum",    "Gemini/Groq AI backend durumu"),
            BotCommand("menu",        "Interaktif komut paneli"),
            BotCommand("bloklar",     "Aktif HARD BLOCK listesi"),
            BotCommand("spread",      "Spread tarama ve guncelleme"),
            BotCommand("volatilite",  "Volatilite ve risk kontrolu"),
            BotCommand("unut",        "Kaydedilen kullanici notlarini sil"),
            BotCommand("help",        "Tum komutlar ve kullanim rehberi"),
        ])
        logging.info("Telegram menu (BotCommand) ayarlandi")

        # Sol alttaki menu butonu - COMMANDS tipinde ayarla
        # "/" yazinca komut listesi acilir
        try:
            from telebot.types import MenuButtonCommands
            bot.set_chat_menu_button(
                chat_id=MY_CHAT_ID,
                menu_button=MenuButtonCommands()
            )
            logging.info("Menu butonu (Commands) ayarlandi")
        except Exception as mb_e:
            logging.debug(f"Menu butonu ayar hatasi (normal): {mb_e}")

    except Exception as e:
        logging.warning("BotCommand ayar hatasi: " + str(e))

    def telegram_polling_with_watchdog():
        """Telegram polling - crash olursa yeniden baslatir, trading durmaz."""
        global _tg_disabled
        while True:
            try:
                logging.info("Telegram polling baslatiliyor...")
                with _tg_lock:
                    _tg_disabled = False
                bot.infinity_polling(timeout=30, long_polling_timeout=25)
            except Exception as e:
                err = str(e).lower()
                logging.warning(f"Telegram polling hatasi: {e}")
                if any(x in err for x in ["unauthorized", "forbidden", "token", "blocked"]):
                    logging.error("Telegram token gecersiz - polling durduruldu, trading devam ediyor")
                    with _tg_lock:
                        _tg_disabled = True
                    break  # Gecersiz token - yeniden deneme anlamsiz
                logging.info("Telegram yeniden baslatiliyor... 30s bekleniyor")
                time.sleep(30)

    threading.Thread(target=telegram_polling_with_watchdog, daemon=True).start()
    threading.Thread(target=schutz_loop, daemon=True).start()
    threading.Thread(target=news_collector_loop, daemon=True).start()
    logging.info("Koruma-Thread: 5 Dak | Haber-Thread: 60 Dak | Telegram: Watchdog aktif")
    main_loop()
