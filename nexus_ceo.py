# -*- coding: utf-8 -*-
# +======================================================================+
# |  NEXUS NATURE v15.8 - BRIDGEWATER EDITION                          |
# |  Datei: nexus_ceo.py                                                |
# |  Erstellt: 2026-07-14  |  Zuletzt geaendert: 2026-09-21            |
# |  Aenderungen v15.24 (2026-10-08):                                   |
# |    - Stop-Leiter: nach Mirror-TP-Stufe 1 Stop auf den Einstieg,    |
# |      nach Stufe 2 auf den Kurs von Stufe 1, nach Stufe 3 auf den   |
# |      Kurs von Stufe 2 (.env STOP_LEITER, Standard true)            |
# |    - Gruppen-Limit: hoechstens MAX_JE_GRUPPE (Standard 2) Maerkte  |
# |      je Gruppe offen (Energie, Metalle, Agrar, Krypto)             |
# |    - Krypto-Erkennung nach Basis-Kuerzel statt Teilwort: Gasoline  |
# |      ("SOL") galt als Krypto (Gremium 3/5, Wochenend-Scan)         |
# |  Aenderungen v15.23 (2026-10-08):                                   |
# |    - /handbuch (/handbook, /kilavuz): schickt das komplette Handbuch |
# |      als Datei in der eigenen Sprache (/handbuch en = Englisch),   |
# |      mit einer Tabelle der Einstellungen, die der Bot jetzt nutzt  |
# |  Aenderungen v15.22 (2026-10-06):                                   |
# |    - Groq / Qwen (OpenRouter) / Nvidia: Modell-Schleife wie in     |
# |      swarm.py - Modellliste, Kette aus Haupt- und Ersatzmodellen,  |
# |      totes Modell 24 h gesperrt, Ersatz per Mini-Aufruf geprueft   |
# |      und in die .env geschrieben (Sicherung + Kontrolle)           |
# |    - alle Keys aus QWEN_KEYS / NVIDIA_KEYS werden benutzt          |
# |    - /update_models zeigt und prueft auch Groq, Qwen, Nvidia;      |
# |      /update_models best = auf das beste Modell wechseln           |
# |  Aenderungen v15.21 (2026-10-06):                                   |
# |    - Gegensignal = nur schliessen: keine sofortige Gegen-Order     |
# |      mehr (sie lief ohne Pruefungen und ohne Bestaetigung); die    |
# |      neue Richtung eroeffnet der naechste Scan als normale Order   |
# |    - Ergebnis jedes Scans steht jetzt auch im Log (Trade-Ergebnis) |
# |    - Schliessen fehlgeschlagen: Grund wird gemeldet; ein Verlust   |
# |      zaehlt nur, wenn die Position wirklich geschlossen wurde      |
# |  Aenderungen v15.20 (2026-10-06):                                   |
# |    - /diagnose (/diagnosis, /teshis) und Taste: startet            |
# |      nexus_diagnose.py (eigene Datei, nur lesend) und schickt die  |
# |      Kurzfassung als Nachricht, den ganzen Bericht als Datei       |
# |  Aenderungen v15.19 (2026-10-05):                                   |
# |    - Sprachen: Deutsch / English / Tuerkce. Sprachwahl beim ersten  |
# |      Start per Telegram, Wahl steht als BOT_LANGUAGE in der .env;   |
# |      Texte in nexus_lang.py, Uebersetzung erst beim Senden          |
# |    - Befehle haben deutsche und englische Namen zusaetzlich         |
# |    - SICHERHEIT: Befehle und Tasten nur noch aus dem Chat           |
# |      MY_CHAT_ID (vorher prueften das nur einzelne Befehle)          |
# |    - Ohne MY_CHAT_ID nennt der Bot dem Schreibenden seine Chat-ID   |
# |  Aenderungen v15.18 (2026-10-05):                                   |
# |    - Wiedereinstiegs-Sperre: nach einer Schliessung x Stunden kein  |
# |      neuer Einstieg in dasselbe Symbol/dieselbe Richtung            |
# |      (.env: WIEDEREINSTIEG_SPERRE_STD, Standard 6)                  |
# |    - Gemini: abgelehnte Keys (401) werden ausgesetzt; Modell ruht,  |
# |      wenn alle GUELTIGEN Keys am Tageslimit sind; 503 -> 2. Versuch |
# |    - Weniger Telegram: Scan ohne Trade / Gemini-Grund nur bei       |
# |      Aenderung (.env: SCAN_MELDUNGEN=alle = wie vorher)             |
# |    - Breakeven-Stop zaehlt nicht mehr als Stop-Loss-Verlust         |
# |  Aenderungen v15.17 (2026-10-05):                                   |
# |    - Rausch-Schutz: Stop Loss neuer Positionen mindestens           |
# |      Tagesspanne (Tages-ATR) x SL_ATR_MULT vom Kurs entfernt        |
# |      (vorher fest 1.5 %); .env: SL_ATR_MULT, SL_MAX_PCT             |
# |    - /sl_weiten: Stops offener Positionen pruefen / weiten          |
# |    - Positions-Report zeigt den Stop-Abstand in Tagesspannen        |
# |  Aenderungen v15.16 (2026-10-05):                                   |
# |    - Schliess-Melder: jede geschlossene Position wird mit Grund     |
# |      (Stop Loss / Take Profit / ...) und Ergebnis gemeldet;         |
# |      Stop-Loss-Verluste zaehlen fuer die Tages-Verlustsperre        |
# |    - FIX: Max-Positionen wird vor JEDER Eroeffnung geprueft         |
# |      (.env: MAX_POSITIONEN, MAX_VERLUSTE_PRO_TAG)                   |
# |    - "Gemini quota doldu" nennt den Grund je Modell                 |
# |    - Startmeldung zeigt die echte Version                           |
# |  Aenderungen v15.15 (2026-10-05):                                   |
# |    - Positions-Report zeigt SL, TP, Tages-ATR, Tagesziel und        |
# |      Mirror-TP-Stufen je Position                                   |
# |    - Gemini Modell-Schleife wie swarm.py (Live-Modellliste, Kette,  |
# |      Key-/Modell-Wechsel, Tageslimit-Gedaechtnis), /update_models   |
# |    - .env: QWEN_KEYS / NVIDIA_KEYS / NVIDIA_MODEL werden gelesen    |
# |  Aenderungen v15.14 (2026-10-04):                                   |
# |    - Krypto-Nachtsperre (Cihat/Taleb 23-06 Uhr) standardmaessig AUS |
# |      Einschalten in der .env: KRYPTO_NACHT_SPERRE=true              |
# |  Aenderungen v15.13 (2026-10-04):                                   |
# |    - FIX: Krypto-Kerzen 20m/45m/2h aus 5m/15m/1h zusammengesetzt    |
# |      (MINUTE_20/MINUTE_45/HOUR_2 gibt es bei Capital.com nicht ->   |
# |      Krypto war immer NOTR und kam nie zum Gate-Keeper)             |
# |    - FIX: Stunden-ATR "HOUR_1" -> "HOUR" (ATR war immer 0)          |
# |    - Gremium: Krypto 3/5 JA (GREMIUM_MIN_JA_KRYPTO), sonst 4/5      |
# |  Aenderungen v15.12 (2026-10-03):                                   |
# |    - Mirror-TP: Prozent < Mindestgroesse -> Mindestgroesse verkaufen|
# |      (keine Stufe auslassen); Rest < Mindestgroesse -> ganz zu      |
# |  Aenderungen v15.11 (2026-10-03):                                   |
# |    - FIX: TP bleibt bei SL-Aenderungen (Breakeven/Trailing) erhalten|
# |    - FIX: Mirror-TP Teilverkauf ueber Gegen-Order + Depot-Pruefung  |
# |      (vorher DELETE mit Groesse - gibt es bei Capital.com nicht)    |
# |    - FIX: Logging force=True (INFO-Meldungen gingen verloren)       |
# |  Aenderungen v15.10 (2026-10-03):                                   |
# |    - FIX: KI-Fallback (Gemini-Quota voll) nur noch mit echten Daten |
# |      (Gate-Keeper-Kandidaten + Live-Kurse), sonst kein Trade        |
# |    - FIX: safe_trade_size AUTO: min_size hebelt .env-Limit nicht    |
# |      mehr aus; bei Fehlern 0 statt min_size; EUR-Epics korrekt      |
# |    - FIX: execute_nexus_trade: Groesse einmal berechnen, Margin-    |
# |      Check mit echten Units, SL/TP-Plausibilitaet, SL/TP-Sync       |
# |  Aenderungen v15.9 (2026-09-27/28):                                 |
# |    - MAX_POSITION_EUR (.env), MAX_SPREAD leer = kein Limit          |
# |  Aenderungen v15.8 (2026-09-21):                                    |
# |    - FIX: Markt-geschlossen Telegram-Benachrichtigung mit           |
# |      tahmini açılış saati (Wochentag/Uhrzeit-basiert, UTC)         |
# |    - NEU: Post-Order Verifikation — 8 Sek nach Order Depot prüfen  |
# |      ✅ bestätigt oder ⚠️ nicht gefunden → Telegram Nachricht       |
# |  Aenderungen v15.7 (2026-09-19):                                    |
# |    - FIX: get_candles() gibt jetzt (data, grund) Tuple zurueck      |
# |      Grund sichtbar in MA-Nachricht: Session yok / API 401 / etc.  |
# |      _analyse_timeframe + alle Caller auf Tuple-Rueckgabe umgebaut  |
# |  Aenderungen v15.6 (2026-09-18, Merge):                             |
# |    - MERGE: Mirror-TP Multi-Level (House Edge) in update_trailing_sl|
# |      ATR-basiert: 3 Level (0.5×/1.0×/1.5×), je 25% Partial-Close   |
# |      Steuerbar per .env: MIRROR_TP_ENABLED, MIRROR_TP_LEVEL_x_MULT  |
# |      Parallel zum bestehenden daily_tp_watcher (kein Konflikt)      |
# |    - MERGE: Provider-Anzeige zeigt Key-Anzahl pro Provider          |
# |      z.B. "groq(3), gemini(10), qwen(1), nvidia(1)"                 |
# |    - UPDATE: /help + BotCommand Liste komplett — alle Befehle drin  |
# |      /kapat + /manuell ergänzt, mit/ohne / Varianten dokumentiert   |
# |  Aenderungen v15.5 (2026-09-16, Merge):                             |
# |    - MERGE: /kapat Befehl (SYMBOL / ALLE) + BotCommand Eintrag      |
# |    - MERGE: MAX_SPREAD .env-konfigurierbar (os.getenv)              |
# |    - MERGE: SPREAD HARD BLOCK - check_spread_ok() wird echt         |
# |      aufgerufen, Gemini kann Spread-Regel nicht mehr umgehen        |
# |    - MERGE: get_atr_tp_sl() korrekt implementiert (war Geisterlink  |
# |      - wurde aufgerufen aber existierte nirgends, Feature lief nie) |
# |    - MERGE: ATR-Fallback TP/SL (TP=90%/SL=40% Daily-ATR, RR 1:2.25) |
# |      nur wenn Gemini TP/SL fehlt oder <0.3% vom Kurs entfernt ist   |
# |  Aenderungen v15.3 Bridgewater (2026-09-07):                        |
# |    - BRIDGEWATER: load_bridgewater_rules() aus .txt Datei           |
# |    - BRIDGEWATER: _format_kandidaten_strict() Hidden-Engine Pattern |
# |    - BRIDGEWATER: Gemini sieht keine rohen JSONs mehr (Anti-Halluz) |
# |    - BRIDGEWATER: Externe bridgewater_rules.txt steuerbar ohne Code |
# |  Aenderungen v15.2 Sniper (2026-09-04):                             |
# |    - SNIPER: safe_trade_size is_manual=True fuer /manuell Handler   |
# |    - SNIPER: /manuell Handler respektiert User-Eingabe (Limits OK)  |
# |    - SNIPER: sleep(1800) x4 → SCAN_INTERVAL_SEC im main_loop       |
# |    - SNIPER: Version-Strings korrigiert                             |
# |  Aenderungen v15.1 Sniper (2026-08-24):                             |
# |    - SNIPER: Gremium→Score→Execute vollständig verknüpft           |
# |    - SNIPER: news_sentiment DB→Gremium→Execute→Log                 |
# |    - SNIPER: EIA/COT/USDA/Transport direkt im Gemini-Prompt        |
# |    - SNIPER: Gremium-Begründungen (grunler) im Prompt sichtbar     |
# |    - SNIPER: Execute loggt Gremium-Stimmen pro Symbol              |
# |  Aenderungen v14.9 (2026-08-23):                                    |
# |    - Gremium: Cihat/Rogers/Dalio/Taleb/Soros (5 echte Mentoren)     |
# |    - GDELT finally-block, Reuters entfernt, WAL Mode               |
# |    - KRITIK FIX: Trailing SL Peak = echter Einstandspreis (nicht    |
# |      sl_float/0.95 Berechnung — das war der -251 EUR Bug!)          |
# |    - safe_trade_size() bereits vorhanden: EUR->Units korrekt        |
# |  Aenderungen v14.8 (2026-08-12):                                    |
# |    - KRITIK FIX: Trailing SL Peak-Reset bei neuer Position          |
# |    - NEU: EIA Weekly Petroleum (Öl-Lagerbestände, kein Key)         |
# |    - NEU: CFTC COT Report (Gold/Silber/Öl Positioning, kein Key)   |
# |    - NEU: USDA WASDE (Kakao/Kaffee/Weizen Supply/Demand, kein Key) |
# |    - NEU: Transport-CO2 / Eurostat LKW-Verkehr (Wirtschaftsindik.) |
# |    - GDELT Doc 2.0 (kostenlos) + Alpha Vantage News (mit Sentiment) |
# |    - GDELT: 7 Finanzthemen × 25 Artikel = bis zu 175 Artikel/Lauf  |
# |    - Haber thread: stündlich RSS + alle 3h GDELT                    |
# |    - Telegram-Meldung: nur alle 3h (nicht jede Stunde)             |
# +======================================================================+
# IATA Jet Fuel + Airline Sentiment
# GDACS + NHC Hurricanes + HDD/CDD + EU Gas Storage + ECMWF + NOAA Anomaly
# Global Weather + Disasters + Google Trends + 31 Airlines + 18 Ship Regions
# Alternative Data: Cargo Flüge + Schiffsverkehr + BDI + E-Commerce
# News Cache (RSS + X/Nitter) | 14 Tage Trend-Analyse
# 3-Stufen Kara Kugu: -8% Gemini, -12% Auto, -18% Notfall
# Stage 1: Python Gate-Keeper (ADX+RSI+MA+Bollinger+Fibonacci)
# Stage 2: Gemini Internet-Suche + Interpretation + Trade
# SQLite Gedaechtnis | Google Search Grounding | Kelly-Kriterium
import os, time, requests, telebot, re, logging, json, threading, sys
import sqlite3
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- CONFIG IMPORT VERSUCH ---
try:
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from capital_markets_config import MARKET_CONFIG
    logging.info(f"capital_markets_config.py geladen: {len(MARKET_CONFIG)} asset")
except ImportError:
    logging.warning("capital_markets_config.py bulunamadi — dahili liste")
    MARKET_CONFIG = {
        "EURUSD":    {"epic": "EURUSD",    "min_size": 100.0, "spread": 0.0001},
        "GOLD":      {"epic": "GOLD",      "min_size": 0.01,  "spread": 0.75},
        "SILVER":    {"epic": "SILVER",    "min_size": 1.0,   "spread": 0.05},
        "OIL_CRUDE": {"epic": "OIL_CRUDE", "min_size": 1.0,   "spread": 0.04},
        "OIL_BRENT": {"epic": "OIL_BRENT", "min_size": 1.0,   "spread": 0.01},
        "BTC_USD":   {"epic": "BTCUSD",    "min_size": 0.01,  "spread": 10.0},
        "ETH_USD":   {"epic": "ETHUSD",    "min_size": 0.01,  "spread": 1.75},
        "XRP_USD":   {"epic": "XRPUSD",    "min_size": 1.0,   "spread": 0.007},
        "SOL_USD":   {"epic": "SOLUSD",    "min_size": 0.1,   "spread": 0.52},
    }

# .env TRADING_ASSETS Filter: TRADING_ASSETS=GOLD,SILVER,OIL_CRUDE,EURUSD
# Wenn gesetzt → nur diese Assets handeln
# Wenn leer → alle Assets aus capital_markets_config.py
# TRADING_ASSETS aus .env: TRADING_ASSETS=GOLD,SILVER,OIL_CRUDE
# Wenn LEER → alle Assets aus capital_markets_config.py (kein Filter)
_trading_assets_env = os.getenv("TRADING_ASSETS", "").strip()
if _trading_assets_env:
    _wanted = {a.strip().upper() for a in _trading_assets_env.split(",") if a.strip()}
    _before = len(MARKET_CONFIG)
    MARKET_CONFIG = {k: v for k, v in MARKET_CONFIG.items() if k in _wanted}
    logging.info(f"TRADING_ASSETS aus .env: {list(MARKET_CONFIG.keys())}")
else:
    logging.info(f"TRADING_ASSETS nicht gesetzt → alle {len(MARKET_CONFIG)} Assets aus capital_markets_config.py")

# ── Logging: reines Text, tägliche Rotation ──────────────────────────
import logging.handlers as _log_handlers

_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_ceo.log")
_log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

_file_handler = _log_handlers.TimedRotatingFileHandler(
    _log_file, when="midnight", backupCount=7, encoding="utf-8"
)
_file_handler.setFormatter(_log_formatter)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_log_formatter)

# v15.11: force=True. Weiter oben (Config-Import) wird schon geloggt, dadurch
# war dieser Aufruf wirkungslos: kein Datei-Log, alle INFO-Meldungen verloren.
_log_handlers_aktiv = [_file_handler]
try:
    # Konsole nur, wenn stdout nicht ohnehin in dieselbe Datei umgeleitet ist
    if not os.path.samestat(os.fstat(sys.stdout.fileno()), os.stat(_log_file)):
        _log_handlers_aktiv.append(_console_handler)
except Exception:
    _log_handlers_aktiv.append(_console_handler)
logging.basicConfig(level=logging.INFO, handlers=_log_handlers_aktiv, force=True)
logging.info(f"NEXUS NATURE v15.3 Log gestartet → {_log_file}")
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
# KONFIGURASYON — alles aus .env, kein Hardcode
# ============================================================
TG_TOKEN   = os.getenv("TG_TOKEN") or os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
# Alternative-Data Zugangsdaten (opsiyonel - bos ise fonksiyonlar anonim/limitli calisir)
OPENSKY_USER = os.getenv("OPENSKY_USER", "")
OPENSKY_PASS = os.getenv("OPENSKY_PASS", "")
AISHUB_USER  = os.getenv("AISHUB_USER", "")
AISHUB_PASS  = os.getenv("AISHUB_PASS", "")

# ── Gemini ──────────────────────────────────────────────────
# Unterstützt beide Formate:
#   GEMINI_KEYS=key1,key2,key3          (kommagetrennt, deine .env)
#   GEMINI_API_KEY_1=key1               (nummeriert, alte .env)
def _parse_gemini_keys():
    # Format 1: GEMINI_KEYS=k1,k2,k3
    raw = os.getenv("GEMINI_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    # Format 2: GEMINI_API_KEY_1 ... GEMINI_API_KEY_9
    for i in range(1, 10):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys

GEMINI_KEYS = _parse_gemini_keys()

# ── Groq ────────────────────────────────────────────────────
GROQ_KEYS  = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Qwen / OpenRouter ───────────────────────────────────────
# v15.15: auch die Namen aus swarm.py lesen (QWEN_KEYS / NVIDIA_KEYS / NVIDIA_MODEL)
QWEN_API_KEY  = os.getenv("QWEN_API_KEY", "").strip() or os.getenv("QWEN_KEYS", "").split("#")[0].split(",")[0].strip()
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://openrouter.ai/api/v1")
QWEN_MODEL    = os.getenv("QWEN_MODEL", "qwen/qwen-2.5-32b-instruct")

# ── Nvidia NIM ──────────────────────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip() or os.getenv("NVIDIA_KEYS", "").split("#")[0].split(",")[0].strip()
NVIDIA_MODEL   = (os.getenv("NVIDIA_MODELS") or os.getenv("NVIDIA_MODEL") or "qwen/qwen2.5-coder-32b").split("#")[0].split("->")[0].strip()

# ── Ollama (lokal) ──────────────────────────────────────────
OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
OLLAMA_PRIORITY = os.getenv("OLLAMA_PRIORITY", "last")  # first | last | only

# ── Provider-Reihenfolge ────────────────────────────────────
# .env: PROVIDER_ORDER=groq,gemini,qwen,nvidia
PROVIDER_ORDER = [p.strip() for p in os.getenv("PROVIDER_ORDER", "gemini,groq,qwen,nvidia").split(",") if p.strip()]

# ── Capital.com ─────────────────────────────────────────────
CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID  = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW  = os.getenv("CAPITAL_PASSWORD")
CAPITAL_URL = os.getenv("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"

logging.info(f"Provider-Reihenfolge: {PROVIDER_ORDER}")
logging.info(f"Gemini Keys: {len(GEMINI_KEYS)} | Groq Keys: {len(GROQ_KEYS)} | Qwen: {'✅' if QWEN_API_KEY else '❌'} | Nvidia: {'✅' if NVIDIA_API_KEY else '❌'} | Ollama: {OLLAMA_MODEL}")

MAX_SPREAD_ENV = os.getenv("MAX_SPREAD", "0.5").strip()
MAX_SPREAD = float(MAX_SPREAD_ENV) if MAX_SPREAD_ENV else None  # None = unlimited

# v15.14: Nacht-Beschraenkung fuer Krypto (23-06 Uhr). Standard: AUS.
# .env: KRYPTO_NACHT_SPERRE=true -> nachts stimmen Cihat (immer) und Taleb
# (am Wochenende) bei Krypto mit NEIN - so wie bis v15.13 fest eingebaut.
KRYPTO_NACHT_SPERRE = os.getenv("KRYPTO_NACHT_SPERRE", "false").strip().lower() in ("true", "1", "ja", "yes", "on")
KRYPTO_NACHT_REGEL_TXT = ("Kripto sadece 3/3 sinyal uyumunda" if KRYPTO_NACHT_SPERRE
                          else "Kripto icin ek kisit YOK")

# KARA KUĞU SCHWELLEN
KARA_KUGU_GEMINI_THRESHOLD  = -8.0
KARA_KUGU_AUTO_THRESHOLD    = -12.0
KARA_KUGU_NOTFALL_THRESHOLD = -18.0

# NEWS & X INTELLIGENCE
NEWS_HISTORY_DAYS     = 14
NEWS_COLLECT_INTERVAL = 3600
_quota_msg_ts = 0.0  # Global (statt function-attribute)

# ============================================================
# ALPHA VANTAGE NEWS SENTIMENT (kostenlos, 500 Calls/Tag)
# Ergaenzt GDELT mit professionellem Sentiment-Score
# Key aus .env: ALPHA_VANTAGE_KEY=
# ============================================================
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")
EIA_API_KEY       = os.getenv("EIA_API_KEY", "")   # Kostenlos: api.eia.gov/opendata registrieren
_av_cache = {}

# ============================================================
# EIA WEEKLY PETROLEUM STATUS (v14.8)
# Jeden Mittwoch 10:30 ET aktualisiert
# Kein Key nötig für DEMO, echter Key kostenlos auf eia.gov
# ============================================================
_eia_cache = {}

def get_eia_petroleum():
    """
    EIA US Rohöl-Lagerbestände (Weekly).
    Signal: Abweichung vom 5-Jahres-Durchschnitt.
    Relevant für: OIL, HEATING_OIL, NATURAL_GAS
    """
    global _eia_cache
    now = datetime.now()
    if _eia_cache.get("ts") and (now - _eia_cache["ts"]).seconds < 3600 * 6:
        return _eia_cache["data"]

    try:
        # EIA v2 API - kostenlos, kein Key für Basisdaten
        url = (
            "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
            "?api_key=" + (EIA_API_KEY or "DEMO_KEY") +
            "&frequency=weekly"
            "&data[0]=value"
            "&facets[series][]=WCRSTUS1"   # Crude Oil Total US
            "&sort[0][column]=period&sort[0][direction]=desc"
            "&offset=0&length=10"
        )
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")

        data    = r.json()
        records = data.get("response", {}).get("data", [])
        if not records:
            raise ValueError("Keine Daten")

        # Neueste Werte
        latest  = float(records[0].get("value", 0) or 0)
        prev_wk = float(records[1].get("value", 0) or 0) if len(records) > 1 else latest
        change  = latest - prev_wk

        # 5-Jahres-Durchschnitt (52 Wochen × 5 = 260 - nehmen wir 8 vorliegende)
        avg_5yr = sum(float(r.get("value", 0) or 0) for r in records) / len(records)
        deviation_pct = (latest - avg_5yr) / avg_5yr * 100 if avg_5yr else 0

        if deviation_pct > 10:
            signal, sent = "BEARISH", -0.6
        elif deviation_pct < -10:
            signal, sent = "BULLISH", 0.6
        elif deviation_pct > 5:
            signal, sent = "SLIGHT_BEARISH", -0.3
        elif deviation_pct < -5:
            signal, sent = "SLIGHT_BULLISH", 0.3
        else:
            signal, sent = "NEUTRAL", 0.0

        result = {
            "latest_mb":      round(latest, 1),
            "weekly_change":  round(change, 1),
            "avg_8wk_mb":     round(avg_5yr, 1),
            "deviation_pct":  round(deviation_pct, 1),
            "signal":         signal,
            "sentiment":      sent,
            "period":         records[0].get("period", "?"),
            "assets":         ["OIL", "HEATING_OIL", "NATURAL_GAS"],
            "summary": (
                f"EIA Lagerbestand {latest:.0f}Mio Barrel | "
                f"Veränderung {change:+.1f}Mio | "
                f"Abweichung 8W-Schnitt {deviation_pct:+.1f}% → {signal}"
            )
        }
        _eia_cache = {"ts": now, "data": result}
        logging.info(f"EIA Petroleum: {result['summary']}")
        return result

    except Exception as e:
        logging.warning(f"EIA Petroleum: {e}")
        return {"signal": "UNKNOWN", "sentiment": 0, "summary": f"EIA Fehler: {e}"}


# ============================================================
# CFTC COT REPORT - Commitment of Traders (v14.8)
# Kein API Key nötig - öffentliches CSV
# Jeden Freitag 15:30 ET
# ============================================================
_cot_cache = {}

def get_cot_positioning(asset="GOLD"):
    """
    CFTC Commitment of Traders - Net-Positioning großer Trader.
    Contrarian-Signal: Extreme Long der Spekulanten = TOP
                       Extreme Short der Spekulanten = BODEN
    Relevant für: GOLD, SILVER, OIL, COPPER
    """
    global _cot_cache
    cache_key = asset
    now = datetime.now()
    if _cot_cache.get(cache_key, {}).get("ts") and \
       (now - _cot_cache[cache_key]["ts"]).seconds < 3600 * 24:
        return _cot_cache[cache_key]["data"]

    # CFTC Futures-only Report (CME Group)
    # Mapping: Asset → CFTC Commodity Code
    cftc_codes = {
        "GOLD":    "088691",   # Gold Futures - COMEX
        "SILVER":  "084691",   # Silver Futures - COMEX
        "OIL":     "067651",   # Crude Oil WTI - NYMEX
        "COPPER":  "085692",   # Copper Futures - COMEX
        "NATURAL_GAS": "023651",  # Natural Gas - NYMEX
        "WHEAT":   "001602",   # Wheat Futures - CBOT
        "CORN":    "002602",   # Corn Futures - CBOT
    }
    code = cftc_codes.get(asset.upper())

    try:
        if code:
            # CFTC Public Reporting API (OData, kein Key)
            url = (
                f"https://publicreporting.cftc.gov/api/odata/v1/"
                f"HistoricalViewOiCombined?"
                f"$filter=cftc_commodity_code eq '{code}'"
                f"&$orderby=report_date_as_yyyy_mm_dd desc"
                f"&$top=4"
                f"&$format=json"
            )
            r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                records = r.json().get("value", [])
            else:
                records = []
        else:
            records = []

        if not records:
            # Fallback: öffentliche TXT-Datei
            url2 = "https://www.cftc.gov/dea/futures/deacmesf.txt"
            r2 = requests.get(url2, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            if r2.status_code == 200:
                # CSV parsen - Header-Zeile überspringen
                lines = [l for l in r2.text.splitlines() if asset.upper()[:4] in l.upper()]
                records = []  # Vereinfacht - OData bevorzugt
            else:
                raise ValueError("CFTC nicht erreichbar")

        if not records:
            return {"signal": "UNKNOWN", "sentiment": 0, "summary": f"COT {asset}: keine Daten"}

        rec = records[0]
        # Felder aus CFTC API
        comm_long  = int(rec.get("comm_positions_long_all",  0) or 0)
        comm_short = int(rec.get("comm_positions_short_all", 0) or 0)
        spec_long  = int(rec.get("noncomm_positions_long_all",  0) or 0)
        spec_short = int(rec.get("noncomm_positions_short_all", 0) or 0)
        date       = rec.get("report_date_as_yyyy_mm_dd", "?")

        comm_net = comm_long - comm_short
        spec_net = spec_long - spec_short

        # Contrarian-Signal
        if spec_net > 200000:
            signal, sent = "CONTRARIAN_BEARISH", -0.7
            reason = f"Spekulanten extrem long ({spec_net:+,}) → Contrarian SELL"
        elif spec_net < -100000:
            signal, sent = "CONTRARIAN_BULLISH", 0.7
            reason = f"Spekulanten extrem short ({spec_net:+,}) → Contrarian BUY"
        elif spec_net > 100000:
            signal, sent = "SLIGHT_BEARISH", -0.3
            reason = f"Spekulanten leicht long ({spec_net:+,})"
        elif spec_net < -50000:
            signal, sent = "SLIGHT_BULLISH", 0.3
            reason = f"Spekulanten leicht short ({spec_net:+,})"
        else:
            signal, sent = "NEUTRAL", 0.0
            reason = f"Spekulanten neutral ({spec_net:+,})"

        result = {
            "asset":       asset,
            "date":        date,
            "comm_net":    comm_net,
            "spec_net":    spec_net,
            "signal":      signal,
            "sentiment":   sent,
            "reason":      reason,
            "summary":     f"COT {asset} ({date}): Komm={comm_net:+,} | Spek={spec_net:+,} → {signal}"
        }
        _cot_cache[cache_key] = {"ts": now, "data": result}
        logging.info(f"COT {asset}: {result['summary']}")
        return result

    except Exception as e:
        logging.warning(f"COT {asset}: {e}")
        return {"signal": "UNKNOWN", "sentiment": 0, "summary": f"COT {asset} Fehler: {e}"}


# ============================================================
# USDA WASDE - World Agricultural Supply and Demand (v14.8)
# Kein API Key - öffentliche USDA PSD API
# Monatlich aktualisiert (2. Dienstag)
# ============================================================
_usda_cache = {}

def get_usda_supply_demand(commodity="Cocoa"):
    """
    USDA PSD Online - Weltweite Angebot/Nachfrage-Bilanz.
    Commodities: Cocoa, Coffee, Sugar, Wheat, Corn, Soybeans
    Signal: Ending Stocks Veränderung YoY
    Relevant für: COCOA, COFFEE, WHEAT, CORN, SUGAR
    """
    global _usda_cache
    now = datetime.now()
    if _usda_cache.get(commodity, {}).get("ts") and \
       (now - _usda_cache[commodity]["ts"]).seconds < 3600 * 12:
        return _usda_cache[commodity]["data"]

    # USDA PSD Commodity Codes
    usda_codes = {
        "Cocoa":    "072300", "Coffee":   "073200", "Sugar":    "066300",
        "Wheat":    "010100", "Corn":     "040200", "Soybeans": "022110",
        "Cotton":   "082130", "Rice":     "027000",
    }
    code = usda_codes.get(commodity, "072300")
    current_year = datetime.now().year

    try:
        url = (
            f"https://apps.fas.usda.gov/psdonline/api/psd/commodity"
            f"?commodityCode={code}"
            f"&marketYear={current_year - 1},{current_year}"
        )
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")

        records = r.json()
        if not records:
            raise ValueError("Keine Daten")

        # Ending Stocks YoY vergleichen
        # Attribut 176 = Ending Stocks (1000 MT)
        ending_stocks = {}
        for rec in records:
            if rec.get("attributeId") == 176:
                yr = rec.get("marketYear", 0)
                val = float(rec.get("value", 0) or 0)
                if yr in (current_year - 1, current_year):
                    ending_stocks[yr] = val

        if len(ending_stocks) >= 2:
            curr = ending_stocks.get(current_year, 0)
            prev = ending_stocks.get(current_year - 1, 0)
            change_pct = (curr - prev) / prev * 100 if prev else 0

            if change_pct < -15:
                signal, sent = "BULLISH", 0.8
            elif change_pct < -5:
                signal, sent = "SLIGHT_BULLISH", 0.4
            elif change_pct > 15:
                signal, sent = "BEARISH", -0.8
            elif change_pct > 5:
                signal, sent = "SLIGHT_BEARISH", -0.4
            else:
                signal, sent = "NEUTRAL", 0.0
        else:
            curr = prev = change_pct = 0
            signal, sent = "UNKNOWN", 0.0

        result = {
            "commodity":    commodity,
            "ending_stocks_current":  curr,
            "ending_stocks_prev":     prev,
            "change_pct":   round(change_pct, 1),
            "signal":       signal,
            "sentiment":    sent,
            "year":         current_year,
            "summary": (
                f"USDA {commodity}: Ending Stocks {curr:.0f}k MT "
                f"(YoY {change_pct:+.1f}%) → {signal}"
            )
        }
        _usda_cache[commodity] = {"ts": now, "data": result}
        logging.info(f"USDA {commodity}: {result['summary']}")
        return result

    except Exception as e:
        logging.warning(f"USDA {commodity}: {e}")
        return {"signal": "UNKNOWN", "sentiment": 0, "summary": f"USDA {commodity} Fehler: {e}"}


# ============================================================
# CO2 TRANSPORT-INDIKATOR - LKW & Güterverkehr (v14.8)
# Eurostat Güterverkehr + Our World in Data CO2
# Transport-CO2 als Wirtschaftsaktivitäts-Indikator
# ============================================================
_transport_cache = {}

def get_transport_activity():
    """
    Transport CO2 / LKW-Güterverkehr als Wirtschaftsindikator.
    
    Datenquellen:
    1. Eurostat: Straßengüterverkehr (Tonnen-km) - EU LKW-Aktivität
    2. Our World in Data: Transport-CO2-Emissionen (jährlich)
    
    Signal-Logik:
    LKW-Verkehr steigt → Wirtschaft boomt → BULLISH Kupfer, Öl
    LKW-Verkehr fällt → Rezession → BEARISH Industriemetalle
    
    Relevant für: OIL, COPPER, NATURAL_GAS, allgemeine Makrolage
    """
    global _transport_cache
    now = datetime.now()
    if _transport_cache.get("ts") and (now - _transport_cache["ts"]).seconds < 3600 * 24:
        return _transport_cache["data"]

    result = {
        "eurostat_yoy_pct": None,
        "owid_transport_co2_mt": None,
        "signal": "UNKNOWN",
        "sentiment": 0.0,
        "summary": "Transport-Daten werden geladen..."
    }

    # --- Quelle 1: Eurostat Straßengüterverkehr ---
    try:
        # Eurostat API - Güterbeförderung auf der Straße (Mio. Tonnen-km)
        # Dataset: road_go_ta_tott (Total road freight transport)
        url_eurostat = (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
            "road_go_ta_tott?format=JSON&lang=EN&geo=EU27_2020"
            "&lastTimePeriod=4"
        )
        r = requests.get(url_eurostat, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            values = list(data.get("value", {}).values())
            if len(values) >= 2:
                curr_val = float(values[-1] or 0)
                prev_val = float(values[-2] or 0)
                yoy = (curr_val - prev_val) / prev_val * 100 if prev_val else 0
                result["eurostat_yoy_pct"] = round(yoy, 1)
                result["eurostat_value_mtkm"] = round(curr_val, 0)
                logging.info(f"Eurostat LKW: {curr_val:.0f} Mio.t-km | YoY {yoy:+.1f}%")
    except Exception as e:
        logging.debug(f"Eurostat Güterverkehr: {e}")

    # --- Quelle 2: Our World in Data - Transport CO2 ---
    try:
        # CSV direkt von GitHub (kein Key)
        url_owid = (
            "https://raw.githubusercontent.com/owid/co2-data/master/"
            "owid-co2-data.csv"
        )
        r2 = requests.get(url_owid, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r2.status_code == 200:
            import io, csv
            reader = csv.DictReader(io.StringIO(r2.text))
            world_data = []
            for row in reader:
                if row.get("country") == "World" and row.get("year", "").isdigit():
                    yr = int(row["year"])
                    transport_co2 = row.get("transport_co2", "") or ""
                    if transport_co2 and int(row["year"]) >= 2015:
                        try:
                            world_data.append((yr, float(transport_co2)))
                        except ValueError:
                            pass
            if len(world_data) >= 2:
                world_data.sort(key=lambda x: x[0])
                last_yr, last_val = world_data[-1]
                prev_yr, prev_val = world_data[-2]
                co2_yoy = (last_val - prev_val) / prev_val * 100 if prev_val else 0
                result["owid_transport_co2_mt"]  = round(last_val, 1)
                result["owid_transport_co2_year"] = last_yr
                result["owid_co2_yoy_pct"]        = round(co2_yoy, 1)
                logging.info(f"OWID Transport CO2 {last_yr}: {last_val:.1f} Gt | YoY {co2_yoy:+.1f}%")
    except Exception as e:
        logging.debug(f"OWID CO2: {e}")

    # --- Signal bestimmen ---
    yoy = result.get("eurostat_yoy_pct") or result.get("owid_co2_yoy_pct") or 0

    if yoy > 8:
        result["signal"]    = "BULLISH"
        result["sentiment"] = 0.6
        note = f"LKW/Transport +{yoy:.1f}% YoY → Wirtschaft expandiert"
    elif yoy > 3:
        result["signal"]    = "SLIGHT_BULLISH"
        result["sentiment"] = 0.3
        note = f"LKW/Transport +{yoy:.1f}% YoY → leichte Expansion"
    elif yoy < -8:
        result["signal"]    = "BEARISH"
        result["sentiment"] = -0.6
        note = f"LKW/Transport {yoy:.1f}% YoY → Rezessionssignal"
    elif yoy < -3:
        result["signal"]    = "SLIGHT_BEARISH"
        result["sentiment"] = -0.3
        note = f"LKW/Transport {yoy:.1f}% YoY → leichte Abschwächung"
    elif yoy == 0:
        result["signal"]    = "UNKNOWN"
        result["sentiment"] = 0.0
        note = "Keine Transportdaten verfügbar"
    else:
        result["signal"]    = "NEUTRAL"
        result["sentiment"] = 0.0
        note = f"LKW/Transport {yoy:+.1f}% YoY → neutral"

    result["assets"] = ["OIL", "COPPER", "NATURAL_GAS"]
    result["summary"] = (
        f"Transport-Aktivität: {note} | "
        f"Eurostat LKW: {result.get('eurostat_yoy_pct', 'N/A')}% YoY | "
        f"OWID CO2: {result.get('owid_transport_co2_mt', 'N/A')} Gt"
    )

    _transport_cache = {"ts": now, "data": result}
    logging.info(f"Transport-Indikator: {result['summary']}")
    return result


_av_cache = {}

def get_alphavantage_news(topics="economy_macro,forex,financial_markets", limit=20):
    """Alpha Vantage News mit fertigem Sentiment. 500 Calls/Tag kostenlos."""
    if not ALPHA_VANTAGE_KEY:
        return []
    cache_key = f"av_{topics}"
    now = time.time()
    if cache_key in _av_cache and now - _av_cache[cache_key]["ts"] < 1800:
        return _av_cache[cache_key]["data"]
    try:
        url = (f"https://www.alphavantage.co/query?"
               f"function=NEWS_SENTIMENT&topics={topics}"
               f"&limit={limit}&apikey={ALPHA_VANTAGE_KEY}")
        r = requests.get(url, timeout=10, headers={"User-Agent": "NexusCEO/1.0"})
        if r.status_code != 200:
            return []
        articles = r.json().get("feed", [])
        _av_cache[cache_key] = {"data": articles, "ts": now}
        logging.info(f"[OK] Alpha Vantage: {len(articles)} makale")
        return articles
    except Exception as e:
        logging.warning(f"[WARN] Alpha Vantage: {e}")
        return []

def collect_alphavantage_news_to_db():
    """Alpha Vantage Nachrichten mit Sentiment in DB. Ergaenzt GDELT."""
    articles = get_alphavantage_news(
        topics="economy_macro,forex,financial_markets,commodity,energy_transportation",
        limit=50
    )
    if not articles:
        return 0
    collected = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cutoff  = (datetime.now() - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")
    label_map = {"Bullish":"BULL","Somewhat-Bullish":"BULL",
                 "Bearish":"BEAR","Somewhat-Bearish":"BEAR","Neutral":"NEUTRAL"}
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        for art in articles:
            title  = (art.get("title") or "")[:300]
            source = (art.get("source") or "alphavantage")[:60]
            pub    = (art.get("time_published") or now_str[:10])[:10]
            if not title or pub < cutoff:
                continue
            av_score = float(art.get("overall_sentiment_score") or 0)
            av_label = art.get("overall_sentiment_label") or "Neutral"
            label = label_map.get(av_label, "NEUTRAL")
            if not conn.execute("SELECT 1 FROM news_cache WHERE title=?", (title,)).fetchone():
                conn.execute(
                    "INSERT INTO news_cache "
                    "(source,asset_tag,title,published_at,fetched_at,sentiment,sentiment_label) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (source, detect_asset_tag(title), title, pub, now_str, av_score, label)
                )
                collected += 1
        conn.commit()
        conn.close()
    if collected:
        logging.info(f"[OK] Alpha Vantage DB: {collected} haber eklendi")
    return collected



# ============================================================
# KONFIGURIERBARE KONSTANTEN (vorher hardcoded Magic Numbers)
# Alle via .env überschreibbar
# ============================================================
TQS_MIN_SCORE        = int(os.getenv("TQS_MIN_SCORE",        "68"))   # TQS Gate Schwelle
CORR_RISK_MAX        = float(os.getenv("CORR_RISK_MAX",      "500"))  # Max Korrelations-Risiko
DAILY_TARGET_EUR     = float(os.getenv("DAILY_TARGET_EUR",   "50"))   # Tagesziel EUR
MAX_DAILY_LOSS_EUR   = float(os.getenv("MAX_DAILY_LOSS_EUR", "-100")) # Max Tagesverlust EUR
ATR_MULTIPLIER       = float(os.getenv("ATR_MULTIPLIER",     "2.0"))  # ATR SL Multiplikator
META_LEARN_MIN_TRADES= int(os.getenv("META_LEARN_MIN_TRADES","15"))   # Min Trades für Meta-Learn
META_LEARN_BLOCK_WR  = float(os.getenv("META_LEARN_BLOCK_WR","0.33")) # Win-Rate unter der geblockt wird
HEARTBEAT_INTERVAL   = int(os.getenv("HEARTBEAT_INTERVAL",  "6"))     # Heartbeat alle N Zyklen
SCAN_INTERVAL_SEC    = int(os.getenv("SCAN_INTERVAL_SEC", "21600"))  # 6h (v15.0 Macro-Scan)
NEXUS_VERSION        = "v16.0"                                    # steht in der Startmeldung
MAX_POSITIONEN       = int(os.getenv("MAX_POSITIONEN", "5"))          # v15.16: max. offene Positionen (vorher fest 5)
MAX_VERLUSTE_PRO_TAG = int(os.getenv("MAX_VERLUSTE_PRO_TAG", "3"))    # v15.16: so viele Verluste pro Symbol/Tag, dann gesperrt (0 = aus; vorher fest 3)
SL_ATR_MULT          = float(os.getenv("SL_ATR_MULT", "1.0"))         # v15.17: Stop mind. so viele Tagesspannen (Tages-ATR) vom Kurs; 0 = aus (fest 1.5% wie vorher)
SL_MAX_PCT           = float(os.getenv("SL_MAX_PCT", "6.0"))          # v15.17: Obergrenze fuer diesen Mindestabstand in % (bleibt unter Kara Kugu -8%)
STOP_LEITER          = os.getenv("STOP_LEITER", "true").strip().lower() not in ("false", "0", "nein", "no", "aus", "off")  # v15.24: Stop nach jeder Mirror-TP-Stufe nachziehen
try:
    MAX_JE_GRUPPE    = int(float(os.getenv("MAX_JE_GRUPPE", "2") or 0))  # v15.24: max. offene Maerkte je Gruppe (0 = aus)
except ValueError:
    MAX_JE_GRUPPE    = 2


def _env_zahl(name, std, typ=float):
    """Zahl aus der .env; leer, Kommentar oder Unsinn -> Standardwert."""
    try:
        return typ(float(os.getenv(name, str(std)).split("#")[0].strip() or std))
    except ValueError:
        return typ(std)


# v16.0 GREMIUM: 11 Mentoren stimmen unabhaengig ab (nexus_gremium.py)
GREMIUM_MODUS          = (os.getenv("GREMIUM_MODUS", "ki").split("#")[0].strip().lower() or "ki")  # ki = neues Gremium, regeln = alter Ablauf (v15)
GREMIUM_MEHRHEIT       = _env_zahl("GREMIUM_MEHRHEIT", 6)          # gewichtete Stimmen von 11 fuer einen Beschluss
GREMIUM_MEHRHEIT_KRYPTO = _env_zahl("GREMIUM_MEHRHEIT_KRYPTO", 5)  # Krypto am Wochenende
GREMIUM_MIN_ANTWORTEN  = _env_zahl("GREMIUM_MIN_ANTWORTEN", 8, int)   # weniger gueltige Antworten = nicht beschlussfaehig
GREMIUM_MAX_KANDIDATEN = _env_zahl("GREMIUM_MAX_KANDIDATEN", 2, int)  # so viele Maerkte beraet das Gremium je Scan hoechstens
GREMIUM_GUELTIG_STD    = _env_zahl("GREMIUM_GUELTIG_STD", 4)       # ein Beschluss gilt so viele Stunden (kein neues Beraten desselben Markts)
GREMIUM_PARALLEL       = _env_zahl("GREMIUM_PARALLEL", 2, int)     # gleichzeitige KI-Aufrufe
GREMIUM_BEWERTUNG_STD  = _env_zahl("GREMIUM_BEWERTUNG_STD", 24)    # nach so vielen Stunden wird jede Stimme am Kurs gemessen
GREMIUM_GEWICHTUNG     = os.getenv("GREMIUM_GEWICHTUNG", "true").split("#")[0].strip().lower() not in ("false", "0", "nein", "no", "aus", "off")
WIEDEREINSTIEG_SPERRE_STD = float(os.getenv("WIEDEREINSTIEG_SPERRE_STD", "6"))  # v15.18: so viele Stunden nach einer Schliessung kein neuer Einstieg in dasselbe Symbol/dieselbe Richtung (0 = aus)
SCAN_MELDUNGEN       = os.getenv("SCAN_MELDUNGEN", "neu").strip().lower()  # v15.18: "neu" = Scan ohne Trade nur melden, wenn sich etwas aendert; "alle" = wie vorher


# ============================================================
# CAPITAL.COM API — RETRY MIT EXPONENTIAL BACKOFF
# Alle 4 KIs: kein Retry bei 429 → Bot stoppt
# ============================================================
def _api_request(method, url, headers=None, json_data=None, timeout=10, max_retries=3):
    """
    Einheitliche API-Request Funktion mit Retry.
    429 → Exponential Backoff.
    503 → kurz warten, neu versuchen.
    """
    for attempt in range(max_retries):
        try:
            r = requests.request(
                method, url, headers=headers,
                json=json_data, timeout=timeout
            )
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                logging.warning(f"Capital.com 429 Rate-Limit → {wait}s warten (Versuch {attempt+1}/{max_retries})")
                Health.report("capital_api", False, f"429 Rate-Limit")
                time.sleep(wait)
                continue
            if r.status_code in (503, 502, 504):
                wait = 10 * (attempt + 1)
                logging.warning(f"Capital.com {r.status_code} → {wait}s warten")
                time.sleep(wait)
                continue
            if r.status_code == 401:
                logging.warning("Capital.com 401 → Session erneuern")
                Health.report("capital_api", False, "401 Unauthorized")
                return r  # Session muss neu aufgebaut werden
            return r  # Andere Status-Codes direkt zurückgeben
        except requests.exceptions.Timeout:
            logging.warning(f"Capital.com Timeout (Versuch {attempt+1}/{max_retries})")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Capital.com Request Fehler: {e}")
            if attempt == max_retries - 1:
                Health.report("capital_api", False, str(e))
                raise
            time.sleep(5)
    return None



# ╔══════════════════════════════════════════════════════════════════════╗
# ║  NEXUS NATURE v14.0 — Neue Systeme                                  ║
# ║  1. TQS Gate (Trade Quality Score)                                  ║
# ║  2. ATR Stop Loss (dynamisch)                                        ║
# ║  3. FRED API + DXY Live                                             ║
# ║  4. Korrelationsmatrix                                               ║
# ║  5. Groq Pre-Filter                                                 ║
# ║  6. Enhanced Macro Signal                                            ║
# ║  7. Daily Drawdown Manager                                          ║
# ║  8. Meta Learning (wöchentlich)                                     ║
# ║  9. Orchestrator Health Journal                                      ║
# ╚══════════════════════════════════════════════════════════════════════╝

import threading as _orch_threading

# ── 1. DXY LIVE ───────────────────────────────────────────────────────
_dxy_cache = {"val": None, "ts": 0}

def get_dxy_live():
    """DXY von Yahoo Finance. Gecacht 15 Min. Kein halluzinierter Wert."""
    now = time.time()
    if _dxy_cache["val"] and now - _dxy_cache["ts"] < 900:
        return _dxy_cache["val"]
    for sym in ["DX-Y.NYB", "UUP"]:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d",
                timeout=8, headers={"User-Agent": "Mozilla/5.0"}
            )
            if r.status_code != 200: continue
            meta = r.json()["chart"]["result"][0]["meta"]
            p, prev = meta.get("regularMarketPrice"), meta.get("previousClose")
            if not p: continue
            chg = f"{(p-prev)/prev*100:+.2f}%" if prev else ""
            val = f"{p:.2f} {chg}"
            _dxy_cache.update({"val": val, "ts": now})
            return val
        except: pass
    return _dxy_cache.get("val") or "N/A"

# ── 2. FRED API ────────────────────────────────────────────────────────
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE    = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES  = {
    "FEDFUNDS":         ("Fed Funds Rate",     "%"),
    "T10Y2Y":           ("Yield Spread 10Y-2Y","%"),
    "DGS10":            ("10Y Treasury",       "%"),
    "BAMLH0A0HYM2":     ("High Yield Spread",  "%"),
    "DTWEXBGS":         ("USD Broad Index",    ""),
    "GOLDAMGBD228NLBM": ("Gold London Fix",    "USD"),
    "DCOILWTICO":       ("WTI Öl",             "USD"),
    "CPIAUCSL":         ("CPI USA",            "idx"),
    "UNRATE":           ("Unemployment USA",   "%"),
}
_fred_cache = {}
_fred_ts    = {}

def get_fred_series(sid):
    if not FRED_API_KEY: return None, None
    if sid in _fred_cache and time.time() - _fred_ts.get(sid,0) < 21600:
        return _fred_cache[sid]
    try:
        r = requests.get(f"{FRED_BASE}?series_id={sid}&api_key={FRED_API_KEY}&limit=2&sort_order=desc&file_type=json", timeout=10)
        if r.status_code != 200: return None, None
        for o in r.json().get("observations",[]):
            if o.get("value") not in (".",""): 
                v = float(o["value"])
                _fred_cache[sid] = (v, o["date"])
                _fred_ts[sid] = time.time()
                return v, o["date"]
    except: pass
    return None, None

def get_fred_macro_signal():
    if not FRED_API_KEY:
        return {"status":"NO_KEY","signal":"NEUTRAL","key_data":[],"warnings":[],"dxy_fred":"N/A"}
    results, warnings, signals = {}, [], []
    for sid,(name,unit) in FRED_SERIES.items():
        v, d = get_fred_series(sid)
        if v is not None: results[sid] = {"name":name,"value":v,"unit":unit,"date":d}
    if "T10Y2Y" in results and results["T10Y2Y"]["value"] < 0:
        warnings.append(f"⚠️ Invertierte Zinskurve {results['T10Y2Y']['value']:.2f}% → Rezession")
        signals.append("BEARISH")
    if "FEDFUNDS" in results and results["FEDFUNDS"]["value"] > 5:
        signals.append("BEARISH_RISK")
    if "BAMLH0A0HYM2" in results and results["BAMLH0A0HYM2"]["value"] > 6:
        warnings.append(f"🚨 HY-Spread {results['BAMLH0A0HYM2']['value']:.2f}%")
        signals.append("BEARISH")
    bc = sum(1 for s in signals if "BEAR" in s)
    overall = "BEARISH" if bc > 0 else "NEUTRAL"
    key_data = [f"{r['name']}: {r['value']:.2f}{r['unit']} ({r['date']})"
                for sid,r in results.items()
                if sid in ["FEDFUNDS","T10Y2Y","DTWEXBGS","GOLDAMGBD228NLBM","BAMLH0A0HYM2"]]
    return {"status":"OK","signal":overall,"warnings":warnings,
            "key_data":key_data,"dxy_fred":results.get("DTWEXBGS",{}).get("value","N/A")}

# ── 3. TQS GATE ────────────────────────────────────────────────────────
def compute_tqs(epic, sinyal, guc, fear_greed_val, spread, regime):
    """Trade Quality Score 0-100. Unter 68 → kein AI-Call, kein Trade."""
    if sinyal not in ("BUY","SELL"): return 0, "NOTR Signal"
    score = 0
    d = []
    # Technisch (35 Pkt)
    tech = {1:15, 2:25, 3:35}.get(int(guc or 0), 0)
    score += tech; d.append(f"Teknik:{tech}/35")
    # Regime (25 Pkt)
    base = {"RISK_ON":25,"NEUTRAL":18,"RISK_OFF":12,"RISK_OFF_FEAR":8,
            "RISK_OFF_SPREAD":5,"RISK_OFF_EXTREME":3}.get(regime, 15)
    fg = fear_greed_val or 50
    if 40<=fg<=60: base = min(25, base+3)
    elif fg < 20:  base = max(0, base-5)
    elif fg > 80:  base = max(0, base-3)
    score += base; d.append(f"Regime:{base}/25")
    # Spread (20 Pkt)
    sp = 20 if spread<=0.05 else (16 if spread<=0.15 else (10 if spread<=0.3 else (5 if spread<=0.5 else 0)))
    score += sp; d.append(f"Spread:{sp}/20")
    # Tageszeit (20 Pkt)
    h = datetime.now().hour
    tp = 20 if (is_crypto(epic) if callable(globals().get("is_crypto")) else False)          else (20 if 8<=h<=17 else (12 if 6<=h<=20 else 5))
    score += tp; d.append(f"Zeit:{tp}/20")
    return min(100, score), " | ".join(d)

def tqs_gate(epic, sinyal, guc, fear_greed_val, spread, regime, min_score=None):
    if min_score is None: min_score = TQS_MIN_SCORE
    score, details = compute_tqs(epic, sinyal, guc, fear_greed_val, spread, regime)
    passed = score >= min_score
    logging.info(f"TQS {epic}: {score}/100 ({'✅' if passed else '❌'}) | {details}")
    return passed, score, details

# ── 4. ATR STOP LOSS ───────────────────────────────────────────────────
def get_atr_stop_loss(epic, entry_price, direction, atr_mult=2.0):
    """Dynamischer SL basierend auf ATR. Fallback: 1.5% SL."""
    try:
        h = capital_session.get_headers() if hasattr(capital_session,"get_headers") else None
        if not h: raise ValueError("Keine API")
        r = requests.get(f"{CAPITAL_URL}/prices/{epic}",
                         headers=h, params={"resolution":"HOUR","max":20}, timeout=10)  # v15.13: "HOUR_1" gibt es nicht
        if r.status_code != 200: raise ValueError(f"API {r.status_code}")
        prices = r.json().get("prices",[])
        if len(prices) < 5: raise ValueError("Zu wenige Preise")
        trs = []
        for i in range(1,len(prices)):
            hi = float(prices[i].get("highPrice",{}).get("bid",0))
            lo = float(prices[i].get("lowPrice", {}).get("bid",0))
            pc = float(prices[i-1].get("closePrice",{}).get("bid",hi))
            if hi>0 and lo>0:
                trs.append(max(hi-lo, abs(hi-pc), abs(lo-pc)))
        if not trs: raise ValueError("TR leer")
        atr = sum(trs[-14:]) / min(14, len(trs))
        dist = max(entry_price*0.003, min(entry_price*0.08, atr*atr_mult))
        sl = (entry_price - dist) if direction=="BUY" else (entry_price + dist)
        return round(sl,5), round(atr,6), f"ATR={atr:.5f}×{atr_mult}={dist:.5f} ({dist/entry_price*100:.2f}%)"
    except Exception as e:
        dist = entry_price * 0.015
        sl = (entry_price-dist) if direction=="BUY" else (entry_price+dist)
        return round(sl,5), 0.0, f"Fallback 1.5% ({e})"


# ── 4b. GUNLUK ATR (Tages-Band TP Hinweis-System) ──────────────────────
def get_daily_atr(epic, period=14):
    """
    Gunluk ATR (Average True Range) - DAY cozunurlugunde.
    Sadece Daily-TP-Hatirlatma sistemi icin - normal SL/TP mantigina
    (get_atr_stop_loss, HOUR_1) dokunmaz, tamamen ayri/bagimsiz.

    Doner: (atr_fiyat, atr_pct, hata_str)
    """
    try:
        h = capital_session.get_headers() if hasattr(capital_session, "get_headers") else None
        if not h: raise ValueError("Keine API")
        r = requests.get(f"{CAPITAL_URL}/prices/{epic}",
                         headers=h, params={"resolution": "DAY", "max": period + 5}, timeout=10)
        if r.status_code != 200: raise ValueError(f"API {r.status_code}")
        prices = r.json().get("prices", [])
        if len(prices) < 3: raise ValueError("Zu wenige Tages-Kerzen")

        trs = []
        for i in range(1, len(prices)):
            hi = float(prices[i].get("highPrice", {}).get("bid", 0))
            lo = float(prices[i].get("lowPrice", {}).get("bid", 0))
            pc = float(prices[i-1].get("closePrice", {}).get("bid", hi))
            if hi > 0 and lo > 0:
                trs.append(max(hi - lo, abs(hi - pc), abs(lo - pc)))
        if not trs: raise ValueError("TR listesi bos")

        atr_fiyat = sum(trs[-period:]) / min(period, len(trs))
        son_kapanis = float(prices[-1].get("closePrice", {}).get("bid", 0)) or 1.0
        atr_pct = atr_fiyat / son_kapanis * 100
        return round(atr_fiyat, 6), round(atr_pct, 3), ""
    except Exception as e:
        return 0.0, 0.0, str(e)


def get_atr_tp_sl(epic, current_price, direction, period=14, tp_oran=0.90, sl_oran=0.40):
    """
    ATR-bazli GUVENLIK-AGI TP/SL hesabi (v15.4 Smart-Exit fikri, dogru
    implementasyon - onceki versiyonda bu fonksiyon HICBIR YERDE tanimli
    degildi, cagrilinca sessizce (try/except) hep basarisiz oluyordu).

    Sadece FALLBACK olarak kullanilir: Gemini'nin kendi TP/SL degeri
    eksik veya anlamsizsa (fiyata cok yakinsa) burada hesaplanan
    ATR-bazli deger devreye girer. Gemini duzgun bir TP/SL verdiyse
    bu fonksiyonun sonucu KULLANILMAZ.

    TP = current_price +/- (Gunluk ATR * %90)
    SL = current_price -/+ (Gunluk ATR * %40)
    Risk/Reward = 90/40 = 1:2.25

    Doner: (tp_fiyat, sl_fiyat, gunluk_atr_fiyat)
    """
    atr_fiyat, _, hata = get_daily_atr(epic, period)

    if atr_fiyat <= 0:
        # ATR alinamadi - guvenli sabit yuzde fallback (get_atr_stop_loss ile tutarli)
        atr_fiyat = current_price * 0.015 / sl_oran  # ~%1.5 SL mesafesine denk gelecek sekilde

    tp_mesafe = atr_fiyat * tp_oran
    sl_mesafe = atr_fiyat * sl_oran

    if direction == "BUY":
        tp = current_price + tp_mesafe
        sl = current_price - sl_mesafe
    else:  # SELL
        tp = current_price - tp_mesafe
        sl = current_price + sl_mesafe

    return round(tp, 5), round(sl, 5), round(atr_fiyat, 6)


# ── 4c. RAUSCH-SCHUTZ (v15.17): Stop Loss ausserhalb der normalen Tagesspanne ──
def sl_min_distance(epic, price, min_stop_pct=0.015):
    """
    Mindestabstand des Stop Loss vom Kurs (in Preis-Einheiten).

    Die Tagesspanne (Tages-ATR) ist der Weg, den das Asset an einem normalen Tag
    zuruecklegt. Ein Stop, der naeher am Kurs liegt als diese Spanne, wird schon
    vom normalen Auf und Ab getroffen. Deshalb:
        Abstand = Tages-ATR x SL_ATR_MULT (.env, Standard 1.0)
        mindestens  der bisherige feste Abstand (min_stop_pct, Standard 1.5 %)
        hoechstens  SL_MAX_PCT (.env, Standard 6 %)
    SL_ATR_MULT=0 oder Tages-ATR nicht abrufbar -> fester Abstand wie vor v15.17.

    Rueckgabe: (abstand, text)
    """
    fest = price * min_stop_pct
    if SL_ATR_MULT <= 0:
        return fest, f"fester Mindestabstand {min_stop_pct * 100:.2f}%"
    atr, _atr_pct, err = get_daily_atr(epic, DAILY_TP_ATR_PERIOD)
    if atr <= 0:
        return fest, f"Tagesspanne nicht abrufbar ({err}) - fester Mindestabstand {min_stop_pct * 100:.2f}%"
    dist = max(fest, atr * SL_ATR_MULT)
    deckel = max(fest, price * SL_MAX_PCT / 100.0)
    if dist > deckel:
        return deckel, (f"{SL_ATR_MULT:g} × Tagesspanne {atr:g} wäre {dist / price * 100:.2f}% - "
                        f"begrenzt auf {deckel / price * 100:.2f}% (SL_MAX_PCT)")
    if dist <= fest:
        return fest, f"fester Mindestabstand {min_stop_pct * 100:.2f}% (Tagesspanne {atr:g} ist kleiner)"
    return dist, f"{SL_ATR_MULT:g} × Tagesspanne {atr:g} = {dist / price * 100:.2f}%"


def sl_auf_mindestabstand(side, sl, price, dist):
    """Schiebt einen zu nahen (oder auf der falschen Seite liegenden) Stop auf den
    Mindestabstand. Ein weiter entfernter Stop bleibt, wie er ist.
    Rueckgabe: (sl, geaendert)"""
    if str(side).upper() == "BUY":
        grenze = round(price - dist, 5)
        zu_nah = sl > grenze
    else:
        grenze = round(price + dist, 5)
        zu_nah = sl < grenze
    if zu_nah:
        return grenze, True
    return sl, False


def sl_weiten_plan(h):
    """Fuer /sl_weiten: Welche Stops OFFENER Positionen liegen im Tagesrauschen?
    Gemessen wird vom Einstiegskurs. Angefasst werden nur Stops auf der Verlustseite,
    und nur in Richtung 'weiter weg'. Rueckgabe: Liste von Dicts
    {p, name, richtung, alt, neu (None = bleibt), text}."""
    plan = []
    for p in get_positions(h) or []:
        pos, mkt = p.get("position", {}), p.get("market", {})
        epic, richtung = mkt.get("epic", ""), pos.get("direction", "")
        name = mkt.get("instrumentName") or epic
        try:
            entry = float(pos.get("level", 0) or 0)
            alt = float(pos.get("stopLevel", 0) or 0)
            size = float(pos.get("size", 0) or 0)
        except (TypeError, ValueError):
            continue
        eintrag = {"p": p, "name": name, "richtung": richtung, "alt": alt, "neu": None, "text": ""}
        plan.append(eintrag)
        if entry <= 0 or richtung not in ("BUY", "SELL"):
            eintrag["text"] = "Einstieg/Richtung nicht lesbar - bleibt"
            continue
        if alt <= 0:
            eintrag["text"] = "kein Stop gesetzt - bleibt unverändert"
            continue
        if (richtung == "BUY" and alt >= entry) or (richtung == "SELL" and alt <= entry):
            eintrag["text"] = f"Stop {alt:g} liegt am Einstieg oder im Gewinn - bleibt"
            continue
        sym = next((s for s, c in MARKET_CONFIG.items() if c.get("epic") == epic), None)
        min_pct = (MARKET_CONFIG.get(sym) or {}).get("min_stop_pct", 0.015) if sym else 0.015
        dist, info = sl_min_distance(epic, entry, min_pct)
        neu, _ = sl_auf_mindestabstand(richtung, alt, entry, dist)
        if abs(neu - alt) < 1e-9:
            eintrag["text"] = f"Stop {alt:g} ({abs(entry - alt) / entry * 100:.2f}%) ist weit genug - bleibt"
            continue
        eintrag["neu"] = neu
        eintrag["text"] = (f"Stop {alt:g} ({abs(entry - alt) / entry * 100:.2f}%) → {neu:g} "
                           f"({abs(entry - neu) / entry * 100:.2f}%) | {info} | "
                           f"Verlust am neuen Stop ca. {size * abs(entry - neu):.2f} (Währung des Instruments)")
    return plan


# ── 5. KORRELATIONSMATRIX ─────────────────────────────────────────────
CORRELATION_MATRIX = {
    ("BTC_USD","ETH_USD"):0.87, ("BTC_USD","SOL_USD"):0.79,
    ("BTC_USD","XRP_USD"):0.65, ("ETH_USD","SOL_USD"):0.82,
    ("OIL_CRUDE","OIL_BRENT"): 0.97,  # FIX: nie beide gleichzeitig!
    ("GOLD","SILVER"):0.74,     ("OIL_BRENT","NATURAL_GAS"):0.52,
    ("EURUSD","GBPUSD"):0.68,   ("EURUSD","USDJPY"):-0.61,
}

def check_portfolio_correlation(new_sym, positions):
    """Verhindert mehrere hochkorrelierte Positionen gleichzeitig."""
    risk = 0.0
    for pos in positions:
        epic = pos.get("market",{}).get("epic","")
        sym  = next((s for s,c in MARKET_CONFIG.items() if c.get("epic")==epic), None)
        if not sym: continue
        key  = tuple(sorted([new_sym, sym]))
        corr = CORRELATION_MATRIX.get(key, 0.25)
        size = float(pos.get("position",{}).get("size", 0))
        risk += corr * size
    if risk > CORR_RISK_MAX:
        return False, f"Korelasyon riski yüksek: {risk:.1f}"
    return True, f"OK (risk={risk:.1f})"

# ── 6. ENHANCED MACRO SIGNAL ──────────────────────────────────────────
def get_enhanced_macro_signal(fear_greed_val, vol_regime, cargo_data=None, bdi_data=None, eu_gas_data=None):
    """Alle Makrodaten zu einem Score 0-100 zusammenfassen."""
    fred  = get_fred_macro_signal()
    score = 50
    details = []
    if fred.get("signal") == "BEARISH":
        score -= 15; details.append("FRED BEARISH -15")
    elif fred.get("signal") == "BULLISH":
        score += 10; details.append("FRED BULLISH +10")
    fg = fear_greed_val or 50
    if fg < 25:
        score += 8; details.append(f"Extreme Fear +8 (fırsat)")
    elif fg > 75:
        score -= 5; details.append(f"Extreme Greed -5")
    if vol_regime == "HIGH":
        score -= 10; details.append("Yüksek Volatilite -10")
    if cargo_data and cargo_data.get("trend") == "RISK_OFF":
        score -= 6; details.append("Cargo Risk-Off -6")
    if bdi_data and bdi_data.get("value",1500) < 800:
        score -= 5; details.append("BDI düşük -5")
    if eu_gas_data and eu_gas_data.get("pct",50) < 35:
        score += 5; details.append("EU Gas düşük +5 (enerji)")
    final = max(0, min(100, score))
    return {
        "score": final,
        "signal": "BULLISH" if final>60 else ("BEARISH" if final<40 else "NEUTRAL"),
        "details": details,
        "fred_warnings": fred.get("warnings",[]),
        "fred_key_data": fred.get("key_data",[]),
    }

# ── 7. DAILY DRAWDOWN MANAGER ─────────────────────────────────────────
DAILY_TARGET_EUR = float(os.getenv("DAILY_TARGET_EUR", "50"))
MAX_DAILY_LOSS_EUR = float(os.getenv("MAX_DAILY_LOSS_EUR", "-100"))

def check_daily_limits():
    """Stoppt Trading wenn Tagesziel erreicht oder Max-Verlust überschritten."""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("""
                SELECT COALESCE(SUM(pnl_eur),0) FROM trades
                WHERE status='CLOSED' AND DATE(exit_time)=DATE('now')
            """).fetchone()
            conn.close()
            today_pnl = row[0] if row and row[0] else 0.0
        if today_pnl >= DAILY_TARGET_EUR:
            return "TARGET_REACHED", f"Günlük hedef: +{today_pnl:.2f}€ ✅"
        if today_pnl <= MAX_DAILY_LOSS_EUR:
            return "MAX_LOSS", f"Maks kayıp: {today_pnl:.2f}€ 🛑"
        return "NORMAL", f"Bugün PnL: {today_pnl:+.2f}€"
    except Exception as e:
        return "NORMAL", f"Limit check hata: {e}"

# ── 8. META LEARNING (wöchentlich) ────────────────────────────────────
def meta_learn_weekly():
    """Analysiert Trade-History → blockt schlechte Muster automatisch."""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            trades = conn.execute("""
                SELECT symbol, direction,
                       strftime('%w', entry_time) as weekday,
                       strftime('%H', entry_time) as hour,
                       macro_regime, pnl_eur
                FROM trades
                WHERE status='CLOSED'
                AND entry_time > datetime('now','-30 days')
            """).fetchall()
            conn.close()
        if len(trades) < 15:
            return f"Meta-Learn: Yeterli veri yok ({len(trades)}/15)"
        patterns = {}
        for sym,direction,wd,hr,regime,pnl in trades:
            key = f"{sym}_{direction}_{wd}_{regime}"
            if key not in patterns: patterns[key] = []
            patterns[key].append(1 if (pnl or 0)>0 else 0)
        report = []
        for key,wins in patterns.items():
            if len(wins) >= META_LEARN_MIN_TRADES // 3:
                wr = sum(wins)/len(wins)
                if wr < META_LEARN_BLOCK_WR:
                    report.append(f"META-BLOCK: {key}: %{wr*100:.0f} win_rate")
                    logging.warning(f"Meta-Learn: {key} win_rate={wr:.0%} GEBLOCKT")
                    # apply_hard_block aufrufen wenn verfügbar
                    sym_key = key.split("_")[0] if "_" in key else key
                    if callable(globals().get("apply_hard_block")):
                        try:
                            apply_hard_block(sym_key, "ALL",
                                f"Meta-Lernen: {key} win_rate={wr:.0%} unter 33%")
                        except Exception as _mle:
                            logging.debug(f"Meta-Block {sym_key}: {_mle}")
                elif wr > 0.70:
                    report.append(f"✅ {key}: %{wr*100:.0f} → GÜÇLÜ")
        summary = f"Meta-Learn: {len(patterns)} pattern, {len(report)} önemli"
        try: bot.send_message(MY_CHAT_ID, "🧠 " + summary + "\n" + "\n".join(report[:10]))
        except: pass
        return summary
    except Exception as e:
        return f"Meta-Learn hata: {e}"

# ── 9. ORCHESTRATOR HEALTH JOURNAL ────────────────────────────────────
class _ModuleHealth:
    """Überwacht Modul-Gesundheit und loggt ins Terminal + Telegram."""
    _status = {}

    @classmethod
    def report(cls, module, ok, msg=""):
        prev = cls._status.get(module, True)
        cls._status[module] = ok
        if not ok and prev:  # Nur beim ersten Fehler melden
            logging.error(f"[ERR] [{module}] FEHLER: {msg}")
            try: bot.send_message(MY_CHAT_ID,
                f"🚨 NEXUS JOURNAL\n❌ Modul: {module}\nFehler: {msg}\n"
                f"Zeit: {datetime.now().strftime('%d.%m %H:%M')}")
            except: pass
        elif ok and not prev:  # Wiederherstellung melden
            logging.info(f"[OK] [{module}] wiederhergestellt: {msg}")
            try: bot.send_message(MY_CHAT_ID,
                f"✅ NEXUS JOURNAL\n{module} wiederhergestellt")
            except: pass

    @classmethod
    def is_healthy(cls, module):
        return cls._status.get(module, True)

Health = _ModuleHealth



# ============================================================
# X (TWITTER) API FREE TIER — 0€, kein Billing nötig
# 10.000 Tweets/Monat kostenlos (developer.twitter.com)
# Safety Lock: bei Limit → nur X stoppt, RSS + Bot laufen weiter
# ============================================================
X_API_BEARER         = os.getenv("X_API_BEARER", "")
X_MAX_MONTHLY_TWEETS = 9500   # Limit 10.000, Puffer 500
X_MAX_15MIN_REQUESTS = 200    # Limit 300, Puffer 100
X_TWEETS_PER_USER    = 4      # Max Tweets pro Account pro Runde
X_LIMIT_FILE         = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x_api_limits.json")
X_LIMIT_NOTIFIED     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x_limit_notified.json")

def _load_x_limits():
    try:
        if os.path.exists(X_LIMIT_FILE):
            with open(X_LIMIT_FILE, "r") as f:
                data = json.load(f)
            cur_month = datetime.now().strftime("%Y-%m")
            if data.get("month") != cur_month:
                data = {"month": cur_month, "monthly_tweets": 0, "requests_15min": 0, "last_reset": time.time()}
            if time.time() - data.get("last_reset", 0) > 900:
                data["requests_15min"] = 0
                data["last_reset"] = time.time()
            return data
    except: pass
    return {"month": datetime.now().strftime("%Y-%m"), "monthly_tweets": 0, "requests_15min": 0, "last_reset": time.time()}

def _save_x_limits(data):
    try:
        with open(X_LIMIT_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.warning(f"X Limit kaydetme: {e}")

def check_x_limits():
    lim = _load_x_limits()
    if lim["monthly_tweets"] >= X_MAX_MONTHLY_TWEETS:
        return True, f"Aylık limit doldu ({lim['monthly_tweets']}/{X_MAX_MONTHLY_TWEETS})"
    if lim["requests_15min"] >= X_MAX_15MIN_REQUESTS:
        return True, f"15 dakika limiti doldu ({lim['requests_15min']}/{X_MAX_15MIN_REQUESTS})"
    return False, "OK"

def _notify_x_limit_once(reason):
    try:
        notified = {}
        if os.path.exists(X_LIMIT_NOTIFIED):
            with open(X_LIMIT_NOTIFIED, "r") as f:
                notified = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        key = "monthly" if "Aylık" in reason else "rate"
        if notified.get(key) == today:
            return
        bot.send_message(MY_CHAT_ID,
            f"🔒 X API Güvenlik Kilidi: {reason}\n✅ RSS ve bot çalışmaya devam ediyor.")
        notified[key] = today
        with open(X_LIMIT_NOTIFIED, "w") as f:
            json.dump(notified, f)
    except: pass

def fetch_x_user_tweets_safe(username):
    """X API v2 Free Tier ile tweet çek. Limit dolunca boş döner."""
    if not X_API_BEARER:
        return []
    blocked, reason = check_x_limits()
    if blocked:
        _notify_x_limit_once(reason)
        return []
    headers = {"Authorization": f"Bearer {X_API_BEARER}", "User-Agent": "NexusCEO/1.0"}
    try:
        r = requests.get(
            f"https://api.twitter.com/2/users/by/username/{username.lstrip('@')}",
            headers=headers, timeout=10
        )
        if r.status_code != 200:
            return []
        user_id = r.json()["data"]["id"]
        r2 = requests.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers=headers, timeout=10,
            params={
                "max_results": X_TWEETS_PER_USER,
                "tweet.fields": "created_at,public_metrics",
                "exclude": "retweets,replies"
            }
        )
        if r2.status_code != 200:
            return []
        tweets = r2.json().get("data", [])
        lim = _load_x_limits()
        lim["requests_15min"] += 2
        lim["monthly_tweets"] += len(tweets)
        _save_x_limits(lim)
        return tweets
    except Exception as e:
        logging.warning(f"X API {username}: {e}")
        return []

def collect_x_free_tier(sources_data):
    """
    Tüm X hesaplarından tweet topla (X API Free Tier, 0€).
    Limit dolunca SADECE bu fonksiyon durur — RSS ve bot ETKİLENMEZ.
    """
    if not X_API_BEARER:
        return 0
    blocked, reason = check_x_limits()
    if blocked:
        _notify_x_limit_once(reason)
        return 0
    x_accounts = sources_data.get("x_accounts", [])
    collected  = 0
    now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cutoff     = (datetime.now() - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")
    for x_acc in x_accounts:
        blocked, reason = check_x_limits()
        if blocked:
            _notify_x_limit_once(reason)
            break
        handle = x_acc["handle"].lstrip("@")
        tweets = fetch_x_user_tweets_safe(handle)
        for tw in tweets:
            if tw.get("created_at", "")[:10] < cutoff:
                continue
            sentiment, label = quick_sentiment(tw["text"])
            with db_lock:
                conn = sqlite3.connect(DB_FILE)
                if not conn.execute(
                    "SELECT 1 FROM x_cache WHERE tweet_text=? AND account=?",
                    (tw["text"][:300], handle)
                ).fetchone():
                    conn.execute(
                        "INSERT INTO x_cache "
                        "(account,asset_tag,tweet_text,tweet_date,fetched_at,sentiment,sentiment_label,likes) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (handle, detect_asset_tag(tw["text"]), tw["text"][:500],
                         tw.get("created_at","")[:10], now_str, sentiment, label,
                         tw.get("public_metrics",{}).get("like_count",0))
                    )
                    collected += 1
                conn.commit()
                conn.close()
        time.sleep(2)
    if collected:
        logging.info(f"X Free Tier: {collected} yeni tweet toplandı")
    return collected


X_COLLECT_INTERVAL    = 1800

# TABU ASSETS - kesinlikle trade yapilmaz
TABU_ASSETS = set()  # WHEAT ve CORN kaldirildi - kullanici talimatiyla

# ============================================================
# HARD BLOCK - Kullanici talimatiyla runtime'da engellenen assetler
# Gemini override edemez. Telegram'dan otomatik parse edilir.
# ============================================================
hard_block_lock = threading.Lock()
HARD_BLOCK_ASSETS = {}  # {symbol: {"reason": str, "action": "BUY"|"SELL"|"ALL", "timestamp": str}}

# Keyword -> Asset mapping (Telegram mesajlarindan otomatik parse)
ASSET_KEYWORDS = {
    "silver": "SILVER", "silber": "SILVER",
    "gold": "GOLD", "altin": "GOLD",
    "oil": "OIL_BRENT", "brent": "OIL_BRENT", "petrol": "OIL_BRENT",
    "crude": "OIL_CRUDE",
    "gas": "NATURAL_GAS", "naturalgas": "NATURAL_GAS", "dogalgaz": "NATURAL_GAS",
    "gasoline": "GASOLINE", "benzin": "GASOLINE",
    "btc": "BTC_USD", "bitcoin": "BTC_USD",
    "eth": "ETH_USD", "ethereum": "ETH_USD",
    "sol": "SOL_USD", "solana": "SOL_USD",
    "xrp": "XRP_USD", "ripple": "XRP_USD",
    "copper": "COPPER", "bakir": "COPPER",
    "heatingoil": "HEATING_OIL",
    "eurusd": "EURUSD",
}

# Engelleme / serbest birakma kelimeleri
gemini_kandidaten = {}  # Global - wird in fetch_strategic_response gefüllt
BLOCK_KEYWORDS     = ["nicht handeln", "alma", "satma", "trade etme", "kauf nicht",
                      "nicht kaufen", "engelle", "blokla", "durdur", "stop trading",
                      "halt", "yasak", "verbot", "verkaufen und heute"]
SELL_KEYWORDS      = ["verkaufen", "sat ", "sell", "kapat", "close", "schliessen"]
BUY_BLOCK_KEYWORDS = ["nicht kaufen", "kauf nicht", "alma", "buy yapma"]
UNBLOCK_KEYWORDS   = ["freigeben", "serbest", "tekrar al", "engeli kaldir",
                      "unblock", "wieder handeln", "izin ver", "artik al", "artik sat"]

def parse_hard_block(text):
    """
    Kullanici mesajindan asset + islem yonu ve blok tipini cikart.
    Donus: (asset_sym, action, block_type)
      block_type : "BLOCK" | "UNBLOCK" | None
      action     : "ALL" | "BUY" | "SELL"
    """
    t = text.lower()
    detected_asset = None
    for kw, sym in ASSET_KEYWORDS.items():
        if kw in t:
            detected_asset = sym
            break
    if not detected_asset:
        return None, None, None

    for kw in UNBLOCK_KEYWORDS:
        if kw in t:
            return detected_asset, "ALL", "UNBLOCK"

    for kw in BUY_BLOCK_KEYWORDS:
        if kw in t:
            return detected_asset, "BUY", "BLOCK"

    is_sell  = any(kw in t for kw in SELL_KEYWORDS)
    is_block = any(kw in t for kw in BLOCK_KEYWORDS)

    if is_sell or is_block:
        return detected_asset, "ALL", "BLOCK"

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
# Nur aus .env — kein einziges Modell hardcodiert!
#
# .env Beispiel:
#   GEMINI_MODEL_1=gemini-3.5-flash
#   GEMINI_MODEL_2=gemini-3.1-pro
#   GEMINI_MODEL_3=gemini-3-flash
#   GEMINI_MODEL_4=gemini-2.5-flash
#   GEMINI_MODEL_5=gemini-2.0-flash
#
# Neue Interactions API (Juli 2026):
#   GEMINI_USE_INTERACTIONS_API=true  -> neue API bevorzugen
#   GEMINI_USE_INTERACTIONS_API=false -> alte generate_content API
# ============================================================
def _load_gemini_models():
    models = []
    for i in range(1, 15):
        m = os.getenv(f"GEMINI_MODEL_{i}", "").strip()
        if m:
            models.append(m)
    if not models:
        fallback = os.getenv("GEMINI_MODEL", "").strip()
        if fallback:
            models = [fallback]
    if not models:
        logging.error("KEINE GEMINI_MODEL_* in .env! Bitte .env pruefen.")
    return models

GEMINI_MODELS           = _load_gemini_models()
GEMINI_USE_INTERACTIONS = os.getenv("GEMINI_USE_INTERACTIONS_API", "true").lower() == "true"

logging.info(f"Gemini Modelle ({len(GEMINI_MODELS)}): {GEMINI_MODELS}")
logging.info(f"Gemini API-Modus: {'Interactions API (neu)' if GEMINI_USE_INTERACTIONS else 'generate_content (alt)'}")

_model_lock = threading.Lock()
_current_model_idx = 0
_current_key_idx   = 0

def get_next_model():
    """Mevcut modeli döner. GEMINI_MODELS boşsa hata vermez."""
    global _current_model_idx
    with _model_lock:
        if not GEMINI_MODELS:
            logging.error("GEMINI_MODELS boş! .env dosyasında GEMINI_MODEL_1= girilmeli.")
            return ""
        return GEMINI_MODELS[_current_model_idx % len(GEMINI_MODELS)]

def get_current_key():
    """Mevcut Gemini key'i döner. Key yoksa None."""
    valid_keys = [k for k in GEMINI_KEYS if k]
    if not valid_keys:
        return None
    return valid_keys[_current_key_idx % len(valid_keys)]

def rotate_key_or_model():
    """
    v12.5: Önce tüm keyleri dene, sonra modeli değiştir.
    Sıra: Key1+M1 → Key2+M1 → Key3+M1 → Key1+M2 → Key2+M2 → ...
    Güvenli: GEMINI_MODELS veya valid_keys boşsa ZeroDivisionError olmaz.
    Döner: (yeni_model, yeni_key)
    """
    global _current_model_idx, _current_key_idx
    with _model_lock:
        valid_keys = [k for k in GEMINI_KEYS if k]
        n_keys   = max(1, len(valid_keys))   # asla 0 değil
        n_models = max(1, len(GEMINI_MODELS)) # asla 0 değil

        _current_key_idx += 1

        if _current_key_idx >= n_keys:
            _current_key_idx   = 0
            _current_model_idx = (_current_model_idx + 1) % n_models
            model_degisti = True
        else:
            model_degisti = False

        new_model = GEMINI_MODELS[_current_model_idx % n_models] if GEMINI_MODELS else ""
        new_key   = valid_keys[_current_key_idx % n_keys] if valid_keys else None
        logging.info(
            f"Quota rotation: key_idx={_current_key_idx}/{n_keys-1} | "
            f"model={new_model} | {'MODEL DEĞİŞTİ' if model_degisti else 'Aynı model'}"
        )
        return new_model, new_key

# Eski fonksiyon adı — geriye dönük uyumluluk
def rotate_model_on_quota():
    new_model, _ = rotate_key_or_model()
    return new_model

# ============================================================
# v15.15: GEMINI MODELL-SCHLEIFE wie in swarm.py (Dexter v2.8/v2.9)
#
# Uebernommen aus swarm.py:
#   - Notfallliste _GEMINI_FALLBACK_FLASH (gilt, bis der Live-Abgleich lief)
#   - echte Google-ListModels-Abfrage + Rangfolge _gemini_rank
#     (neueste Version -> stabil vor Preview -> Flash vor Pro vor Flash-Lite)
#   - pro Anfrage eine Kette aus hoechstens GEMINI_CHAIN_MAX Modellen:
#     Key-Wechsel bei 429/401, Modell-Wechsel bei 404 / "limit: 0" / 5xx
#   - Auto-Update-Thread: 45 s nach Start, danach alle MODEL_AUTOUPDATE_HOURS,
#     ausser der Reihe wenn ein Modell wegfaellt (_GEMINI_HEAL_EVENT)
#
# Bewusst anders als swarm.py:
#   - KEINE Mini-Test-Calls: jeder Test-Call kostet eine Tagesanfrage des
#     Gratis-Kontingents. Ob ein Modell frei nutzbar ist, lernt Nexus am
#     echten Aufruf ("limit: 0" / 404 -> Modell 24 h gesperrt).
#   - Tageslimit-Gedaechtnis: melden ALLE Keys fuer ein Modell "PerDay", ruht
#     das Modell bis Mitternacht Pacific Time (dann setzt Google zurueck).
#   - Die .env wird nicht umgeschrieben; was dort steht, bleibt vorne.
#
# .env:  GEMINI_CHAIN_MAX=4   MODEL_AUTOUPDATE=true   MODEL_AUTOUPDATE_HOURS=6
#        MODEL_AUTOUPDATE_NOTIFY=true
# ============================================================
_GEMINI_FALLBACK_FLASH = [
    "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite",
]
_GEMINI_SKIP_RE = re.compile(
    r"image|tts|live|audio|embed|computer|robot|dialog|native|imagen|veo|aqa|latest",
    re.IGNORECASE)
_GEMINI_ENV_MODELS = list(GEMINI_MODELS)   # das, was in der .env steht - bleibt vorne
_GEMINI_CATALOG    = []                    # Live-Liste von Google, beste zuerst
_GEMINI_DEAD       = {}                    # Modell -> gesperrt bis (404 / kein Free-Tier)
_GEMINI_DAYLIMIT   = {}                    # Modell -> Tageskontingent leer bis
_GEMINI_DEAD_TTL   = 24 * 3600
_GEMINI_CATALOG_KEEP = 12
_GEMINI_HEAL_EVENT = threading.Event()
_gemini_state_lock = threading.Lock()
_gemini_key_idx    = 0


def _gemini_env_int(name, default):
    try:
        return int(os.getenv(name, str(default)).split("#")[0].strip())
    except ValueError:
        return default


GEMINI_CHAIN_MAX = max(1, _gemini_env_int("GEMINI_CHAIN_MAX", 4))


def _gemini_rank(model_id: str):
    """Sortierschlüssel (größer = besser) oder None = kein Kandidat. Alle Familien erlaubt:
    neueste Version → stabil vor Preview/Exp → Flash vor Pro vor Flash-Lite.
    Aliase (-latest), nummerierte Snapshots (-001), Gemma/Nicht-Text-Modelle fallen raus."""
    m = re.match(r"^gemini-(\d+(?:\.\d+)*)-(flash-lite|flash|pro)(.*)$", model_id or "")
    if not m or _GEMINI_SKIP_RE.search(model_id) or re.search(r"-\d{3}$", model_id):
        return None
    ver = tuple(int(x) for x in m.group(1).split("."))
    stable = not re.search(r"preview|beta|exp|thinking|\d{2}-\d{2}", m.group(3) or "")
    fam = {"flash": 3, "pro": 2, "flash-lite": 1}[m.group(2)]
    return (ver, 1 if stable else 0, fam)


def _gemini_list_models(keys: list) -> list:
    """Echte Google-ListModels-Abfrage → alle Text-Modelle mit generateContent, beste zuerst."""
    last = None
    for key in keys or []:
        try:
            names, token = [], None
            for _ in range(8):                       # Pagination
                params = {"pageSize": 200}
                if token:
                    params["pageToken"] = token
                r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                                 params=params, headers={"x-goog-api-key": key}, timeout=20)
                r.raise_for_status()
                j = r.json()
                for mdl in j.get("models", []):
                    if "generateContent" in (mdl.get("supportedGenerationMethods") or ["generateContent"]):
                        names.append(str(mdl.get("name", "")).replace("models/", ""))
                token = j.get("nextPageToken")
                if not token:
                    break
            ranked = sorted({n for n in names if _gemini_rank(n)}, key=_gemini_rank, reverse=True)
            if ranked:
                return ranked
            last = "keine Gemini-Textmodelle in der Antwort"
        except Exception as e:
            last = str(e)[:100]
    raise RuntimeError(f"Gemini-Katalog: {last}")


def _gemini_pacific_midnight(now: float = None) -> float:
    """Zeitpunkt (Unix) der naechsten Mitternacht Pacific Time = Reset des Tageskontingents."""
    now = time.time() if now is None else now
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        jetzt = datetime.fromtimestamp(now, tz)
        morgen = (jetzt + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        return morgen.timestamp()
    except Exception:
        return now + 6 * 3600   # ohne Zeitzonen-Daten: 6 h ruhen


def gemini_model_chain(now: float = None) -> list:
    """Kette fuer EINE Anfrage: .env-Modelle zuerst, dann Live-Liste (beste zuerst),
    ohne gesperrte / fuer heute erschoepfte Modelle, hoechstens GEMINI_CHAIN_MAX."""
    now = time.time() if now is None else now
    with _gemini_state_lock:
        kandidaten = []
        for m in list(_GEMINI_ENV_MODELS) + list(_GEMINI_CATALOG or _GEMINI_FALLBACK_FLASH):
            if m and m not in kandidaten:
                kandidaten.append(m)
        frei = [m for m in kandidaten
                if _GEMINI_DEAD.get(m, 0) <= now and _GEMINI_DAYLIMIT.get(m, 0) <= now]
    return frei[:GEMINI_CHAIN_MAX]


def _gemini_classify(err: str) -> str:
    """Fehlertext einordnen (Reihenfolge wie call_gemini in swarm.py):
    'tot'        Modell weg / kein Free-Tier      -> naechstes Modell, 24 h sperren
    'tageslimit' 429 mit PerDay                   -> naechster Key (alle gueltigen Keys: Modell ruht)
    'key'        429 (Minutenlimit) / 403         -> naechster Key
    'keytot'     401 / Key ungueltig              -> naechster Key, Key 6 h nicht mehr benutzen (v15.18)
    'modell'     5xx / ueberlastet                -> ein 2. Versuch, dann naechstes Modell
    'abbruch'    alles andere                     -> Gemini fuer diese Anfrage aufgeben"""
    if re.search(r"limit:\s*0\b", err) or "NOT_FOUND" in err or ("404" in err and "429" not in err):
        return "tot"
    if "429" in err or "RESOURCE_EXHAUSTED" in err:
        return "tageslimit" if re.search(r"PerDay|Daily", err) else "key"
    if any(x in err for x in ("401", "UNAUTHENTICATED", "API_KEY_INVALID", "API key not valid")):
        return "keytot"
    if any(x in err for x in ("403", "PERMISSION_DENIED")):
        return "key"
    if any(x in err for x in ("500", "502", "503", "504", "UNAVAILABLE", "overloaded")):
        return "modell"
    return "abbruch"


_GEMINI_LAST_FAIL = {}   # Modell -> {art: [anzahl, detail]} der letzten Anfrage (v15.16, v15.18: Detail je Fehlerart)
_GEMINI_BAD_KEYS = {}    # v15.18: Key -> gesperrt bis (Zeitstempel); von Google mit 401 abgelehnt
_GEMINI_BAD_KEY_TTL = 6 * 3600
_GEMINI_503_PAUSE = float(os.getenv("GEMINI_503_PAUSE", "6"))   # Sekunden bis zum 2. Versuch bei 503; 0 = kein 2. Versuch
_GEMINI_ART_TXT = {
    "tot": "kein Gratis-Kontingent / nicht verfügbar", "tageslimit": "Tageslimit erreicht",
    "key": "Minutenlimit", "keytot": "Key abgelehnt", "modell": "Server überlastet (503)",
    "abbruch": "anderer Fehler",
}


def gemini_usable_keys():
    """v15.18: Keys, die Google nicht (in den letzten 6 h) als ungueltig abgelehnt hat."""
    now = time.time()
    with _gemini_state_lock:
        return [k for k in GEMINI_KEYS if k and _GEMINI_BAD_KEYS.get(k, 0) <= now]


def _gemini_note_fail(model, art, err):
    """Fehler der laufenden Anfrage merken (fuer die Telegram-Meldung)."""
    err = str(err or "")
    m = re.search(r"quotaId['\"]?\s*:\s*['\"]?([A-Za-z0-9_\-]+)", err)
    lim = re.search(r"limit:\s*(\d+)", err)
    if art == "tageslimit":
        detail = f"limit {lim.group(1)}/Tag" if lim else ""
    elif art == "key":
        detail = m.group(1) if m else ""
    elif art == "abbruch":
        detail = " ".join(err.split())[:110]
    else:
        detail = ""
    with _gemini_state_lock:
        d = _GEMINI_LAST_FAIL.setdefault(model, {})
        eintrag = d.setdefault(art, [0, ""])
        eintrag[0] += 1
        eintrag[1] = detail or eintrag[1]


def gemini_last_fail_text():
    """Kurze Begruendung, warum Gemini zuletzt nichts geliefert hat.
    v15.18: abgelehnte Keys in EINER Zeile, Modelle mit gleichem Grund zusammengefasst."""
    now = time.time()
    fmt = lambda ts: datetime.fromtimestamp(ts).strftime('%d.%m %H:%M')
    with _gemini_state_lock:
        snap = {m: {a: list(v) for a, v in d.items()} for m, d in _GEMINI_LAST_FAIL.items()}
        ruht = {m: t for m, t in _GEMINI_DAYLIMIT.items() if t > now}
        tot = {m: t for m, t in _GEMINI_DEAD.items() if t > now}
        bad = [k for k, t in _GEMINI_BAD_KEYS.items() if t > now]
    n_alle = len([k for k in GEMINI_KEYS if k])
    zeilen = []
    if bad:
        zeilen.append(f"• Keys: nur {n_alle - len(bad)} von {n_alle} nutzbar - von Google abgelehnt (401): "
                      + ", ".join("…" + k[-4:] for k in bad))
    gruende = {}                                   # Grundtext -> Modelle (Reihenfolge bleibt)
    for m, arten in snap.items():
        teile = []
        for a, (n, detail) in arten.items():
            if a == "keytot":
                continue                           # steht oben in der Keys-Zeile
            t = _GEMINI_ART_TXT.get(a, a)
            if a == "tageslimit":
                t += f" ({n} Key{'s' if n != 1 else ''}" + (f", {detail}" if detail else "") + ")"
                if m in ruht:
                    t += f", ruht bis {fmt(ruht[m])}"
            elif a == "modell" and _GEMINI_503_PAUSE > 0:
                t = "Server überlastet (503, auch beim 2. Versuch)"
            elif detail:
                t += f" [{detail}]"
            teile.append(t)
        if teile:
            gruende.setdefault(", ".join(teile), []).append(m)
    for m, t in ruht.items():
        if m not in snap:
            gruende.setdefault(f"Tageslimit, ruht bis {fmt(t)}", []).append(m)
    for m, t in tot.items():
        if m not in snap:
            gruende.setdefault(f"nicht verfügbar, gesperrt bis {fmt(t)}", []).append(m)
    for text, modelle in gruende.items():
        zeilen.append(f"• {', '.join(modelle)}: {text}")
    return "\n".join(zeilen)


def _gemini_einmal(model, key, contents, system_instruction=None):
    """Ein einzelner Aufruf. Rueckgabe: (text, art, fehlertext); text ist None bei Fehler."""
    try:
        client = genai.Client(api_key=key)
        cfg = {"system_instruction": system_instruction} if system_instruction else {}
        resp = client.models.generate_content(
            model=model, contents=contents,
            config=types.GenerateContentConfig(**cfg) if cfg else None)
        text = getattr(resp, "text", None)
        if text and text.strip():
            return text, "", ""
        return None, "modell", "leere Antwort"
    except Exception as e:
        err = str(e)
        return None, _gemini_classify(err), err


def gemini_chain_generate(contents, system_instruction=None):
    """Anfrage an Gemini ueber die Modell-Kette. Gibt den Antworttext zurueck oder None,
    wenn kein Modell/Key der Kette liefert. Fallen in einem Durchgang Modelle weg
    (gesperrt / Tageskontingent leer), wird einmal mit den nachrueckenden Modellen
    weiterprobiert.
    v15.18: von Google abgelehnte Keys (401) werden 6 h nicht mehr benutzt und zaehlen
    nicht mehr mit - ein Modell ruht, sobald alle GUELTIGEN Keys am Tageslimit sind
    (vorher: nie, solange ungueltige Keys in der Liste standen). Bei 503 ein 2. Versuch."""
    global _gemini_key_idx
    keys = [k for k in GEMINI_KEYS if k]
    if not keys:
        logging.warning("Gemini: key yok")
        return None
    with _gemini_state_lock:
        _GEMINI_LAST_FAIL.clear()
    ueberlastet = set()                           # in dieser Anfrage schon 2x 503 -> im 2. Durchgang nicht nochmal
    for _runde in (1, 2):
        chain = gemini_model_chain()
        if not chain:
            logging.warning("Gemini: alle Modelle gesperrt oder Tageskontingent leer - kein Aufruf")
            return None
        weggefallen = False
        for model in chain:
            if model in ueberlastet:
                continue
            if not gemini_usable_keys():
                logging.warning("Gemini: alle Keys von Google abgelehnt (401) - kein Aufruf")
                return None
            tageslimit_keys, wiederholt = 0, False
            for _ in range(len(keys)):
                key = keys[_gemini_key_idx % len(keys)]
                if _GEMINI_BAD_KEYS.get(key, 0) > time.time():      # abgelehnter Key: ueberspringen
                    _gemini_key_idx = (_gemini_key_idx + 1) % len(keys)
                    continue
                text, art, err = _gemini_einmal(model, key, contents, system_instruction)
                if text is None and art == "modell" and not wiederholt and _GEMINI_503_PAUSE > 0:
                    wiederholt = True
                    logging.warning(f"Gemini {model}: {err[:100]} - zweiter Versuch in {_GEMINI_503_PAUSE:g} s")
                    time.sleep(_GEMINI_503_PAUSE)
                    text, art, err = _gemini_einmal(model, key, contents, system_instruction)
                if text is not None:
                    logging.info(f"[OK] Başarılı: {model} | key=...{key[-6:]}")
                    return text
                logging.warning(f"Gemini {model} key=...{key[-6:]}: {art} | {err[:160]}")
                _gemini_note_fail(model, art, err)
                if art == "tot":
                    with _gemini_state_lock:
                        _GEMINI_DEAD[model] = time.time() + _GEMINI_DEAD_TTL
                    _GEMINI_HEAL_EVENT.set()      # Modell weg / kein Free-Tier -> Katalog neu holen
                    weggefallen = True
                    break
                if art == "keytot":
                    with _gemini_state_lock:
                        _GEMINI_BAD_KEYS[key] = time.time() + _GEMINI_BAD_KEY_TTL
                    logging.warning(f"Gemini key=...{key[-6:]}: von Google abgelehnt - wird "
                                    f"{_GEMINI_BAD_KEY_TTL / 3600:g} h nicht mehr benutzt")
                    _gemini_key_idx = (_gemini_key_idx + 1) % len(keys)
                    continue
                if art in ("key", "tageslimit"):
                    if art == "tageslimit":
                        tageslimit_keys += 1
                    _gemini_key_idx = (_gemini_key_idx + 1) % len(keys)
                    continue
                if art == "modell":
                    ueberlastet.add(model)
                    break
                return None                       # unbekannter Fehler: Gemini fuer diese Anfrage aufgeben
            else:
                # alle Keys durchprobiert, keiner hat geliefert
                if tageslimit_keys > 0 and tageslimit_keys >= len(gemini_usable_keys()):
                    bis = _gemini_pacific_midnight()
                    with _gemini_state_lock:
                        _GEMINI_DAYLIMIT[model] = bis
                    weggefallen = True
                    logging.warning(f"Gemini {model}: Tageskontingent auf allen gueltigen Keys leer - ruht bis "
                                    f"{datetime.fromtimestamp(bis).strftime('%d.%m %H:%M')}")
        if not weggefallen:
            break
    return None


def gemini_refresh_catalog() -> tuple:
    """Live-Modellliste von Google holen. Rueckgabe: (geaendert, text)."""
    global _GEMINI_CATALOG
    keys = [k for k in GEMINI_KEYS if k]
    if not keys:
        return False, "Gemini: key yok"
    alt = gemini_model_chain()
    try:
        ids = _gemini_list_models(keys)
    except Exception as e:
        logging.warning(f"[MODELUPDATE] {e}")
        return False, str(e)
    with _gemini_state_lock:
        _GEMINI_CATALOG = ids[:_GEMINI_CATALOG_KEEP]
    neu = gemini_model_chain()
    logging.info(f"[MODELUPDATE] Gemini-Katalog: {len(ids)} Textmodelle | Kette: {' → '.join(neu) or '-'}")
    return neu != alt, " → ".join(neu) or "-"


def gemini_status_text() -> str:
    now = time.time()
    fmt = lambda ts: datetime.fromtimestamp(ts).strftime('%d.%m %H:%M')
    with _gemini_state_lock:
        tot = {m: t for m, t in _GEMINI_DEAD.items() if t > now}
        leer = {m: t for m, t in _GEMINI_DAYLIMIT.items() if t > now}
        katalog = list(_GEMINI_CATALOG)
    zeilen = ["🤖 GEMINI MODELL-KETTE",
              "Kette jetzt: " + (" → ".join(gemini_model_chain()) or "keine (alles gesperrt/leer)"),
              ".env: " + (", ".join(_GEMINI_ENV_MODELS) or "-"),
              "Live-Liste: " + (", ".join(katalog) if katalog else "noch nicht abgerufen (Notfallliste aktiv)")]
    if leer:
        zeilen.append("Tageskontingent leer: " + ", ".join(f"{m} (bis {fmt(t)})" for m, t in leer.items()))
    if tot:
        zeilen.append("Gesperrt (kein Free-Tier / nicht vorhanden): " + ", ".join(f"{m} (bis {fmt(t)})" for m, t in tot.items()))
    _bad = [k for k in GEMINI_KEYS if k and k not in gemini_usable_keys()]  # v15.18
    if _bad:
        zeilen.append(f"Keys: nur {len([k for k in GEMINI_KEYS if k]) - len(_bad)} nutzbar - von Google abgelehnt (401): "
                      + ", ".join("…" + k[-4:] for k in _bad))
    return "\n".join(zeilen)


def _gemini_modelupdate_loop():
    """Wie _model_autoupdate_loop in swarm.py: 45 s nach Start, dann alle
    MODEL_AUTOUPDATE_HOURS; ausser der Reihe nach einem Heal-Trigger (entprellt, 5 Min)."""
    def _flag(name, default="true"):
        return os.getenv(name, default).split("#")[0].strip().lower() in ("1", "true", "yes", "on")
    if not _flag("MODEL_AUTOUPDATE"):
        logging.info("[MODELUPDATE] deaktiviert (MODEL_AUTOUPDATE=false)")
        return
    try:
        hours = float(os.getenv("MODEL_AUTOUPDATE_HOURS", "6").split("#")[0].strip())
    except ValueError:
        hours = 6.0
    interval = max(hours, 0.25) * 3600
    time.sleep(45)
    while True:
        try:
            geaendert, kette = gemini_refresh_catalog()
            if geaendert and _flag("MODEL_AUTOUPDATE_NOTIFY"):
                try: bot.send_message(MY_CHAT_ID, f"🤖 Gemini-Kette aktualisiert:\n{kette}")
                except Exception: pass
        except Exception as e:
            logging.warning(f"[MODELUPDATE] {e}")
        ausgeloest = _GEMINI_HEAL_EVENT.wait(timeout=interval)   # True = Trigger, False = Timer
        if ausgeloest:
            time.sleep(300)                                      # entprellen
        _GEMINI_HEAL_EVENT.clear()


# ============================================================
# v15.22: MODELL-SCHLEIFE FUER GROQ / QWEN (OpenRouter) / NVIDIA - wie in swarm.py
#
# Bis v15.21 lief jeder dieser Anbieter mit dem EINEN Modell aus der .env. Nimmt der
# Anbieter das Modell aus dem Programm, scheiterte er bei jedem Scan (Log vom 30.09.-06.10.:
# Groq 426x "model does not exist", Qwen "No endpoints found", Nvidia "410 Gone").
#
# Uebernommen aus swarm.py (MODEL-AUTOUPDATE, _model_chain, _chat_completions_chain):
#   - Modellliste des Anbieters abrufen, Nicht-Chat-Modelle aussortieren, Rangfolge
#     (stabil vor Preview -> Groesse, gedeckelt -> Kontext -> Alter)
#   - pro Anfrage eine Kette: Hauptmodell + Ersatzmodelle (hoechstens AI_CHAIN_MAX)
#       401/403/429 -> naechster Key (alle Keys durch -> naechstes Modell)
#       404/410 / "does not exist" / "decommissioned" / "No endpoints found"
#                   -> Modell 24 h gesperrt, naechstes Modell, Pruefung ausser der Reihe
#       400/5xx / leere Antwort -> naechstes Modell
#   - faellt das Hauptmodell weg: Ersatz suchen, jeden Kandidaten mit einem echten
#     Mini-Aufruf pruefen, das neue Modell in die .env schreiben (Sicherung
#     .env.modelupdate.bak, Kontrolle, bei Fehler zurueck) und sofort benutzen
#   - Pruef-Thread: 75 s nach dem Start, dann alle MODEL_AUTOUPDATE_HOURS, ausser der
#     Reihe nach einem Ausfall (entprellt, 5 Min)
#
# Anders als swarm.py:
#   - Sperren gelten je Anbieter (dieselbe Modell-ID gibt es bei Groq UND Nvidia).
#   - <think>...</think> wird aus jeder Antwort entfernt (Ersatzmodelle der Kette sind
#     nicht einzeln geprueft; "Denk"-Text darf nicht als Handelssignal gelesen werden).
#   - Ein gesperrtes Hauptmodell wird in der Kette uebersprungen, solange Ersatz da ist.
#   - Ein Modell, das nicht in der Liste steht oder im Betrieb gesperrt wurde, wird erst
#     gefragt und nur ersetzt, wenn es wirklich nicht antwortet; bleibt die Pruefung ohne
#     Ergebnis (Limit, Netz), wird nichts geaendert.
#   - Qwen/OpenRouter: zuerst Gratis-Qwen-Modelle; besteht keines die Pruefung, ein
#     anderes Gratis-Modell (Nexus hat keinen eigenen OpenRouter-Platz wie swarm.py).
#   - /update_models prueft und repariert nur. Auf das beste Modell wechselt erst
#     /update_models best - ein von Hand gewaehltes Modell bleibt sonst stehen.
#
# .env:  MODEL_AUTOUPDATE=true  MODEL_AUTOUPDATE_HOURS=6  MODEL_AUTOUPDATE_NOTIFY=true
#        MODEL_AUTOUPDATE_PIN=GROQ_MODEL,QWEN_MODEL,NVIDIA_MODEL   (diese nie anfassen)
#        AI_CHAIN_MAX=4
# ============================================================
def _ai_key_liste(*namen):
    keys = []
    for n in namen:
        for k in os.getenv(n, "").split("#")[0].split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    return keys


_AI_PROVIDER = ("groq", "qwen", "nvidia")
_AI_LABEL    = {"groq": "Groq", "qwen": "Qwen", "nvidia": "Nvidia"}
_AI_GLOBAL   = {"groq": "GROQ_MODEL", "qwen": "QWEN_MODEL", "nvidia": "NVIDIA_MODEL"}
_AI_ENV_KEY  = {"groq": "GROQ_MODEL", "qwen": "QWEN_MODEL",
                "nvidia": "NVIDIA_MODELS" if os.getenv("NVIDIA_MODELS", "").strip() else "NVIDIA_MODEL"}
_AI_KEYS     = {"groq": GROQ_KEYS,
                "qwen": _ai_key_liste("QWEN_API_KEY", "QWEN_KEYS"),
                "nvidia": _ai_key_liste("NVIDIA_API_KEY", "NVIDIA_KEYS")}
GROQ_BASE_URL   = (os.getenv("GROQ_BASE_URL") or "https://api.groq.com").split("#")[0].strip().rstrip("/")
NVIDIA_BASE_URL = (os.getenv("NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1").split("#")[0].strip().rstrip("/")

_AI_HEAL_EVENT  = threading.Event()
_AI_RUN_LOCK    = threading.Lock()         # nur ein Prueflauf gleichzeitig
_ai_state_lock  = threading.Lock()
_AI_REJECTED    = {}                       # (anbieter, modell) -> Zeitpunkt der Sperre
_AI_REJECT_TTL  = 24 * 3600
_AI_BACKUPS     = {p: [] for p in _AI_PROVIDER}    # Ersatzmodelle aus dem Katalog, beste zuerst
_AI_KEY_IDX     = {p: 0 for p in _AI_PROVIDER}
_AI_HINT        = {}                       # anbieter -> Hinweis (z.B. Konto-Einstellung bei OpenRouter)
_AI_LAST        = {"zeit": 0.0, "changes": [], "info": [], "errors": []}
_AI_CHAIN_MAX   = max(1, _gemini_env_int("AI_CHAIN_MAX", 4))
_AI_PROBE_MAX   = 3                        # Mini-Aufrufe je Anbieter und Lauf
_AI_PROBE_TIMEOUT = 40
_AI_SIZE_CAP_B  = 120                      # ueber 120B kaum besser, aber langsamer / oefter 429
_AI_BACKUP_KEEP = 8
_AI_NON_CHAT_RE = re.compile(
    r"whisper|guard|tts|embed|moderat|compound|orpheus|playai|transcri|rerank|image-gen",
    re.IGNORECASE)
# Der Nvidia-Katalog enthaelt viel Nicht-Chat (Bild, Embedding, Bio, Sprache, Safety ...)
_AI_NVIDIA_NON_CHAT_RE = re.compile(
    r"(?:^|[-/_.])(?:vl|vlm|vision|clip|asr|riva|reward|neva|kosmos|paligemma|fuyu|sdxl|flux|"
    r"cosmos|genmol|molmim|diffdock|esm\d*|protein|bionemo|retriev\w*|ocr|parse|nemoguard|"
    r"safety|topic|jailbreak|translate)(?:$|[-/_.])|"
    r"stable-diffusion|embed|rerank|deplot|parakeet|canary|fastpitch|magpie|maxine|studiovoice",
    re.IGNORECASE)
_AI_DEAD_TXT = ("model_not_found", "decommissioned", "does not exist", "no longer supported",
                "no endpoints found", "not a valid model id",
                "'title': 'gone'", '"title": "gone"', '"title":"gone"')


def ai_primary(prov):
    return (globals().get(_AI_GLOBAL[prov]) or "").strip()


def _ai_base(prov):
    if prov == "groq":
        return GROQ_BASE_URL + "/openai/v1"
    if prov == "qwen":
        return QWEN_BASE_URL.rstrip("/")
    return NVIDIA_BASE_URL


def _ai_gesperrt(prov, model, now=None):
    now = time.time() if now is None else now
    return now - _AI_REJECTED.get((prov, model), 0) < _AI_REJECT_TTL


def ai_model_chain(prov, now=None):
    """Kette fuer EINE Anfrage: Hauptmodell, dann Ersatzmodelle - ohne die in den letzten
    24 h als tot erkannten. Ist das Hauptmodell gesperrt und kein Ersatz bekannt, wird es
    trotzdem versucht (vielleicht ist es wieder da)."""
    now = time.time() if now is None else now
    primary = ai_primary(prov)
    with _ai_state_lock:
        rest = [m for m in _AI_BACKUPS.get(prov, []) if m and m != primary and not _ai_gesperrt(prov, m, now)]
        primary_ok = bool(primary) and not _ai_gesperrt(prov, primary, now)
    if primary_ok:
        return [primary] + rest[:_AI_CHAIN_MAX - 1]
    if rest:
        return rest[:_AI_CHAIN_MAX]
    return [primary] if primary else []


def ai_model_dead(prov, model):
    """Im Betrieb als tot erkannt: 24 h nicht mehr nehmen. War es das Hauptmodell,
    die Pruefung ausser der Reihe anstossen (einmal je Sperre)."""
    with _ai_state_lock:
        neu = not _ai_gesperrt(prov, model)
        _AI_REJECTED[(prov, model)] = time.time()
    # nur beim ERSTEN Erkennen anstossen: bleibt das Modell tot und gibt es keinen Ersatz
    # (festgehalten, keine Liste), wuerde sonst jede Anfrage einen neuen Prueflauf ausloesen
    if neu and model == ai_primary(prov):
        _AI_HEAL_EVENT.set()


def _ai_classify(e):
    """Fehler eines Aufrufs einordnen:
    'tot'     Modell gibt es nicht mehr            -> 24 h sperren, naechstes Modell
    'key'     401 / 402 / 403 / 429                -> naechster Key, dann naechstes Modell
    'modell'  400 / 408 / 413 / 422 / 5xx / Antwort ohne Inhalt -> naechstes Modell
    'konto'   OpenRouter: Konto-Einstellung sperrt Gratis-Modelle -> Anbieter aufgeben
    'abbruch' Netz / unbekannt                     -> Anbieter fuer diese Anfrage aufgeben"""
    code = getattr(e, "status_code", None)
    err = str(e)
    low = err.lower()
    if isinstance(e, (IndexError, TypeError, AttributeError, KeyError)):
        return "modell"                    # Antwort ohne Inhalt / in unerwarteter Form
    if "data policy" in low:
        return "konto"
    if code in (404, 410) or any(x in low for x in _AI_DEAD_TXT):
        return "tot"
    if code in (401, 402, 403, 429):
        return "key"
    if code is None:
        m = re.search(r"Error code:\s*(\d{3})", err)
        if m:
            code = int(m.group(1))
            if code in (401, 402, 403, 429):
                return "key"
    if code in (400, 408, 413, 422) or (isinstance(code, int) and code >= 500) or "overloaded" in low:
        return "modell"
    return "abbruch"


def _ai_clean(text):
    """Antwort saeubern: <think>...</think> gehoert nicht in die Analyse - dort koennten
    Probe-Zeilen wie "TRADE: ..." stehen, die der Bot sonst als Signal lesen wuerde.
    Ein nicht geschlossenes <think> heisst: Antwort abgeschnitten -> wie eine leere Antwort.
    Steht nur ein </think> da (oeffnendes Zeichen fehlt), zaehlt der Text dahinter."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S | re.I)
    if "<think>" in text.lower():
        return ""
    ende = text.lower().rfind("</think>")          # oeffnendes <think> fehlt: nur der Text danach zaehlt
    if ende >= 0:
        text = text[ende + len("</think>"):]
    return text.strip()


def ai_chain_call(prov, call_once):
    """Anfrage an Groq / Qwen / Nvidia ueber die Modell-Kette. call_once(key, modell) gibt
    den Antworttext zurueck oder wirft. Rueckgabe: Text oder None."""
    label = _AI_LABEL[prov]
    keys = [k for k in _AI_KEYS.get(prov, []) if k]
    if not keys:
        return None
    primary = ai_primary(prov)
    chain = ai_model_chain(prov)
    if not chain:
        logging.warning(f"{label} hata: kein Modell gesetzt")
        return None
    for model in chain:
        for _ in range(len(keys)):
            idx = _AI_KEY_IDX[prov] % len(keys)
            try:
                text = _ai_clean(call_once(keys[idx], model))
            except Exception as e:
                art = _ai_classify(e)
                logging.warning(f"{label} key {idx + 1} hata: {model}: {str(e)[:300]}")
                if art == "tot":
                    ai_model_dead(prov, model)
                    break
                if art == "key":
                    _AI_KEY_IDX[prov] = (idx + 1) % len(keys)
                    time.sleep(1)
                    continue
                if art == "modell":
                    break
                if art == "konto":
                    logging.warning(f"{label}: OpenRouter lehnt Gratis-Modelle wegen der Konto-Einstellung ab "
                                    f"(data policy) - bitte auf openrouter.ai unter Settings > Privacy freigeben")
                return None
            if text:
                if model != primary:
                    logging.warning(f"[{label.upper()}] Hauptmodell {primary or '-'} ausgefallen -> {model} antwortet")
                logging.info(f"[OK] {label} ({model}, key {idx + 1})")
                return text
            logging.warning(f"{label} key {idx + 1} hata: {model}: leere Antwort")
            break
    return None


# ---- Katalog + Rangfolge (aus swarm.py) ---------------------------------
def _ai_model_size_b(model_id):
    """Groesste erkennbare Parameterzahl aus der ID (...-70b-...). 0 = unbekannt."""
    sizes = re.findall(r'(?<![\d.])(\d{1,4}(?:\.\d+)?)b(?![a-z])', (model_id or "").lower())
    return max((float(x) for x in sizes), default=0.0)


def _ai_price_zero(v):
    try:
        return float(v) == 0.0
    except (TypeError, ValueError):
        return False


def _ai_or_is_free(m):
    p = m.get("pricing") or {}
    return _ai_price_zero(p.get("prompt")) and _ai_price_zero(p.get("completion"))


def _ai_or_is_text_chat(m):
    """Text rein -> Text raus. Fehlt 'architecture', wird nicht ausgeschlossen."""
    mid = m.get("id", "")
    if not mid or _AI_NON_CHAT_RE.search(mid):
        return False
    arch = m.get("architecture") or {}
    outs, ins = arch.get("output_modalities"), arch.get("input_modalities")
    if outs is not None and set(outs) != {"text"}:
        return False
    if ins is not None and "text" not in ins:
        return False
    if outs is None and isinstance(arch.get("modality"), str) and not arch["modality"].endswith("->text"):
        return False
    return True


def _ai_or_expires_soon(m, days=7):
    exp = m.get("expiration_date")
    if not exp:
        return False
    try:
        from datetime import timezone as _tz
        dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        return (dt - datetime.now(_tz.utc)).total_seconds() < days * 86400
    except Exception:
        return False


def _ai_model_rank(m, cap=None):
    """Groesser = besser: stabil vor Preview, dann Groesse (gedeckelt), Kontext, Alter."""
    mid = m.get("id", "")
    ctx = m.get("context_length") or m.get("context_window") or 0
    try:
        ctx, created = int(ctx), int(m.get("created") or 0)
    except (TypeError, ValueError):
        ctx, created = 0, 0
    return (0 if "preview" in mid.lower() else 1,
            min(_ai_model_size_b(mid), cap or _AI_SIZE_CAP_B), ctx, created)


def _ai_catalog(prov):
    """Modellliste des Anbieters. OpenRouter ist oeffentlich, Groq/Nvidia brauchen einen Key."""
    url = _ai_base(prov) + "/models"
    if prov == "qwen":
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        data = r.json().get("data", [])
        if len(data) < 20:
            raise RuntimeError(f"Liste unplausibel ({len(data)} Einträge)")
        return data
    keys = [k for k in _AI_KEYS.get(prov, []) if k]
    last = "kein Key"
    for i in range(len(keys)):
        key = keys[(_AI_KEY_IDX[prov] + i) % len(keys)]
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=20)
        if r.status_code in (401, 403):
            last = f"HTTP {r.status_code}"
            continue
        r.raise_for_status()
        data = r.json().get("data", [])
        if len(data) < (3 if prov == "groq" else 5):
            raise RuntimeError(f"Liste unplausibel ({len(data)} Einträge)")
        return data
    raise RuntimeError(f"Key abgelehnt ({last})")


def _ai_probe(prov, model_id):
    """Echter Mini-Aufruf. Rueckgabe: 'ok' | 'dead' | 'inconclusive' (429 / 5xx / Key / Netz).
    Bei 401/403/429 wird einmal der naechste Key versucht."""
    keys = [k for k in _AI_KEYS.get(prov, []) if k]
    if not keys:
        return "inconclusive"
    url = _ai_base(prov) + "/chat/completions"
    for versuch in range(min(2, len(keys))):
        key = keys[(_AI_KEY_IDX[prov] + versuch) % len(keys)]
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {key}"},
                              json={"model": model_id, "max_tokens": 512,
                                    "messages": [{"role": "user", "content": "Antworte nur mit: OK"}]},
                              timeout=_AI_PROBE_TIMEOUT)
        except Exception as e:
            logging.debug(f"[MODELUPDATE] Probe {prov}/{model_id}: {e}")
            return "inconclusive"
        if r.status_code == 200:
            try:
                wahl = (r.json().get("choices") or [None])[0]
            except Exception:
                return "inconclusive"
            if not wahl:
                return "inconclusive"          # 200 ohne Antwort (OpenRouter meldet so auch Limits)
            roh = (wahl.get("message") or {}).get("content") or ""
            if _ai_clean(roh):
                return "ok"
            # nur "Denken" oder am Laengenlimit abgeschnitten: das Modell lebt, das Urteil bleibt offen
            if "<think>" in roh.lower() or wahl.get("finish_reason") == "length":
                return "inconclusive"
            return "dead"
        if "data policy" in (r.text or "").lower():
            _AI_HINT[prov] = ("OpenRouter lehnt Gratis-Modelle wegen der Konto-Einstellung ab (data policy) - "
                              "bitte auf openrouter.ai unter Settings > Privacy freigeben")
            return "inconclusive"
        if r.status_code in (401, 403, 429):
            continue
        if r.status_code in (402, 408) or r.status_code >= 500:
            return "inconclusive"
        return "dead"
    return "inconclusive"


def _ai_pick_verified(prov, candidates, current, limit=None):
    """Erster Kandidat, der den Mini-Aufruf besteht. Rueckgabe: (modell | None, anzahl_tests)."""
    tested, now = 0, time.time()
    for mid in candidates:
        if mid == current or _ai_gesperrt(prov, mid, now):
            continue
        if tested >= (limit or _AI_PROBE_MAX) or prov in _AI_HINT:
            break
        tested += 1
        res = _ai_probe(prov, mid)
        logging.info(f"[MODELUPDATE] Probe {prov}/{mid}: {res}")
        if res == "ok":
            return mid, tested
        if res == "dead":
            with _ai_state_lock:
                _AI_REJECTED[(prov, mid)] = now
    return None, tested


def _ai_env_set_verified(updates):
    """KEY=WERT in der .env setzen: Kommentare, Reihenfolge und Zeilenenden bleiben, fehlende
    Eintraege kommen ans Ende. Sicherung .env.modelupdate.bak, danach Kontrolle; stimmt etwas
    nicht, kommt der alte Inhalt zurueck. Rueckgabe: (ok, meldung)"""
    if not updates:
        return True, "nichts zu tun"
    path = os.path.join(BASE_DIR, ".env")
    original = None

    def _schreiben(text):
        tmp = path + ".modelupdate.tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        try:
            os.chmod(tmp, os.stat(path).st_mode & 0o777 if os.path.exists(path) else 0o600)
        except Exception:
            pass
        os.replace(tmp, path)

    with _ENV_WRITE_LOCK:
        try:
            if not os.path.exists(path):
                return False, ".env nicht gefunden"
            with open(path, encoding="utf-8", newline="") as f:
                original = f.read()
            text = original
            nl = "\r\n" if "\r\n" in original else "\n"
            for key, val in updates.items():
                pat = re.compile(rf'^([ \t]*{re.escape(key)}[ \t]*=[ \t]*)([^#\r\n]*?)([ \t]+#[^\r\n]*)?(\r?)$', re.M)
                if pat.search(text):
                    text = pat.sub(lambda mo, v=val: f"{mo.group(1)}{v}{mo.group(3) or ''}{mo.group(4)}", text)
                else:
                    text = text.rstrip("\r\n") + f"{nl}{key}={val}{nl}"
            bak = path + ".modelupdate.bak"
            with open(bak, "w", encoding="utf-8", newline="") as f:
                f.write(original)
            try:
                os.chmod(bak, 0o600)
            except Exception:
                pass
            _schreiben(text)
            from dotenv import dotenv_values
            got = dotenv_values(path)
            bad = [k for k, v in updates.items() if got.get(k) != v]
            if bad:
                _schreiben(original)
                return False, f"Kontrolle fehlgeschlagen ({', '.join(bad)}), alter Inhalt wiederhergestellt"
            return True, "ok"
        except Exception as e:
            if original is not None:
                try:
                    _schreiben(original)
                except Exception:
                    pass
            return False, f"{str(e)[:80]}, alter Inhalt wiederhergestellt"


def _ai_heal(prov, by_id, ranked_ids, best, paid_ok=True, verify=False, max_probes=None):
    """Entscheidung fuer EINEN Anbieter. Rueckgabe: (neues_modell | None, hinweis | None, fehler | None).
    paid_ok=True (OpenRouter): ein bewusst gewaehltes bezahltes Modell bleibt.
    verify=True: auch ein gelistetes Modell bekommt EINEN Mini-Aufruf - ein Eintrag in der
    Liste heisst nicht, dass es antwortet (Nvidia: 410 trotz Listung, Groq: 404 ohne Zugriff).
    Anders als swarm.py: Ein Modell, das NICHT in der Liste steht oder im Betrieb gesperrt
    wurde, wird erst gefragt und nur ersetzt, wenn es wirklich nicht mehr antwortet.
    Bleibt die Pruefung ohne Ergebnis (Limit, Netz), wird nichts geaendert."""
    label, current = _AI_LABEL[prov], ai_primary(prov)
    entry = by_id.get(current)
    listed = entry is not None
    if listed and paid_ok and not _ai_or_is_free(entry) and not current.endswith(":free"):
        return None, f"{label}: {current} - bezahltes Modell, bewusst gewählt: bleibt", None
    if not current:
        healthy, why = False, "kein Modell gesetzt"
    elif listed and paid_ok and (not _ai_or_is_free(entry) or _ai_or_expires_soon(entry)):
        healthy, why = False, "nicht mehr gratis oder läuft bald aus"
    else:
        healthy, why = True, ""
        if not listed or verify or _ai_gesperrt(prov, current):
            res = _ai_probe(prov, current)
            logging.info(f"[MODELUPDATE] Probe {prov}/{current}: {res}")
            if res == "dead":
                healthy, why = False, "antwortet nicht mehr"
            elif res == "ok":
                with _ai_state_lock:
                    _AI_REJECTED.pop((prov, current), None)      # war im Betrieb gesperrt, lebt aber
            else:
                return None, f"{label}: {current} - Prüfung ohne Ergebnis (Limit oder Netz): bleibt vorerst", None
    if healthy and not best:
        return None, f"{label}: {current} ✓ in Ordnung", None
    if healthy:      # best: nur wechseln, wenn ein Kandidat strikt besser eingestuft ist
        better = ranked_ids[:ranked_ids.index(current)] if current in ranked_ids else ranked_ids
        why = "besseres Modell gefunden"
    else:
        better = ranked_ids
    new, tested = _ai_pick_verified(prov, better, current, max_probes)
    if new:
        return new, f"{label}: Modell ersetzt: {current or '(leer)'} → {new} (Grund: {why})", None
    if healthy:
        return None, f"{label}: {current} ✓ in Ordnung (kein besseres Modell hat die Prüfung bestanden)", None
    return None, None, (f"{label}: {current or '(leer)'} fällt aus ({why}), aber kein Ersatz hat die Prüfung "
                        f"bestanden ({tested} Tests, {len(ranked_ids)} Kandidaten) - neuer Versuch beim nächsten Lauf")


def ai_refresh_models(best=False, verify_current=False):
    """best=False (Pruef-Thread, /update_models): nur reparieren, was tot ist.
    best=True (/update_models best): zusaetzlich auf das beste Modell wechseln, das die Pruefung besteht.
    verify_current=True: auch das gelistete Qwen-Modell per Mini-Aufruf pruefen. Groq und
    Nvidia werden immer mit einem Mini-Aufruf geprueft.
    Rueckgabe: {"changes": [...], "info": [...], "errors": [...]}"""
    out = {"changes": [], "info": [], "errors": []}
    if not _AI_RUN_LOCK.acquire(blocking=False):
        out["info"].append("Modell-Prüfung läuft bereits")
        return out
    try:
        updates = {}
        pinned = {x.strip().upper() for x in os.getenv("MODEL_AUTOUPDATE_PIN", "").split("#")[0].split(",") if x.strip()}
        _AI_HINT.clear()

        def _lauf(prov, ranked, by_id, **kw):
            ids = [m["id"] for m in ranked]
            if best and ids:
                out["info"].append(f"{_AI_LABEL[prov]}: beste Kandidaten: " + ", ".join(ids[:3]))
            with _ai_state_lock:
                _AI_BACKUPS[prov] = ids[:_AI_BACKUP_KEEP]
            new, info, err = _ai_heal(prov, by_id, ids, best, **kw)
            if err:
                out["errors"].append(err)
            elif info:
                (out["changes"] if new else out["info"]).append(info)
            if prov in _AI_HINT:
                out["errors"].append(f"{_AI_LABEL[prov]}: {_AI_HINT[prov]}")
            if new:
                updates[prov] = new

        def _aktiv(prov):
            if not [k for k in _AI_KEYS.get(prov, []) if k]:
                return False
            if _AI_GLOBAL[prov] in pinned or _AI_ENV_KEY[prov] in pinned:
                out["info"].append(f"{_AI_LABEL[prov]}: {ai_primary(prov) or '-'} - festgehalten (MODEL_AUTOUPDATE_PIN): bleibt")
                return False
            return True

        # ── Groq ──
        if _aktiv("groq"):
            try:
                cat = [m for m in _ai_catalog("groq") if m.get("id") and m.get("active", True) is not False]
                ranked = sorted((m for m in cat if not _AI_NON_CHAT_RE.search(m["id"])), key=_ai_model_rank, reverse=True)
                _lauf("groq", ranked, {m["id"]: m for m in cat}, paid_ok=False, verify=True)
            except Exception as e:
                out["errors"].append(f"{_AI_LABEL['groq']}: Modellliste nicht abrufbar: {str(e)[:100]}")

        # ── Qwen ueber OpenRouter: Gratis-Qwen zuerst, dann andere Gratis-Modelle ──
        if _aktiv("qwen"):
            if "openrouter.ai" not in QWEN_BASE_URL:
                out["info"].append("Qwen: QWEN_BASE_URL ist nicht OpenRouter - kein automatischer Wechsel")
            else:
                try:
                    cat = [m for m in _ai_catalog("qwen") if m.get("id")]
                    frei = sorted((m for m in cat if _ai_or_is_free(m) and _ai_or_is_text_chat(m)
                                   and not _ai_or_expires_soon(m)), key=_ai_model_rank, reverse=True)
                    ranked = [m for m in frei if "qwen" in m["id"].lower()] + [m for m in frei if "qwen" not in m["id"].lower()]
                    _lauf("qwen", ranked, {m["id"]: m for m in cat}, paid_ok=True, verify=verify_current, max_probes=5)
                except Exception as e:
                    out["errors"].append(f"{_AI_LABEL['qwen']}: Modellliste nicht abrufbar: {str(e)[:100]}")

        # ── Nvidia (die Liste fuehrt auch abgeschaltete Modelle -> immer pruefen) ──
        if _aktiv("nvidia"):
            try:
                cat = [m for m in _ai_catalog("nvidia") if m.get("id")]
                ranked = sorted((m for m in cat if not _AI_NON_CHAT_RE.search(m["id"])
                                 and not _AI_NVIDIA_NON_CHAT_RE.search(m["id"])),
                                key=lambda m: _ai_model_rank(m, cap=80), reverse=True)
                _lauf("nvidia", ranked, {m["id"]: m for m in cat}, paid_ok=False, verify=True, max_probes=6)
            except Exception as e:
                out["errors"].append(f"{_AI_LABEL['nvidia']}: Modellliste nicht abrufbar: {str(e)[:100]}")

        # ── Anwenden: erst .env (mit Rueckweg), dann die laufenden Werte ──
        if updates:
            env_werte = {}
            for p, v in updates.items():
                wert = v
                if _AI_ENV_KEY[p] == "NVIDIA_MODELS":      # Schreibweise "a->b->c": nur das erste ersetzen
                    rest = [x.strip() for x in os.getenv("NVIDIA_MODELS", "").split("#")[0].split("->")[1:]]
                    wert = "->".join([v] + [x for x in rest if x and x != v])
                env_werte[_AI_ENV_KEY[p]] = wert
            ok, msg = _ai_env_set_verified(env_werte)
            if not ok:
                out["errors"].append(f".env nicht geschrieben ({msg}) - das neue Modell gilt bis zum nächsten Neustart")
            for p, v in updates.items():
                os.environ[_AI_ENV_KEY[p]] = env_werte[_AI_ENV_KEY[p]]
                globals()[_AI_GLOBAL[p]] = v
            logging.info(f"[MODELUPDATE] Ersatz-KI gesetzt: {updates} | .env: {msg}")
        for line in out["changes"] + out["info"]:
            logging.info(f"[MODELUPDATE] Ersatz-KI: {line}")
        for line in out["errors"]:
            logging.warning(f"[MODELUPDATE] Ersatz-KI: {line}")
        with _ai_state_lock:
            _AI_LAST.update(zeit=time.time(), changes=list(out["changes"]), info=list(out["info"]), errors=list(out["errors"]))
        return out
    finally:
        _AI_RUN_LOCK.release()


def ai_status_text(res=None):
    """Stand der Ersatz-Anbieter fuer /update_models."""
    now = time.time()
    fmt = lambda ts: datetime.fromtimestamp(ts).strftime('%d.%m %H:%M')
    with _ai_state_lock:
        gesperrt = [(p, m, t + _AI_REJECT_TTL) for (p, m), t in _AI_REJECTED.items() if now - t < _AI_REJECT_TTL]
        backups = {p: list(v) for p, v in _AI_BACKUPS.items()}
        last = {k: (list(v) if isinstance(v, list) else v) for k, v in _AI_LAST.items()}
    res = res or last
    zeilen = ["🧩 ERSATZ-KI: MODELLE"]
    for p in _AI_PROVIDER:
        n = len([k for k in _AI_KEYS.get(p, []) if k])
        if not n:
            zeilen.append(f"{_AI_LABEL[p]}: kein Key in der .env - nicht benutzt")
            continue
        zeilen.append(f"{_AI_LABEL[p]}: {ai_primary(p) or '-'} (Keys: {n})")
        kette = ai_model_chain(p)
        if len(kette) > 1 or (kette and kette[0] != ai_primary(p)):
            zeilen.append("   Kette jetzt: " + " → ".join(kette))
        elif not backups.get(p):
            zeilen.append("   Ersatzmodelle: noch keine Liste abgerufen")
    if gesperrt:
        zeilen.append("Gesperrt für 24 h (antwortet nicht): "
                      + ", ".join(f"{_AI_LABEL[p]} {m} (bis {fmt(t)})" for p, m, t in gesperrt))
    if last.get("zeit"):
        zeilen.append(f"Letzte Prüfung: {fmt(last['zeit'])}")
    for titel, key in (("Geändert:", "changes"), ("Hinweise:", "info"), ("Probleme:", "errors")):
        if res.get(key):
            zeilen.append(titel)
            zeilen += [f"• {z}" for z in res[key]]
    return "\n".join(zeilen)


def _ai_modelupdate_loop():
    """Wie _model_autoupdate_loop in swarm.py: 75 s nach dem Start, dann alle
    MODEL_AUTOUPDATE_HOURS; ausser der Reihe, wenn ein Hauptmodell wegfaellt (entprellt, 5 Min)."""
    def _flag(name, default="true"):
        return os.getenv(name, default).split("#")[0].strip().lower() in ("1", "true", "yes", "on")
    if not _flag("MODEL_AUTOUPDATE"):
        return
    try:
        hours = float(os.getenv("MODEL_AUTOUPDATE_HOURS", "6").split("#")[0].strip())
    except ValueError:
        hours = 6.0
    interval = max(hours, 0.5) * 3600          # nie oefter als alle 30 Min
    logging.info(f"[MODELUPDATE] Ersatz-KI: Prüfung alle {interval / 3600:g} h und nach einem Modell-Ausfall")
    time.sleep(75)                             # Start nicht bremsen, nach dem Gemini-Abgleich
    forced = False
    while True:
        try:
            res = ai_refresh_models(best=False, verify_current=forced)
            if res["changes"] and _flag("MODEL_AUTOUPDATE_NOTIFY"):
                try:
                    bot.send_message(MY_CHAT_ID, "🔄 Ersatz-KI: Modell automatisch ersetzt\n"
                                     + "\n".join(f"• {z}" for z in res["changes"]))
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"[MODELUPDATE] Ersatz-KI: Lauf fehlgeschlagen: {e}")
        forced = _AI_HEAL_EVENT.wait(timeout=interval)       # True = Ausfall, False = Zeit um
        if forced:
            time.sleep(300)                                  # entprellen: eine Fehlerserie = ein Lauf
        _AI_HEAL_EVENT.clear()


# ============================================================
# UNIVERSELLER AI-CALLER — alle Provider nach PROVIDER_ORDER
# ============================================================
def call_ai(prompt: str, system: str = "", use_grounding: bool = False) -> str:
    """
    Ruft KI-Provider in der Reihenfolge aus PROVIDER_ORDER auf.
    Ollama-Priorität (OLLAMA_PRIORITY) wird berücksichtigt:
      first → Ollama zuerst, dann PROVIDER_ORDER
      last  → PROVIDER_ORDER, dann Ollama als letzter Fallback
      only  → nur Ollama

    Gemini: alle Keys × alle Modelle werden rotiert.
    Groq:   alle Keys werden rotiert.
    Qwen/Nvidia: OpenAI-kompatibler Endpunkt.

    Gibt immer einen String zurück (nie Exception nach außen).
    """
    system = lang_ai(system)  # v15.19
    import openai as _openai  # Für Qwen + Nvidia (OpenAI-kompatibel)

    def _try_ollama():
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": f"{system}\n\n{prompt}" if system else prompt,
                      "stream": False},
                timeout=60
            )
            if r.status_code == 200:
                result = r.json().get("response", "").strip()
                if result:
                    logging.info(f"[OK] Ollama ({OLLAMA_MODEL})")
                    return result
        except Exception as e:
            logging.warning(f"Ollama hata: {e}")
        return None

    def _try_gemini():
        # v15.15: gleiche Modell-Schleife wie die Hauptanalyse (Logik aus swarm.py)
        text = gemini_chain_generate(prompt, system or None)
        return text.strip() if text else None

    def _msgs():
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    # v15.22: Groq / Qwen / Nvidia laufen ueber die Modell-Kette (ai_chain_call, Logik aus
    # swarm.py): Key-Wechsel bei 401/429, Modell-Wechsel bei 404/410/5xx; ein totes Modell
    # wird 24 h gesperrt und vom Pruef-Thread ersetzt. Vorher: ein festes Modell je Anbieter.
    def _try_groq():
        def _einmal(key, model):
            import groq as _groq
            resp = _groq.Groq(api_key=key).chat.completions.create(
                model=model, messages=_msgs(), max_tokens=4096)
            return resp.choices[0].message.content
        return ai_chain_call("groq", _einmal)

    def _try_qwen():
        def _einmal(key, model):
            client = _openai.OpenAI(api_key=key, base_url=QWEN_BASE_URL)
            resp = client.chat.completions.create(model=model, messages=_msgs(), max_tokens=4096)
            return resp.choices[0].message.content
        return ai_chain_call("qwen", _einmal)

    def _try_nvidia():
        def _einmal(key, model):
            client = _openai.OpenAI(api_key=key, base_url=NVIDIA_BASE_URL)
            resp = client.chat.completions.create(model=model, messages=_msgs(), max_tokens=4096)
            return resp.choices[0].message.content
        return ai_chain_call("nvidia", _einmal)

    PROVIDER_FN = {
        "gemini": _try_gemini,
        "groq":   _try_groq,
        "qwen":   _try_qwen,
        "nvidia": _try_nvidia,
    }

    # Ollama first
    if OLLAMA_PRIORITY == "only":
        return _try_ollama() or "⚠️ Ollama yanıt vermedi."
    if OLLAMA_PRIORITY == "first":
        result = _try_ollama()
        if result:
            return result

    # Provider-Reihenfolge aus .env
    for provider in PROVIDER_ORDER:
        fn = PROVIDER_FN.get(provider.lower())
        if fn:
            result = fn()
            if result:
                return result

    # Ollama last
    if OLLAMA_PRIORITY == "last":
        result = _try_ollama()
        if result:
            return result

    logging.error("Tüm AI provider başarısız!")
    return "⚠️ Tüm AI sağlayıcılar şu an kullanılamıyor. Lütfen daha sonra tekrar dene."


# ============================================================
# NEXUS NATURE LAYER v12.0
# ============================================================

# --- SQLite DB ---
db_lock = threading.Lock()

def init_db():
    """Alle Tabellen anlegen."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode=WAL")    # v14.9: Concurrent reads
        conn.execute("PRAGMA synchronous=NORMAL")  # v14.9: Performance
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
    """Asset-Performance fuer Gemini."""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        rows = conn.execute("""SELECT symbol,win_rate_overall,win_rate_weekend,
            total_trades,total_pnl,loss_streak_current,gemini_notes
            FROM asset_learnings ORDER BY total_pnl DESC""").fetchall()
        conn.close()
    if not rows:
        return "Henuz asset istatistigi yok."
    lines = []
    for sym,wr,wer,tot,pnl,ls,notes in rows:
        warn = " KAYIP SERISI!" if (ls and ls >= 2) else ""
        lines.append(f"  {sym}: Win%={wr:.0%} HaftasonuWin%={wer:.0%} ({tot}t) PnL:{pnl:.2f}EUR{warn}")
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
            with _api_cache_lock:
                already_sent = cache_key in _api_cache
            if not already_sent:
                try:
                    msg = (f"GDACS KRİTİK UYARI!\n"
                           f"Tip: {alert['type']} | Büyüklük:{alert['mag']}\n"
                           f"Konum: {alert['title']}\n"
                           f"Etkilenen Assetler: {', '.join(alert['assets']) or 'Belirsiz'}")
                    bot.send_message(MY_CHAT_ID, msg)
                    with _api_cache_lock:
                        _api_cache[cache_key] = (time.time(), True)
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
    wx_alerts = wx_glob.get("alerts", [])
    L += [f"KURESEL EMTIA HAVA: {len(wx_alerts)} uyari"]
    for alert in wx_alerts[:4]:
        L.append(f"  {alert}")

    # USGS/ReliefWeb Dogal Afet (GDACS'tan ayri, ikinci kaynak)
    L.append(f"USGS/ReliefWeb AFET: {disaster.get('signal','?')} | {disaster.get('notes','?')}")

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

    # 6. EIA Petroleum (v14.8)
    try:
        eia = get_eia_petroleum()
        L.append(f"EIA PETROL DEPOLARI: {eia.get('summary', 'N/A')}")
    except Exception as _e:
        L.append(f"EIA PETROL DEPOLARI: Fehler {_e}")
    L.append("")

    # 7. CFTC COT Report (v14.8)
    try:
        cot_gold = get_cot_positioning("GOLD")
        cot_oil  = get_cot_positioning("OIL")
        L.append(f"CFTC COT GOLD: {cot_gold.get('summary', 'N/A')}")
        L.append(f"CFTC COT OIL:  {cot_oil.get('summary', 'N/A')}")
    except Exception as _e:
        L.append(f"CFTC COT: Fehler {_e}")
    L.append("")

    # 8. USDA WASDE (v14.8)
    try:
        usda_cocoa  = get_usda_supply_demand("Cocoa")
        usda_coffee = get_usda_supply_demand("Coffee")
        usda_wheat  = get_usda_supply_demand("Wheat")
        L.append(f"USDA COCOA:  {usda_cocoa.get('summary', 'N/A')}")
        L.append(f"USDA COFFEE: {usda_coffee.get('summary', 'N/A')}")
        L.append(f"USDA WHEAT:  {usda_wheat.get('summary', 'N/A')}")
    except Exception as _e:
        L.append(f"USDA WASDE: Fehler {_e}")
    L.append("")

    # 9. Transport CO2 / LKW-Aktivität (v14.8)
    try:
        transport = get_transport_activity()
        L.append(f"TRANSPORT/LKW-AKTIVITAET: {transport.get('summary', 'N/A')}")
    except Exception as _e:
        L.append(f"TRANSPORT/LKW: Fehler {_e}")
    L.append("")

    # Sinyal ozeti (erweitert)
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
        "  EIA Lager>+10% = BEARISH OIL | EIA Lager<-10% = BULLISH OIL",
        "  COT Spek.ExtremLong Gold = Contrarian SELL | ExtremShort = Contrarian BUY",
        "  USDA Ending Stocks -15% = BULLISH Agrar | +15% = BEARISH Agrar",
        "  LKW-Aktivitaet +8% YoY = BULLISH Kupfer/Oel | -8% = BEARISH (Rezession)",
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

def get_macro_regime(fg_val, vol_regime):
    # EXTREME Spreads + Extreme Fear = echtes RISK_OFF_EXTREME
    if vol_regime == "EXTREME" and fg_val < 25:
        return "RISK_OFF_EXTREME"
    # Nur hohe Spreads → HIGH_SPREAD (handeln erlaubt mit Asset-Filter)
    if vol_regime == "EXTREME":
        return "RISK_OFF_SPREAD"
    # Nur Extreme Fear ohne hohe Spreads → RISK_OFF_FEAR
    if fg_val >= 75:   return "RISK_ON_GREEDY"
    elif fg_val >= 55: return "RISK_ON"
    elif fg_val >= 45: return "NEUTRAL"
    elif fg_val >= 25: return "RISK_OFF"
    else:              return "RISK_OFF_FEAR"  # Fear<25, spreads normal

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
# JIM ROGERS FILTER - v12.0
# Antizyklisch: EMA50/200 Ausbruch aus Seitwärtsphase
# ============================================================
def check_jim_rogers_setup(candles_dict):
    """
    Rogers-Logik für Stage 1:
    1. Lange Seitwärtsphase: BB-Squeeze (Bandwidth < 0.04, 30 Kerzen)
       UND EMA50 ≈ EMA200 (Abstand < 2%)
    2. Ausbruch: Close kreuzt EMA50 von unten (BUY) oder oben (SELL)
    3. Historisch günstig: Close < EMA200 * 1.05 (BUY) oder > EMA200 * 0.95 (SELL)

    Gibt (bool, signal, reason) zurück.
    """
    closes = candles_dict.get('close', [])
    if len(closes) < 205:
        return False, "NOTR", "Veri yetersiz (Rogers EMA200 icin min 205 mum)"

    import statistics

    # --- EMA Hesaplama ---
    def ema(data, span):
        k = 2 / (span + 1)
        result = [data[0]]
        for p in data[1:]:
            result.append(p * k + result[-1] * (1 - k))
        return result

    ema50_series  = ema(closes, 50)
    ema200_series = ema(closes, 200)
    sma20_series  = [sum(closes[i-20:i])/20 for i in range(20, len(closes))]

    if len(sma20_series) < 32:
        return False, "NOTR", "SMA20 verisi yetersiz"

    latest_close  = closes[-1]
    prev_close    = closes[-2]
    latest_ema50  = ema50_series[-1]
    prev_ema50    = ema50_series[-2]
    latest_ema200 = ema200_series[-1]

    # --- Bollinger Bandwidth (son 30 mum) ---
    bb_widths = []
    for i in range(max(0, len(sma20_series)-30), len(sma20_series)):
        sma = sma20_series[i]
        window_closes = closes[i:i+20] if i+20 <= len(closes) else closes[i:]
        if len(window_closes) < 5:
            continue
        std = statistics.stdev(window_closes)
        bw = (std * 4) / sma if sma > 0 else 999
        bb_widths.append(bw)

    if not bb_widths:
        return False, "NOTR", "BB Bandwidth hesaplanamadı"

    avg_bandwidth = sum(bb_widths) / len(bb_widths)

    # --- EMA50 / EMA200 Yakınlık ---
    ema_distance_pct = abs(latest_ema50 - latest_ema200) / latest_ema200 * 100 if latest_ema200 > 0 else 999

    # --- Check 1: Seitwärtsphase ---
    was_sideways = avg_bandwidth < 0.04 and ema_distance_pct < 2.0

    # --- Check 2: Ausbruch ---
    buy_breakout  = prev_close <= prev_ema50 and latest_close > latest_ema50
    sell_breakout = prev_close >= prev_ema50 and latest_close < latest_ema50

    # --- Check 3: Historisch günstig/teuer ---
    is_cheap     = latest_close < latest_ema200 * 1.05   # BUY için
    is_expensive = latest_close > latest_ema200 * 0.95   # SELL için

    reason_parts = [
        f"BB_BW:{avg_bandwidth:.4f}",
        f"EMA_DIST:{ema_distance_pct:.1f}%",
        f"Sideways:{was_sideways}",
    ]

    if was_sideways and buy_breakout and is_cheap:
        return True, "BUY", "ROGERS_BUY: " + " | ".join(reason_parts)
    if was_sideways and sell_breakout and is_expensive:
        return True, "SELL", "ROGERS_SELL: " + " | ".join(reason_parts)

    return False, "NOTR", "Rogers koşulları sağlanmadı: " + " | ".join(reason_parts)


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
    resolution = "DAY"
    data, _err = get_candles(epic, resolution, 210)  # 55 mum: Fib icin yeterli

    # None-Check nach get_candles Fix v14.2
    if data is None:
        return {
            "score": 0, "max_score": 5, "signal": "NOTR",
            "details": f"API verisi alinamadi ({_err or 'None'})",
            "bollinger": None, "fibonacci": None,
            "passed": False
        }

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
    adx_ok = adx > 15  # v12.1: 20→15 (sakin piyasada da sinyal üretsin)
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
    # v12.1: MIDDLE da puan alır. Sadece tam ters konumda (BUY+NEAR_UPPER veya SELL+NEAR_LOWER) = 0
    boll = berechne_bollinger(closes, period=20)
    boll_ok = False
    if boll:
        boll_bad = (signal == "BUY"  and boll["position"] == "NEAR_UPPER") or \
                   (signal == "SELL" and boll["position"] == "NEAR_LOWER")
        boll_ok = not boll_bad
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
        if fib["nearest_level"] in key_levels and fib["distance_pct"] <= 3.0:  # v12.1: 1.5→3.0%
            fib_ok = True
        if fib_ok:
            score += 1
            details.append(f"FIB:{fib['nearest_level']}@{fib['distance_pct']:.1f}%(+1)")
        else:
            details.append(f"FIB:{fib['nearest_level']}@{fib['distance_pct']:.1f}%(0)")
    else:
        details.append("FIB:NODATA(0)")

    # --- 6. Jim Rogers Filter (Bonus Punkt) ---
    # EMA50/200 Squeeze Ausbruch - nur für Nicht-Krypto (Rohstoffe, Forex)
    rogers_bonus = False
    rogers_reason = ""
    if not is_crypto(epic):
        # Mehr Kerzen für EMA200 holen (205 benötigt)
        data_rogers, _err_r = get_candles(epic, resolution, 210)
        if data_rogers is None:
            rogers_ok, rogers_sig, rogers_reason = False, "NOTR", f"Veri yok ({_err_r or '-'})"
        else:
            rogers_ok, rogers_sig, rogers_reason = check_jim_rogers_setup(data_rogers)
        if rogers_ok and rogers_sig == signal:
            rogers_bonus = True
            score += 1
            details.append(f"ROGERS:JA(+1)")
        else:
            details.append(f"ROGERS:NEIN(0)")
    else:
        details.append("ROGERS:N/A(Kripto)")

    # --- Gate-Keeper Esigi ---
    # Normal: 3/6 | Krypto Haftasonu/Gece: 4/5 (Rogers N/A)
    saat = datetime.now().hour
    gece = saat >= 23 or saat < 6
    max_score = 6 if not is_crypto(epic) else 5
    if is_crypto(epic) and (is_weekend() or gece):
        threshold = 5  # v15.0
    else:
        threshold = 5  # v15.0

    passed = (score >= threshold) and (signal != "NOTR")

    # ── GREMIUM ABSTIMMUNG (5 Mentoren) ─────────────────────────────────
    # Verbindung: berechne_signal_score → gremium_oylama → passed
    gremium_karar  = False
    gremium_ja_cnt = 0
    gremium_oylar  = {}
    gremium_grunler = {}
    try:
        # news_sentiment: letzte 3 Tage aus DB
        _ns = 0.0
        try:
            with db_lock:
                _conn = sqlite3.connect(DB_FILE)
                _row  = _conn.execute(
                    "SELECT AVG(sentiment) FROM news_cache "
                    "WHERE published_at >= date('now','-3 days')"
                ).fetchone()
                _conn.close()
                if _row and _row[0] is not None:
                    _ns = float(_row[0])
        except Exception: pass

        # FRED Signal
        _fred_sig = "NEUTRAL"
        try:
            _fm = get_fred_macro_signal()
            if isinstance(_fm, dict):
                _fred_sig = _fm.get("signal", "NEUTRAL")
        except Exception: pass

        # Makro-Regime
        _macro = globals().get("macro_regime", "NEUTRAL")

        # UPL aus laufenden Positionen
        _upl = 0.0
        try:
            _h = capital_session.get_headers()
            if _h:
                _poz = get_positions(_h)
                _upl = sum(float(p.get("position", {}).get("upl", 0) or 0) for p in _poz)
        except Exception: pass

        # Gremium aufrufen
        gremium_karar, gremium_ja_cnt, _gnein, gremium_oylar, gremium_grunler = gremium_oylama(
            sinyal=signal,
            guc=sum(1 for d in details if "(+1)" in d),
            sym_key=sym,
            instrument={"rogers_bonus": rogers_bonus},
            upl_toplam=_upl,
            saat=datetime.now().hour,
            macro_regime=_macro,
            news_sentiment=_ns,
            fred_signal=_fred_sig,
        )
        logging.info(
            f"GREMIUM {sym}: {gremium_ja_cnt}/5 JA | "
            f"{'GEÇTI' if gremium_karar else 'BLOK'} | "
            + " | ".join(f"{m.split('_')[0]}:{v}" for m, v in gremium_oylar.items())
        )
    except Exception as _ge:
        logging.warning(f"Gremium {sym}: {_ge}")

    return {
        "score":            score,
        "max_score":        max_score,
        "signal":           signal,
        "threshold":        threshold,
        "passed":           passed and gremium_karar,  # beide müssen durch
        "passed_gate":      passed,           # nur technisch
        "gremium_passed":   gremium_karar,    # nur Gremium
        "gremium_ja":       gremium_ja_cnt,
        "gremium_oylar":    gremium_oylar,
        "gremium_grunler":  gremium_grunler,
        "news_sentiment":   _ns,
        "details":          " | ".join(details),
        "adx":              adx,
        "rsi":              rsi,
        "bollinger":        boll,
        "fibonacci":        fib,
        "rogers_bonus":     rogers_bonus,
        "rogers_reason":    rogers_reason,
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
DEPOT_DD_LIMIT = -5.0   # % - Tageshöchststand Limit (eski: -10, yeni: -5)
MAX_DAILY_LOSS_EUR = -40.0  # Sabit EUR limiti - bu asilinca trading dur
depot_dd_lock  = threading.Lock()

def _load_dd_tracker():
    try:
        if os.path.exists(DEPOT_DD_FILE):
            with open(DEPOT_DD_FILE, 'r') as f:
                data = json.load(f)
            if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return data
    except: pass
    return {"date": datetime.now().strftime("%Y-%m-%d"),
            "peak_value": 0.0, "trading_halt": False, "halt_reason": ""}

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
# v15.19: SPRACHE (Deutsch / English / Türkçe) + ZUGRIFFSSCHUTZ
# ------------------------------------------------------------
# - Die Texte stehen in nexus_lang.py (neben dieser Datei). Jede Telegram-Nachricht
#   wird erst beim SENDEN uebersetzt; die Handelslogik arbeitet mit den Originaltexten.
# - .env: BOT_LANGUAGE=de | en | tr   (leer = der Bot fragt beim Start per Telegram;
#   orig = nie uebersetzen)
# - Befehle und Tasten nimmt der Bot nur noch aus dem Chat MY_CHAT_ID an. Vorher
#   pruefte das nur ein Teil der Befehle - wer den Bot-Namen kannte, konnte z.B.
#   /kapat oder /manuell schicken.
# ============================================================
try:
    import nexus_lang as _NL
except Exception as _nl_e:
    _NL = None
    logging.warning(f"nexus_lang.py nicht geladen ({_nl_e}) - der Bot sendet die Originaltexte")

BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "").split("#")[0].strip().lower()


def lang_aktiv():
    return _NL is not None and BOT_LANGUAGE in ("de", "en", "tr")


def L(text):
    """Text in die gewaehlte Sprache uebersetzen (ohne Sprache oder bei Fehler: unveraendert)."""
    if not lang_aktiv() or not isinstance(text, str):
        return text
    try:
        return _NL.translate(text, BOT_LANGUAGE)
    except Exception as _e:
        logging.debug(f"Uebersetzung: {_e}")
        return text


def lang_ai(system):
    """KI-Anweisung um die Antwortsprache ergaenzen."""
    if not lang_aktiv():
        return system
    return (system or "") + _NL.ai_hint(BOT_LANGUAGE)


def CMD(name):
    """Alle Namen eines Befehls, z.B. kapat -> ['kapat', 'schliessen', 'close']."""
    return _NL.command_names(name) if _NL else [name]


_bot_send_raw = bot.send_message            # ohne Uebersetzung (Sprachwahl)
_bot_edit_raw = bot.edit_message_text


def _send_uebersetzt(chat_id, text=None, *a, **k):
    text = L(text)
    if isinstance(text, str) and len(text) > 4096:
        # Telegram nimmt hoechstens 4096 Zeichen - an Zeilengrenzen teilen statt die Nachricht zu verlieren
        teile, akt = [], ""
        for zeile in text.split("\n"):
            while len(zeile) > 4000:
                if akt:
                    teile.append(akt); akt = ""
                teile.append(zeile[:4000]); zeile = zeile[4000:]
            if len(akt) + len(zeile) + 1 > 4000:
                teile.append(akt); akt = zeile
            else:
                akt = zeile if not akt else akt + "\n" + zeile
        if akt:
            teile.append(akt)
        res = None
        for i, t in enumerate(teile):
            res = _bot_send_raw(chat_id, t, *a, **(k if i == len(teile) - 1 else {}))
        return res
    return _bot_send_raw(chat_id, text, *a, **k)


def _lang_wrap(fn, pos):
    def wrapper(*a, **k):
        a = list(a)
        if len(a) > pos:
            a[pos] = L(a[pos])
        elif "text" in k:
            k["text"] = L(k["text"])
        return fn(*a, **k)
    return wrapper


bot.send_message = _send_uebersetzt
bot.reply_to = _lang_wrap(bot.reply_to, 1)
bot.edit_message_text = _lang_wrap(bot.edit_message_text, 0)
bot.answer_callback_query = _lang_wrap(bot.answer_callback_query, 1)

# --- Zugriffsschutz: Befehle, Text und Tasten nur aus dem eigenen Chat ---
_bot_message_handler_raw = bot.message_handler
_bot_callback_handler_raw = bot.callback_query_handler


def _ist_besitzer(chat_id):
    return bool(MY_CHAT_ID) and str(chat_id) == str(MY_CHAT_ID)


def _message_handler_nur_besitzer(*a, **k):
    eigen = k.get("func")
    k["func"] = lambda m: _ist_besitzer(getattr(getattr(m, "chat", None), "id", None)) and (eigen(m) if eigen else True)
    return _bot_message_handler_raw(*a, **k)


def _callback_handler_nur_besitzer(*a, **k):
    eigen = k.get("func")
    k["func"] = lambda c: (_ist_besitzer(getattr(getattr(getattr(c, "message", None), "chat", None), "id", None))
                           and (eigen(c) if eigen else True))
    return _bot_callback_handler_raw(*a, **k)


bot.message_handler = _message_handler_nur_besitzer
bot.callback_query_handler = _callback_handler_nur_besitzer

if not MY_CHAT_ID:
    # Erste Einrichtung: Ohne MY_CHAT_ID weiss der Bot nicht, wem er gehoert. Er nennt
    # jedem, der ihm schreibt, nur dessen EIGENE Chat-ID - sonst tut er nichts.
    @_bot_message_handler_raw(func=lambda m: True)
    def _einrichtung_chat_id(message):
        try:
            _bot_send_raw(message.chat.id,
                          f"🆔 Chat-ID: {message.chat.id}\n\n"
                          f"DE: Trage MY_CHAT_ID={message.chat.id} in die .env ein und starte den Bot neu.\n"
                          f"EN: Put MY_CHAT_ID={message.chat.id} into the .env file and restart the bot.\n"
                          f"TR: .env dosyasına MY_CHAT_ID={message.chat.id} yaz ve botu yeniden başlat.")
        except Exception as _e:
            logging.warning(f"Einrichtung Chat-ID: {_e}")


_ENV_WRITE_LOCK = threading.RLock()   # v15.22: ein Schreiber an der .env zur Zeit (Sprachwahl, Modellwechsel)


def env_set(name, value):
    """v15.22: nie gleichzeitig mit dem automatischen Modellwechsel in die .env schreiben."""
    with _ENV_WRITE_LOCK:
        return _env_set_roh(name, value)


def _env_set_roh(name, value):
    """Einen Eintrag in der .env setzen: vorhandene Zeile ersetzen, sonst anhaengen.
    Rueckgabe: (ok, fehlertext). Schreibt erst in eine Nebendatei und tauscht dann."""
    path = os.path.join(BASE_DIR, ".env")
    try:
        zeilen = open(path, encoding="utf-8").read().split("\n") if os.path.exists(path) else []
        neu, gesetzt = [], False
        for z in zeilen:
            if re.match(r"\s*" + re.escape(name) + r"\s*=", z):
                if not gesetzt:
                    neu.append(f"{name}={value}")
                    gesetzt = True
                continue                      # doppelte Eintraege desselben Namens entfallen
            neu.append(z)
        if not gesetzt:
            while neu and not neu[-1].strip():
                neu.pop()
            neu += ["", "# Bot language: de, en or tr (set via Telegram: /language, /sprache, /dil)", f"{name}={value}"]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(neu).rstrip("\n") + "\n")
        try:
            os.chmod(tmp, os.stat(path).st_mode if os.path.exists(path) else 0o600)
        except Exception:
            pass
        os.replace(tmp, path)
        return True, ""
    except Exception as e:
        logging.error(f".env schreiben ({name}): {e}")
        return False, str(e)


def language_chooser_markup():
    mk = telebot.types.InlineKeyboardMarkup()
    mk.row(*[telebot.types.InlineKeyboardButton(_NL.LANG_NAMES[c], callback_data=f"lang_pick_{c}") for c in _NL.LANGS])
    return mk


def send_language_chooser():
    """Sprachwahl schicken (dreisprachig, drei Tasten)."""
    if _NL is None:
        return False
    try:
        _bot_send_raw(MY_CHAT_ID, _NL.UI["choose"], reply_markup=language_chooser_markup())
        return True
    except Exception as e:
        logging.warning(f"Sprachwahl: {e}")
        return False


def apply_language_ui(mit_tasten=True):
    """Telegram-Menue (Befehlsliste) und Tasten auf die gewaehlte Sprache stellen."""
    if not lang_aktiv():
        return
    try:
        from telebot.types import BotCommand
        bot.set_my_commands([BotCommand(n, d[:256]) for n, d in _NL.menu_commands(BOT_LANGUAGE)])
    except Exception as e:
        logging.warning(f"Befehlsmenue ({BOT_LANGUAGE}): {e}")
    if mit_tasten:
        try:
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            for reihe in _NL.BUTTONS[BOT_LANGUAGE]:
                kb.row(*[telebot.types.KeyboardButton(t) for t in reihe])
            _bot_send_raw(MY_CHAT_ID, _NL.UI["keyboard"][BOT_LANGUAGE], reply_markup=kb)
        except Exception as e:
            logging.warning(f"Tasten ({BOT_LANGUAGE}): {e}")


def set_language(code):
    """Sprache setzen: fuer diese Sitzung und in der .env. Rueckgabe: Meldungstext."""
    global BOT_LANGUAGE
    BOT_LANGUAGE = code
    os.environ["BOT_LANGUAGE"] = code
    ok, fehler = env_set("BOT_LANGUAGE", code)
    logging.info(f"Sprache gesetzt: {code} (.env geschrieben: {ok})")
    return _NL.UI["saved"][code] if ok else _NL.UI["not_saved"][code].format(fehler)

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
    def __init__(self):
        self.cst = None
        self.token = None
        self.expires = 0
        self.lock = threading.Lock()

    def get_headers(self):
        with self.lock:
            if time.time() < self.expires and self.cst:
                return {
                    "X-CAP-API-KEY": CAP_KEY,
                    "CST": self.cst,
                    "X-SECURITY-TOKEN": self.token,
                    "Content-Type": "application/json"
                }
            try:
                r = requests.post(
                    f"{CAPITAL_URL}/session",
                    json={"identifier": CAP_ID, "password": CAP_PW},
                    headers={"X-CAP-API-KEY": CAP_KEY},
                    timeout=15
                )
                if r.status_code == 200:
                    self.cst = r.headers.get("CST")
                    self.token = r.headers.get("X-SECURITY-TOKEN")
                    self.expires = time.time() + 1200
                    logging.info("✅ Neue Session erstellt")
                    return {
                        "X-CAP-API-KEY": CAP_KEY,
                        "CST": self.cst,
                        "X-SECURITY-TOKEN": self.token,
                        "Content-Type": "application/json"
                    }
            except Exception as e:
                logging.error(f"Session hatasi: {e}")
            return None

capital_session = CapitalSession()

def safe_trade_size(size_eur_input, cfg, epic, is_manual=False):
    """
    BRIDGEWATER RETAIL EDITION (Risk Parity für <2000€ ohne Leverage):
    1. Basis: 5% des Depots, mindestens 50€.
    2. Risk-Parity Cap: Position darf im Worst-Case (SL) max 2% des Gesamtdepots kosten.
    3. Volatilitäts-Check: Bei hoher Volatilität (Krypto) wird die Größe halbiert.
    """
    # v15.10: AUTO-Trades schlagen "geschlossen" fehl (0 = kein Trade).
    # Manuelle Trades behalten das bisherige Verhalten (min_size).
    _fehler_size = cfg.get("min_size", 0.01) if is_manual else 0
    try:
        size_eur = float(size_eur_input)
    except Exception:
        return _fehler_size

    try:
        h = capital_session.get_headers()
        if not h: return _fehler_size

        r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=10)
        if r.status_code != 200: return _fehler_size
        
        snap = r.json().get("snapshot", {})
        bid = float(snap.get("bid", 0) or 0)
        offer = float(snap.get("offer", 0) or 0)
        price = (bid + offer) / 2 if bid and offer else max(bid, offer)
        if price <= 0: return _fehler_size

        # --- BRIDGEWATER LOGIK ---
        # Hole aktuelles Depot (Fallback 1000€)
        acc = get_account_info(h) or {}
        balance = float(acc.get("toplam", acc.get("balance", 1000.0)))
        min_eur = float(os.getenv("MIN_POSITION_EUR", "50.0"))

        if is_manual:
            # ✅ MANUELL: Benutzereingabe respektieren, nur Sicherheitslimits prüfen
            final_eur = size_eur
            # Mindestbetrag
            if final_eur < min_eur:
                logging.warning(f"Manuell {epic}: {final_eur}€ unter MIN_POSITION_EUR {min_eur}€ → wird angehoben")
                final_eur = min_eur
            # Hard Cap 50% des Depots
            cap_50 = balance * 0.50
            if final_eur > cap_50:
                logging.warning(f"Manuell {epic}: {final_eur}€ > 50% Depot ({cap_50:.2f}€) → wird begrenzt")
                final_eur = cap_50
            # Risk-Parity Warnung (kein hartes Limit bei manuell)
            max_risk_warn = (balance * 0.02) / 0.03
            if final_eur > max_risk_warn:
                logging.warning(f"Manuell {epic}: {final_eur}€ überschreitet Risk-Parity Empfehlung ({max_risk_warn:.2f}€)")
        else:
            # 🔁 AUTOMATISCH: Berechnung aus .env
            pos_pct = float(os.getenv("POSITION_SIZE_PCT", "10.0"))
            base_eur = max(min_eur, balance * (pos_pct / 100.0))
            # Risk-Parity Cap: Max 2% Depot-Risiko bei geschätztem 3% SL-Abstand
            max_risk_eur = balance * 0.02
            estimated_sl_distance = 0.03
            max_position_eur = max_risk_eur / estimated_sl_distance
            # Hard Cap: Nie mehr als 50% des Depots in einem Trade
            # oder User-definiertes MAX_POSITION_EUR aus .env
            max_pos_env = os.getenv("MAX_POSITION_EUR", "").strip()
            if max_pos_env:
                try:
                    max_position_eur_env = float(max_pos_env)
                    max_position_eur = min(max_position_eur, max_position_eur_env)
                except:
                    pass  # Invalid env value, use Risk-Parity cap
            final_eur = min(base_eur, max_position_eur, balance * 0.50)
            # v15.10: Obergrenze merken (Mindestgroessen-Pruefung weiter unten)
            limit_eur = min(max_position_eur, balance * 0.50)

        # 4. Volatilitäts-Check (Risk Parity)
        is_crypto = _krypto_kuerzel(epic) in ("BTC", "ETH", "SOL", "XRP")  # v15.24: GASOLINE ist kein SOL
        if is_crypto:
            final_eur *= 0.5  # Halbierung bei Krypto für gleiche Risiko-Wichtung

        # In Units umrechnen
        eur_usd = 1.08
        try:
            fx = requests.get(f"{CAPITAL_URL}/markets/EURUSD", headers=h, timeout=5).json()
            fxb = float(fx.get("snapshot", {}).get("bid", 0) or 0)
            if fxb > 0: eur_usd = fxb
        except: pass
        
        # v15.10: EUR-notierte Epics (z.B. ETHEUR) nicht durch EURUSD teilen
        price_eur = price if epic.upper().endswith("EUR") else price / eur_usd
        units = final_eur / price_eur
        min_size = cfg.get("min_size", 0.01)
        if not is_manual and units < min_size:
            # v15.10: Die Mindestgroesse der Boerse darf die .env-Limits
            # (MAX_POSITION_EUR / Risk-Parity / 50% Depot) nicht aushebeln.
            min_kosten_eur = min_size * price_eur
            if min_kosten_eur > limit_eur:
                logging.warning(
                    f"AUTO-SIZE {epic}: Mindestgroesse {min_size} kostet {min_kosten_eur:.2f}€ "
                    f"> Limit {limit_eur:.2f}€ (.env) -> KEIN TRADE")
                return 0
        units = max(round(units, 6), min_size)
        
        trade_type_str = "MANUELL" if is_manual else "AUTO"
        logging.info(f"{trade_type_str}-SIZE {epic}: {final_eur:.2f}€ -> {units:.4f} units (MIN:{min_eur}€)")
        return units
    except Exception as e:
        logging.warning(f"safe_trade_size Fehler {epic}: {e}")
        return _fehler_size

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
        acc = acc_req['accounts'][0]
        return {
            "nakit": acc['balance'].get('balance', 0),
            "toplam": acc['balance'].get('deposit', 0),
            "upl": acc['balance'].get('profitLoss', 0),
            "marjin": 0,  # Kaldıraç devre dışı - marjin kullanılmıyor
            "musait": acc['balance'].get('available', 0)
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

# v15.13: Capital.com kennt nur MINUTE, MINUTE_5, MINUTE_15, MINUTE_30, HOUR,
# HOUR_4, DAY, WEEK. Andere Kerzen werden aus kleineren zusammengesetzt:
#   gewuenscht -> (echte API-Aufloesung, Anzahl Kerzen pro Buendel)
CANDLE_BUNDLE = {
    "MINUTE_20": ("MINUTE_5", 4),
    "MINUTE_45": ("MINUTE_15", 3),
    "HOUR_2":    ("HOUR", 2),
    "HOUR_1":    ("HOUR", 1),
}
_candle_fehler_gemeldet = set()


def _bundle_candles(closes, highs, lows, n):
    """n kleine Kerzen zu einer grossen zusammenfassen (vom neuesten Ende her)."""
    m = min(len(closes), len(highs), len(lows))
    if m == 0:
        return [], [], []
    closes, highs, lows = closes[-m:], highs[-m:], lows[-m:]
    c2, h2, l2 = [], [], []
    for ende in range(m, 0, -n):
        start = ende - n
        if start < 0:
            break  # unvollstaendiges aeltestes Buendel weglassen
        c2.append(closes[ende - 1])
        h2.append(max(highs[start:ende]))
        l2.append(min(lows[start:ende]))
    c2.reverse(); h2.reverse(); l2.reverse()
    return c2, h2, l2


def get_candles(epic, resolution, max_candles=30):
    h = capital_session.get_headers()
    if not h:
        return None, "Session yok (oturum kapali)"  # Fix v15.6: reason tuple
    try:
        api_res, bundle = CANDLE_BUNDLE.get(resolution, (resolution, 1))  # v15.13
        url = f"{CAPITAL_URL}/prices/{epic}?resolution={api_res}&max={min(max_candles * bundle, 1000)}"
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
            if bundle > 1:  # v15.13: z.B. 4 x 5 Min -> 20 Min
                closes, highs, lows = _bundle_candles(closes, highs, lows, bundle)
            return {'close': closes, 'high': highs, 'low': lows}, None
        else:
            # v15.13: Fehler sichtbar machen (je Aufloesung + Status nur einmal pro Lauf)
            if (resolution, r.status_code) not in _candle_fehler_gemeldet:
                _candle_fehler_gemeldet.add((resolution, r.status_code))
                logging.warning(f"Kursdaten {epic}/{resolution}: API {r.status_code} {r.text[:120]}")
            return None, f"API {r.status_code}"
    except Exception as e:
        logging.warning(f"Mum verisi alinamadi {epic}/{resolution}: {e}")
        return None, f"Hata: {str(e)[:40]}"

# ============================================================
# 2-of-3 TEKNİK KONTROL (MA + ADX + RSI) - BUGFIX
# ============================================================
def _analyse_timeframe(epic, resolution, max_candles=30):
    """Tek bir timeframe için MA/ADX/RSI analizi. (sinyal, guc, detay) döner."""
    data, err = get_candles(epic, resolution, max_candles)
    if data is None:
        neden = err if err else "Veri yok"
        return "NOTR", 0, f"⚠️ {neden}"
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
        sinyal, guc, details = _analyse_timeframe(epic, "DAY", 30)
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

        logging.info(f"[OK] Spreads in capital_markets_config.py aktualisiert ({len(spread_data)} Assets)")
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
    if MAX_SPREAD is not None and spread > MAX_SPREAD: return False, f"Spread çok yüksek: {spread}"
    return True, "OK"

def is_weekend():
    return datetime.now().weekday() >= 5

# v15.24: Vorher wurde nach Teilwoertern gesucht - "GASOLINE" enthaelt "SOL" und galt als
# Krypto (Gremium 3/5 statt 4/5, Wochenend-Scan, Krypto-Halbierung). Jetzt zaehlt nur das
# Basis-Kuerzel vor _USD/_EUR bzw. vor USD/EUR im Epic. Die Liste der Coins ist dieselbe wie vorher.
_KRYPTO_BASIS = {"BTC", "ETH", "XRP", "SOL", "LTC", "ADA", "DOT", "LINK", "DOGE", "AVAX",
                 "MATIC", "BNB", "SHIB", "UNI", "ATOM"}


def _krypto_kuerzel(name):
    """Basis-Kuerzel eines Symbols/Epics: BTC_USD -> BTC, ETHEUR -> ETH, GASOLINE -> GASOLINE."""
    basis = str(name or "").upper().replace("-", "_").replace("/", "_").split("_")[0]
    for q in ("USDT", "USD", "EUR", "GBP"):
        if basis.endswith(q) and len(basis) > len(q):
            return basis[:-len(q)]
    return basis


def is_crypto(sym_key):
    """Prueft ob ein Symbol Krypto ist (Symbol-Name oder Epic, z.B. BTC_USD / BTCUSD)."""
    if not sym_key:
        return False
    s = str(sym_key).upper().replace("-", "_").replace("/", "_")
    namen = {s}
    cfg = MARKET_CONFIG.get(sym_key) or MARKET_CONFIG.get(s)
    if cfg:
        namen.add(str(cfg.get("epic", "")).upper())
    for _k, _c in MARKET_CONFIG.items():
        if str(_c.get("epic", "")).upper() == s:
            namen.add(str(_k).upper())
    return any(_krypto_kuerzel(n) in _KRYPTO_BASIS for n in namen)


# v15.24 GRUPPEN-LIMIT: Maerkte, die meist gemeinsam steigen und fallen. Am 07.10. eroeffnete
# der Bot in derselben Minute Brent, Heizoel, Benzin und Kupfer SELL - eine Wette, viermal gesetzt.
_MARKT_GRUPPEN = {
    "ENERGIE": {"OIL_CRUDE", "OIL_BRENT", "NATURAL_GAS", "NATURALGAS", "HEATING_OIL", "HEATINGOIL", "GASOLINE"},
    "METALLE": {"GOLD", "SILVER", "PLATINUM", "PALLADIUM", "COPPER", "ALUMINUM", "ZINC", "MZN3", "NICKEL"},
    "AGRAR": {"WHEAT", "CORN", "SOYBEANS", "SOYBEAN", "COFFEE", "COFFEEARABICA", "SUGAR", "UKSUGAR",
              "COTTON", "USCOTTON", "COCOA", "USCOCOA"},
}


def markt_gruppe(sym_or_epic):
    """Gruppe eines Symbols oder Epics (ENERGIE, METALLE, AGRAR, KRYPTO) oder None."""
    s = str(sym_or_epic or "").upper()
    for g, mitglieder in _MARKT_GRUPPEN.items():
        if s in mitglieder:
            return g
    if is_crypto(s):
        return "KRYPTO"
    return None


def gruppen_belegt(sym, epic, positionen):
    """Epics offener Positionen aus derselben Gruppe wie sym/epic (ohne epic selbst)."""
    g = markt_gruppe(sym) or markt_gruppe(epic)
    if not g:
        return None, []
    belegt = set()
    for px in positionen or []:
        try:
            e = px["market"]["epic"]
        except Exception:
            continue
        if e != epic and markt_gruppe(e) == g:
            belegt.add(e)
    return g, sorted(belegt)


def check_weekend_allowed(sym_key):
    if is_weekend():
        # Wochenende: Alle Assets erlaubt, keine speziellen Krypto-Einschränkungen
        return True, "Asset haftasonu acik"
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
    valid_keys = [k for k in GEMINI_KEYS if k]
    if not valid_keys: return "KAPAT", "Key yok"
    for model in (gemini_model_chain() or list(_GEMINI_FALLBACK_FLASH[:3])):  # v15.15: vorher feste, abgeschaltete Modelle
        try:
            response = genai.Client(api_key=valid_keys[0]).models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="Acil kriz. Hizli karar. KAPAT/HEDGE/TUT.")
            )
            text = response.text.strip().upper()
            karar = "KAPAT" if "KAPAT" in text[:20] else ("HEDGE" if "HEDGE" in text[:20] else ("TUT" if "TUT" in text[:20] else "KAPAT"))
            try: db_gemini_write("EMERGENCY", f"{sym} {degisim_pct:.1f}%% karar:{karar}", sym)
            except: pass
            logging.info(f"Emergency: {sym} {degisim_pct:.1f}%% to {karar}")
            return karar, text[:150]
        except Exception as e:
            logging.warning(f"Emergency {model}: {e}")
    return "KAPAT", "Modeller basarisiz"


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

# ── v15.11: SL-Update mit TP, Mirror-TP-Merker, Teilverkauf ───────────
def _sl_update_body(p, new_sl):
    """
    Body fuer PUT /positions/{dealId}: neuer SL + bestehender TP.
    Capital.com loescht den Take Profit, wenn bei einer SL-Aenderung nur
    stopLevel gesendet wird (in der Konto-Historie nachgewiesen).
    """
    body = {"stopLevel": new_sl}
    try:
        tp = float(p["position"].get("profitLevel") or 0)
        if tp > 0:
            body["profitLevel"] = tp
    except Exception:
        pass
    return body


def _mirror_key(epic, direction, entry):
    return f"{epic}_{direction}_{entry:.5f}"


def _mirror_persist(state):
    """Nur die mirror_*-Merker sofort in die State-Datei schreiben (Peaks bleiben wie sie sind)."""
    try:
        disk = _load_trailing_state()
        for k in [k for k in disk if k.startswith("mirror_")]:
            disk.pop(k, None)
        disk.update({k: v for k, v in state.items() if k.startswith("mirror_")})
        _save_trailing_state(disk)
    except Exception as e:
        logging.warning(f"Mirror-TP State speichern: {e}")


def mirror_cleanup(state, pozisyonlar):
    """Merker von Positionen entfernen, die es nicht mehr gibt."""
    aktiv = set()
    for p in pozisyonlar:
        try:
            aktiv.add(_mirror_key(p["market"]["epic"], p["position"]["direction"],
                                  float(p["position"]["level"])))
        except Exception:
            pass
    alt = [k for k in state if k.startswith("mirror_") and not any(k.endswith("_" + m) for m in aktiv)]
    for k in alt:
        state.pop(k, None)
    if alt:
        _mirror_persist(state)


def mirror_orig_size(state, mkey, deal_id, pos_size, aktive_deals):
    """
    Bezugsgroesse fuer die Mirror-TP-Stufen = Groesse beim ersten Sehen.
    Taucht am selben Einstieg eine NEUE Position auf (andere dealId, nicht
    kleiner als die gemerkte, und die gemerkte ist nicht mehr offen), werden
    die Stufen zurueckgesetzt.
    """
    rec = state.get("mirror_orig_" + mkey)
    neu = not isinstance(rec, dict)
    if not neu and rec.get("deal") != deal_id and rec.get("deal") not in aktive_deals \
            and pos_size >= float(rec.get("size", 0)) * 0.999:
        neu = True
    if neu:
        for i in (1, 2, 3):
            state.pop(f"mirror_l{i}_{mkey}", None)
            state.pop(f"mirror_warn{i}_{mkey}", None)
            state.pop(f"mirror_p{i}_{mkey}", None)   # v15.24 Stop-Leiter
            state.pop(f"mirror_lw{i}_{mkey}", None)
        rec = {"size": pos_size, "deal": deal_id}
        state["mirror_orig_" + mkey] = rec
        _mirror_persist(state)
    return float(rec["size"])


def mirror_close_size(orig_size, rest_size, close_pct, min_size):
    """
    Prozent -> Einheiten.  (v15.12: Mindestgroesse statt Auslassen)
    - Sind die Prozent kleiner als die Mindestgroesse der Boerse, wird die
      Mindestgroesse verkauft - keine Stufe wird ausgelassen.
    - Bliebe danach ein Rest unter der Mindestgroesse, wird der ganze Rest
      geschlossen (auch wenn das die ganze Position ist).
    """
    if rest_size <= 1e-9:
        return 0.0
    size = max(orig_size * close_pct, min_size)
    if rest_size - size < min_size - 1e-9:
        size = rest_size
    return round(size, 6)


def partial_close_position(h, epic, direction, close_size):
    """
    Teilverkauf. Capital.com kennt kein "Schliessen mit Menge" (DELETE hat
    keinen size-Parameter). Ein Teil wird geschlossen, indem eine Order in
    Gegenrichtung gesendet wird. Das verrechnet nur, wenn der Hedging-Modus
    des Kontos AUS ist - sonst entstuende eine zweite, entgegengesetzte Position.
    Bei mehreren Positionen im selben Epic verrechnet der Broker selbst;
    geprueft wird deshalb die Summe pro Epic + Richtung.

    Rueckgabe: (ok, geschlossene_groesse, info)
      info "HEDGING"       -> Hedging-Modus an, nichts gesendet
      info "UNKLAR"        -> Order gesendet, Wirkung nicht sicher sichtbar: NICHT wiederholen
      info "GEGENPOSITION" -> es entstand eine Gegenposition; sie wurde sofort wieder geschlossen
    """
    gegen = "SELL" if direction == "BUY" else "BUY"
    gesendet = False

    def _lage():
        summe, gegen_ids = 0.0, set()
        for px in get_positions(h):
            if px["market"]["epic"] != epic:
                continue
            if px["position"]["direction"] == direction:
                summe += float(px["position"].get("size", 0) or 0)
            else:
                gegen_ids.add(px["position"]["dealId"])
        return round(summe, 8), gegen_ids

    try:
        pr = requests.get(f"{CAPITAL_URL}/accounts/preferences", headers=h, timeout=10)
        if pr.status_code != 200:
            return False, 0.0, f"Konto-Einstellungen nicht lesbar (HTTP {pr.status_code})"
        if pr.json().get("hedgingMode") is not False:
            return False, 0.0, "HEDGING"

        vor, gegen_vor = _lage()
        if vor <= 0:
            return False, 0.0, "keine offene Position gefunden"

        r = requests.post(f"{CAPITAL_URL}/positions",
                          json={"epic": epic, "direction": gegen, "size": close_size},
                          headers=h, timeout=10)
        if r.status_code != 200:
            return False, 0.0, f"Order abgelehnt: {r.text[:120]}"
        gesendet = True

        # Wurde die Order nachtraeglich abgelehnt? (dann darf spaeter erneut versucht werden)
        try:
            ref = r.json().get("dealReference")
            if ref:
                time.sleep(1)
                cf = requests.get(f"{CAPITAL_URL}/confirms/{ref}", headers=h, timeout=10)
                if cf.status_code == 200 and cf.json().get("dealStatus") == "REJECTED":
                    return False, 0.0, f"Order abgelehnt: {str(cf.json().get('rejectReason', cf.text))[:120]}"
        except Exception:
            pass

        for warte in (2, 3, 5):
            time.sleep(warte)
            nach, gegen_nach = _lage()
            neue_gegen = gegen_nach - gegen_vor
            if neue_gegen:
                for did in neue_gegen:
                    try:
                        requests.delete(f"{CAPITAL_URL}/positions/{did}", headers=h, timeout=10)
                    except Exception as e:
                        logging.error(f"Gegenposition {did} schliessen: {e}")
                return False, 0.0, "GEGENPOSITION"
            # nach == 0 kann auch "Depot gerade nicht lesbar" heissen -> nicht als Erfolg werten
            if 0 < nach < vor - 1e-9:
                return True, round(vor - nach, 6), "OK"
        return False, 0.0, "UNKLAR"
    except Exception as e:
        return False, 0.0, ("UNKLAR" if gesendet else f"Fehler: {e}")


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

        # v15.11: Mirror-TP-Merker geschlossener Positionen entfernen
        mirror_cleanup(state, pozisyonlar)
        aktive_deals = {px["position"]["dealId"] for px in pozisyonlar}

        for epic, positions in epic_groups.items():
            try:
                direction  = positions[0]["position"]["direction"]
                instrument = positions[0]["market"].get("instrumentName", epic)
                stufe      = get_pyramiding_stufe(epic)
                current    = float(positions[0]["market"].get("bid", 0))
                if current <= 0:
                    continue

                peak_key = "peak_" + epic + "_" + direction
                saved_peak = state.get(peak_key, {}).get("value", current)

                # Einstiegspreis der ältesten Position (Level)
                entry_prices = [float(p["position"].get("level", current)) for p in positions]
                min_entry = min(entry_prices) if direction == "BUY" else max(entry_prices)

                # KRITISCHER FIX v14.6: Alter Peak aus vorheriger Position → reset
                # Wenn gespeicherter Peak unrealistisch hoch/tief vs. Einstieg → ignorieren
                if direction == "BUY":
                    if saved_peak > min_entry * 1.15:  # >15% über Einstieg = alter Peak
                        logging.info(f"Trailing SL: Alter Peak {saved_peak} fuer {epic} zurueckgesetzt (Einstieg: {min_entry})")
                        peak = current  # Frisch starten mit aktuellem Preis
                    else:
                        peak = max(saved_peak, current)
                    target_sl = round(peak * (1 - TRAIL_PCT), 5)
                else:
                    if saved_peak > 0 and saved_peak < min_entry * 0.85:  # >15% unter Einstieg
                        logging.info(f"Trailing SL: Alter Peak {saved_peak} fuer {epic} zurueckgesetzt (Einstieg: {min_entry})")
                        peak = current
                    else:
                        peak = saved_peak if (saved_peak > 0 and current < saved_peak) else current
                    target_sl = round(peak * (1 + TRAIL_PCT), 5)

                any_updated = False
                for p in positions:
                    deal_id  = p["position"]["dealId"]
                    cur_sl   = float(p["position"].get("stopLevel", 0) or 0)
                    entry    = float(p["position"]["level"])
                    pos_size = float(p["position"].get("size", 0))
                    if entry <= 0:
                        continue
                    profit_pct = ((current - entry) / entry * 100) if direction == "BUY"                                  else ((entry - current) / entry * 100)

                    # ── SMART EXIT SYSTEM v15.1 ──────────────────────────
                    # 1. BREAKEVEN-SL ab +1%: Position kann nicht mehr im Verlust schließen
                    if profit_pct >= 1.0:
                        be_sl = round(entry * 1.0003, 5) if direction == "BUY"                                 else round(entry * 0.9997, 5)
                        be_ok = (cur_sl < be_sl) if direction == "BUY"                                 else (cur_sl == 0 or cur_sl > be_sl)
                        if be_ok:
                            r_be = requests.put(
                                CAPITAL_URL + "/positions/" + deal_id,
                                json=_sl_update_body(p, be_sl), headers=h, timeout=10  # v15.11: TP bleibt
                            )
                            if r_be.status_code == 200:
                                cur_sl = be_sl
                                any_updated = True
                                logging.info(f"Breakeven-SL: {instrument} {direction} "
                                             f"{be_sl:.5f} (+{profit_pct:.1f}%)")
                                try:
                                    bot.send_message(MY_CHAT_ID,
                                        f"Breakeven: {instrument} {direction} "
                                        f"+{profit_pct:.1f}% → SL={be_sl:.4f}")
                                except: pass

                    # ───────────────────────────────────────────────────────
                    # MIRROR-TP MULTI-LEVEL (House Edge) — ATR-basiert
                    # Fügt 3 Gewinnmitnahme-Level hinzu (je 25% der Position),
                    # ohne Trailing SL, Breakeven oder Pyramiding zu berühren.
                    # Steuerbar per .env: MIRROR_TP_ENABLED=true/false
                    # ───────────────────────────────────────────────────────
                    _mtp_zu = False  # v15.12: True = Mirror-TP hat die Position ganz geschlossen
                    if os.getenv("MIRROR_TP_ENABLED", "true").lower() == "true":
                        try:
                            _atr_sl_val, atr_v, _ = get_atr_stop_loss(epic, current, direction)
                            if atr_v > 0 and entry > 0:
                                m1 = float(os.getenv("MIRROR_TP_LEVEL_1_MULT", "0.5"))
                                m2 = float(os.getenv("MIRROR_TP_LEVEL_2_MULT", "1.0"))
                                m3 = float(os.getenv("MIRROR_TP_LEVEL_3_MULT", "1.5"))
                                close_pct = float(os.getenv("MIRROR_TP_CLOSE_PCT", "25.0")) / 100.0
                                cfg_sym = next((c for s, c in MARKET_CONFIG.items() if c.get("epic") == epic), {})
                                min_sz  = float(cfg_sym.get("min_size", 0.01))

                                if direction == "BUY":
                                    levels = [entry + atr_v*m1, entry + atr_v*m2, entry + atr_v*m3]
                                    hits   = [current >= l for l in levels]
                                else:
                                    levels = [entry - atr_v*m1, entry - atr_v*m2, entry - atr_v*m3]
                                    hits   = [current <= l for l in levels]

                                # v15.11: Teilverkauf ueber Gegen-Order (partial_close_position).
                                # Bezug = Groesse beim ersten Sehen; Merker haengen an
                                # Epic+Richtung+Einstieg und werden sofort gespeichert.
                                mkey = _mirror_key(epic, direction, entry)
                                orig_size = mirror_orig_size(state, mkey, deal_id, pos_size, aktive_deals)
                                rest_size = pos_size
                                for i, hit in enumerate(hits, 1):
                                    key = f"mirror_l{i}_{mkey}"
                                    if hit and not state.get(key):
                                        close_size = mirror_close_size(orig_size, rest_size, close_pct, min_sz)
                                        if close_size <= 0:
                                            continue  # Mindestgroesse laesst hier keinen Teilverkauf zu
                                        if close_size >= rest_size - 1e-9:
                                            # v15.12: ganzer Rest -> Position normal schliessen
                                            r_full = requests.delete(CAPITAL_URL + "/positions/" + deal_id,
                                                                     headers=h, timeout=10)
                                            ok_mtp = r_full.status_code == 200
                                            sold = rest_size if ok_mtp else 0.0
                                            info_mtp = "OK" if ok_mtp else f"Schliessen abgelehnt: {r_full.text[:120]}"
                                            if ok_mtp and len(positions) == 1:
                                                reset_pyramiding_stufe(epic)
                                        else:
                                            ok_mtp, sold, info_mtp = partial_close_position(h, epic, direction, close_size)
                                        if ok_mtp or info_mtp in ("UNKLAR", "GEGENPOSITION"):
                                            state[key] = True  # Stufe erledigt - nie doppelt verkaufen
                                            if ok_mtp:
                                                state[f"mirror_p{i}_{mkey}"] = round(current, 5)  # v15.24: fuer die Stop-Leiter
                                            _mirror_persist(state)
                                        if ok_mtp:
                                            rest_size = max(rest_size - sold, 0.0)
                                            _mtp_zu = rest_size <= 1e-9
                                            _rest_txt = ("Position damit komplett geschlossen." if _mtp_zu
                                                         else f"Rest {round(rest_size, 6)} läuft weiter.")
                                            logging.info(
                                                f"MIRROR-TP L{i}: {instrument} {direction} "
                                                f"{sold} von {orig_size} geschlossen @ {current:.5f} "
                                                f"(ATR×{[m1,m2,m3][i-1]}) Rest {rest_size}"
                                            )
                                            try:
                                                bot.send_message(MY_CHAT_ID,
                                                    f"🎯 MIRROR-TP Level {i}: {instrument} {direction}\n"
                                                    f"✅ {sold} von {orig_size} Einheiten geschlossen "
                                                    f"({sold/orig_size*100:.0f}%) @ {current:.5f}\n"
                                                    f"📊 ATR-Ziel: {levels[i-1]:.5f} | {_rest_txt}"
                                                )
                                            except: pass
                                        else:
                                            logging.warning(f"MIRROR-TP L{i} {instrument} {direction}: {info_mtp}")
                                            wkey = f"mirror_warn{i}_{mkey}"
                                            if not state.get(wkey):
                                                state[wkey] = True
                                                _mirror_persist(state)
                                                if info_mtp == "HEDGING":
                                                    _mtp_txt = ("Teilverkauf nicht möglich: Im Capital.com-Konto ist der "
                                                                "Hedging-Modus eingeschaltet. Bitte dort ausschalten, "
                                                                "dann verkauft der Bot in Stufen.")
                                                elif info_mtp == "UNKLAR":
                                                    _mtp_txt = ("Order gesendet, aber im Depot keine Verkleinerung gesehen. "
                                                                "Stufe wird NICHT wiederholt - bitte Position prüfen.")
                                                elif info_mtp == "GEGENPOSITION":
                                                    _mtp_txt = ("Statt eines Teilverkaufs entstand eine Gegenposition; "
                                                                "sie wurde sofort wieder geschlossen. Bitte Depot prüfen.")
                                                else:
                                                    _mtp_txt = f"{info_mtp} - wird beim nächsten Durchlauf erneut versucht."
                                                try:
                                                    bot.send_message(MY_CHAT_ID,
                                                        f"⚠️ MIRROR-TP Level {i}: {instrument} {direction}\n{_mtp_txt}")
                                                except: pass
                                            if info_mtp in ("HEDGING", "GEGENPOSITION"):
                                                break
                                        if _mtp_zu:
                                            break
                        except Exception as _mtp_e:
                            logging.debug(f"Mirror-TP {epic}: {_mtp_e}")
                    # ─── ENDE MIRROR-TP ──────────────────────────────────────

                    # v15.24 STOP-LEITER: Hat eine Position Stufen verkauft, darf der Rest nicht mehr
                    # mit dem vollen Stop schliessen. Stufe 1 -> Stop auf den Einstieg, Stufe 2 -> auf
                    # den Verkaufskurs von Stufe 1, Stufe 3 -> auf den von Stufe 2. Der Stop wird nur
                    # enger, nie weiter. Liegt das Ziel schon jenseits des Kurses (z.B. zwei Stufen im
                    # selben Lauf verkauft, oder der Kurs ist zurueckgelaufen), nimmt der Bot die naechst
                    # tiefere Sprosse (bis hinunter zum Einstieg). Laeuft auch, wenn die ATR fehlt.
                    if STOP_LEITER and not _mtp_zu:
                        try:
                            _lk = _mirror_key(epic, direction, entry)
                            _k = 0
                            for _i in (1, 2, 3):
                                if not state.get(f"mirror_l{_i}_{_lk}"):
                                    break
                                _k = _i
                            if _k > 0:
                                _vz = 1 if direction == "BUY" else -1
                                _ask = float(positions[0]["market"].get("offer", 0) or current)
                                _tol = entry * 0.0001          # Rundung des Brokers (Tick) nicht als Verbesserung zaehlen
                                _sprossen = []                 # (Ziel, Stufe des Kurses; 0 = Einstieg), beste zuerst
                                for _j in range(_k - 1, 0, -1):
                                    _pv = state.get(f"mirror_p{_j}_{_lk}")
                                    if _pv:
                                        _sprossen.append((round(float(_pv), 5), _j))
                                _sprossen.append((round(entry * (1 + _vz * 0.0003), 5), 0))
                                _wahl = None
                                for _ziel, _wo in _sprossen:
                                    _gueltig = (_ziel < current) if direction == "BUY" else (_ziel > _ask)
                                    _besser = (_ziel > cur_sl + _tol) if direction == "BUY" \
                                        else (cur_sl <= 0 or _ziel < cur_sl - _tol)
                                    if _gueltig and _besser:
                                        _wahl = (_ziel, _wo)
                                        break
                                    if not _besser:
                                        break      # Stop sitzt schon mindestens so eng - tiefere Sprossen waeren weiter
                                if _wahl:
                                    _ziel, _wo = _wahl
                                    r_lt = requests.put(CAPITAL_URL + "/positions/" + deal_id,
                                                        json=_sl_update_body(p, _ziel), headers=h, timeout=10)
                                    if r_lt.status_code == 200:
                                        _sl_alt, cur_sl = cur_sl, _ziel
                                        updated += 1
                                        logging.info(f"Stop-Leiter: {instrument} {direction} Stufe {_k} "
                                                     f"SL {_sl_alt:g} -> {_ziel:g}")
                                        try:
                                            if _wo == 0:
                                                bot.send_message(MY_CHAT_ID,
                                                    f"🪜 Stop-Leiter: {instrument} {direction} - Stufe {_k} verkauft, "
                                                    f"Stop auf Einstieg: {_sl_alt:g} -> {_ziel:g}")
                                            else:
                                                bot.send_message(MY_CHAT_ID,
                                                    f"🪜 Stop-Leiter: {instrument} {direction} - Stufe {_k} verkauft, "
                                                    f"Stop auf Kurs von Stufe {_wo}: {_sl_alt:g} -> {_ziel:g}")
                                        except Exception:
                                            pass
                                    else:
                                        _wk = f"mirror_lw{_k}_{_lk}"
                                        if not state.get(_wk):
                                            state[_wk] = True
                                            _mirror_persist(state)
                                            logging.warning(f"Stop-Leiter {instrument} {direction} Stufe {_k}: "
                                                            f"SL {_ziel:g} abgelehnt: {r_lt.status_code} {r_lt.text[:120]}")
                        except Exception as _lt_e:
                            logging.warning(f"Stop-Leiter {epic}: {_lt_e}")

                    # 2. TRAILING SL erst ab +1.5% aktivieren
                    if profit_pct < 1.5 or _mtp_zu:
                        continue

                    # 3. PARTIAL EXIT ab +2%: kleinste Position schließen
                    if profit_pct >= 2.0 and len(positions) > 1:
                        min_sz = min(float(px["position"].get("size", 999)) for px in positions)
                        if pos_size <= min_sz:
                            r_p = requests.delete(
                                CAPITAL_URL + "/positions/" + deal_id,
                                headers=h, timeout=10
                            )
                            if r_p.status_code == 200:
                                logging.info(f"Partial Exit: {instrument} +{profit_pct:.1f}%")
                                try:
                                    bot.send_message(MY_CHAT_ID,
                                        f"Partial Exit: {instrument} {direction} "
                                        f"+{profit_pct:.1f}% | {pos_size} units gesichert")
                                except: pass
                            continue

                    # 4. NORMALER TRAILING SL (erst ab +1.5%)
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
                        json=_sl_update_body(p, final_sl),  # v15.11: TP bleibt
                        headers=h, timeout=10
                    )
                    if r.status_code == 200:
                        updated += 1
                        any_updated = True
                        logging.info(
                            "Trailing SL: " + instrument + " " + direction +
                            " Sv:" + str(stufe) +
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

                if any_updated:
                    # v14.9: Trailing SL → nur Log (kein Telegram-Spam)
                    # Telegram nur wenn SL sich >1% ändert (wirklich wichtig)
                    n_pos = len(positions)
                    msg = (
                        "Trailing SL: " + instrument + " " + direction +
                        " Sv." + str(stufe) + " (aktif) | " +
                        str(n_pos) + " pos | Peak:" + str(round(peak, 5)) +
                        " | Yeni SL: " + str(target_sl)
                    )
                    logging.info(msg)
                    # Telegram nur bei signifikanter SL-Änderung (>1%)
                    sl_pct = abs(final_sl - cur_sl) / max(cur_sl, 0.0001) * 100
                    if sl_pct >= 1.0:
                        try:
                            bot.send_message(MY_CHAT_ID,
                                "SL Guncellendi: " + instrument + " " + direction +
                                " | Yeni SL: " + str(target_sl) +
                                " (%" + str(round(sl_pct,1)) + " degisim)")
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
    Kaynakları iki GitHub dosyasından okur ve birleştirir:
    - toplam_egitim.txt  → haber siteleri + X hesapları (büyük liste)
    - Abfrage_Quellen.txt → X hesapları (birincil X listesi)
    Blacklisted kaynakları (source_credibility DB) filtreler.
    Döner: {"x_accounts": [...], "news_sites": [...], "all": [...]}
    """
    SOURCE_URLS = [
        "https://raw.githubusercontent.com/KhungFu/kisilerim/refs/heads/main/toplam_egitim.txt",
        "https://raw.githubusercontent.com/KhungFu/kisilerim/main/Abfrage_Quellen.txt",
    ]

    x_seen     = set()
    x_accounts = []
    news_sites  = []

    for url in SOURCE_URLS:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                logging.warning(f"Kaynak dosya yüklenemedi: {url}")
                continue
            for line in r.text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if 'x.com/' in line.lower() or 'twitter.com/' in line.lower():
                    handle = line.split('x.com/')[-1].split('/')[0].strip()
                    if handle and handle not in x_seen:
                        x_seen.add(handle)
                        x_accounts.append({"handle": f"@{handle}", "url": line.strip()})
                elif line.startswith('http') and 'youtube.com' not in line.lower():
                    if line not in news_sites:
                        news_sites.append(line)
                elif line.startswith('www.'):
                    full = "https://" + line
                    if full not in news_sites:
                        news_sites.append(full)
        except Exception as e:
            logging.warning(f"Kaynak yuklenemedi ({url}): {e}")

    # Blacklisted kaynakları filtrele
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            blacklisted = set(row[0] for row in conn.execute(
                "SELECT source_name FROM source_credibility WHERE blacklisted=1"
            ).fetchall())
            conn.close()
        x_accounts = [x for x in x_accounts if x["handle"] not in blacklisted]
        news_sites  = [s for s in news_sites  if s not in blacklisted]
    except Exception as e:
        logging.warning(f"Blacklist filtre hatası: {e}")

    all_sources = [x["handle"] for x in x_accounts] + news_sites
    logging.info(f"Kaynaklar yuklendi: {len(x_accounts)} X hesabi, {len(news_sites)} haber sitesi")
    return {"x_accounts": x_accounts, "news_sites": news_sites, "all": all_sources}


# ============================================================
# NEWS & X INTELLIGENCE - 14 Tage Cache
# ============================================================

# Asset-Tag Mapping: Welches Keyword gehört zu welchem Asset
ASSET_KEYWORDS = {
    "SILVER":      ["silver","gümüş","xag","silber"],
    # ZUSAMMENGEFÜHRT IN NÄCHSTER ZEILE
    "BTC_USD":     ["bitcoin","btc","crypto","kripto"],
    "ETH_USD":     ["ethereum","eth","crypto","kripto"],
    "SOL_USD":     ["solana","sol"],
    "XRP_USD":     ["ripple","xrp"],
    "OIL_BRENT":   ["oil","brent","crude","petrol"],
    "NATURAL_GAS": ["natural gas","natgas","doğalgaz"],
    "EURUSD":      ["euro","eur","dolar","dollar","dxy"],
    "GOLD": ["gold","altın","xau","federal reserve","fed","inflation","ecb","zins"],
}

def detect_asset_tag(text):
    """Metinden asset tag tespit et."""
    text_lower = text.lower()
    for asset, keywords in ASSET_KEYWORDS.items():
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
        # Mevcut kaynaklar
        "wallstreet-online.de": "https://www.wallstreet-online.de/rss/nachrichten.xml",
        "bloomberght.com":      "https://www.bloomberght.com/rss",
        "sozcu.com.tr/ekonomi": "https://www.sozcu.com.tr/rss/ekonomi.xml",
        "n-tv.de":              "https://www.n-tv.de/rss",
        "focus.de":             "https://rss.focus.de/fol/XML/rss_folnews.xml",
        # v12.1: toplam_egitim.txt kaynaklarından eklendi
        "investing.com":        "https://www.investing.com/rss/news.rss",
        "finanzmarktwelt.de":   "https://www.finanzmarktwelt.de/feed/",
        "marketwatch.com":      "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        # reuters.com/business: DNS tot — auskommentiert (Fix v14.9)
        "bbc.com/business":     "https://feeds.bbci.co.uk/news/business/rss.xml",
        "ekonomi.haber7.com":   "https://ekonomi.haber7.com/rss/haber7.xml",
        "zerohedge.com":        "https://feeds.feedburner.com/zerohedge/feed",
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

            # v12.1: UTF-8 zorla - Umlauts düzelsin (Ã¼ → ü)
            r.encoding = r.apparent_encoding or 'utf-8'
            import html as _html, re as _re
            content = _html.unescape(r.text)
            # Titel und Links extrahieren
            titles = _re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>',
                                  content, _re.DOTALL)
            links  = _re.findall(r'<link>(https?://[^<]+)</link>', content)
            dates  = _re.findall(r'<pubDate>(.*?)</pubDate>', content)

            for i, title in enumerate(titles[1:11], 0):  # Max 10 pro Quelle, skip feed-title
                title = _html.unescape(title.strip())  # v12.1: entity decode
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
    """
    v12.1: Nitter tamamen kaldırıldı (tüm instance kapalı 2024+).
    X hesapları artık Gemini Google Search Grounding ile okunuyor.
    Hesap listesi fetch_strategic_response prompt'una enjekte ediliyor.
    Bu fonksiyon sadece mevcut DB postlarını temizler.
    """
    try: init_db()
    except: pass

    x_accounts = sources_data.get("x_accounts", [])
    cutoff = (datetime.now() - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")

    # Eski postları temizle
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("DELETE FROM x_cache WHERE tweet_date < ?", (cutoff,))
            conn.commit()
            db_count = conn.execute("SELECT COUNT(*) FROM x_cache").fetchone()[0]
            conn.close()
        logging.info(f"X/Grounding: {len(x_accounts)} hesap Gemini prompt'una verildi. DB: {db_count} post.")
        return len(x_accounts)
    except Exception as e:
        logging.warning(f"collect_x_via_search: {e}")
        return 0


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

    lines = [f"=== {datetime.now().strftime('%d.%m %H:%M')} | {asset_tag} Haber (Son {days} gun) ==="]

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

    lines = [f"=== {datetime.now().strftime('%d.%m %H:%M')} | GENEL MAKRO HABERLER (Son {days} Gun) ==="]
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
# GEMINI GROUNDING HABER TOPLAMA (v12.2)
# ============================================================
def _grounding_parse_and_save(raw, cutoff, conn):
    """
    Gemini Grounding çıktısını parse et ve DB'ye kaydet.
    Döner: (n_news, n_x)
    """
    import re as _re, html as _html
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n_news = n_x = 0
    for line in raw.split("\n"):
        line = line.strip()
        # Haber: [+BULL] 2026-07-13 | kaynak: başlık
        m = _re.match(r"\[([+~-][A-Z]+)\]\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^:]+):\s*(.+)", line)
        if m:
            lr, tarih, kaynak, baslik = m.groups()
            if tarih < cutoff:
                continue
            label  = "BULL" if "+" in lr else ("BEAR" if "-" in lr else "NEUT")
            sent   = 0.6 if label == "BULL" else (-0.6 if label == "BEAR" else 0.0)
            baslik = _html.unescape(baslik.strip())[:500]
            kaynak = kaynak.strip()[:60]
            if len(baslik) > 10 and not conn.execute(
                    "SELECT 1 FROM news_cache WHERE title=?", (baslik,)).fetchone():
                conn.execute(
                    "INSERT INTO news_cache "
                    "(source,title,published_at,fetched_at,sentiment,sentiment_label,asset_tag) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (kaynak, baslik, tarih, now_str, sent, label, detect_asset_tag(baslik)))
                n_news += 1
        # X post: [+BULL] 2026-07-13 @hesap: metin
        xm = _re.match(r"\[([+~-][A-Z]+)\]\s*(\d{4}-\d{2}-\d{2})\s*@([\w]+):\s*(.+)", line)
        if xm:
            lr, tarih, hesap, metin = xm.groups()
            if tarih < cutoff:
                continue
            label = "BULL" if "+" in lr else ("BEAR" if "-" in lr else "NEUT")
            sent  = 0.6 if label == "BULL" else (-0.6 if label == "BEAR" else 0.0)
            metin = _html.unescape(metin.strip())[:500]
            if len(metin) > 10 and not conn.execute(
                    "SELECT 1 FROM x_cache WHERE tweet_text=?", (metin[:300],)).fetchone():
                conn.execute(
                    "INSERT INTO x_cache "
                    "(account,asset_tag,tweet_text,tweet_date,fetched_at,sentiment,sentiment_label) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (hesap, detect_asset_tag(metin), metin, tarih, now_str, sent, label))
                n_x += 1
    return n_news, n_x



_gdelt_lock = threading.Lock()  # Globaler Lock — nur 1 GDELT-Request gleichzeitig

def gdelt_haber_topla(sources_data, asset=None):
    """
    v14.8: GDELT Doc 2.0 API — Rate-Limit FIX.
    - Globaler Lock: nur 1 Thread gleichzeitig
    - Sleep 8s zwischen Requests (GDELT erlaubt 1/5s, Puffer für Burst)
    - Retry bei 429 mit exponentiellem Backoff
    - Queries auf 5 reduziert (wichtigste Themen)
    """
    import urllib.parse as _urlp
    now_dt  = datetime.now()
    cutoff  = (now_dt - timedelta(days=NEWS_HISTORY_DAYS)).strftime("%Y-%m-%d")
    n_news  = 0
    if asset:
        queries = [asset.replace("_", " ").replace("USD", "").strip()]
    else:
        queries = [
            "gold silver commodities",
            "federal reserve interest rate inflation",
            "crude oil natural gas energy",
            "bitcoin cryptocurrency market",
            "stock market economy recession",
        ]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today   = now_str[:10]

    with _gdelt_lock:  # Nur 1 Thread darf GDELT gleichzeitig nutzen
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            for qi, query in enumerate(queries):
                # Retry-Logik bei 429
                success = False
                for attempt in range(3):
                    try:
                        url = (
                            "https://api.gdeltproject.org/api/v2/doc/doc"
                            f"?query={_urlp.quote(query)}"
                            "&mode=artlist"
                            "&maxrecords=25"
                            "&timespan=2weeks"
                            "&format=json"
                        )
                        r = requests.get(url, timeout=20,
                                         headers={"User-Agent": "Mozilla/5.0 NexusNature/14.8"})
                        logging.info(f"GDELT '{query}': HTTP {r.status_code}, {len(r.text)} byte")

                        if r.status_code == 429:
                            wait = 10 * (2 ** attempt)  # 10s, 20s, 40s
                            logging.warning(f"GDELT 429 Rate-Limit → {wait}s warten (Versuch {attempt+1}/3)")
                            time.sleep(wait)
                            continue

                        if r.status_code != 200:
                            logging.warning(f"GDELT HTTP {r.status_code} — {r.text[:80]}")
                            break

                        try:
                            data = r.json()
                        except Exception as je:
                            logging.warning(f"GDELT JSON parse: {je} | raw: {r.text[:100]}")
                            break

                        articles = data.get("articles") or []
                        logging.info(f"GDELT '{query}': {len(articles)} makale")

                        for art in articles:
                            title = str(art.get("title", "")).strip()[:500]
                            url_a = str(art.get("url", ""))
                            src   = str(art.get("domain", ""))
                            if not src and "://" in url_a:
                                src = url_a.split("/")[2]
                            src   = src[:60]
                            raw_dt = str(art.get("seendate", ""))
                            try:
                                tarih = f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:8]}"
                                if len(raw_dt) < 8: tarih = today
                            except Exception:
                                tarih = today
                            if not title or len(title) < 10 or tarih < cutoff:
                                continue
                            title_l = title.lower()
                            bull_s = sum(1 for k in
                                ["rise","surge","gain","high","bullish","rally","strong",
                                 "beat","record","growth","up","positive","green","soar"]
                                if k in title_l)
                            bear_s = sum(1 for k in
                                ["fall","drop","crash","low","bearish","decline","weak",
                                 "miss","recession","down","negative","red","loss","fear","slide"]
                                if k in title_l)
                            label = "BULL" if bull_s > bear_s else ("BEAR" if bear_s > bull_s else "NEUT")
                            sent  = 0.6 if label == "BULL" else (-0.6 if label == "BEAR" else 0.0)
                            if not conn.execute(
                                    "SELECT 1 FROM news_cache WHERE title=?",
                                    (title,)).fetchone():
                                conn.execute(
                                    "INSERT INTO news_cache "
                                    "(source,title,published_at,fetched_at,sentiment,sentiment_label,asset_tag) "
                                    "VALUES (?,?,?,?,?,?,?)",
                                    (src, title, tarih, now_str, sent, label, detect_asset_tag(title)))
                                n_news += 1

                        success = True
                        break  # Erfolgreich, kein Retry nötig

                    except requests.exceptions.Timeout:
                        logging.warning(f"GDELT '{query}' Timeout (Versuch {attempt+1}/3)")
                    except Exception as e:
                        logging.warning(f"GDELT '{query}' hata: {e}")
                        break

                # Zwischen Queries: 8 Sekunden Pause (GDELT erlaubt 1/5s, Puffer für Burst)
                if qi < len(queries) - 1:
                    time.sleep(8)

            conn.execute("DELETE FROM news_cache WHERE published_at < ?", (cutoff,))
            conn.execute("DELETE FROM x_cache    WHERE tweet_date   < ?", (cutoff,))
            conn.commit()
            conn.close()

    logging.info(f"GDELT toplam: {n_news} haber DB\'ye yazıldı")
    return n_news, 0


def gemini_grounding_haber_topla(sources_data, asset=None):
    """v14.5: Grounding kaldırıldı → GDELT."""
    return gdelt_haber_topla(sources_data, asset=asset)


_news_collector_running = False

def news_collector_loop():
    """
    v12.4: Başlangıçta hemen 14 günlük Grounding çalışır (tüm X batch'leri).
    Sonra: saatte bir RSS, her 6 saatte bir Grounding (76 hesap = ~8 batch → zaman alır).
    Tüm haberler DB'ye yazılır → rolling 14 günlük pencere.
    """
    global _news_collector_running
    _news_collector_running = True
    logging.info("Haber Toplama Thread v12.4 başlatıldı")
    time.sleep(60)  # Bot tam ayağa kalksın

    grounding_sayac = 999  # İlk döngüde hemen Grounding çalışsın (1x täglich)

    while True:
        try:
            sources = load_sources()
            x_cnt   = len(sources.get("x_accounts", []))
            ns_cnt  = len(sources.get("news_sites",  []))
            if not sources["all"]:
                logging.warning("Haber Toplayici: kaynak listesi boş")
                time.sleep(NEWS_COLLECT_INTERVAL)
                continue

            logging.info(f"Haber Toplayici: {x_cnt} X hesabı + {ns_cnt} haber sitesi yüklendi")

            # 1) RSS - her saat (immer aktiv)
            n_rss = collect_news_rss(sources)

            # 1b) X API Free Tier (wenn X_API_BEARER in .env gesetzt)
            n_x_api = collect_x_free_tier(sources)
            if n_x_api:
                logging.info(f"X Free Tier: {n_x_api} tweet DB'ye eklendi")

            # 2) GDELT - her 3 saatte bir (ücretsiz, key yok)
            grounding_sayac += 1
            n_gn = n_gx = 0
            if grounding_sayac >= 3:  # 3 Zyklen × 1h = alle 3 Stunden
                grounding_sayac = 0
                try:
                    n_gn, n_gx = gdelt_haber_topla(sources)
                    logging.info(f"[OK] GDELT: {n_gn} haber")
                except Exception as _ge:
                    logging.warning(f"[WARN] GDELT hata: {_ge}")

            # 3) Alpha Vantage News (mit Sentiment, alle 3h zusammen mit GDELT)
            n_av = 0
            if grounding_sayac == 0 and ALPHA_VANTAGE_KEY:
                try:
                    n_av = collect_alphavantage_news_to_db()
                except Exception as _ave:
                    logging.debug(f"Alpha Vantage: {_ave}")

            # Telegram-Meldung nur alle 3 Stunden (nicht jede Stunde)
            if grounding_sayac == 0:
                try:
                    bot.send_message(MY_CHAT_ID,
                        f"Haber Toplayici: RSS={n_rss} | "
                        f"GDELT={n_gn} | AlphaVantage={n_av} haber | "
                        f"Kaynaklar: {x_cnt} X + {ns_cnt} site")
                except:
                    pass

            logging.info(
                f"Haber Toplayici: RSS={n_rss} | "
                f"Grounding={n_gn} haber + {n_gx} X post"
            )
        except Exception as e:
            logging.error(f"Haber Toplayici hatası: {e}")
        time.sleep(NEWS_COLLECT_INTERVAL)  # 1 saat

def load_doctrine():
    try:
        r = requests.get("https://raw.githubusercontent.com/KhungFu/kisilerim/main/mentor_name.txt", timeout=10)
        if r.status_code == 200: return r.text[:20000]  # v16.0: vorher [:3000] - drei Viertel der Doktrin (10 der 11 Mentoren) kamen nie an
    except: pass
    return "Özel doktrin yok. Standart kurallar uygulanır."

# ============================================================
# GREMIUM OYLAMA
# ============================================================
def gremium_oylama(sinyal, guc, sym_key, instrument, upl_toplam, saat,
                   macro_regime="NEUTRAL", news_sentiment=0.0, fred_signal="NEUTRAL"):
    """
    v14.9: 5 echte Markt-Spezialisten. 4/5 JA nötig (3/5 bei Krypto-Wochenende).
    Rückgabe: (karar, ja, nein, oylar, grunler)
    """
    oylar = {}
    grunler = {}
    h = saat
    is_krypto    = is_crypto(sym_key)
    is_gece      = 23 <= h or h < 6
    is_haftasonu = is_weekend()
    rog_bonus    = instrument.get("rogers_bonus", False) if isinstance(instrument, dict) else False
    is_rohstoff  = any(x in sym_key.upper() for x in
                       ["GOLD","SILVER","OIL","COPPER","WHEAT","CORN","COFFEE","GAS","BRENT"])
    is_forex     = any(x in sym_key.upper() for x in ["USD","EUR","GBP","JPY","CHF","AUD"])
    fred_ok      = fred_signal in ("NEUTRAL","BULLISH")

    # 1. CİHAT ÇİÇEK — Makro/DXY
    if sinyal not in ("BUY","SELL") or guc < 2:
        oylar["Cihat_Cicek"] = "NEIN"; grunler["Cihat_Cicek"] = f"Sinyal yok/zayıf (guc={guc})"
    elif macro_regime == "RISK_OFF_EXTREME" and not is_rohstoff:
        oylar["Cihat_Cicek"] = "NEIN"; grunler["Cihat_Cicek"] = "RISK_OFF_EXTREME — sadece altın/gümüş"
    elif is_krypto and is_gece and KRYPTO_NACHT_SPERRE:  # v15.14: nur wenn in .env eingeschaltet
        oylar["Cihat_Cicek"] = "NEIN"; grunler["Cihat_Cicek"] = "Gece kriptoda makro belirsizlik"
    else:
        oylar["Cihat_Cicek"] = "JA"; grunler["Cihat_Cicek"] = f"Makro uygun ({macro_regime})"

    # 2. JIM ROGERS — Rohstoffe/Trends
    if is_krypto and is_haftasonu:
        oylar["Jim_Rogers"] = "NEIN"; grunler["Jim_Rogers"] = "Krypto haftasonu — katalyzör yok"
    elif rog_bonus:
        oylar["Jim_Rogers"] = "JA"; grunler["Jim_Rogers"] = "Rogers-Filter aktif — EMA200 onayı"
    elif is_rohstoff and guc >= 2:
        oylar["Jim_Rogers"] = "JA"; grunler["Jim_Rogers"] = f"Emtia sinyali güçlü (guc={guc})"
    elif guc >= 3 and not is_krypto:
        oylar["Jim_Rogers"] = "JA"; grunler["Jim_Rogers"] = "Güçlü sinyal (guc=3)"
    else:
        oylar["Jim_Rogers"] = "NEIN"; grunler["Jim_Rogers"] = "Yeterli fundamental katalysator yok"

    # 3. RAY DALIO — Risiko-Parität
    if upl_toplam < -50:
        oylar["Ray_Dalio"] = "NEIN"; grunler["Ray_Dalio"] = f"UPL çok negatif ({upl_toplam:.0f}€)"
    elif not fred_ok and not is_krypto:
        oylar["Ray_Dalio"] = "NEIN"; grunler["Ray_Dalio"] = f"FRED olumsuz ({fred_signal})"
    elif is_haftasonu and not is_krypto:
        oylar["Ray_Dalio"] = "NEIN"; grunler["Ray_Dalio"] = "Haftasonu — likidite riski"
    elif guc < 2:
        oylar["Ray_Dalio"] = "NEIN"; grunler["Ray_Dalio"] = "Sinyal zayıf"
    else:
        oylar["Ray_Dalio"] = "JA"; grunler["Ray_Dalio"] = f"Risk dengesi uygun (UPL={upl_toplam:.0f}€)"

    # 4. NASSİM TALEB — Kara Kuğu/Tail-Risk
    if macro_regime in ("RISK_OFF_EXTREME","RISK_OFF_SPREAD"):
        oylar["Nassim_Taleb"] = "NEIN"; grunler["Nassim_Taleb"] = f"Kuyruk riski ({macro_regime})"
    elif is_krypto and is_gece and is_haftasonu and KRYPTO_NACHT_SPERRE:  # v15.14
        oylar["Nassim_Taleb"] = "NEIN"; grunler["Nassim_Taleb"] = "Gece+Haftasonu+Krypto=max belirsizlik"
    elif news_sentiment < -0.5:
        oylar["Nassim_Taleb"] = "NEIN"; grunler["Nassim_Taleb"] = f"Haber sentiment çok negatif ({news_sentiment:.2f})"
    elif guc >= 2 and sinyal in ("BUY","SELL"):
        oylar["Nassim_Taleb"] = "JA"; grunler["Nassim_Taleb"] = "Kuyruk riski kabul edilebilir"
    else:
        oylar["Nassim_Taleb"] = "NEIN"; grunler["Nassim_Taleb"] = "Belirsizlik fazla"

    # 5. GEORGE SOROS — Reflexivität/Momentum
    if sinyal not in ("BUY","SELL"):
        oylar["George_Soros"] = "NEIN"; grunler["George_Soros"] = "Yön yok — reflexivite işlemez"
    elif is_gece and not is_krypto:
        oylar["George_Soros"] = "NEIN"; grunler["George_Soros"] = "Gece — likidite düşük"
    elif guc >= 2 and news_sentiment >= -0.3:
        oylar["George_Soros"] = "JA"; grunler["George_Soros"] = f"Momentum güçlü (guc={guc})"
    elif guc >= 3:
        oylar["George_Soros"] = "JA"; grunler["George_Soros"] = "Çok güçlü sinyal"
    else:
        oylar["George_Soros"] = "NEIN"; grunler["George_Soros"] = f"Momentum yetersiz (guc={guc})"

    ja   = sum(1 for v in oylar.values() if v == "JA")
    nein = len(oylar) - ja
    # v15.13: Krypto 3/5 (Jim Rogers stimmt bei Krypto immer NEIN), sonst 4/5.
    # Einstellbar in der .env: GREMIUM_MIN_JA_KRYPTO / GREMIUM_MIN_JA
    try:
        esik = int(os.getenv("GREMIUM_MIN_JA_KRYPTO", "3")) if is_krypto else int(os.getenv("GREMIUM_MIN_JA", "4"))
    except ValueError:
        esik = 3 if is_krypto else 4
    karar = ja >= esik
    return karar, ja, nein, oylar, grunler

# ============================================================
# GEMINI ANALIZ (AUTONOMOUS)
# ============================================================

def load_bridgewater_rules() -> str:
    """Laedt Bridgewater Anti-Halluzination Regeln aus bridgewater_rules.txt."""
    try:
        pfad = os.path.join(BASE_DIR, "bridgewater_rules.txt")
        if os.path.exists(pfad):
            with open(pfad, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            logging.debug("bridgewater_rules.txt nicht gefunden — Fallback.")
    except Exception as e:
        logging.warning(f"bridgewater_rules.txt Lesefehler: {e}")
    return ""  # Kein Fehler, nur kein Inhalt


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
        if _krypto_kuerzel(sym) in ("BTC", "ETH", "SOL", "XRP") or "CRYPTO" in sym.upper():  # v15.24
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

def _format_kandidaten_strict(kandidaten) -> str:
    """
    HIDDEN-ENGINE PATTERN (Anti-Halluzination).
    Python uebersetzt Zahlen in Text-Fakten.
    Gemini sieht keine rohen JSON-Werte mehr.
    """
    if not kandidaten:
        return "KEINE KANDIDATEN: Python Gate-Keeper + Gremium haben alle Assets geblockt."

    lines = ["=== STAGE 2: GENEHMIGTE KANDIDATEN (HIDDEN-ENGINE) ==="]
    for sym, skor in kandidaten.items():
        lines.append(f"\n[{sym}]")

        # 1. TECHNIK als Text (keine rohen Zahlen)
        lines.append(f"  PYTHON-URTEIL: {skor.get('signal', 'NOTR')} | Score: {skor.get('score',0)}/{skor.get('max_score',5)}")
        lines.append(f"  DETAILS: {skor.get('details', '-')}")

        boll = skor.get("bollinger")
        if boll:
            pos = boll.get("position", "")
            if pos == "NEAR_LOWER":   bb_text = "PREIS AM UNTEREN BAND (potenziell bullishes Setup)"
            elif pos == "NEAR_UPPER": bb_text = "PREIS AM OBEREN BAND (potenziell bearisches Setup)"
            elif pos == "SQUEEZE":    bb_text = "BOLLINGER SQUEEZE — Ausbruch steht bevor"
            else:                     bb_text = "NEUTRAL (kein extremes Setup)"
            bw = boll.get("bandwidth", 0)
            squeeze_hint = " | ENGER ALS NORMAL (< 0.04)" if bw < 0.04 else ""
            lines.append(f"  BOLLINGER: {bb_text}{squeeze_hint}")
        else:
            lines.append("  BOLLINGER: Keine Daten")

        fib = skor.get("fibonacci")
        if fib:
            sr  = fib.get("sr_type", "?")
            lvl = fib.get("nearest_level", "?")
            dst = fib.get("distance_pct", 0)
            trend = fib.get("trend", "?")
            lines.append(f"  FIBONACCI: Nahe Level {lvl} ({sr}) | Distanz {dst:.1f}% | Trend: {trend}")
        else:
            lines.append("  FIBONACCI: Keine Daten")

        # 2. Gremium-Ergebnis (die 5 Mentoren haben VORHER abgestimmt)
        gremium_ja = skor.get("gremium_ja", 0)
        grunler = skor.get("gremium_grunler", {})
        ja_namen = [k.split("_")[0] for k, v in grunler.items() if v == "JA"]
        ja_names_str = ", ".join(ja_namen) if ja_namen else "-"
        lines.append(f"  GREMIUM: {gremium_ja}/5 JA ({ja_names_str})")

        # 3. News-Sentiment aus DB
        ns = skor.get("news_sentiment", 0.0)
        ns_text = "BULLISH" if ns > 0.2 else ("BEARISH" if ns < -0.2 else "NEUTRAL")
        lines.append(f"  NEWS-SENTIMENT (14T): {ns_text} ({ns:.2f})")

        # 4. Klarer Auftrag an Gemini
        lines.append(f"  DEINE AUFGABE (BRIDGEWATER-PROTOKOLL):")
        lines.append(f"  Python + Gremium haben dieses Asset technisch/fundamental geprueft.")
        lines.append(f"  Suche via GDELT/Google nach AKTUELLEM News-Narrativ fuer {sym}.")
        lines.append(f"  → WENN News DEM technischen Setup widersprechen: TRADE YOK")
        lines.append(f"  → WENN synchron: TRADE-Zeile ausgeben + 1 Satz MAKRO-VISION")
        lines.append(f"  WICHTIG: Erfinde keine Zahlen. Nutze nur die Fakten oben.")

        # 5. Quellen aus der alten Funktion uebernehmen
        if _krypto_kuerzel(sym) in ("BTC", "ETH", "SOL", "XRP") or "CRYPTO" in sym.upper():  # v15.24
            asset_sources = "@zerohedge, @Danny_Crypton, @unusual_whales"
            search_terms  = f'"{sym} price outlook today"'
        elif any(c in sym.upper() for c in ["GOLD","SILVER","XAU","XAG"]):
            asset_sources = "@SchiffGold, @PeterSchiff, @KobeissiLetter"
            search_terms  = f'"{sym} price forecast today"'
        elif any(c in sym.upper() for c in ["OIL","BRENT","CRUDE","GAS","ENERGY"]):
            asset_sources = "@KobeissiLetter, Reuters Energy, EIA.gov"
            search_terms  = f'"{sym} supply demand today"'
        else:
            asset_sources = "@KobeissiLetter, Bloomberg, Reuters"
            search_terms  = f'"{sym} outlook today"'

        asset_news = get_news_summary_for_asset(sym, days=14)
        lines.append(f"  SON 14 GUN HABER:")
        for nl in asset_news.split("\n")[1:8]:  # 7 Zeilen max
            lines.append(f"    {nl}")
        lines.append(f"  QUELLEN: {asset_sources} | SUCHE: {search_terms}")
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
    dxy_live     = get_dxy_live()
    fred_macro   = get_fred_macro_signal()
    # vol_regime korrekt berechnen (fix: market_intel statt fear_greed Wert)
    try:
        _market_intel = {
            "fear_greed": fear_greed.get("value", 50),
            "dxy": dxy_live,
            "fred": fred_macro,
        }
        vol_regime = get_volatility_regime(_market_intel) if callable(globals().get("get_volatility_regime")) else "NEUTRAL"
    except Exception:
        vol_regime = "NEUTRAL"
    macro_signal = get_enhanced_macro_signal(
        fear_greed.get("value", 50),
        vol_regime,
        cargo_data=get_cargo_flight_signal() if callable(globals().get("get_cargo_flight_signal")) else None,
        bdi_data=get_baltic_dry_index() if callable(globals().get("get_baltic_dry_index")) else None,
        eu_gas_data=get_eu_gas_storage() if callable(globals().get("get_eu_gas_storage")) else None,
    )
    daily_status, daily_msg = check_daily_limits()
    Health.report("fear_greed", bool(fear_greed), "")
    Health.report("econ_cal", bool(econ_cal), "")
    wx_agrar     = get_weather_signal("AGRAR")
    wx_energy    = get_weather_signal("ENERGY")

    # === ALTERNATİF VERİ SİNYALLERİ ===
    alt_data_summary = get_alternative_data_summary()
    disaster_data    = get_natural_disaster_signal()
    wx_commodity     = get_global_commodity_weather()

    # === V14.8 DATEN: EIA / COT / USDA / TRANSPORT ===
    try:
        eia_data       = get_eia_petroleum()
    except Exception as _e:
        eia_data       = {"signal": "UNKNOWN", "summary": f"EIA Fehler: {_e}"}
    try:
        cot_gold       = get_cot_positioning("GOLD")
        cot_oil        = get_cot_positioning("OIL")
        cot_silver     = get_cot_positioning("SILVER")
    except Exception as _e:
        cot_gold = cot_oil = cot_silver = {"signal": "UNKNOWN", "summary": f"COT Fehler: {_e}"}
    try:
        usda_cocoa     = get_usda_supply_demand("Cocoa")
        usda_coffee    = get_usda_supply_demand("Coffee")
        usda_wheat     = get_usda_supply_demand("Wheat")
    except Exception as _e:
        usda_cocoa = usda_coffee = usda_wheat = {"signal": "UNKNOWN", "summary": f"USDA Fehler: {_e}"}
    try:
        transport_data = get_transport_activity()
    except Exception as _e:
        transport_data = {"signal": "UNKNOWN", "summary": f"Transport Fehler: {_e}"}
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
    _kandidaten_lock = threading.Lock()
    with _kandidaten_lock:
        global gemini_kandidaten
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
                # Gremium Stimmen für Log
                _oy_str = " | ".join(
                    f"{m.split('_')[0]}:{v2}"
                    for m, v2 in skor.get("gremium_oylar", {}).items()
                )
                logging.info(
                    f"GATE+GREMIUM GECTI: {k} | "
                    f"Tech:{skor['score']}/{skor['max_score']} | "
                    f"Gremium:{skor.get('gremium_ja','?')}/5 JA | "
                    f"{_oy_str}"
                )
            else:
                _why = []
                if not skor.get("passed_gate", True):
                    _why.append(f"Tech:{skor['score']}/{skor['max_score']}<{skor['threshold']}")
                if not skor.get("gremium_passed", True):
                    _why.append(f"Gremium:{skor.get('gremium_ja','?')}/5 JA")
                logging.info(
                    f"GATE BLOK: {k} | "
                    + " + ".join(_why) + " | "
                    + skor.get("details", "")[:80]
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

    # === REGIME BERECHNUNG ===
    vol_regime   = get_volatility_regime(market_intel)
    macro_regime = get_macro_regime(fear_greed["value"], vol_regime)

    # === VOLLSTAENDIGES GEDAECHTNIS (VOR Gemini-Analyse) ===
    full_memory = db_get_full_memory()

    current_model = get_next_model()
    saat = datetime.now().hour
    dynamic_doctrine    = load_doctrine()
    bridgewater_rules   = load_bridgewater_rules()
    sources_data        = load_sources()

    # v12.1: Tüm X hesapları Gemini Grounding ile okunuyor (Nitter kaldırıldı)
    x_list     = [x["handle"] for x in sources_data["x_accounts"]]  # TÜM hesaplar
    x_url_list = [x["url"]    for x in sources_data["x_accounts"]]  # Tam URL'ler
    news_list  = sources_data["news_sites"][:15]  # 10→15 haber sitesi

    # === 14 GUN HABER & X INTELLIGENCE ===
    global_news  = get_global_news_summary(days=3)
    # Kandidat assetler icin ozel haber ozeti (henuz bilinmiyor,
    # sonradan _format_kandidaten icinde ekleniyor)

    # Gemini bekommt die exakte Symbol-Liste damit er keine Namen erfindet
    symbol_liste  = "\n".join([f"  {k}" for k in MARKET_CONFIG.keys()])
    x_kaynak_str  = ", ".join(x_list) if x_list else "Yukleniyor..."
    haber_str     = "\n   ".join(news_list) if news_list else "Yukleniyor..."

    system_prompt = f"""Sen NEXUS NATURE v15.0 - BRIDGEWATER MACRO FUND Edition modundasin.
Kimlik: Renaissance Technologies / Two Sigma seviyesinde veri odakli karar alici.
Cihat E. Cicek tarzi: direkt, ogretici, Turkce, piyasayi seven bir mentor.
Fiat para = "kagit para" | Enflasyon = "sistematik hirsizlik"

ÖNEMLİ HESAP KURALI - KALDIRAÇ DEVRE DIŞI:
Capital.com hesabında kaldıraç/leverage TAMAMEN KAPALI.
Tüm işlemler 1:1 oranında gerçekleşir - ne koyarsan onu riske atarsın.
CFD olarak işlem görse de ekonomik etki tam hisse/emtia alımı gibidir.
Marjin riski, likidasyasyon riski, kaldıraç kayıpları: MEVCUT DEĞİL.
Buna göre karar ver: Pozisyon büyüklüğünü belirlerken kaldıraç faktörü KULLANMA.
Mevcut Model: {current_model}

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

TRADE FORMAT REGEL: Im TRADE-Befehl IMMER den exakten Symbol-Namen aus obiger Liste verwenden.
FALSCH: HEATINGOIL, NATURALGAS, OILBRENT
RICHTIG: HEATING_OIL, NATURAL_GAS, OIL_BRENT

KRITİK KURALLAR:
1. TEKNİK FİLTRE:
   KRİPTO: 3 timeframe analizi → 20dk (giriş) + 45dk (ara trend) + 2sa (üst trend)
   En az 2/3 timeframe aynı yönü göstermeli + her TF'de min 2/3 indikatör (MA+ADX+RSI)
   FOREX/EMTİA: HOUR_4 tek timeframe, min 2/3 indikatör onayı
2. SPREAD: Maksimum {MAX_SPREAD} spread - yüksek spread'te işlem YOK
3. Pyramiding: Sinir yok - her seviye min %2 karda. EXIT: Gemini karar verir veya Trailing SL (%5) tetiklenir
4. Volatilite: Tek mumda -%10 = HEMEN KAP
5. Gece (23-06): {KRYPTO_NACHT_REGEL_TXT}
6. Haftasonu: SADECE kripto! ALTIN/GUMUS/ENERJI/TARIM YASAK!
   YASAK: GOLD, SILVER, OIL_BRENT, OIL_CRUDE, NATURAL_GAS, HEATING_OIL, GASOLINE, COPPER, WHEAT, CORN, VIX
   HAFTASONU KRIPTO KURALI: Tüm kripto sinyallerini karşılaştır (ADX + RSI + MA gücü).
   EN GÜÇLÜ 1 (bir) kripto asset seç - sadece ona trade yap! Birden fazla kripto pozisyonu YASAK!
   Seçim kriteri: En yüksek guc skoru (3>2>1), eşitse spread en düşük olanı seç.
7. HER KARAR 5 Macro-Spezialisten'den 4+ JA oy almalı - KRIPTO icin 3+ JA yeterli (v15.13)
8. KAPATMA EMRİ: Teknik sinyal bozuldu veya zarar büyüyorsa, mevcut pozisyonu KAPAT (SIDE: SELL bei BUY).
   NOT: Kaldıraç KAPALI (1:1). Sadece teknik/fundamental bozulursa kapat.
9. POZİSYON BOYUTU: Kaldıraç YOK (1:1). Kelly formülü kullan.
   Örnek: €1000 depoda %5 Kelly = €50 pozisyon. Fazlası RİSK!
10. KAPITAL-ASSET KURALI → DEVREdışı (Kaldıraç kapalı = Margin Call yok)
    €0-199 depo = max 1 | €200-399 = max 2 | ... → Bu kural şu an UYGULANMIYOR.
    Kaldıraç tekrar açılırsa Python otomatik aktifleştirir.
    Şu an: Gremium ve Kelly yeterli risk kontrolü sağlıyor.
10. SEN YINEDE KENDI DÜSÜNCENE GÖRE KONTROL ETTIKTEN SONRA ALIM SATIM YAP

GREMİUM (5 Macro-Spezialisten - v15.0 Bridgewater):
Macro_Analyst | Commodity_Expert | Risk_Manager | Timing_Specialist | News_Validator

JIM ROGERS KİMLİĞİ:
"Ben Rogers'ım. 40 yılda dünyayı iki kez motosikletle dolaştım, tarlalara baktım ve
 fabrikaları gördüm - gerçek ekonomiyi. Ben şunu söylerim: Kimse bakmak istemediğinde
 al, herkes coşkuyla alırken sat. Fiat para kağıttır - sadece emtia ve tarım gerçektir.
 Kısa vadeli gürültüye bakma: EMA200'ün altındaki bir varlık bana ucuz görünebilir,
 ama kataliz olmadan hareket etmez. BB Squeeze + EMA50 kırılımı = piyasanın yeniden
 uyandığının işareti. Kripto? Anlamıyorum. Haftasonu trading? Çiftçiler dinlenmez,
 ama ben dinlenirim. Uzun vadeli düşün, makroyu takip et, gerçek varlıklara yönel."
Rogers NEIN der bei: Krypto | Haftasonu | RSI überkauft | kein Katalysator sichtbar
Rogers JA sagt bei: Rogers-Filter aktiv | Rohstoffe/Forex mit starkem Fundamentalgrund

DİNAMİK DOKTRİN:
{dynamic_doctrine}

{bridgewater_rules}

FORMAT (KESİNLİKLE KORU):
NEXUS HESAP DURUMU
Nakit: [EUR]
Toplam Deger: [EUR]
Acik Kar/Zarar: [+/- EUR]

GREMİUM KARAR: [JA/NEIN] ([X]/5 oy)
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

    # ── Gremium-Summary für Gemini-Prompt (mit Begründungen) ───
    _gremium_lines = []
    for _gsym, _gskor in gemini_kandidaten.items():
        _gja     = _gskor.get("gremium_ja", "?")
        _goylar  = _gskor.get("gremium_oylar",  {})
        _grunler = _gskor.get("gremium_grunler", {})
        _tech    = f"Tech:{_gskor.get('score','?')}/{_gskor.get('max_score','?')}"
        _oy_str  = " | ".join([
            f"{m.split('_')[0]}:{v} ({_grunler.get(m,'')[:40]})"
            for m, v in _goylar.items()
        ])
        _gremium_lines.append(f"  {_gsym}: {_gja}/5 JA | {_tech} | {_oy_str}")
    # NOT: Gremium-Oy-Detaylari zaten _format_kandidaten icinde
    # her aday icin ayri ayri prompt'a ekleniyor - burada tekrar
    # hesaplamaya/degiskene gerek yok (gremium_karar_str/ozet_str
    # onceden hesaplaniyor ama hicbir yerde kullanilmiyordu).

    # Kelly boyutlari hesapla
    # Kaynak listesi icin tam format
    # v12.1: URL listesi de eklendi (Gemini Grounding için tam adres)
    x_tam_liste   = "\n".join([f"  {x}" for x in x_list]) if x_list else "  (Yukleniyor...)"
    x_url_tam     = "\n".join([f"  {u}" for u in x_url_list]) if x_url_list else ""
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
MAKRO REJiM: {macro_regime} | VOLATiLiTE: {vol_regime}
KORKU/ACGOZLULUK: {fear_greed["value"]}/100 ({fear_greed["label"]})
DXY CANLI: {dxy_live}
FRED MAKRO: {" | ".join(fred_macro.get("key_data",[])[:4]) if fred_macro.get("status")=="OK" else "FRED N/A"}
MAKRO SINYAL: {macro_signal["signal"]} ({macro_signal["score"]}/100) | {", ".join(macro_signal["details"][:3])}
GUNLUK DURUM: {daily_msg}
EKONOMIK TAKVIM: Sonraki olay={econ_cal["next_event"]} ({econ_cal["days_until"]} gun sonra)
HAVA (AGRAR/Kansas): {wx_agrar["signal"]} - {wx_agrar["notes"]}
HAVA (ENERJi/KuzeyDenizi): {wx_energy["signal"]} - {wx_energy["notes"]}

{alt_data_summary}

=== V14.8 ÖZEL VERİ (Sniper-Daten) ===
EIA PETROL DEPOLARI: {eia_data.get('summary','N/A')}
CFTC COT GOLD:       {cot_gold.get('summary','N/A')}
CFTC COT OIL:        {cot_oil.get('summary','N/A')}
CFTC COT SILVER:     {cot_silver.get('summary','N/A')}
USDA KAKAO:          {usda_cocoa.get('summary','N/A')}
USDA KAHVE:          {usda_coffee.get('summary','N/A')}
USDA BUGDAY:         {usda_wheat.get('summary','N/A')}
TRANSPORT/LKW:       {transport_data.get('summary','N/A')}

=== ACIL UYARILAR ===
Deprem/Afet: {disaster_data["signal"]} | {disaster_data["notes"]}
Emtia Hava: {len(wx_commodity.get("alerts",[]))} aktif uyari
SEZONSAL UYARILAR: {", ".join(seasonal_warns) if seasonal_warns else "Yok"}

=== HESAP ===
Nakit={acc["nakit"]}, Toplam={acc["toplam"]}, UPL={acc["upl"]}, Musait={acc["musait"]} [KALDIRAÇ KAPALI - 1:1]

=== PORTFOY ===
{json.dumps(portfolio, ensure_ascii=False)}

=== TUM TEKNIK TARAMA (Bilgi icin) ===
{json.dumps(tech_sinyaller, ensure_ascii=False)}

=== STAGE 1 GATE-KEEPER SONUCLARI ===
{_format_kandidaten_strict(gemini_kandidaten)}

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
X HESAPLARI ({x_adet} hesap - Google Search Grounding ile oku):
{x_tam_liste}

X TAM URL LiSTESi (bu adresleri Google Search ile kontrol et - hepsi public):
{x_url_tam}

HABER SiTELERi ({news_adet} site):
{news_tam_liste}

NOT: Bu listeyi degistirmek icin GitHub'daki toplam_egitim.txt dosyasini guncelle.
Blacklisted kaynaklar otomatik filtrelenmistir.

EXTRA: {json.dumps(extra_data) if extra_data else "Yok"}

KOMUT: Google Search Grounding ile yukardaki X hesaplarini ve haber sitelerini tara.
X hesaplarinin hepsi public - direkt URL'den oku. Nitter kullanma.
Son 24-48 saat haberleri: DXY, FED, M2, altin, emtia, kripto.
Sonra quant verileri degerlendir, 2-of-3 teknik filtre + spread kontrol + Gremium oylama yap.
Uygun ise TRADE satiri uret. Her trade icin: KAYNAKLAR, GUVEN, UYARILAR yaz."""

    if not [k for k in GEMINI_KEYS if k]: return "GEMINI_KEY_EKSIK"

    # v15.15: Modell-Schleife wie swarm.py (Kette, Key-Wechsel bei 429/401,
    # Modell-Wechsel bei 404 / "limit: 0" / 5xx, Tageslimit-Gedaechtnis)
    resp_text = gemini_chain_generate(full_prompt, lang_ai(system_prompt))  # v15.19
    if resp_text is None:
        logging.error("Tüm model+key kombinasyonları quota dolu!")
        return "QUOTA_FULL_ALL"
    try:
        parse_and_execute_db_commands(resp_text, 0)
        parse_db_fetch_commands(resp_text)
    except Exception as pe:
        logging.warning(f"DB parse hatasi: {pe}")
    return resp_text


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
    system_prompt = f"""Sen NEXUS NATURE v12.0 yapay zeka asistanısın.
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

    return call_ai(full_prompt, system=system_prompt, use_grounding=False)

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

def execute_nexus_trade(analysis, erlaubte_signale=None):
    # v15.10: erlaubte_signale = {SYMBOL: "BUY"/"SELL"} wird nur im KI-Fallback
    # (Gemini-Quota voll) gesetzt. None = normales Verhalten wie bisher.
    pattern = r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*(BUY|SELL)\s*\|\s*SIZE:\s*([\d\.]+)\s*\|\s*SL:\s*([\d\.]+)\s*\|\s*TP:\s*([\d\.]+)"
    matches = re.findall(pattern, analysis)

    if not matches: return None

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
    try:
        closed_position_watch(h)  # v15.18: fuer die Wiedereinstiegs-Sperre (der 5-Minuten-Lauf kann noch ausstehen)
    except Exception as _cw_e:
        logging.debug(f"Schliess-Melder vor Trade: {_cw_e}")
    
    # REGEL 2: Max Positionen (.env: MAX_POSITIONEN, Standard 5)
    if len(current_positions) >= MAX_POSITIONEN:
        return f"⛔ MAX POSITIONEN: {len(current_positions)}/{MAX_POSITIONEN} erreicht - keine neuen Trades"
    
    results = []

    # Strikte Validierung VOR dem Loop (Fix v14.2)
    VALID_SYMBOLS = set(MARKET_CONFIG.keys())
    def normalize(s):
        return re.sub(r'[\s_\-]', '', s.upper())
    def strict_validate(sym_input):
        if sym_input in VALID_SYMBOLS: return sym_input
        sym_n = normalize(sym_input)
        for v in VALID_SYMBOLS:
            if normalize(v) == sym_n:
                logging.info(f"Symbol-Match: '{sym_input}' -> '{v}'")
                return v
        logging.warning(f"Unbekanntes Symbol: '{sym_input}' — Trade abgebrochen")
        return None

    for sym, side, size, sl, tp in matches:
        sym = sym.upper().strip()

        # --- FUZZY SYMBOL MATCHING ---
        matched_sym = strict_validate(sym)
        if matched_sym is None:
            results.append(f"{sym} config'de bulunamadi (esleme basarisiz)")
            continue
        sym = matched_sym

        sym = matched_sym

        cfg = dict(MARKET_CONFIG[sym])
        epic = cfg["epic"]

        # v15.10: Im Fallback nur Symbol + Richtung, die der Python
        # Gate-Keeper in DIESEM Zyklus freigegeben hat.
        if erlaubte_signale is not None and erlaubte_signale.get(sym) != side.upper():
            msg = (f"⛔ FALLBACK-BLOCK {sym} ({side}): nicht vom Gate-Keeper freigegeben "
                   f"(erlaubt: {erlaubte_signale.get(sym, 'nichts')})")
            results.append(msg); logging.warning(msg); continue

        # ── Gremium-Score aus Gate-Keeper holen (Sniper-Verbindung) ─────
        _skor = gemini_kandidaten.get(sym, {})
        cfg["rogers_bonus"]     = _skor.get("rogers_bonus",    False)
        cfg["gremium_ja"]       = _skor.get("gremium_ja",      0)
        cfg["gremium_oylar"]    = _skor.get("gremium_oylar",   {})
        cfg["gremium_grunler"]  = _skor.get("gremium_grunler", {})
        cfg["news_sentiment"]   = _skor.get("news_sentiment",  0.0)
        cfg["tech_score"]       = _skor.get("score",           0)

        # Gremium-Ergebnis loggen (Sniper-Transparenz)
        if _skor:
            _oy_log = " | ".join(
                f"{m.split('_')[0]}:{v}"
                for m, v in cfg["gremium_oylar"].items()
            )
            logging.info(
                f"EXECUTE {sym}: Gremium={cfg['gremium_ja']}/5 JA | "
                f"Tech={cfg['tech_score']} | Sentiment={cfg['news_sentiment']:.2f} | "
                f"{_oy_log}"
            )
        else:
            # Gemini hat Symbol vorgeschlagen das nicht im Gate-Keeper war
            logging.warning(
                f"EXECUTE {sym}: NICHT im Gate-Keeper — "
                f"Gemini hat Symbol ohne Vorprüfung vorgeschlagen!"
            )

        # --- HAFTASONU WHITELIST ---
        # Wochenende: Keine speziellen Krypto-Beschränkungen mehr
        # if is_weekend() and is_crypto(sym):
        #     if sym.upper() not in WEEKEND_CRYPTO_WHITELIST:
        #         msg = f"BLOK {sym}: Haftasonu yasak"
        #         results.append(msg); logging.warning(msg); continue

        # --- TABU CHECK ---
        if sym in TABU_ASSETS:
            msg = f"TABU {sym}: Kesinlikle trade yapilmaz"
            results.append(msg); logging.warning(msg); continue

        # --- HARD BLOCK CHECK (Kullanici talimati - Gemini override edemez!) ---
        hb, hb_reason = check_hard_block(sym, side)
        if hb:
            msg = f"⛔ HARD BLOCK {sym} ({side}): Kullanici talimati aktif — {hb_reason}"
            results.append(msg); logging.warning(msg); continue

        # --- PIYASA ACIK MI? (Capital.com market status) + SPREAD HARD BLOCK ---
        try:
            mkt_r = requests.get(f"{CAPITAL_URL}/markets/{cfg['epic']}",
                                 headers=h, timeout=8)
            if mkt_r.status_code == 200:
                mkt_data  = mkt_r.json()
                tradeable = mkt_data.get("dealingEnabled", True)
                mkt_status = mkt_data.get("snapshot", {}).get("marketStatus", "TRADEABLE")
                if not tradeable or mkt_status not in ("TRADEABLE", "OPEN"):
                    # v15.8: Telegram bildirimi + tahmini açılış saati
                    if is_crypto(sym):
                        _next_open = "Kripto 7/24 açık olmalı — Capital.com oturumu kontrol et"
                    elif mkt_status == "CLOSED":
                        _now_h = datetime.utcnow().hour
                        _now_wd = datetime.utcnow().weekday()  # 0=Mo, 5=Sa, 6=So
                        if _now_wd >= 5:
                            _next_open = "Pazartesi 00:00 UTC (Forex) / 02:00 UTC (Emtia)"
                        elif _now_h >= 21:
                            _next_open = "Yarın 00:00 UTC (Forex) / 02:00 UTC (Emtia)"
                        else:
                            _next_open = f"Bugün açılacak — şu an {_now_h:02d}:xx UTC, bekleniyor"
                    else:
                        _next_open = f"Durum: {mkt_status} — Capital.com panelini kontrol et"
                    msg = (f"⏰ PİYASA KAPALI: {sym}\n"
                           f"Durum: {mkt_status}\n"
                           f"Tahmini açılış: {_next_open}\n"
                           f"→ Trade planlandı ama şu an işlem yapılamaz")
                    bot.send_message(MY_CHAT_ID, msg)
                    results.append(f"KAPALI {sym}: {mkt_status}")
                    logging.warning(f"KAPALI {sym}: {mkt_status} — Telegram bildirimi gönderildi")
                    continue

                # SPREAD HARD BLOCK (.env: MAX_SPREAD) - Gemini bu kurali
                # metinde gormezden gelse bile Python seviyesinde ZORUNLU kontrol
                _snap = mkt_data.get("snapshot", {})
                _bid  = float(_snap.get("bid", 0) or 0)
                _ask  = float(_snap.get("offer", 0) or 0)
                if _bid > 0 and _ask > 0:
                    _live_spread = round(abs(_ask - _bid), 6)
                    spread_ok, spread_reason = check_spread_ok(epic, _live_spread)
                    if not spread_ok:
                        msg = (f"⛔ SPREAD BLOK {sym}: Canli spread {_live_spread} > "
                               f"MAX_SPREAD {MAX_SPREAD} (.env) - Gemini onerse dahi ISLEM REDDEDILDI")
                        results.append(msg); logging.warning(msg); continue
        except Exception as me:
            logging.debug(f"Market status check {sym}: {me}")

        # --- GUNLUK KAYIP KONTROLU (v12.0: sadece uyarı, hard block YOK) ---
        kayip = gunluk_kayip_sayisi(sym)
        if kayip >= 1:
            warn_msg = f"⚠️ UYARI {sym}: Bugun {kayip}x kayip var - Gremium dikkatli olsun"
            results.append(warn_msg); logging.warning(warn_msg)
            # Hard block kaldırıldı: trade devam ediyor
        if MAX_VERLUSTE_PRO_TAG > 0 and kayip >= MAX_VERLUSTE_PRO_TAG:  # v15.16: vorher fest 3
            msg = f"🔴 HARD BLOK {sym}: Bugun {kayip}x kayip (limit={MAX_VERLUSTE_PRO_TAG}) - trade durduruldu"
            results.append(msg); logging.warning(msg); continue

        # FIX6: Alle Positionen dieses Epics (Long + Short)
        epic_positions = [p for p in current_positions if p['market']['epic'] == epic]

        if epic_positions:
            curr_direction = epic_positions[0]['position']['direction']
            is_gegenrichtung = (side == "SELL" and curr_direction == "BUY") or \
                               (side == "BUY" and curr_direction == "SELL")

            # v15.21: Gegensignal = NUR SCHLIESSEN. Es wird keine Gegenposition mehr eroeffnet.
            # Vorher schickte der Bot sofort eine Gegen-Order - ohne die Pruefungen und ohne die
            # Bestaetigung einer normalen Order (05.10.: dreimal gedreht, keine Gegenposition
            # entstanden, einmal blieb sogar die alte Position offen). Bleibt das Signal bestehen,
            # eroeffnet der naechste Scan die neue Richtung als normale Position mit allen Pruefungen.
            if is_gegenrichtung:
                logging.warning(f"EXIT: {sym} {curr_direction}->{side}, {len(epic_positions)} Pos")
                geschlossen = 0
                for pos in epic_positions:
                    try:
                        r = requests.delete(f"{CAPITAL_URL}/positions/{pos['position']['dealId']}", headers=h, timeout=10)
                        if r.status_code == 200:
                            geschlossen += 1
                            try:  # Verlust nur zaehlen, wenn die Position wirklich geschlossen wurde
                                upl_val = float(pos["position"].get("upl", 0) or 0)
                                if upl_val < 0:
                                    kayip_ekle(sym)
                                    logging.warning(f"EXIT kayip: {sym} UPL={upl_val:.2f}")
                            except Exception:
                                pass
                        else:
                            _grund = f"HTTP {r.status_code} {r.text[:120]}"
                            logging.error(f"Exit Fehler {sym}: {_grund}")
                            results.append(f"⚠️ {sym}: Schließen fehlgeschlagen - {_grund}")
                    except Exception as e:
                        logging.error(f"Exit Fehler: {e}")
                        results.append(f"⚠️ {sym}: Schließen fehlgeschlagen - {str(e)[:120]}")
                if geschlossen == len(epic_positions):
                    reset_pyramiding_stufe(epic)
                results.append(f"{sym}: {geschlossen}/{len(epic_positions)} kapatıldı (ÇIKIŞ)")
                if geschlossen > 0:
                    results.append(f"↩️ {sym}: Gegensignal {curr_direction}->{side} - nur geschlossen, keine Gegenposition")
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

        # v15.16: Die Regel oben prueft nur einmal vor der Schleife. Kamen mehrere
        # TRADE-Zeilen auf einmal, wurden es mehr als erlaubt (05.10.: 3 offen + 3 neu = 6).
        # v15.18 WIEDEREINSTIEGS-SPERRE: Das Signal fuer Rohstoffe kommt aus Tageskerzen und
        # aendert sich untertags nicht. Ohne Sperre wurde jede geschlossene Position beim
        # naechsten Scan sofort wieder eroeffnet (05.10.: Crude 3x, Heating Oil 3x an einem Tag).
        if not epic_positions and WIEDEREINSTIEG_SPERRE_STD > 0:
            _zu_ts = letzte_schliessung(epic, side.upper())
            _rest_s = WIEDEREINSTIEG_SPERRE_STD * 3600 - (time.time() - _zu_ts)
            if _zu_ts > 0 and _rest_s > 0:
                msg = (f"⏳ {sym} {side.upper()}: vor {int((time.time() - _zu_ts) // 60)} min geschlossen - "
                       f"Wiedereinstieg gesperrt, noch {int(_rest_s // 3600)} h {int(_rest_s % 3600 // 60)} min "
                       f"(WIEDEREINSTIEG_SPERRE_STD={WIEDEREINSTIEG_SPERRE_STD:g})")
                results.append(msg); logging.info(msg); continue
        if not epic_positions:
            _offen_pos = get_positions(h) or []
            _offen_n = len(_offen_pos)
            if _offen_n >= MAX_POSITIONEN:
                msg = f"⛔ {sym}: MAX POSITIONEN {_offen_n}/{MAX_POSITIONEN} erreicht - nicht eröffnet"
                results.append(msg); logging.warning(msg); continue
            # v15.24 GRUPPEN-LIMIT (.env MAX_JE_GRUPPE, 0 = aus)
            if MAX_JE_GRUPPE > 0:
                _grp, _grp_offen = gruppen_belegt(sym, epic, _offen_pos)
                if _grp and len(_grp_offen) >= MAX_JE_GRUPPE:
                    msg = (f"⛔ {sym}: Gruppen-Limit {len(_grp_offen)}/{MAX_JE_GRUPPE} - aus derselben Gruppe "
                           f"schon offen: {', '.join(_grp_offen)} - nicht eröffnet")
                    results.append(msg); logging.warning(msg); continue

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
            # v12.1: Backtest mesajı sadece log'a yazılıyor (Telegram quota tasarrufu)

            # Backtest cok kotu ise uyari
            if not bt_ok:
                msg = (f"⚠️ {sym} backtest zayif "
                       f"(WR<35% veya yetersiz veri) - "
                       f"trade devam ediyor ama dikkat!")
                results.append(msg)
                logging.warning(msg)

            # DB'ye kaydet
            try:
                db_gemini_write(
                    "PRE_BACKTEST",
                    f"{sym} {side}: Best={best_tf} | " +
                    " | ".join([f"{l}:WR={r.get('win_rate','?')}"
                                for l,r in bt_all.items() if "error" not in r]),
                    sym
                )
            except: pass

        except Exception as bt_e:
            logging.warning(f"Pre-BT hatasi {sym}: {bt_e}")
            best_tf = "4sa"  # Varsayilan

        # SL-minimum mesafe pruefen und korrigieren
        sl_float = float(sl)
        tp_float = float(tp)
        current_price = 0.0  # v15.10: definiert, auch wenn die Preisabfrage scheitert
        _sl_min_dist, _sl_min_info = 0.0, ""  # v15.17: Rausch-Schutz (wird unten nochmal gebraucht)
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
                min_stop_pct = cfg.get('min_stop_pct', 0.015)  # FIX v14.9: 1.5% default (war 0.2% → zu eng)
                if is_weekend() and is_crypto(sym):
                    min_stop_pct *= 2.5  # Haftasonu kripto: daha genis SL
                # v15.17 RAUSCH-SCHUTZ: Mindestabstand = Tagesspanne (Tages-ATR) x SL_ATR_MULT,
                # mindestens der feste Abstand von oben. Vorher nur der feste Abstand (1.5%):
                # bei 4-5% normaler Tagesspanne loeste schon das Tagesrauschen den Stop aus.
                _sl_min_dist, _sl_min_info = sl_min_distance(epic, current_price, min_stop_pct)
                old_sl = sl_float
                sl_float, _sl_geaendert = sl_auf_mindestabstand(side, sl_float, current_price, _sl_min_dist)
                if _sl_geaendert:
                    logging.warning(f"{sym} SL düzeltildi: {old_sl} -> {sl_float} (minimum mesafe: {_sl_min_info})")
                    results.append(f"{sym} SL güncellendi: {old_sl} -> {sl_float} ({_sl_min_info})")
        except Exception as e:
            logging.warning(f"{sym} fiyat kontrolü başarısız: {e}")

        # v15.10: Ohne Live-Preis kann nichts geprueft werden -> kein Trade
        if not current_price or current_price <= 0:
            msg = f"⛔ {sym}: kein Live-Preis von Capital.com -> Trade verworfen"
            results.append(msg); logging.warning(msg); continue

        # ATR-SL Check (v14.0) - stuendliche ATR, korrigiert nur SL
        try:
            _atr_sl, _atr_v, _atr_i = get_atr_stop_loss(epic, current_price, side.upper())
            if _atr_v > 0:
                _sl_pct = abs(current_price - sl_float) / current_price * 100
                if _sl_pct < 0.3 or _sl_pct > 8:
                    logging.info(f"ATR-SL: {sym} KI-SL {sl_float} ({_sl_pct:.1f}%) → {_atr_sl}")
                    sl_float = _atr_sl
        except Exception as _ae:
            logging.debug(f"ATR-SL {sym}: {_ae}")

        # ATR-TP/SL Fallback (v15.5, Tages-ATR): Gemini'nin TP degeri
        # eksikse veya fiyata cok yakinsa (<%0.3, pratikte anlamsiz),
        # Gunluk ATR bazli guvenli bir TP/SL devreye girer.
        # TP=%90 / SL=%40 Gunluk-ATR (RR ~1:2.25). Gemini duzgun bir
        # TP/SL verdiyse buraya hic dokunulmaz.
        try:
            _atr_tp2, _atr_sl2, _daily_atr = get_atr_tp_sl(epic, current_price, side.upper())
            if tp_float <= 0 or abs(tp_float - current_price) / current_price * 100 < 0.3:
                logging.info(f"ATR-TP Fallback: {sym} TP {tp_float} -> {_atr_tp2} (Gunluk-ATR={_daily_atr})")
                tp_float = _atr_tp2
            if sl_float <= 0 or abs(sl_float - current_price) / current_price * 100 < 0.3:
                logging.info(f"ATR-SL Fallback: {sym} SL {sl_float} -> {_atr_sl2} (Gunluk-ATR={_daily_atr})")
                sl_float = _atr_sl2
        except Exception as _atr_e:
            logging.debug(f"ATR-TP/SL Fallback {sym}: {_atr_e}")

        # v15.17: Die beiden ATR-Pruefungen oben koennen den Stop wieder enger setzen
        # (Stunden-ATR x 2 bzw. 40% der Tagesspanne). Mindestabstand zum Schluss sichern.
        if _sl_min_dist > 0:
            _sl_vor = sl_float
            sl_float, _sl_geaendert = sl_auf_mindestabstand(side, sl_float, current_price, _sl_min_dist)
            if _sl_geaendert:
                logging.warning(f"{sym} SL düzeltildi: {_sl_vor} -> {sl_float} (minimum mesafe: {_sl_min_info})")
                results.append(f"{sym} SL güncellendi: {_sl_vor} -> {sl_float} ({_sl_min_info})")

        # v15.10 Plausibilitaet: SL und TP muessen auf der richtigen Seite des
        # Live-Kurses liegen. Sonst stammen die Preise nicht aus echten
        # Marktdaten (KI-Halluzination) -> Trade wird verworfen.
        if side.upper() == "BUY":
            _preise_ok = sl_float < current_price < tp_float
        else:
            _preise_ok = tp_float < current_price < sl_float
        if not _preise_ok:
            msg = (f"⛔ {sym} {side}: SL/TP unplausibel (Kurs {current_price}, "
                   f"SL {sl_float}, TP {tp_float}) -> Trade verworfen")
            results.append(msg); logging.warning(msg); continue

        # v15.10: Groesse EINMAL berechnen (aus .env, nicht aus dem KI-Wert)
        # und ueberall denselben Wert verwenden.
        _units = safe_trade_size(size, cfg, epic)
        if not _units or _units <= 0:
            msg = (f"⛔ {sym}: Groesse ausserhalb der .env-Limits oder Depot/Kurs "
                   f"nicht lesbar -> kein Trade")
            results.append(msg); logging.warning(msg); continue

        # Margin Check v14.9 (v15.10: echte Units + richtiges Depot-Feld "musait")
        try:
            _acc_m = get_account_info(h) or {}
            _cash  = float(_acc_m.get("musait", 0) or 0)
            _trade_eur = float(_units) * current_price * 0.88
            if _cash > 10 and _trade_eur > _cash * 0.90:
                logging.warning(f"Margin ENGEL: {sym} ~{_trade_eur:.0f}€ > 90% von {_cash:.0f}€")
                results.append(f"Margin ENGEL: {sym}")
                continue
        except Exception as _me:
            logging.debug(f"Margin Check: {_me}")

        payload = {
            "epic": epic, "direction": side.upper(),
            "size": _units,
            "type": "MARKET", "stopLevel": sl_float, "profitLevel": tp_float
        }
        r = requests.post(f"{CAPITAL_URL}/positions", json=payload, headers=h, timeout=10)
        if r.status_code == 200:
            # v15.8: Post-Order Verifikation — wirklich offen?
            import time as _time
            _time.sleep(8)  # Capital.com braucht ~5-8 Sek bis Position erscheint
            _verify_positions = get_positions(h)
            _pos_confirmed = any(p['market']['epic'] == epic for p in _verify_positions)
            if _pos_confirmed:
                _confirm_msg = (f"✅ POZİSYON ONAYLANDI: {sym}\n"
                                f"Yön: {side} | Size: {_units}\n"
                                f"SL: {sl_float} | TP: {tp_float}\n"
                                f"Capital.com depo doğrulandı ✓")
            else:
                _confirm_msg = (f"⚠️ POZİSYON DOĞRULANAMADI: {sym}\n"
                                f"Order gönderildi (HTTP 200) ama depoda pozisyon görünmüyor.\n"
                                f"Olası neden: Piyasa kapalı veya Capital.com gecikmesi.\n"
                                f"→ Lütfen Capital.com panelini kontrol et!")
            bot.send_message(MY_CHAT_ID, _confirm_msg)
            logging.info(f"Post-Order Verify {sym}: {'OK' if _pos_confirmed else 'NICHT GEFUNDEN'}")

            stufe = get_pyramiding_stufe(epic) + 1
            set_pyramiding_stufe(epic, stufe)
            results.append(f"{sym} yeni pozisyon açıldı ({side}) Seviye {stufe}")
            # DB'ye kaydet
            try:
                db_open_trade(
                    symbol=sym, direction=side, size=_units,
                    entry_price=sl_float, sl=sl_float, tp=tp_float,
                    spread=float(cfg.get("spread", 0)),
                    gremium_score="?",
                    macro_regime=get_macro_regime(get_fear_greed().get('value', 50), get_volatility_regime({})),
                    fear_greed=get_fear_greed().get('value', 50),
                )
            except Exception as db_e:
                logging.warning(f"DB Trade kayit hatasi: {db_e}")
            sync_ok = 0
            alle_pos_aktuell = get_positions(h)
            for pos in [p for p in alle_pos_aktuell if p['market']['epic'] == epic]:
                try:
                    r_upd = requests.put(
                        f"{CAPITAL_URL}/positions/{pos['position']['dealId']}",
                        json={"stopLevel": sl_float, "profitLevel": tp_float},  # v15.10: korrigierte Werte
                        headers=h, timeout=10)
                    if r_upd.status_code == 200: sync_ok += 1
                except Exception as e:
                    logging.error(f"SL/TP Sync Fehler: {e}")
            if sync_ok > 0:
                results.append(f"{sym} SL/TP senkron: {sync_ok} Pos -> SL:{sl_float} TP:{tp_float}")
            # Trailing SL peak state - hemen initialize et (5 dk bekleme)
            try:
                trail_state = _load_trailing_state()
                peak_key = "peak_" + epic + "_" + side.upper()
                if peak_key not in trail_state:
                    # v14.9 FIX: Echter Einstiegspreis als Peak — NICHT SL/0.95!
                    # SL/0.95 war der Bug → falscher Peak → SL zu früh ausgelöst (-€251)
                    if current_price and current_price > 0:
                        initial_peak = current_price
                    else:
                        # Fallback: SL + vernünftiger Abstand (nicht mathematisch invertiert)
                        initial_peak = float(sl_float) * 1.01 if side.upper() == "BUY" else float(sl_float) * 0.99
                    trail_state[peak_key] = {
                        "value": round(initial_peak, 5),
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    _save_trailing_state(trail_state)
                    results.append(f"{sym} Trailing SL aktif: -%5 ({round(initial_peak,3)} peak = Einstandspreis)")
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
# ============================================================
# v15.20: /diagnose - Bericht von nexus_diagnose.py per Telegram
# ------------------------------------------------------------
# nexus_diagnose.py liegt als eigene Datei neben nexus_ceo.py (wie nexus_lang.py) und
# liest nur. Der Bot startet es als eigenen Prozess: Die Kurzfassung kommt als Nachricht,
# der ganze Bericht als Textdatei. Aufruf: /diagnose  oder  /diagnose 3  (Tage, 1-30).
# ============================================================
_DIAG_LOCK = threading.Lock()
_DIAG_TIMEOUT = 240


def _diagnose_lauf(tage):
    pfad = os.path.join(BASE_DIR, "nexus_diagnose.py")
    if not os.path.isfile(pfad):
        bot.send_message(MY_CHAT_ID, "⚠️ nexus_diagnose.py fehlt im Bot-Ordner - Diagnose nicht möglich.")
        return
    if not _DIAG_LOCK.acquire(blocking=False):
        bot.send_message(MY_CHAT_ID, "🔎 Diagnose läuft schon - bitte warten.")
        return
    try:
        import subprocess as _sp
        import io as _io
        bot.send_message(MY_CHAT_ID, f"🔎 Diagnose läuft ({tage} Tage) ... das dauert bis zu einer Minute.")
        sprache = BOT_LANGUAGE if BOT_LANGUAGE in ("de", "en", "tr") else "de"
        try:
            lauf = _sp.run([sys.executable, pfad, "--dir", BASE_DIR, "--days", str(tage), "--lang", sprache],
                           capture_output=True, text=True, timeout=_DIAG_TIMEOUT)
        except _sp.TimeoutExpired:
            bot.send_message(MY_CHAT_ID, f"⚠️ Diagnose abgebrochen: nach {_DIAG_TIMEOUT} Sekunden nicht fertig.")
            return
        bericht = lauf.stdout or ""
        if not bericht.strip():
            grund = (lauf.stderr or "keine Ausgabe").strip().splitlines()[-1][:200]
            bot.send_message(MY_CHAT_ID, f"⚠️ Diagnose fehlgeschlagen: {grund}")
            return
        # Kurzfassung = alles nach der Zeile KURZFASSUNG (steht schon in der gewaehlten Sprache)
        kurz, zeilen = "", bericht.splitlines()
        for i, z in enumerate(zeilen):
            if z.strip() == "KURZFASSUNG":
                kurz = "\n".join(x for x in zeilen[i + 2:] if x.strip() and x.strip() != "Fertig.")
        if kurz:
            for i in range(0, len(kurz), 3900):
                _bot_send_raw(MY_CHAT_ID, kurz[i:i + 3900])
        datei = _io.BytesIO(bericht.encode("utf-8"))
        datei.name = "nexus_diagnose_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M")
        bot.send_document(MY_CHAT_ID, datei, caption=L("Vollständiger Diagnose-Bericht (auf Deutsch)"))
        logging.info(f"Diagnose gesendet: {tage} Tage, {len(zeilen)} Zeilen")
    except Exception as e:
        logging.error(f"Diagnose: {e}")
        try:
            bot.send_message(MY_CHAT_ID, f"⚠️ Diagnose fehlgeschlagen: {str(e)[:200]}")
        except Exception:
            pass
    finally:
        _DIAG_LOCK.release()


@bot.message_handler(commands=CMD('diagnose'))
def handle_diagnose(message):
    """v15.20: /diagnose [Tage] - Diagnose-Bericht per Telegram (auch ueber die Taste)."""
    teile = (message.text or "").split()
    try:
        tage = max(1, min(30, int(teile[1]))) if len(teile) > 1 else 7
    except ValueError:
        tage = 7
    threading.Thread(target=_diagnose_lauf, args=(tage,), daemon=True).start()


# ============================================================
# v15.23: /handbuch - das komplette Handbuch als Datei per Telegram
# ------------------------------------------------------------
# Quelle: MANUAL.<sprache>.md neben dem Bot oder im Unterordner docs/. Fehlt die Datei oder
# gehoert sie zu einer anderen Version, laedt der Bot sie von GitHub (HANDBUCH_URL in der
# .env aenderbar). Am Ende haengt der Bot eine Tabelle mit den Werten an, die er JETZT benutzt
# (aus den Handbuch-Tabellen Handel / Stop Loss / KI; Zugangsdaten stehen dort nicht und
# werden ausserdem namentlich ausgefiltert). Aufruf: /handbuch  oder  /handbuch en  (de, en, tr).
# ============================================================
_HB_LOCK = threading.Lock()
HANDBUCH_URL = os.getenv("HANDBUCH_URL") or "https://raw.githubusercontent.com/KhungFu/nexus/main/docs/MANUAL.{lang}.md"
_HB_GEHEIM = re.compile(r"KEY|TOKEN|PASS|SECRET|CHAT_ID|LOGIN|MAIL|IDENTIFIER|COOKIE|URL", re.I)
_HB_TXT = {
    "de": {"titel": "Anhang L – Deine Einstellungen jetzt (live aus der .env, Stand {0}, Bot {1})",
           "kopf": ("Eintrag", "Dein Wert", "Standard"), "leer": "nicht gesetzt",
           "info": "Diese Tabelle zeigt die Werte, mit denen der Bot gerade läuft. Änderungen in der .env wirken erst nach einem Neustart.",
           "start": "📘 Handbuch wird erstellt ...",
           "cap": "📘 NEXUS-Handbuch (Deutsch), Stand {0}, Bot {1}. Am Ende: deine Einstellungen von jetzt.",
           "fehlt": "⚠️ Handbuch nicht gefunden: weder im Bot-Ordner (MANUAL.{0}.md oder docs/) noch von GitHub ladbar ({1}).",
           "fehler": "⚠️ Handbuch fehlgeschlagen: {0}"},
    "en": {"titel": "Appendix L – Your settings right now (live from the .env, as of {0}, bot {1})",
           "kopf": ("Entry", "Your value", "Default"), "leer": "not set",
           "info": "This table shows the values the bot is running with right now. Changes in the .env only take effect after a restart.",
           "start": "📘 Creating the manual ...",
           "cap": "📘 NEXUS manual (English), as of {0}, bot {1}. At the end: your settings right now.",
           "fehlt": "⚠️ Manual not found: neither in the bot folder (MANUAL.{0}.md or docs/) nor downloadable from GitHub ({1}).",
           "fehler": "⚠️ Manual failed: {0}"},
    "tr": {"titel": "Ek L – Şu anki ayarların (canlı olarak .env'den, {0}, bot {1})",
           "kopf": ("Ayar", "Senin değerin", "Varsayılan"), "leer": "ayarlı değil",
           "info": "Bu tablo botun şu anda çalıştığı değerleri gösterir. .env'deki değişiklikler yalnızca yeniden başlatmadan sonra geçerli olur.",
           "start": "📘 Kılavuz hazırlanıyor ...",
           "cap": "📘 NEXUS kılavuzu (Türkçe), {0}, bot {1}. Sonunda: şu anki ayarların.",
           "fehlt": "⚠️ Kılavuz bulunamadı: ne bot klasöründe (MANUAL.{0}.md veya docs/) ne de GitHub'dan indirilebildi ({1}).",
           "fehler": "⚠️ Kılavuz başarısız: {0}"},
}
_HB_NAME = {"de": "Handbuch", "en": "Manual", "tr": "Kilavuz"}


def _hb_version(text):
    m = re.search(r"\(v(\d+\.\d+)\)", (text or "")[:300])
    return "v" + m.group(1) if m else None


def _hb_lade(lang):
    """(Text, Quelle). Reihenfolge: passende Datei neben dem Bot, sonst GitHub, sonst irgendeine Datei."""
    name = "MANUAL.%s.md" % lang
    lokal = None
    for p in (os.path.join(BASE_DIR, name), os.path.join(BASE_DIR, "docs", name)):
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                lokal = (f.read(), p)
            break
    if lokal and _hb_version(lokal[0]) == NEXUS_VERSION:
        return lokal
    url = HANDBUCH_URL.format(lang=lang)
    fehler = ""
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.text.strip():
            return r.text, url
        fehler = "HTTP %s" % r.status_code
    except Exception as e:
        fehler = str(e)[:100]
    if lokal:
        return lokal
    raise FileNotFoundError(fehler or "leer")


def _hb_live(text, lang):
    """Tabelle der aktuellen Werte aus den .env-Tabellen des Handbuchs (Kapitel 11)."""
    t = _HB_TXT[lang]
    a = text.find("\n## 11.")
    if a < 0:
        return ""
    b = text.find("\n## 12.", a + 1)
    teile = re.split(r"\n### ", text[a:b if b > 0 else len(text)])
    zeilen, gesehen = [], set()
    for tl in teile[1:-1]:            # letzte Unterrubrik (Zugang und Datenquellen) bleibt aussen vor
        for z in tl.splitlines():
            if not z.startswith("|"):
                continue
            zellen = [c.strip() for c in z.strip().strip("|").split("|")]
            if len(zellen) < 2:
                continue
            for n in re.findall(r"`([A-Z][A-Z0-9_]+)`", zellen[0]):
                if n in gesehen or _HB_GEHEIM.search(n):
                    continue
                gesehen.add(n)
                wert = BOT_LANGUAGE if n == "BOT_LANGUAGE" else os.getenv(n)
                wert = (wert or "").strip()
                wert = (wert[:57] + "...") if len(wert) > 60 else wert
                zeilen.append("| `%s` | %s | %s |" % (n, ("`%s`" % wert) if wert else "_%s_" % t["leer"],
                                                      zellen[1].replace("\n", " ")))
    if not zeilen:
        return ""
    k = t["kopf"]
    return ("\n\n---\n\n## %s\n\n%s\n\n| %s | %s | %s |\n| --- | --- | --- |\n%s\n"
            % (t["titel"].format(datetime.now().strftime("%d.%m.%Y %H:%M"), NEXUS_VERSION), t["info"],
               k[0], k[1], k[2], "\n".join(zeilen)))


def _handbuch_lauf(lang):
    t = _HB_TXT[lang]
    if not _HB_LOCK.acquire(blocking=False):
        return
    try:
        import io as _io
        _bot_send_raw(MY_CHAT_ID, t["start"])
        try:
            text, quelle = _hb_lade(lang)
        except Exception as e:
            _bot_send_raw(MY_CHAT_ID, t["fehlt"].format(lang, str(e)[:100]))
            return
        text = text.rstrip("\n") + _hb_live(text, lang)
        datei = _io.BytesIO(text.encode("utf-8"))
        datei.name = "NEXUS_%s_%s_%s.md" % (_HB_NAME[lang], lang, datetime.now().strftime("%Y%m%d"))
        bot.send_document(MY_CHAT_ID, datei, caption=t["cap"].format(_hb_version(text) or "?", NEXUS_VERSION))
        logging.info("Handbuch gesendet: %s, %d Zeichen, Quelle %s" % (lang, len(text), quelle))
    except Exception as e:
        logging.error("Handbuch: %s" % e)
        try:
            _bot_send_raw(MY_CHAT_ID, t["fehler"].format(str(e)[:200]))
        except Exception:
            pass
    finally:
        _HB_LOCK.release()


@bot.message_handler(commands=CMD('handbuch'))
def handle_handbuch(message):
    """v15.23: /handbuch [de|en|tr] - komplettes Handbuch als Datei, mit den Einstellungen von jetzt."""
    teile = (message.text or "").split()
    lang = teile[1].lower() if len(teile) > 1 and teile[1].lower() in ("de", "en", "tr") else \
        (BOT_LANGUAGE if BOT_LANGUAGE in ("de", "en", "tr") else "de")
    threading.Thread(target=_handbuch_lauf, args=(lang,), daemon=True).start()


# ============================================================
# v16.0 GREMIUM - 11 Mentoren stimmen unabhaengig ab (nexus_gremium.py)
# ------------------------------------------------------------
# Vorher: fuenf feste Wenn-dann-Regeln mit Mentoren-Namen (gremium_oylama), die
# alle JA sagten, sobald das Tages-MA-Signal Staerke 2 hatte. Die KI bekam die
# Richtung vorgegeben und im Ersatzbetrieb fast keine Daten.
# Jetzt: Python baut je Kandidat ein Dossier mit echten Daten, jedes Mitglied
# stimmt in einem eigenen KI-Aufruf ab (BUY/SELL/BEKLE), Python zaehlt, der
# Vorsitz prueft. Alle Python-Sperren in execute_nexus_trade gelten weiter.
# .env GREMIUM_MODUS=regeln stellt den alten Ablauf wieder her.
# ============================================================
try:
    import nexus_gremium as _NG
except Exception as _ng_e:
    _NG = None
    logging.error(f"nexus_gremium.py fehlt oder fehlerhaft ({_ng_e}) - Gremium im alten Modus")

_GD = None
if _NG is not None:
    try:
        _GD = _NG.Gedaechtnis(os.path.join(BASE_DIR, "nexus_gremium.db"))
    except Exception as _gd_e:
        logging.error(f"Gremium-Gedaechtnis: {_gd_e}")

_GREMIUM_LOCK = threading.Lock()


def gremium_aktiv():
    return GREMIUM_MODUS == "ki" and _NG is not None and _GD is not None


def _gremium_lang():
    return BOT_LANGUAGE if BOT_LANGUAGE in ("de", "en", "tr") else "tr"


def _gremium_senden(text):
    """Bericht in der Bot-Sprache senden (ohne Regel-Uebersetzung), in Stuecken <= 4000 Zeichen."""
    rest = text or ""
    while rest:
        if len(rest) <= 4000:
            stueck, rest = rest, ""
        else:
            cut = rest.rfind("\n", 0, 4000)
            cut = cut if cut > 0 else 4000
            stueck, rest = rest[:cut], rest[cut:].lstrip("\n")
        try:
            _bot_send_raw(MY_CHAT_ID, stueck)
        except Exception as e:
            logging.warning(f"Gremium-Bericht: {e}")
            return


def _g_ema(werte, n):
    if len(werte) < n:
        return None
    k = 2.0 / (n + 1)
    e = sum(werte[:n]) / n
    for v in werte[n:]:
        e = v * k + e * (1 - k)
    return e


def _g_rsi(werte, n=14):
    if len(werte) <= n:
        return None
    gew, ver = 0.0, 0.0
    for i in range(1, n + 1):
        d = werte[i] - werte[i - 1]
        gew += max(d, 0); ver += max(-d, 0)
    gew /= n; ver /= n
    for i in range(n + 1, len(werte)):
        d = werte[i] - werte[i - 1]
        gew = (gew * (n - 1) + max(d, 0)) / n
        ver = (ver * (n - 1) + max(-d, 0)) / n
    return 100.0 if ver == 0 else 100 - 100 / (1 + gew / ver)


def _g_pct(a, b):
    return (a - b) / b * 100 if b else 0.0


_G_NEWS_TAG = {"OIL_CRUDE": "OIL_BRENT", "OIL_BRENT": "OIL_BRENT", "HEATING_OIL": "OIL_BRENT",
               "GASOLINE": "OIL_BRENT", "NATURALGAS": "NATURAL_GAS", "NATURAL_GAS": "NATURAL_GAS"}


def _gremium_makro():
    """Daten, die fuer alle Kandidaten gleich sind - einmal je Scan. Jede Quelle einzeln
    abgesichert: faellt eine aus, steht das im Dossier, statt dass alles scheitert."""
    m = {}
    def _q(key, fn):
        try:
            m[key] = fn()
        except Exception as e:
            m[key] = None
            logging.debug(f"Gremium-Makro {key}: {e}")
    _q("fg", get_fear_greed)
    _q("dxy", get_dxy_live)
    _q("fred", get_fred_macro_signal)
    _q("cal", get_economic_calendar)
    _q("eia", get_eia_petroleum)
    _q("cot_gold", lambda: get_cot_positioning("GOLD"))
    _q("cot_oil", lambda: get_cot_positioning("OIL"))
    _q("cot_silver", lambda: get_cot_positioning("SILVER"))
    _q("usda_wheat", lambda: get_usda_supply_demand("Wheat"))
    _q("usda_coffee", lambda: get_usda_supply_demand("Coffee"))
    _q("usda_cocoa", lambda: get_usda_supply_demand("Cocoa"))
    _q("wx_agrar", lambda: get_weather_signal("AGRAR"))
    _q("wx_energy", lambda: get_weather_signal("ENERGY"))
    try:
        fg_val = (m.get("fg") or {}).get("value", 50)
        m["regime"] = get_macro_regime(fg_val, get_volatility_regime({}))
    except Exception:
        m["regime"] = "?"
    return m


def _g_sum(d, feld="summary"):
    if isinstance(d, dict):
        return str(d.get(feld) or d.get("notes") or d.get("signal") or "k. A.")[:300]
    return "k. A."


def _gremium_dossier(sym, cfg, h, makro, positionen, acc, tech):
    """Dossier fuer einen Kandidaten. Rueckgabe (text, info) - info: kurs, bid, ask, spread, atr_pct, tech."""
    epic = cfg["epic"]
    info = {"kurs": 0.0, "bid": 0.0, "ask": 0.0, "spread": 0.0, "atr_pct": 0.0, "status": "?",
            "tech": f"{tech.get('sinyal')} (Stärke {tech.get('guc')})"}
    z = []
    jetzt = datetime.now()
    z.append(f"=== DOSSIER {sym} ({cfg.get('name', epic)}) | {jetzt.strftime('%a %d.%m.%Y %H:%M')} Ortszeit | "
             f"Gruppe: {markt_gruppe(sym) or markt_gruppe(epic) or '-'} ===")

    # Kurs
    try:
        r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=10)
        snap = r.json().get("snapshot", {}) if r.status_code == 200 else {}
        info["bid"] = float(snap.get("bid", 0) or 0)
        info["ask"] = float(snap.get("offer", 0) or 0)
        info["status"] = snap.get("marketStatus", "?")
        info["kurs"] = (info["bid"] + info["ask"]) / 2 if info["bid"] and info["ask"] else info["bid"]
        info["spread"] = round(abs(info["ask"] - info["bid"]), 6) if info["bid"] and info["ask"] else 0.0
    except Exception as e:
        logging.debug(f"Gremium-Kurs {sym}: {e}")
    k = info["kurs"]
    z.append(f"KURS: Bid {info['bid']} / Ask {info['ask']} | Spread {info['spread']}"
             + (f" ({info['spread'] / k * 100:.3f} % vom Kurs)" if k else "") + f" | Markt: {info['status']}")

    # Tagesspanne
    try:
        atr, atr_pct, _ = get_daily_atr(epic)
        info["atr_pct"] = float(atr_pct or 0)
        z.append(f"TAGESSPANNE (ATR 14 Tage): {atr} = {atr_pct} % vom Kurs")
    except Exception:
        z.append("TAGESSPANNE: k. A.")

    # Technik Tag
    try:
        data, _err = get_candles(epic, "DAY", 210)
        c = (data or {}).get("close", []) if data else []
        c = [float(x) for x in c if x]
        if len(c) >= 30:
            last = c[-1]
            e20, e50, e200 = _g_ema(c, 20), _g_ema(c, 50), _g_ema(c, 200)
            def _abst(e):
                return f"{e:.5g} ({_g_pct(last, e):+.1f} %)" if e else "k. A."
            hi, lo = max(c), min(c)
            z.append(f"TECHNIK TAG ({len(c)} Kerzen): Schluss {last:.6g} | EMA20 {_abst(e20)} | EMA50 {_abst(e50)} | EMA200 {_abst(e200)}")
            z.append(f"  Veränderung: 5 Tage {_g_pct(last, c[-6]):+.1f} % | 20 Tage {_g_pct(last, c[-21]):+.1f} % | "
                     + (f"60 Tage {_g_pct(last, c[-61]):+.1f} % | " if len(c) > 61 else "")
                     + f"Spanne {len(c)} Tage: {lo:.6g} - {hi:.6g} (Kurs bei {(last - lo) / (hi - lo) * 100 if hi > lo else 50:.0f} %)"
                     + (f" | RSI14 {_g_rsi(c):.0f}" if _g_rsi(c) is not None else ""))
        else:
            z.append(f"TECHNIK TAG: zu wenige Kerzen ({len(c)})")
    except Exception as e:
        z.append(f"TECHNIK TAG: k. A. ({str(e)[:60]})")
    z.append(f"SIGNAL PYTHON (Tages-MA/ADX/RSI): {tech.get('sinyal')} Stärke {tech.get('guc')} | {str(tech.get('aciklama', ''))[:200]}")
    if tech.get("skor"):
        z.append(f"  Score {tech['skor'].get('score', '?')}/{tech['skor'].get('max_score', '?')}: {str(tech['skor'].get('details', ''))[:250]}")

    # Technik 4h (kurzfristige Bestaetigung)
    if not is_crypto(sym):
        try:
            s4, g4, d4 = _analyse_timeframe(epic, "HOUR_4", 30)
            z.append(f"TECHNIK 4H: {s4} Stärke {g4} | {str(d4)[:160]}")
        except Exception:
            z.append("TECHNIK 4H: k. A.")

    # Fundamentaldaten je Gruppe
    grp = markt_gruppe(sym) or markt_gruppe(epic)
    su = sym.upper()
    fund = []
    if grp == "ENERGIE":
        fund.append("EIA Öl-Lager: " + _g_sum(makro.get("eia")))
        fund.append("COT Öl: " + _g_sum(makro.get("cot_oil")))
        fund.append("Wetter Energie: " + _g_sum(makro.get("wx_energy"), "notes"))
    if "GOLD" in su:
        fund.append("COT Gold: " + _g_sum(makro.get("cot_gold")))
    if "SILVER" in su:
        fund.append("COT Silber: " + _g_sum(makro.get("cot_silver")))
    if grp == "AGRAR":
        if "WHEAT" in su: fund.append("USDA Weizen: " + _g_sum(makro.get("usda_wheat")))
        if "COFFEE" in su: fund.append("USDA Kaffee: " + _g_sum(makro.get("usda_coffee")))
        if "COCOA" in su: fund.append("USDA Kakao: " + _g_sum(makro.get("usda_cocoa")))
        fund.append("Wetter Agrar: " + _g_sum(makro.get("wx_agrar"), "notes"))
    if fund:
        z.append("FUNDAMENTAL: " + " | ".join(fund))

    # Makro
    fg = makro.get("fg") or {}
    fred = makro.get("fred") or {}
    cal = makro.get("cal") or {}
    fred_txt = " | ".join((fred.get("key_data") or [])[:4]) if isinstance(fred, dict) and fred.get("status") == "OK" else "k. A."
    z.append(f"MAKRO: Regime {makro.get('regime', '?')} | Fear&Greed {fg.get('value', '?')} ({fg.get('label', '?')}) | "
             f"DXY {makro.get('dxy') if makro.get('dxy') is not None else 'k. A.'} | FRED: {fred_txt}"
             + (f" | FRED-Signal {fred.get('signal')}" if isinstance(fred, dict) and fred.get("signal") else ""))
    z.append(f"TERMINE: nächster großer Termin {cal.get('next_event', '?')} in {cal.get('days_until', '?')} Tagen "
             "(Schätzung aus dem Kalender: NFP erster Freitag, CPI Mitte Monat)")

    # Nachrichten zum Asset
    try:
        news = get_news_summary_for_asset(_G_NEWS_TAG.get(sym, sym if sym in ASSET_KEYWORDS else "GENEL"), days=7)
        z.append("NACHRICHTEN (Datenbank, 7 Tage):\n" + str(news)[:1400])
    except Exception:
        z.append("NACHRICHTEN: k. A.")

    # Depot
    pos_z = []
    for p in positionen or []:
        try:
            pe = p["market"]["epic"]
            pos_z.append(f"{pe} {p['position']['direction']} Größe {p['position'].get('size')} "
                         f"Einstieg {p['position'].get('level')} UPL {p['position'].get('upl')} "
                         f"[{markt_gruppe(pe) or '-'}]")
        except Exception:
            continue
    z.append(f"DEPOT: Gesamt {acc.get('toplam', '?')} EUR | verfügbar {acc.get('musait', '?')} EUR | "
             f"offener Gewinn/Verlust {acc.get('upl', '?')} EUR | Positionen {len(positionen or [])}/{MAX_POSITIONEN}")
    z.append("OFFENE POSITIONEN: " + ("; ".join(pos_z) if pos_z else "keine"))
    try:
        z.append(f"HEUTE: {gunluk_kayip_sayisi(sym)} Stop-Loss-Verluste in {sym}")
    except Exception:
        pass
    try:
        for d in ("BUY", "SELL"):
            ts = letzte_schliessung(epic, d)
            if ts > 0 and time.time() - ts < 48 * 3600:
                z.append(f"LETZTE SCHLIESSUNG {sym} {d}: vor {(time.time() - ts) / 3600:.1f} h")
    except Exception:
        pass
    z.append(f"REGELN PYTHON: Stop mind. {SL_ATR_MULT:g} × Tagesspanne (max. {SL_MAX_PCT:g} %), Teilverkäufe in 3 Stufen, "
             f"Stop-Leiter {'an' if STOP_LEITER else 'aus'}, max. {MAX_JE_GRUPPE or 'beliebig'} Märkte je Gruppe, "
             f"Positionsgröße aus der .env.")
    return "\n".join(z), info


def gremium_kandidaten(h, positionen):
    """Maerkte, ueber die das Gremium in diesem Scan beraet. Alle Maerkte werden angeschaut
    (vorher brach der Scan nach 15 ab). Python-Signal ist nur ein Aufmerksamkeitsfilter:
    die Mitglieder duerfen auch die Gegenrichtung oder BEKLE waehlen.
    Was ohnehin gesperrt waere, wird gar nicht erst beraten (spart KI-Aufrufe)."""
    offen = {}
    for p in positionen or []:
        try:
            offen[p["market"]["epic"]] = p["position"]["direction"]
        except Exception:
            continue
    voll = len(positionen or []) >= MAX_POSITIONEN
    liste = []
    for k, v in MARKET_CONFIG.items():
        if k in TABU_ASSETS:
            continue
        if is_weekend() and not is_crypto(k):
            continue
        epic = v["epic"]
        pos_dir = offen.get(epic)
        if not pos_dir:
            if voll:
                continue
            if MAX_JE_GRUPPE > 0:
                _g, _go = gruppen_belegt(k, epic, positionen)
                if _g and len(_go) >= MAX_JE_GRUPPE:
                    continue
        try:
            if _GD.letzter_beschluss(k, GREMIUM_GUELTIG_STD):
                continue
        except Exception:
            pass
        try:
            sinyal, guc, aciklama = technical_confluence(epic)
        except Exception as e:
            logging.debug(f"Gremium-Kandidat {k}: {e}")
            continue
        if sinyal not in ("BUY", "SELL") or guc < 2:
            continue
        if pos_dir == sinyal:
            try:
                ok, _neden = pyramiding_kontrol(h, epic, k)
            except Exception:
                ok = False
            if not ok:
                continue
        if not pos_dir and WIEDEREINSTIEG_SPERRE_STD > 0:
            _zu = letzte_schliessung(epic, sinyal)
            if _zu > 0 and time.time() - _zu < WIEDEREINSTIEG_SPERRE_STD * 3600:
                continue
        try:
            skor = berechne_signal_score(k, epic)
        except Exception:
            skor = {"score": 0, "max_score": 5, "details": ""}
        liste.append({"sym": k, "cfg": v, "sinyal": sinyal, "guc": guc, "aciklama": aciklama, "skor": skor,
                      "pos_dir": pos_dir})
    liste.sort(key=lambda x: (x["skor"].get("score", 0), x["guc"]), reverse=True)
    return liste[:max(0, GREMIUM_MAX_KANDIDATEN)]


def _gremium_ask(prompt, system):
    return call_ai(prompt, system=system, use_grounding=False)


def gremium_zyklus():
    """Ein Scan im Gremium-Modus. Rueckgabe (analysis, erlaubte_signale) fuer execute_nexus_trade."""
    if not _GREMIUM_LOCK.acquire(blocking=False):
        return "GREMIUM: läuft schon", {}
    try:
        h = capital_session.get_headers()
        if not h:
            return "API Baglanti Hatasi", {}
        # alte Stimmen am Kurs messen (Glaubwuerdigkeit)
        try:
            def _preis(epic):
                r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=10)
                s = r.json().get("snapshot", {}) if r.status_code == 200 else {}
                b, o = float(s.get("bid", 0) or 0), float(s.get("offer", 0) or 0)
                return (b + o) / 2 if b and o else b
            n_bew = _GD.bewerten(_preis, std=GREMIUM_BEWERTUNG_STD)
            if n_bew:
                logging.info(f"GREMIUM: {n_bew} Stimmen bewertet")
        except Exception as e:
            logging.warning(f"GREMIUM Bewertung: {e}")

        positionen = get_positions(h) or []
        acc = get_account_info(h) or {}
        kandidaten = gremium_kandidaten(h, positionen)
        global gemini_kandidaten
        gemini_kandidaten = {}
        if not kandidaten:
            logging.info("GREMIUM: kein Kandidat in diesem Scan")
            return "GREMIUM: kein Kandidat", {}

        makro = _gremium_makro()
        gewichte = _GD.gewichte() if GREMIUM_GEWICHTUNG else None
        lang = _gremium_lang()
        zeilen, erlaubt, kurz = [], {}, []
        for kd in kandidaten:
            sym, cfg = kd["sym"], kd["cfg"]
            tech = {"sinyal": kd["sinyal"], "guc": kd["guc"], "aciklama": kd["aciklama"], "skor": kd["skor"]}
            dossier, info = _gremium_dossier(sym, cfg, h, makro, positionen, acc, tech)
            if MAX_SPREAD is not None and info["spread"] > MAX_SPREAD:
                logging.info(f"GREMIUM {sym}: Spread {info['spread']} > MAX_SPREAD {MAX_SPREAD} - nicht beraten")
                continue
            t0 = time.time()
            stimmen = _NG.abstimmen(sym, dossier, _gremium_ask, parallel=GREMIUM_PARALLEL)
            mehrheit = GREMIUM_MEHRHEIT_KRYPTO if (is_crypto(sym) and is_weekend()) else GREMIUM_MEHRHEIT
            erg = _NG.auswerten(stimmen, gewichte, mehrheit=mehrheit, min_antworten=GREMIUM_MIN_ANTWORTEN)
            vs = None
            karar, grund = "BEKLE", erg.get("grund", "")
            if erg["richtung"]:
                vs = _NG.vorsitz(sym, erg["richtung"], dossier, stimmen, erg, _gremium_ask, kurs=info["kurs"])
                if vs.get("ok") and vs["karar"] == "UYGULA":
                    karar, grund = "UYGULA", ""
                    sl, tp = vs["sl"], vs["tp"]
                    if (not sl or not tp) and info["kurs"] > 0:
                        try:
                            _tp2, _sl2, _ = get_atr_tp_sl(cfg["epic"], info["kurs"], erg["richtung"])
                            sl, tp = sl or _sl2, tp or _tp2
                        except Exception:
                            pass
                    zeilen.append(_NG.trade_zeile(sym, erg["richtung"], sl, tp))
                    erlaubt[sym] = erg["richtung"]
                    skor = dict(kd["skor"])
                    skor.update({"signal": erg["richtung"], "gremium_ja": round(erg["gewicht"][erg["richtung"]]),
                                 "gremium_oylar": {s["name"]: s["oy"] for s in stimmen}})
                    gemini_kandidaten[sym] = skor
                else:
                    grund = "vorsitz_stop" if vs.get("ok") else "vorsitz_fehlt"
            try:
                _GD.speichern(sym, cfg["epic"], stimmen, info["kurs"], info["atr_pct"], erg, karar, grund)
            except Exception as e:
                logging.warning(f"GREMIUM speichern: {e}")
            logging.info(
                f"GREMIUM {sym}: {erg['richtung'] or '-'} | {karar} {grund} | BUY {erg['gewicht']['BUY']:.1f} "
                f"SELL {erg['gewicht']['SELL']:.1f} BEKLE {erg['gewicht']['BEKLE']:.1f} | Antworten "
                f"{erg['antworten']}/{erg['mitglieder']} | {time.time() - t0:.0f}s | "
                + " ".join(f"{s['id']}:{s['oy'] if s['ok'] else '-'}" for s in stimmen))
            _gremium_senden(_NG.bericht(sym, stimmen, erg, vs, lang=lang, kurs=info["kurs"], tech=info["tech"],
                                        min_antworten=GREMIUM_MIN_ANTWORTEN))
            kurz.append(f"{sym}: {erg['richtung'] or '-'} {karar}")
        analysis = "GREMIUM v16: " + " | ".join(kurz) + ("\n" + "\n".join(zeilen) if zeilen else "")
        return analysis, erlaubt
    finally:
        _GREMIUM_LOCK.release()


@bot.message_handler(commands=CMD('gremium'))
def handle_gremium(message):
    """v16.0: /gremium - Glaubwuerdigkeit der Mitglieder und die letzten Beschluesse."""
    if not gremium_aktiv():
        _bot_send_raw(MY_CHAT_ID, f"🏛️ Gremium: {'alter Modus (GREMIUM_MODUS=regeln)' if _NG else 'nexus_gremium.py fehlt'}")
        return
    try:
        _gremium_senden(_NG.gewichte_bericht(_GD, lang=_gremium_lang(), std=GREMIUM_BEWERTUNG_STD))
    except Exception as e:
        _bot_send_raw(MY_CHAT_ID, f"🏛️ Gremium: {str(e)[:200]}")


@bot.message_handler(commands=CMD('sprache') + ['start'])
def handle_sprache(message):
    """v15.19: /sprache, /language, /dil -> Sprache waehlen.
    /start -> beim ersten Mal die Sprachwahl, danach Tasten + Hilfe."""
    if (message.text or "").startswith("/start") and lang_aktiv():
        apply_language_ui()
        handle_help(message)
        return
    if not send_language_chooser():
        _bot_send_raw(MY_CHAT_ID, "⚠️ nexus_lang.py fehlt - keine Sprachwahl möglich. / nexus_lang.py is missing - cannot choose a language.")


@bot.callback_query_handler(func=lambda call: (call.data or "").startswith("lang_"))
def handle_language_callback(call):
    """v15.19: Tasten der Sprachwahl: auswaehlen -> bestaetigen -> in die .env schreiben."""
    try:
        data = call.data or ""
        wo = dict(chat_id=call.message.chat.id, message_id=call.message.message_id)
        if data.startswith("lang_pick_") and data[10:] in _NL.LANGS:
            code = data[10:]
            mk = telebot.types.InlineKeyboardMarkup()
            mk.row(telebot.types.InlineKeyboardButton(_NL.UI["yes"][code], callback_data=f"lang_ok_{code}"),
                   telebot.types.InlineKeyboardButton(_NL.UI["back"][code], callback_data="lang_back"))
            _bot_edit_raw(_NL.UI["confirm"][code], reply_markup=mk, **wo)
        elif data == "lang_back":
            _bot_edit_raw(_NL.UI["choose"], reply_markup=language_chooser_markup(), **wo)
        elif data.startswith("lang_ok_") and data[8:] in _NL.LANGS:
            meldung = set_language(data[8:])
            _bot_edit_raw(meldung, **wo)
            apply_language_ui()
        try: bot.answer_callback_query(call.id)
        except Exception: pass
    except Exception as e:
        logging.warning(f"Sprachwahl-Taste: {e}")


@bot.message_handler(commands=CMD('status'))
def handle_status(message):
    sync_bericht = sync_pyramiding_from_capital()
    bot.send_message(MY_CHAT_ID, f"Piramiding Senkron: {sync_bericht}")
    bot.send_message(MY_CHAT_ID, f"🔍 {datetime.now().strftime('%d.%m %H:%M')} | NEXUS NATURE v12.0 - Analiz yapılıyor...")
    analysis = fetch_strategic_response("STATUS_REQUEST")
    bot.send_message(MY_CHAT_ID, analysis[:4000])

def position_detail_lines(p, h, state=None):
    """
    v15.15: Detailzeilen fuer den Positions-Report - damit sichtbar ist, wo die
    Position steht und ab wann der Bot verkauft:
      Groesse / Einstieg / Kurs, Stop Loss, Take Profit,
      durchschnittliche Tagesspanne (Tages-ATR) + Tagesziel (dann fragt der Bot),
      Mirror-TP-Stufen (Stunden-ATR) mit Status.
    Nur lesend. Rueckgabe: Liste von Textzeilen (leer bei Fehler).
    """
    lines = []
    try:
        state = state or {}
        pos, mkt = p["position"], p["market"]
        epic, direction = mkt["epic"], pos["direction"]
        entry = float(pos.get("level", 0) or 0)
        size = float(pos.get("size", 0) or 0)
        current = float(mkt.get("bid", 0) or 0) or float(mkt.get("offer", 0) or 0)
        if entry <= 0 or current <= 0:
            return lines
        vz = 1 if direction == "BUY" else -1

        def noch(preis):   # Weg vom aktuellen Kurs bis zu diesem Preis, in Gewinnrichtung (%)
            return (preis - current) / current * 100 * vz

        lines.append(f"   Größe {size:g} | Einstieg {entry:g} | Kurs {current:g}")

        sl = float(pos.get("stopLevel", 0) or 0)
        tp = float(pos.get("profitLevel", 0) or 0)
        lines.append(f"   🛑 SL {sl:g} ({(sl - entry) / entry * 100 * vz:+.2f}% vom Einstieg)"
                     if sl > 0 else "   🛑 SL: KEINER gesetzt")
        lines.append(f"   🎯 TP {tp:g} (noch {noch(tp):+.2f}%)"
                     if tp > 0 else "   🎯 TP: KEINER gesetzt")

        atr_d, atr_pct, _err = get_daily_atr(epic, DAILY_TP_ATR_PERIOD)
        if atr_d > 0:
            ziel = entry + vz * atr_d * DAILY_TP_ATR_ORAN
            lines.append(f"   📏 Ø Tagesspanne (ATR {DAILY_TP_ATR_PERIOD} T): {atr_d:g} = {atr_pct:.2f}%")
            lines.append(f"   Tagesziel {int(DAILY_TP_ATR_ORAN * 100)}% davon: {ziel:g} "
                         + ("✅ erreicht - der Bot fragt dich" if noch(ziel) <= 0
                            else f"(noch {noch(ziel):+.2f}%) → dann fragt der Bot"))
            if sl > 0 and (sl - entry) * vz < 0:   # v15.17: nur Stops auf der Verlustseite
                _sl_x = abs(entry - sl) / atr_d
                lines.append(f"   Stop-Abstand = {_sl_x:.2f} × Tagesspanne"
                             + (" ⚠️ im Tagesrauschen → /sl_weiten" if SL_ATR_MULT > 0 and _sl_x < SL_ATR_MULT * 0.95 else ""))
        else:
            lines.append("   📏 Ø Tagesspanne: gerade nicht abrufbar")

        if os.getenv("MIRROR_TP_ENABLED", "true").lower() == "true":
            _sl, atr_h, _info = get_atr_stop_loss(epic, current, direction)
            if atr_h > 0:
                mkey = _mirror_key(epic, direction, entry)
                teile = []
                for i, std in ((1, "0.5"), (2, "1.0"), (3, "1.5")):
                    lvl = entry + vz * atr_h * float(os.getenv(f"MIRROR_TP_LEVEL_{i}_MULT", std))
                    if state.get(f"mirror_l{i}_{mkey}"):
                        teile.append(f"L{i} {lvl:g} ✅ verkauft")
                    elif noch(lvl) <= 0:
                        teile.append(f"L{i} {lvl:g} ⏳ erreicht")
                    else:
                        teile.append(f"L{i} {lvl:g} (noch {noch(lvl):+.2f}%)")
                lines.append(f"   🪜 Mirror-TP Stufen (Stunden-ATR {atr_h:g}):")
                lines.append("   " + " | ".join(teile))
            else:
                lines.append("   🪜 Mirror-TP: Stunden-ATR gerade nicht abrufbar")
        else:
            lines.append("   🪜 Mirror-TP: aus (.env)")
        lines.append("   Breakeven-SL ab +1.0% | Trailing-SL ab +1.5% (5% unter dem Hoch)")
        if STOP_LEITER:   # v15.24
            lines.append("   🪜 Stop-Leiter: an - nach Stufe 1 Stop auf Einstieg, danach auf die vorige Stufe")
        else:
            lines.append("   🪜 Stop-Leiter: aus (.env STOP_LEITER)")
    except Exception as e:
        logging.warning(f"Positions-Detail: {e}")
    return lines


@bot.message_handler(commands=CMD('sl_weiten'))
def handle_sl_weiten(message):
    """v15.17: Stops offener Positionen einmalig auf den Rausch-Schutz-Abstand setzen.
    /sl_weiten      -> nur anzeigen, was sich aendern wuerde
    /sl_weiten ja   -> ausfuehren (nur weiter weg, nie enger; der Take Profit bleibt)"""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    try:
        ausfuehren = len((message.text or "").split()) > 1 and (message.text or "").split()[1].lower() in ("ja", "evet", "yes")
        h = capital_session.get_headers()
        if not h:
            bot.send_message(MY_CHAT_ID, "❌ API bağlantı hatası")
            return
        plan = sl_weiten_plan(h)
        if not plan:
            bot.send_message(MY_CHAT_ID, "Açık pozisyon yok.")
            return
        zeilen = ["🛑 STOPS AUF TAGESSPANNE " + ("– AUSGEFÜHRT" if ausfuehren else "– VORSCHAU (nichts geändert)")]
        offen = 0
        for e in plan:
            status = ""
            if e["neu"] is not None:
                if ausfuehren:
                    try:
                        r = requests.put(f"{CAPITAL_URL}/positions/{e['p']['position']['dealId']}",
                                         json=_sl_update_body(e["p"], e["neu"]), headers=h, timeout=10)
                        status = " ✅" if r.status_code == 200 else f" ❌ HTTP {r.status_code} {r.text[:80]}"
                    except Exception as ex:
                        status = f" ❌ {ex}"
                    logging.info(f"/sl_weiten {e['name']} {e['richtung']}: {e['text']}{status}")
                else:
                    offen += 1
            zeilen.append(f"• {e['name']} {e['richtung']}: {e['text']}{status}")
        if not ausfuehren:
            zeilen.append(f"\n{offen} Stop(s) würden geweitet. Ausführen mit:  /sl_weiten ja" if offen
                          else "\nNichts zu tun - kein Stop liegt im Tagesrauschen.")
        bot.send_message(MY_CHAT_ID, "\n".join(zeilen)[:4000])
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ /sl_weiten: {e}")


@bot.message_handler(commands=CMD('update_models'))
def handle_update_models(message):
    """v15.15: Gemini-Modellliste jetzt neu holen und die Kette anzeigen (wie in swarm.py).
    v15.22: dazu Groq / Qwen / Nvidia pruefen und reparieren.
    /update_models       -> pruefen; nur ersetzen, was nicht mehr antwortet
    /update_models best  -> zusaetzlich auf das beste Modell wechseln, das die Pruefung besteht"""
    try:
        _teile = (message.text or "").split()
        _best = len(_teile) > 1 and _teile[1].lower() in ("best", "beste", "bestes", "eniyi", "en_iyi")
        bot.send_message(MY_CHAT_ID, "🔍 Modelle werden geprüft ... das kann ein paar Minuten dauern.")
        gemini_refresh_catalog()
        _res = ai_refresh_models(best=_best, verify_current=True)
        bot.send_message(MY_CHAT_ID, (gemini_status_text() + "\n\n" + ai_status_text(_res))[:4000])
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ Modell-Update: {e}")


@bot.message_handler(commands=CMD('pozisyon'))
def handle_pozisyon(message):
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı")
        return
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)
    mesaj = f"📊 {datetime.now().strftime('%d.%m %H:%M')} | NEXUS POZİSYON RAPORU\n"
    mesaj += f"Nakit: {acc['nakit']:.2f} EUR\n"
    mesaj += f"UPL: {acc['upl']:.2f} EUR\n"
    _trail_state = _load_trailing_state()  # v15.15: fuer den Mirror-TP-Status
    # Marjin: Kaldıraç yok - gösterilmiyor
    if pozisyonlar:
        for p in pozisyonlar:
            epic = p['market']['epic']
            stufe = get_pyramiding_stufe(epic)
            upl_val = float(p['position']['upl'])
            level = float(p['position'].get('level', 0))
            size = float(p['position'].get('size', 0))
            notional = level * size if level > 0 and size > 0 else 0
            upl_pct = (upl_val / notional * 100) if notional > 0 else 0
            # v15.15: Prozent aus dem Kurs (so rechnen auch Breakeven und Trailing),
            # nicht EUR-Gewinn durch USD-Positionswert
            _bid = float(p['market'].get('bid', 0) or 0)
            if level > 0 and _bid > 0:
                upl_pct = (_bid - level) / level * 100 * (1 if p['position']['direction'] == "BUY" else -1)
            mesaj += f"• {p['market']['instrumentName']}: {p['position']['direction']} UPL:{upl_val:.2f} ({upl_pct:+.2f}%) Pyr:Sv.{stufe}\n"
            for _zeile in position_detail_lines(p, h, _trail_state):
                mesaj += _zeile + "\n"
    else:
        mesaj += "Açık pozisyon yok."
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=CMD('kapat'))
def handle_kapat(message):
    """
    /kapat SYMBOL      -> Bu asset'in TUM pozisyonlarini kapatir (Pyramiding dahil)
    /kapat ALLE        -> Acik TUM pozisyonlari kapatir (onay ister)
    /kapat ALLE ONAYLA -> Onaydan sonra gercekten hepsini kapatir
    Ornekler:
      /kapat GOLD
      /kapat NATURAL_GAS
      /kapat ALLE
    """
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.send_message(MY_CHAT_ID,
            "Kullanim: /kapat SYMBOL  veya  /kapat ALLE\n"
            "Ornekler:\n"
            "  /kapat GOLD\n"
            "  /kapat NATURAL_GAS\n"
            "  /kapat ALLE          (once onay ister)\n"
            "  /kapat ALLE ONAYLA   (gercekten hepsini kapatir)")
        return

    hedef = parts[1].upper().strip()
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı"); return

    pozisyonlar = get_positions(h)
    if not pozisyonlar:
        bot.send_message(MY_CHAT_ID, "Açık pozisyon yok."); return

    # --- /kapat ALLE ---
    # v15.19: die Woerter in allen drei Sprachen annehmen
    _alle_w = ("ALLE", "ALL", "HEPSI", "HEPSİ")
    _ja_w = ("ONAYLA", "CONFIRM", "BESTAETIGEN", "BESTÄTIGEN")
    if hedef in _alle_w:
        if len(parts) < 3 or parts[2].upper() not in _ja_w:
            bot.send_message(MY_CHAT_ID,
                f"⚠️ Bu komut {len(pozisyonlar)} açık pozisyonun HEPSİNİ kapatacak!\n"
                f"Emin isen: /kapat ALLE ONAYLA")
            return
        kapatilan, hata = 0, 0
        for p in pozisyonlar:
            try:
                deal_id = p['position']['dealId']
                epic    = p['market']['epic']
                r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                if r.status_code == 200:
                    kapatilan += 1
                    reset_pyramiding_stufe(epic)
                else:
                    hata += 1
            except Exception as e:
                hata += 1
                logging.warning(f"/kapat ALLE hatasi: {e}")
        bot.send_message(MY_CHAT_ID, f"✅ {kapatilan} pozisyon kapatıldı. {hata} hata.")
        return

    # --- /kapat SYMBOL ---
    if hedef not in MARKET_CONFIG:
        bot.send_message(MY_CHAT_ID, f"⚠️ '{hedef}' bilinmiyor. Semboller: " +
                         ", ".join(list(MARKET_CONFIG.keys())[:15]))
        return

    epic = MARKET_CONFIG[hedef]['epic']
    hedef_pozisyonlar = [p for p in pozisyonlar if p['market']['epic'] == epic]

    if not hedef_pozisyonlar:
        bot.send_message(MY_CHAT_ID, f"{hedef} icin acik pozisyon yok."); return

    kapatilan, hata = 0, 0
    for p in hedef_pozisyonlar:
        try:
            deal_id = p['position']['dealId']
            r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
            if r.status_code == 200:
                kapatilan += 1
            else:
                hata += 1
                logging.warning(f"/kapat {hedef}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            hata += 1
            logging.warning(f"/kapat {hedef} hatasi: {e}")

    if kapatilan > 0:
        reset_pyramiding_stufe(epic)

    bot.send_message(MY_CHAT_ID,
        f"✅ {hedef}: {kapatilan}/{len(hedef_pozisyonlar)} pozisyon kapatıldı." +
        (f" ({hata} hata)" if hata else ""))


@bot.message_handler(commands=CMD('ma'))
def handle_ma(message):
    mesaj = f"📈 {datetime.now().strftime('%d.%m %H:%M')} | MA 9/26 SİNYALLERİ\n"
    scan_keys = [k for k in MARKET_CONFIG if not is_weekend() or is_crypto(k)]
    count = 0
    for k in scan_keys[:20]:
        v = MARKET_CONFIG[k]
        sinyal, guc, aciklama = technical_confluence(v['epic'])
        emoji = "🟢" if sinyal == "BUY" else "🔴" if sinyal == "SELL" else "⚪"
        mesaj += f"{emoji} {k}: {sinyal} ({guc}/3) - {aciklama}\n"
        count += 1
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=CMD('volatilite'))
def handle_volatilite(message):
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı")
        return
    bot.send_message(MY_CHAT_ID, "🔍 Volatilite kontrolü yapılıyor...")
    kapatilanlar = volatilite_kontrol(h)
    if not kapatilanlar:
        bot.send_message(MY_CHAT_ID, "✅ Tüm pozisyonlar normal aralıkta")

@bot.message_handler(commands=CMD('spread'))
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

@bot.message_handler(commands=CMD('backtest'))
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


@bot.message_handler(commands=CMD('deepdive'))
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


@bot.message_handler(commands=CMD('stats'))
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

@bot.message_handler(commands=CMD('sources'))
def handle_sources(message):
    """Kaynak guvenilirlik skorlarini goster."""
    scores = db_get_source_scores()
    bot.send_message(MY_CHAT_ID, f"KAYNAK GUVENILIRLIK:\n{scores}")

@bot.message_handler(commands=CMD('kayip'))
def handle_kayip(message):
    """Bugunun kayip sayacini goster."""
    data = _load_daily_losses()
    losses = data.get("losses", {})
    if not losses:
        bot.send_message(MY_CHAT_ID, "Bugun kayip yok.")
        return
    tarih = data.get("date","?")
    lines = [f"BUGUNUN KAYIP SAYACI ({tarih}):"]
    for sym, cnt in sorted(losses.items(), key=lambda x: -x[1]):
        lines.append(f"  BLOKLU {sym}: {cnt}x kayip")
    bot.send_message(MY_CHAT_ID, "\n".join(lines))

@bot.message_handler(commands=CMD('news'))
def handle_news(message):
    """
    /news [SYMBOL] [DAYS]
    v12.2 Mantık:
      1. DB'deki son 14 günlük haberleri çek (RSS + Grounding ile birikmiş)
      2. Gemini'ye ver → 14 günlük trend analizi yaptır
      3. Sonucu Telegram'a gönder
    /newscollect → yeni haber topla (ayrı komut)
    """
    parts = message.text.strip().split()
    sym   = parts[1].upper().strip() if len(parts) >= 2 else None
    days  = 14  # Her zaman 14 günlük birikim değerlendirmesi
    ts    = datetime.now().strftime("%d.%m %H:%M")

    bot.send_message(MY_CHAT_ID,
        f"📰 {ts} | 14 günlük haber analizi yapılıyor "
        f"({'#' + sym if sym else 'Genel Makro'})...")

    # === 1. ADIM: DB'den 14 günlük haberleri çek ===
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            news_rows = conn.execute("""
                SELECT source, title, published_at, sentiment, sentiment_label
                FROM news_cache
                WHERE published_at >= ?
                """ + (f"AND asset_tag LIKE '%{sym}%'" if sym else "") + """
                ORDER BY published_at DESC LIMIT 60
            """, (cutoff,)).fetchall()
            x_rows = conn.execute("""
                SELECT account, tweet_text, tweet_date, sentiment, sentiment_label
                FROM x_cache
                WHERE tweet_date >= ?
                """ + (f"AND asset_tag LIKE '%{sym}%'" if sym else "") + """
                ORDER BY tweet_date DESC, ABS(sentiment) DESC LIMIT 30
            """, (cutoff,)).fetchall()
            total_news = conn.execute(
                "SELECT COUNT(*) FROM news_cache WHERE published_at >= ?",
                (cutoff,)).fetchone()[0]
            total_x = conn.execute(
                "SELECT COUNT(*) FROM x_cache WHERE tweet_date >= ?",
                (cutoff,)).fetchone()[0]
            conn.close()
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ DB okuma hatası: {e}")
        return

    # DB boşsa kullanıcıyı bilgilendir
    if not news_rows and not x_rows:
        bot.send_message(MY_CHAT_ID,
            f"⚠️ {ts} | DB'de henüz haber yok.\n"
            f"Önce /newscollect ile haber topla (saatte bir otomatik da toplanır).")
        return

    # === 2. ADIM: DB verisini Gemini'ye gönder → 14 günlük analiz ===
    # Haberleri metin olarak hazırla
    haber_metni = f"=== DB'DEN {len(news_rows)} HABER + {len(x_rows)} X POST (Son 14 gün) ===\n\n"
    haber_metni += "HABERLER:\n"
    for src, title, date, sent, label in news_rows[:40]:
        emoji = "+" if float(sent) > 0.2 else ("-" if float(sent) < -0.2 else "~")
        haber_metni += f"  [{emoji}{label}] {date} | {src}: {title[:100]}\n"

    haber_metni += "\nX POSTLARI:\n"
    for acc, tweet, date, sent, label in x_rows[:20]:
        emoji = "+" if float(sent) > 0.2 else ("-" if float(sent) < -0.2 else "~")
        haber_metni += f"  [{emoji}{label}] {date} @{acc}: {tweet[:100]}\n"

    now_fmt = datetime.now().strftime("%d.%m.%Y %H:%M")
    konu = f"{sym} CFD trading için" if sym else "global makroekonomi için"

    analiz_prompt = f"""Sen NEXUS NATURE v12.2 haber analistisin.

Aşağıda son 14 günün DB'den alınmış gerçek haberleri ve X postları var.
Bu veriyi analiz et ve {konu} 14 günlük TREND değerlendirmesi yap.

{haber_metni}

ÇIKTI (TAM BU FORMAT):
=== {now_fmt} | 14 GÜNLÜK HABER & TREND ANALİZİ ===
{'#' + sym + ' | ' if sym else ''}GENEL SENTIMENT: [BULLISH/BEARISH/NEUTRAL] (+/-X.XX)
Bullish:{"{bull}"} Bearish:{"{bear}"} Neutral:{"{neut}"} | DB: {total_news} haber + {total_x} X post

TREND (Son 14 gün → Son 3 gün):
  [Trendin yönü ve gücü: GÜÇLENIYOR / ZAYIFLIYOR / STABİL]
  [Neden: 1-2 cümle ana katalizör]

ÖNE ÇIKAN HABERLER (en önemli 8):
  [+/-/~] YYYY-MM-DD | kaynak: başlık

X/TWİTTER ÖNE ÇIKANLAR (en önemli 5):
  [+/-/~] YYYY-MM-DD @hesap: özet

TRADING SONUCU:
  Makro Bias: [LONG / SHORT / NÖTR]
  Risk Seviyesi: [DÜŞÜK / ORTA / YÜKSEK]
  Gerekçe: [1 cümle]

ÖNEMLİ: Sadece yukarıdaki DB verisine dayan. Uydurma yok."""

    try:
        valid_keys = [k for k in GEMINI_KEYS if k]
        if not valid_keys:
            raise ValueError("Gemini key yok")

        client = genai.Client(api_key=get_current_key() or valid_keys[0])
        response = client.models.generate_content(
            model=get_next_model(),
            contents=analiz_prompt,
            config=types.GenerateContentConfig(
                # Analiz için Grounding gerekmez - DB verisi kullanıyoruz
                system_instruction=(
                    "Sen bir quant fon yöneticisisin. "
                    "Sadece sana verilen veriyi analiz et, uydurma. "
                    "Türkçe yanıt ver."
                )
            )
        )
        result = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    result += part.text
        result = result.strip() or "Analiz üretilemedi."
        bot.send_message(MY_CHAT_ID, result[:4000])

    except Exception as e:
        logging.warning(f"Haber analiz hatası: {e}")
        # Fallback: basit DB özeti
        summary = get_global_news_summary(days=days)
        bot.send_message(MY_CHAT_ID,
            f"⚠️ Gemini analiz hatası: {e}\n\n{summary[:3500]}")


@bot.message_handler(commands=CMD('newscollect'))
def handle_newscollect(message):
    """Manuel haber toplama: RSS + GDELT → DB kayıt. (v14.4: Grounding kaldırıldı)"""
    ts = datetime.now().strftime('%d.%m %H:%M')
    bot.send_message(MY_CHAT_ID, f"🔄 {ts} | Haber toplama başlatılıyor (RSS + GDELT)...")
    try:
        sources = load_sources()
        # 1) RSS
        n_rss = collect_news_rss(sources)
        # 2) GDELT (ücretsiz, key yok)
        try:
            n_gdelt, _ = gdelt_haber_topla(sources)
        except Exception as _ge:
            logging.warning(f"[WARN] /newscollect GDELT: {_ge}")
            n_gdelt = 0
        ts2 = datetime.now().strftime('%d.%m %H:%M')
        bot.send_message(MY_CHAT_ID,
            f"✅ {ts2} | Haber toplama tamamlandı:\n"
            f"  RSS: {n_rss} haber\n"
            f"  GDELT: {n_gdelt} haber\n"
            f"  DB: 14 günlük birikim aktif")
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ Hata: {e}")


@bot.message_handler(commands=CMD('dbtemizle'))
def handle_dbtemizle(message):
    """Eski/bozuk haberleri DB'den temizle (29 Ap gibi eskiler)."""
    ts = datetime.now().strftime('%d.%m %H:%M')
    try:
        cutoff_hard = "2026-06-01"  # Bu tarihten öncekiler silinir
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            n_news = conn.execute(
                "SELECT COUNT(*) FROM news_cache WHERE published_at < ?",
                (cutoff_hard,)).fetchone()[0]
            n_x = conn.execute(
                "SELECT COUNT(*) FROM x_cache WHERE tweet_date < ?",
                (cutoff_hard,)).fetchone()[0]
            conn.execute("DELETE FROM news_cache WHERE published_at < ?", (cutoff_hard,))
            conn.execute("DELETE FROM x_cache WHERE tweet_date < ?", (cutoff_hard,))
            conn.commit()
            conn.close()
        bot.send_message(MY_CHAT_ID,
            f"🧹 {ts} | DB Temizlendi:\n"
            f"  {n_news} eski haber silindi\n"
            f"  {n_x} eski X post silindi\n"
            f"  Artık /newscollect ile güncel haber topla")
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ DB temizleme hatası: {e}")


@bot.message_handler(commands=CMD('help'))
def handle_help(message):
    mesaj = (
        "🤖 NEXUS NATURE v15.6 — Komut Rehberi\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 ANALİZ & DURUM\n"
        "/status      | status      — Tam Gemini analizi + Gremium oylama\n"
        "/pozisyon    | pozisyon    — Acik pozisyonlar, PnL, Pyramiding\n"
        "/sl_weiten                — Stops offener Positionen an der Tagesspanne pruefen (ausfuehren: /sl_weiten ja)\n"
        "/ma          | ma          — MA9/26 + ADX + RSI sinyalleri\n"
        "/stats       | stats       — Trade istatistikleri + asset performansi\n\n"
        "🔬 ARASTIRMA\n"
        "/backtest SEMBOL GUN      — Ornek: /backtest GOLD 200\n"
        "/deepdive SEMBOL TF GUN   — Ornek: /deepdive GOLD HOUR_4 30\n"
        "/news SEMBOL GUN          — Ornek: /news OIL 7\n"
        "/newscollect | newscollect — Manuel haber toplama: RSS + Grounding\n"
        "/sources     | sources     — Kaynak guvenilirlik skorlari\n"
        "/dbtemizle   | dbtemizle   — Eski/bozuk haberleri DB'den sil\n\n"
        "⚠️ RİSK & KONTROL\n"
        "/volatilite  | volatilite  — Volatilite + Kara Kugu kontrolu\n"
        "/spread      | spread      — Spread tarama + config guncelleme\n"
        "/kayip       | kayip       — Bugunun kayip/zarar sayaci\n"
        "/bloklar     | bloklar     — Aktif HARD BLOCK listesi\n\n"
        "💼 POZİSYON YÖNETİMİ\n"
        "/kapat SEMBOL             — Ornek: /kapat GOLD\n"
        "/kapat ALLE               — Tum pozisyonlari kapat (onay ister)\n"
        "/manuell SEMBOL YON SIZE  — Ornek: /manuell GOLD BUY 100\n"
        "  (opsiyonel: SL TP)      — Ornek: /manuell GOLD BUY 100 1900 2100\n\n"
        "🧠 HAFIZA\n"
        "/unut        | unut        — Kaydedilen kullanici notlarini sil\n\n"
        "💬 NOT GONDERME (quota YOK)\n"
        "Komut olmadan yaz = NOT olarak kaydedilir\n"
        "Gemini 30 dk icinde kullanir (48 saat gecerli)\n"
        "Ornek: Iran rafinerileri kapaniyor, Brent yukselir\n\n"
        "🚫 HARD BLOCK\n"
        "Aninda Python seviyesinde — Gemini override EDEMEZ!\n"
        "  'Silver satma'          → SILVER SELL blok\n"
        "  'Silver alma'           → SILVER BUY blok\n"
        "  'Gold nicht handeln'    → GOLD tam blok\n"
        "  'Silver serbest'        → SILVER blok kaldirilir\n\n"
        "/handbuch    | handbuch    — Komplettes Handbuch als Datei (mit aktuellen Einstellungen)\n"
        "/help        | help        — Bu menü"
    )
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=CMD('manuell'))
def handle_manuell(message):
    """
    /manuell SYMBOL SIDE SIZE [SL] [TP]
    Eröffnet Position direkt ohne Gremium/Gate-Keeper.
    Beispiele:
      /manuell GOLD BUY 100
      /manuell SILVER SELL 200 30.5 35.0
      /manuell NATURAL_GAS BUY 50
    """
    parts = message.text.strip().split()
    if len(parts) < 4:
        bot.send_message(MY_CHAT_ID,
            "⚠️ Usage: /manuell SYMBOL SIDE SIZE [SL] [TP]\n"
            "Beispiele:\n"
            "  /manuell GOLD BUY 100\n"
            "  /manuell SILVER SELL 200 30.5 35.0\n"
            "  /manuell NATURAL_GAS BUY 50")
        return
    
    sym = parts[1].upper().strip()
    side = parts[2].upper().strip()
    
    if side not in ("BUY", "SELL"):
        bot.send_message(MY_CHAT_ID, f"⚠️ SIDE muss BUY oder SELL sein, nicht: {side}")
        return
    
    try:
        size_eur = float(parts[3])
    except ValueError:
        bot.send_message(MY_CHAT_ID, f"⚠️ SIZE muss eine Zahl sein: {parts[3]}")
        return
    
    # Symbol validieren
    if sym not in MARKET_CONFIG:
        bot.send_message(MY_CHAT_ID,
            f"⚠️ Symbol '{sym}' nicht in MARKET_CONFIG.\n"
            f"Verfügbar: {', '.join(MARKET_CONFIG.keys())}")
        return
    
    cfg = MARKET_CONFIG[sym]
    epic = cfg["epic"]
    
    # API Session
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API Verbindung fehlgeschlagen")
        return
    
    # Current price holen
    try:
        price_r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=h, timeout=10)
        if price_r.status_code != 200:
            bot.send_message(MY_CHAT_ID, f"❌ Preis konnte nicht geholt werden: HTTP {price_r.status_code}")
            return
        pdata = price_r.json()
        bid = float(pdata.get('snapshot', {}).get('bid', 0) or 0)
        ask = float(pdata.get('snapshot', {}).get('offer', 0) or 0)
        current_price = (bid + ask) / 2 if bid and ask else max(bid, ask)
        if current_price <= 0:
            bot.send_message(MY_CHAT_ID, "❌ Ungültiger Preis")
            return
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ Preis-Fehler: {e}")
        return
    
    # SL/TP berechnen oder übernehmen
    sl_float = None
    tp_float = None
    
    if len(parts) >= 6:
        # Manuelle SL/TP
        try:
            sl_float = float(parts[4])
            tp_float = float(parts[5])
        except ValueError:
            bot.send_message(MY_CHAT_ID, "⚠️ SL/TP müssen Zahlen sein")
            return
    else:
        # Auto: ATR-SL + R:R 1:3 TP
        try:
            atr_sl, atr_v, atr_info = get_atr_stop_loss(epic, current_price, side)
            sl_float = atr_sl
            if side == "BUY":
                tp_float = current_price + (current_price - sl_float) * 3
            else:
                tp_float = current_price - (sl_float - current_price) * 3
            logging.info(f"Manuell {sym}: ATR-SL={sl_float}, TP={tp_float} (R:R 1:3)")
        except Exception as e:
            # Fallback: 1.5% SL
            dist = current_price * 0.015
            sl_float = current_price - dist if side == "BUY" else current_price + dist
            tp_float = current_price + dist * 3 if side == "BUY" else current_price - dist * 3
            logging.warning(f"Manuell {sym}: ATR fehlgeschlagen, Fallback 1.5%: {e}")
    
    # Size in Units umrechnen
    try:
        units = safe_trade_size(str(size_eur), cfg, epic, is_manual=True)
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ Size-Berechnung fehlgeschlagen: {e}")
        return
    
    # Position eröffnen
    payload = {
        "epic": epic,
        "direction": side,
        "size": units,
        "type": "MARKET",
        "stopLevel": sl_float,
        "profitLevel": tp_float
    }
    
    bot.send_message(MY_CHAT_ID,
        f"⚡ MANUELLER TRADE wird ausgeführt:\n"
        f"Symbol: {sym}\n"
        f"Seite: {side}\n"
        f"Größe: {size_eur}€ ({units} units)\n"
        f"Preis: {current_price}\n"
        f"SL: {sl_float}\n"
        f"TP: {tp_float}")
    
    try:
        r = requests.post(f"{CAPITAL_URL}/positions", json=payload, headers=h, timeout=10)
        if r.status_code == 200:
            # Pyramiding-Stufe auf 1 setzen
            set_pyramiding_stufe(epic, 1)
            
            # Trailing SL Peak initialisieren
            try:
                trail_state = _load_trailing_state()
                peak_key = "peak_" + epic + "_" + side
                trail_state[peak_key] = {
                    "value": round(current_price, 5),
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                _save_trailing_state(trail_state)
            except Exception as te:
                logging.warning(f"Trailing init: {te}")
            
            # DB-Eintrag
            try:
                db_open_trade(
                    symbol=sym, direction=side, size=units,
                    entry_price=current_price, sl=sl_float, tp=tp_float,
                    spread=abs(ask - bid) if ask and bid else 0,
                    gremium_score="MANUELL",
                    macro_regime="MANUELL",
                    fear_greed=50,
                )
            except Exception as db_e:
                logging.warning(f"DB Trade: {db_e}")
            
            msg = (
                f"✅ MANUELLER TRADE eröffnet!\n"
                f"Symbol: {sym} {side}\n"
                f"Größe: {units} units ({size_eur}€)\n"
                f"Entry: {current_price}\n"
                f"SL: {sl_float} | TP: {tp_float}\n"
                f"Pyramiding-Stufe: 1"
            )
            bot.send_message(MY_CHAT_ID, msg)
            logging.info(f"MANUELL {sym} {side} {units} units @ {current_price}")
        else:
            bot.send_message(MY_CHAT_ID, f"❌ Trade fehlgeschlagen: {r.text[:200]}")
            logging.error(f"Manuell Trade Fehler {sym}: {r.text[:200]}")
    except Exception as e:
        bot.send_message(MY_CHAT_ID, f"❌ Exception: {e}")
        logging.error(f"Manuell Exception {sym}: {e}")


# ============================================================
# FREIE TEXTNACHRICHTEN (ohne /) - NEU
# ============================================================
@bot.message_handler(commands=CMD('bloklar'))
def handle_bloklar(message):
    """Aktif HARD BLOCK listesini goster."""
    if str(message.chat.id) != str(MY_CHAT_ID): return
    with hard_block_lock:
        aktif = dict(HARD_BLOCK_ASSETS)
    if not aktif:
        bot.send_message(MY_CHAT_ID, "✅ Aktif HARD BLOCK yok. Tum assetler serbest.")
        return
    lines = ["🔒 AKTİF HARD BLOKLAR:"]
    for sym, info in aktif.items():
        lines.append(f"  ⛔ {sym} ({info['action']}) — {info['timestamp'][:16]}")
        lines.append(f"     Sebep: {info['reason'][:80]}")
    lines.append("\nKaldirmak icin: '<asset> serbest' veya '<asset> freigeben'")
    bot.send_message(MY_CHAT_ID, "\n".join(lines))

@bot.message_handler(commands=CMD('unut'))
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

@bot.message_handler(func=lambda message: True)
def handle_free_text(message):
    """
    Serbest metin handler.
    1. Buton yönlendirme (emoji butonlar /komut'a çevrilir)
    2. HARD BLOCK parse: asset + yon tespit edilirse aninda Python seviyesinde blok
    3. Mevcut pozisyonlari kapat (sat emri varsa)
    4. Gemini hafizasina yaz (quota harcanmaz)
    """
    user_text = message.text.strip()
    if not user_text:
        return
    if str(message.chat.id) != str(MY_CHAT_ID):
        bot.send_message(message.chat.id, "⛔ Yetkisiz erişim.")
        return

    # ---- BUTON YÖNLENDİRME (emoji butonlar) ----
    BUTTON_MAP = {
        "📰 Haberler":   handle_news,
        "📋 Menü":       handle_help,
        "📊 Status":     handle_status,
        "📈 Sinyaller":  handle_ma,
        "📍 Pozisyon":   handle_pozisyon,
        "🧮 Stats":      handle_stats,
        "💸 Kayip":      handle_kayip,
        "🔒 Bloklar":    handle_bloklar,
        "🔎 Diagnose":   handle_diagnose,   # v15.20
    }
    # Tam eşleşme veya içerik eşleşmesi (buton metninin büyük/küçük harf/boşluk varyasyonları)
    matched_handler = BUTTON_MAP.get(user_text)
    if not matched_handler:
        # Kısmi eşleşme: emoji ile başlayan metinler
        for btn_text, handler in BUTTON_MAP.items():
            if user_text.startswith(btn_text.split()[0]):  # emoji kontrolü
                matched_handler = handler
                break
    if matched_handler:
        matched_handler(message)
        return
    try:
        reply_lines = []

        # ---- HARD BLOCK / UNBLOCK PARSE ----
        asset_sym, action, block_type = parse_hard_block(user_text)

        if asset_sym and block_type == "UNBLOCK":
            removed = remove_hard_block(asset_sym)
            if removed:
                reply_lines.append(f"✅ HARD BLOCK kaldirildi: {asset_sym} artik serbest.")
            else:
                reply_lines.append(f"ℹ️ {asset_sym} zaten bloklu degildi.")

        elif asset_sym and block_type == "BLOCK":
            apply_hard_block(asset_sym, action, user_text[:120])
            reply_lines.append(
                f"⛔ HARD BLOCK aktif: {asset_sym} ({action}) — Gemini bu karari override EDEMEZ!"
            )

            # Eger "sat/verkaufen" talimatiysa: mevcut pozisyonlari kapat
            is_sell_order = any(kw in user_text.lower() for kw in ["verkaufen", "sat ", "sell", "kapat", "close"])
            if is_sell_order:
                try:
                    h = capital_session.get_headers()
                    if h:
                        positions = get_positions(h)
                        cfg = None
                        for k, v in MARKET_CONFIG.items():
                            if k == asset_sym:
                                cfg = v; break
                        if cfg:
                            epic_target = cfg["epic"]
                            closed_cnt = 0
                            for pos in positions:
                                if pos["market"]["epic"] == epic_target:
                                    deal_id = pos["position"].get("dealId") or pos["position"].get("deal_id", "")
                                    if deal_id:
                                        close_r = requests.delete(
                                            f"{CAPITAL_URL}/positions/{deal_id}",
                                            headers=h, timeout=10
                                        )
                                        if close_r.status_code in (200, 201, 204):
                                            closed_cnt += 1
                            if closed_cnt > 0:
                                reply_lines.append(f"✅ {closed_cnt} adet {asset_sym} pozisyonu kapatildi.")
                            else:
                                reply_lines.append(f"ℹ️ {asset_sym} icin acik pozisyon bulunamadi.")
                except Exception as ce:
                    logging.error(f"Pozisyon kapatma hatasi: {ce}")
                    reply_lines.append(f"⚠️ Pozisyon kapatirken hata: {ce}")

        # ---- GEMINI HAFIZASINA YAZ ----
        db_gemini_write("USER_INFO", user_text[:500], symbol=asset_sym, cycle=0)

        # ---- AKTIF BLOKLAR OZETI ----
        with hard_block_lock:
            aktif = list(HARD_BLOCK_ASSETS.items())
        if aktif:
            blok_str = " | ".join([f"{s}({v['action']})" for s, v in aktif])
            reply_lines.append(f"🔒 Aktif bloklar: {blok_str}")

        if not reply_lines:
            reply_lines.append("Notun kaydedildi. Bir sonraki analizde (maks 30 dk) Gemini kullanacak. Quota harcanmadi.")

        bot.send_message(MY_CHAT_ID, "\n".join(reply_lines))

    except Exception as e:
        logging.error("handle_free_text: " + str(e))
        bot.send_message(MY_CHAT_ID, "Kayit hatasi: " + str(e))

# ============================================================
# ANA DONGU (HEARTBEAT + SPREAD WRITER)
# ============================================================
# ============================================================
# v15.16: SCHLIESS-MELDER
# Schliesst der Broker eine Position (Stop Loss, Take Profit, Margin) oder
# wird sie von Hand geschlossen, hat der Bot das bisher nur als
# "Pyramiding-Sync ... (kapatıldı)" bemerkt - ohne Grund, ohne Ergebnis,
# und ohne den Tages-Verlustzaehler zu erhoehen.
# Jetzt: offene Positionen merken; verschwindet eine, Grund + Ergebnis aus
# der Capital.com-Historie holen, per Telegram melden, Stop-Loss-Verluste
# zaehlen (damit die Regel "x Verluste pro Tag -> Symbol gesperrt" greift).
# Nur lesend gegenueber Capital.com.
# ============================================================
POS_SEEN_FILE = os.path.join(BASE_DIR, "positions_seen.json")
_pos_seen_lock = threading.Lock()
_SCHLIESS_GRUND = {
    "SL": "Stop Loss", "TP": "Take Profit", "USER": "vom Bot oder von Hand geschlossen",
    "SYSTEM": "Broker (System)", "CLOSE_OUT": "Broker (Margin-Glattstellung)", "DEALER": "Broker (Händler)",
}


def _pos_seen_load():
    """Gemerkte Positionen laden. None = es wurde noch nie etwas gemerkt."""
    try:
        with open(POS_SEEN_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("pos"), dict):
            return d
    except Exception:
        pass
    return None


def _pos_seen_save(d):
    try:
        tmp = POS_SEEN_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        os.replace(tmp, POS_SEEN_FILE)
    except Exception as e:
        logging.warning(f"Schliess-Melder: Merker nicht gespeichert: {e}")


def _hist_zeit(s):
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def _hist_get(h, pfad, periode, feld, extra=None):
    """Capital.com-Historie der letzten <periode> Sekunden lesen. Liste bei Erfolg, None bei Fehler.
    Erst mit lastPeriod; lehnt die API das ab, mit from/to (UTC) - diese Form hat
    nexus_tp_diagnose.py am 03.10. auf diesem Konto erfolgreich benutzt."""
    fmt, jetzt = "%Y-%m-%dT%H:%M:%S", time.time()
    varianten = [dict(extra or {}, lastPeriod=int(periode)),
                 dict(extra or {}, **{"from": time.strftime(fmt, time.gmtime(jetzt - int(periode))),
                                      "to": time.strftime(fmt, time.gmtime(jetzt))})]
    fehler = ""
    for params in varianten:
        try:
            r = requests.get(f"{CAPITAL_URL}{pfad}", headers=h, params=params, timeout=15)
            if r.status_code == 200:
                return r.json().get(feld) or []
            fehler = f"HTTP {r.status_code} {r.text[:120]}"
        except Exception as e:
            fehler = str(e)
    logging.warning(f"Schliess-Melder: {pfad}: {fehler}")
    return None


def _find_close_activity(activities, deal_id, pos_direction):
    """Schliess-Eintrag einer Position in der Historie: Typ POSITION, gleiche dealId
    und entweder mit openPrice oder in Gegenrichtung (der Eroeffnungs-Eintrag hat
    dieselbe dealId, aber die Richtung der Position und kein openPrice).
    Gibt es mehrere (Teilverkaeufe), gilt der neueste."""
    best = None
    for a in activities or []:
        if a.get("type") != "POSITION" or a.get("dealId") != deal_id:
            continue
        if str(a.get("status", "")).upper() == "REJECTED":
            continue
        det = a.get("details") or {}
        richtung = det.get("direction")
        if "openPrice" not in det and not (richtung and pos_direction and richtung != pos_direction):
            continue
        if best is None or str(a.get("dateUTC") or a.get("date") or "") > str(best.get("dateUTC") or best.get("date") or ""):
            best = a
    return best


def _close_ergebnis(act, transactions, benutzt):
    """Ergebnis einer Schliessung: (Betrag, Waehrung, gebucht).
    gebucht=True  -> Betrag stammt aus der Konto-Buchung (Kontowaehrung, inkl. Gebuehren)
    gebucht=False -> aus Einstieg/Ausstieg/Groesse gerechnet (Waehrung des Instruments)
    (None, "", False) wenn nichts ermittelbar ist."""
    det = act.get("details") or {}
    t_act = _hist_zeit(act.get("dateUTC") or act.get("date"))
    namen = {act.get("epic"), det.get("marketName")} - {None, ""}
    if t_act:
        bester, abstand = None, 16.0
        for i, t in enumerate(transactions or []):
            if i in benutzt or t.get("transactionType") != "TRADE" or t.get("instrumentName") not in namen:
                continue
            tz = _hist_zeit(t.get("dateUtc") or t.get("dateUTC") or t.get("date"))
            if tz is None:
                continue
            d = abs((tz - t_act).total_seconds())
            if d < abstand:
                bester, abstand = i, d
        if bester is not None:
            try:
                betrag = float(str(transactions[bester].get("size")).replace(",", ""))
                benutzt.add(bester)
                return betrag, transactions[bester].get("currency") or "EUR", True
            except (TypeError, ValueError):
                pass
    try:
        level, offen, size = float(det["level"]), float(det["openPrice"]), float(det["size"])
        vz = 1 if det.get("direction") == "SELL" else -1      # Schliess-Order SELL = Position war BUY
        return (level - offen) * size * vz, det.get("currency") or "", False
    except (KeyError, TypeError, ValueError):
        return None, "", False


def _melde_schliessung(info, act, transactions, benutzt):
    """Telegram-Meldung zu einer geschlossenen Position; zaehlt Stop-Loss-Verluste."""
    epic = info.get("epic", "")
    sym = next((s for s, c in MARKET_CONFIG.items() if c.get("epic") == epic), epic)
    name, richtung = info.get("name") or epic, info.get("direction") or "?"
    if act is None:
        zeilen = [f"⚪ POSITION GESCHLOSSEN: {name} ({richtung})",
                  "Grund: in der Capital.com-Historie nicht gefunden",
                  f"Einstieg {float(info.get('entry', 0) or 0):g} | Größe {float(info.get('size', 0) or 0):g}"]
    else:
        det = act.get("details") or {}
        quelle = str(act.get("source") or "?").upper()
        pnl, waehrung, gebucht = _close_ergebnis(act, transactions, benutzt)
        try:
            einstieg = float(det.get('openPrice', info.get('entry', 0)) or 0)
            ausstieg = float(det.get('level', 0) or 0)
            groesse = float(det.get('size', info.get('size', 0)) or 0)
        except (TypeError, ValueError):
            einstieg = ausstieg = groesse = 0.0
        # v15.18: Wie weit lag der Ausstieg vom Einstieg weg? Unter 0.1 % = Stop am Einstieg (Breakeven).
        weg = abs(ausstieg - einstieg) / einstieg if einstieg > 0 and ausstieg > 0 else None
        am_einstieg = weg is not None and weg < 0.001
        marke = "⚪" if pnl is None or abs(pnl) < 0.005 or am_einstieg else ("🟢" if pnl > 0 else "🔴")
        ergebnis = ("nicht ermittelbar" if pnl is None else
                    f"{pnl:+.2f} {waehrung}".rstrip() + ("" if gebucht else " (aus den Kursen gerechnet, ohne Gebühren)"))
        if quelle == "USER":
            # v15.18: eine Zeile - seine eigene Schliessung (Mirror-TP, Exit) hat der Bot schon gemeldet
            zeilen = [f"{marke} Geschlossen (Bot/Hand): {name} {richtung} | {einstieg:g} → {ausstieg:g} | "
                      f"Größe {groesse:g} | Ergebnis {ergebnis}"]
        else:
            zeilen = [f"{marke} POSITION GESCHLOSSEN: {name} ({richtung})",
                      f"Grund: {_SCHLIESS_GRUND.get(quelle, quelle)}",
                      f"Einstieg {einstieg:g} → Ausstieg {ausstieg:g} | Größe {groesse:g}",
                      f"Ergebnis: {ergebnis}"]
            if quelle == "SL" and pnl is not None:
                if pnl < -0.005 and not am_einstieg:
                    kayip_ekle(sym)
                    n = gunluk_kayip_sayisi(sym)
                    zeilen.append(f"Heute {n}. Stop-Loss-Verlust bei {sym}"
                                  + (f" (ab {MAX_VERLUSTE_PRO_TAG} für heute gesperrt)" if MAX_VERLUSTE_PRO_TAG > 0 else ""))
                elif pnl < -0.005:
                    zeilen.append("Stop am Einstieg (Breakeven) - zählt nicht als Verlust.")
                else:
                    zeilen.append("Der Stop lag am Einstieg oder im Gewinn (Breakeven / Trailing).")
    text = "\n".join(zeilen)
    logging.info("Schliess-Melder: " + " | ".join(zeilen))
    try:
        bot.send_message(MY_CHAT_ID, text)
    except Exception as e:
        logging.warning(f"Schliess-Melder: Telegram: {e}")


def closed_position_watch(h):
    """Vergleicht die offenen Positionen mit dem letzten Stand und meldet jede
    verschwundene Position mit Grund und Ergebnis. Rueckgabe: Anzahl Meldungen.
    Wird die Positionsliste nicht sauber gelesen, passiert nichts (kein Fehlalarm)."""
    try:
        r = requests.get(f"{CAPITAL_URL}/positions", headers=h, timeout=10)
        if r.status_code != 200:
            return 0
        positions = r.json().get("positions")
        if not isinstance(positions, list):
            return 0
    except Exception as e:
        logging.debug(f"Schliess-Melder: Positionen nicht lesbar: {e}")
        return 0

    jetzt = time.time()
    aktuell = {}
    for p in positions:
        pos, mkt = p.get("position") or {}, p.get("market") or {}
        did = pos.get("dealId")
        if did:
            aktuell[did] = {"epic": mkt.get("epic", ""), "name": mkt.get("instrumentName") or mkt.get("epic", ""),
                            "direction": pos.get("direction", ""), "size": pos.get("size", 0),
                            "entry": pos.get("level", 0)}

    gemeldet = 0
    with _pos_seen_lock:
        alt = _pos_seen_load()
        if alt is None:                       # erster Lauf: nur merken
            _pos_seen_save({"ts": jetzt, "pos": aktuell, "offen": {}})
            return 0
        zuletzt = float(alt.get("ts") or jetzt)
        offen = alt.get("offen") if isinstance(alt.get("offen"), dict) else {}
        zu = alt.get("zu") if isinstance(alt.get("zu"), dict) else {}   # v15.18: Epic_Richtung -> wann verschwunden
        for did, info in alt["pos"].items():
            if did not in aktuell and did not in offen:
                offen[did] = dict(info, weg_seit=zuletzt, versuche=0)   # zuletzt offen gesehen: beim letzten Lauf
                zu[f"{info.get('epic', '')}_{info.get('direction', '')}"] = jetzt
        for did in list(offen):
            if did in aktuell:                # doch wieder da (kurzer API-Aussetzer)
                del offen[did]

        if offen:
            fruehest = min(float(v.get("weg_seit") or zuletzt) for v in offen.values())
            periode = int(min(86400, max(1800, jetzt - fruehest + 600)))
            acts = _hist_get(h, "/history/activity", periode, "activities", {"detailed": "true"})
            trans = _hist_get(h, "/history/transactions", periode, "transactions") or []
            benutzt = set()
            for did in list(offen):
                info = offen[did]
                act = _find_close_activity(acts, did, info.get("direction")) if acts is not None else None
                if act is None:
                    zu_alt = jetzt - float(info.get("weg_seit") or jetzt) > 86400
                    if acts is not None:      # Historie gelesen, Eintrag (noch) nicht da
                        info["versuche"] = int(info.get("versuche", 0)) + 1
                    if info.get("versuche", 0) < 3 and not zu_alt:
                        continue              # naechste Runde nochmal versuchen
                _melde_schliessung(info, act, trans, benutzt)
                del offen[did]
                gemeldet += 1
        _pos_seen_save({"ts": jetzt, "pos": aktuell, "offen": offen,
                        "zu": {k: v for k, v in zu.items() if jetzt - float(v or 0) < 172800}})
    return gemeldet


_SCAN_MSG = {"text": "", "ts": 0.0}     # v15.18: letzte "Scan ohne Trade"-Meldung
_QUOTA_MSG = {"text": None, "ts": 0.0}  # v15.18: zuletzt gemeldeter Gemini-Grund


def scan_meldungen(analysis, res):
    """v15.18: Was nach einem Scan an Telegram geht. Rueckgabe True = es wurde gehandelt
    (der Aufrufer schickt dann den Depot-Stand hinterher).
    Vorher kamen bei JEDEM Scan drei Meldungen (KI-Zeilen, Islem Bildirimi, Depot) -
    auch wenn nichts eroeffnet wurde. Jetzt:
      - gehandelt (Position eroeffnet/gedreht oder Order-Fehler): alles wie bisher
      - nichts gehandelt: eine kurze Meldung, und nur wenn sich die Gruende seit der
        letzten geaendert haben (sonst hoechstens alle 6 h)
    .env SCAN_MELDUNGEN=alle stellt das alte Verhalten wieder her."""
    if SCAN_MELDUNGEN == "alle":
        if res:
            try: bot.send_message(MY_CHAT_ID, f"🔔 İşlem Bildirimi:\n{res}")
            except: pass
        return bool(res)
    gehandelt = bool(res) and any(x in res for x in ("pozisyon açıldı", "kapatıldı (ÇIKIŞ)", "açılış hatası", "BAŞARISIZ"))
    if gehandelt:
        if "TRADE:" in (analysis or ""):
            try: bot.send_message(MY_CHAT_ID, analysis[:4000])
            except: pass
        try: bot.send_message(MY_CHAT_ID, f"🔔 İşlem Bildirimi:\n{res}")
        except: pass
        return True
    if res:
        norm = re.sub(r"[-+]?\d+(?:[.,]\d+)?", "#", res)   # Zahlen (mit Vorzeichen) zaehlen nicht als Aenderung
        if norm != _SCAN_MSG["text"] or time.time() - _SCAN_MSG["ts"] > 6 * 3600:
            try: bot.send_message(MY_CHAT_ID, f"🔔 Scan ohne neuen Trade:\n{res}"[:4000])
            except: pass
            _SCAN_MSG["text"], _SCAN_MSG["ts"] = norm, time.time()
    return False


def quota_meldung():
    """v15.18: 'Gemini quota doldu' nur melden, wenn sich der Grund geaendert hat - sonst
    hoechstens alle 6 h (vorher alle 30 Minuten dieselben Zeilen). True = gesendet."""
    warum = ""
    try: warum = gemini_last_fail_text()
    except Exception: pass
    if warum == _QUOTA_MSG["text"] and time.time() - _QUOTA_MSG["ts"] <= 6 * 3600:
        return False
    try: bot.send_message(MY_CHAT_ID,
        f"INFO {datetime.now().strftime('%d.%m %H:%M')} | "
        f"Gemini quota doldu → Groq ile devam ediliyor"
        + (f"\nGrund:\n{warum}" if warum else ""))
    except: pass
    _QUOTA_MSG["text"], _QUOTA_MSG["ts"] = warum, time.time()
    return True


def letzte_schliessung(epic, direction):
    """v15.18: Zeitstempel, wann die letzte Position dieses Epics in dieser Richtung
    verschwunden ist (vom Schliess-Melder gemerkt). 0 = keine bekannt."""
    with _pos_seen_lock:
        d = _pos_seen_load() or {}
    try:
        return float((d.get("zu") or {}).get(f"{epic}_{direction}", 0) or 0)
    except (TypeError, ValueError, AttributeError):
        return 0.0


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
                try:
                    closed_position_watch(h)  # v15.16: geschlossene Positionen melden (Grund + Ergebnis)
                except Exception as _cw_e:
                    logging.warning(f"Schliess-Melder: {_cw_e}")
        except Exception as e:
            logging.error(f"Schutz-Thread hatasi: {e}")
        time.sleep(300)





def exit_monitor_loop():
    """
    SMART EXIT MONITOR
    Prüft alle 30 Minuten alle offenen Positionen auf Exit-Kriterien.
    
    Exit-Kriterien:
    1. Technischer Signal-Wechsel (BUY→SELL oder umgekehrt)
    2. News-Sentiment < -0.5 (starke negative Nachrichten)
    3. Gremium-Mehrheit für Exit (3/5 JA für Exit)
    
    Standard: Manuelle Bestätigung via Telegram
    Optional: AUTO_EXIT=true in .env für automatische Ausführung
    """
    AUTO_EXIT = os.getenv("AUTO_EXIT", "false").lower() == "true"
    EXIT_CHECK_INTERVAL = 1800  # 30 Minuten
    
    logging.info(" Exit-Monitor gestartet (alle 30 Min)")
    time.sleep(60)  # Warten bis Bot vollständig gestartet
    
    while True:
        try:
            h = capital_session.get_headers()
            if not h:
                time.sleep(EXIT_CHECK_INTERVAL)
                continue
            
            positions = get_positions(h)
            if not positions:
                time.sleep(EXIT_CHECK_INTERVAL)
                continue
            
            exit_candidates = []
            
            for p in positions:
                epic = p['market']['epic']
                direction = p['position']['direction']
                instrument = p['market']['instrumentName']
                
                # Symbol aus epic finden
                sym = next((s for s, c in MARKET_CONFIG.items() if c.get('epic') == epic), None)
                if not sym:
                    continue
                
                # 1. Technischer Signal-Check
                signal, guc, details = technical_confluence(epic)
                signal_wechsel = (direction == "BUY" and signal == "SELL") or \
                                 (direction == "SELL" and signal == "BUY")
                
                # 2. News-Sentiment Check (letzte 24h)
                news_sentiment = 0.0
                try:
                    with db_lock:
                        conn = sqlite3.connect(DB_FILE)
                        row = conn.execute(
                            "SELECT AVG(sentiment) FROM news_cache "
                            "WHERE published_at >= date('now','-1 day') "
                            "AND (asset_tag=? OR asset_tag='GENEL')",
                            (sym,)
                        ).fetchone()
                        conn.close()
                        if row and row[0] is not None:
                            news_sentiment = float(row[0])
                except:
                    pass
                
                news_negativ = news_sentiment < -0.5
                
                # 3. Gremium-Exit-Abstimmung
                exit_ja = 0
                exit_gruende = []
                
                # Cihat: Technischer Signal-Wechsel
                if signal_wechsel:
                    exit_ja += 1
                    exit_gruende.append(f"Cihat: Signal-Wechsel ({direction}→{signal})")
                
                # Rogers: Fundamental negativ
                if news_negativ:
                    exit_ja += 1
                    exit_gruende.append(f"Rogers: News negativ ({news_sentiment:.2f})")
                
                # Dalio: Risk-Off Regime
                macro_regime = get_macro_regime(
                    get_fear_greed().get('value', 50),
                    get_volatility_regime({})
                )
                if macro_regime in ("RISK_OFF_EXTREME", "RISK_OFF"):
                    exit_ja += 1
                    exit_gruende.append(f"Dalio: {macro_regime}")
                
                # Taleb: Extreme News
                if news_sentiment < -0.7:
                    exit_ja += 1
                    exit_gruende.append(f"Taleb: Extreme negative News")
                
                # Soros: Momentum verloren
                if signal_wechsel and guc >= 2:
                    exit_ja += 1
                    exit_gruende.append(f"Soros: Momentum verloren")
                
                # Exit-Empfehlung bei 3/5 JA
                if exit_ja >= 3:
                    exit_candidates.append({
                        'epic': epic,
                        'symbol': sym,
                        'instrument': instrument,
                        'direction': direction,
                        'dealId': p['position']['dealId'],
                        'exit_ja': exit_ja,
                        'exit_gruende': exit_gruende,
                        'signal': signal,
                        'news_sentiment': news_sentiment
                    })
            
            # Exit-Kandidaten melden
            if exit_candidates:
                for cand in exit_candidates:
                    msg = (
                        f"🔍 EXIT-EMPFEHLUNG: {cand['instrument']}\n"
                        f"Richtung: {cand['direction']}\n"
                        f"Exit-Stimmen: {cand['exit_ja']}/5\n"
                        f"Gründe:\n"
                    )
                    for grund in cand['exit_gruende']:
                        msg += f"  • {grund}\n"
                    msg += f"\nNeues Signal: {cand['signal']}\n"
                    msg += f"News-Sentiment: {cand['news_sentiment']:.2f}\n\n"
                    
                    if AUTO_EXIT:
                        msg += "⚡ AUTO-EXIT wird ausgeführt..."
                        bot.send_message(MY_CHAT_ID, msg)
                        
                        # Position schließen
                        try:
                            r = requests.delete(
                                f"{CAPITAL_URL}/positions/{cand['dealId']}",
                                headers=h, timeout=10
                            )
                            if r.status_code == 200:
                                bot.send_message(
                                    MY_CHAT_ID,
                                    f"✅ {cand['instrument']} geschlossen"
                                )
                                reset_pyramiding_stufe(cand['epic'])
                        except Exception as e:
                            bot.send_message(
                                MY_CHAT_ID,
                                f" Fehler beim Schließen: {e}"
                            )
                    else:
                        msg += "⏸️ Manuelle Bestätigung erforderlich\n"
                        msg += "Sende 'exit <SYMBOL>' zum Schließen"
                        bot.send_message(MY_CHAT_ID, msg)
            
            time.sleep(EXIT_CHECK_INTERVAL)
            
        except Exception as e:
            logging.error(f"Exit-Monitor Fehler: {e}")
            time.sleep(EXIT_CHECK_INTERVAL)


# ============================================================
# GUNLUK ATR-BAND TP HATIRLATMA SISTEMI
# Sadece bilgilendirme + kullanici onayi - hicbir SL/TP otomatik
# degistirilmez. Botun normal trade-acma SL/TP mantigi (Gemini +
# get_atr_stop_loss) bundan TAMAMEN bagimsiz ve degismeden calisir.
# ============================================================
DAILY_TP_ATR_PERIOD = int(os.getenv("ATR_DAILY_PERIOD", "14"))   # 14, 50 veya 200 gun - .env'den ayarlanabilir
DAILY_TP_ATR_ORAN    = float(os.getenv("ATR_DAILY_ORAN", "0.90")) # Gunluk ortalama hareketin yuzde kaci hedeflensin
DAILY_TP_STATE_FILE = os.path.join(BASE_DIR, "daily_tp_state.json")
daily_tp_lock = threading.Lock()

def _load_daily_tp_state():
    try:
        if os.path.exists(DAILY_TP_STATE_FILE):
            with open(DAILY_TP_STATE_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def _save_daily_tp_state(state):
    try:
        with open(DAILY_TP_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Daily-TP state kayit: {e}")


def daily_tp_watcher_loop():
    """
    15 dakikada bir tum acik pozisyonlari kontrol eder.
    Kar, gunluk ortalama hareketin (ATR, {period} gun) %{oran} una
    ulasirsa Telegram'a Evet/Hayir butonlu bir soru gonderir.
    'Evet' -> SADECE bu pozisyon kapatilir (kullanicinin kararidir).
    'Hayir' -> hicbir sey degismez, normal Trailing SL/Pyramiding devam eder.
    """
    logging.info(f"Gunluk-TP-Bant Hatirlatma Thread baslatildi "
                 f"(ATR-{DAILY_TP_ATR_PERIOD}gun, hedef %{int(DAILY_TP_ATR_ORAN*100)}, her 15 dk)")
    time.sleep(45)
    while True:
        try:
            h = capital_session.get_headers()
            if not h:
                time.sleep(900); continue

            pozisyonlar = get_positions(h)
            if not pozisyonlar:
                time.sleep(900); continue

            state   = _load_daily_tp_state()
            bugun   = datetime.now().strftime("%Y-%m-%d")
            degisti = False

            for p in pozisyonlar:
                try:
                    deal_id    = p['position']['dealId']
                    epic       = p['market']['epic']
                    direction  = p['position']['direction']
                    entry      = float(p['position']['level'])
                    current    = float(p['market'].get('bid', entry))  # Guncel piyasa fiyati - dogru alan
                    instrument = p['market'].get('instrumentName', epic)
                    upl        = float(p['position'].get('upl', 0) or 0)

                    if entry <= 0 or current <= 0: continue

                    kar_fiyat = (current - entry) if direction == "BUY" else (entry - current)
                    if kar_fiyat <= 0:
                        if deal_id in state:
                            state.pop(deal_id, None); degisti = True
                        continue

                    atr_fiyat, atr_pct, _ = get_daily_atr(epic, DAILY_TP_ATR_PERIOD)
                    if atr_fiyat <= 0:
                        continue

                    hedef = atr_fiyat * DAILY_TP_ATR_ORAN

                    if kar_fiyat < hedef:
                        if deal_id in state and kar_fiyat < hedef * 0.5:
                            state.pop(deal_id, None); degisti = True
                        continue

                    onceki = state.get(deal_id, {})
                    if onceki.get("notified_date") == bugun:
                        continue  # Bugun zaten soruldu

                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.row(
                        telebot.types.InlineKeyboardButton(L("✅ Ja, verkaufen"), callback_data=f"dtp_yes_{deal_id}"),
                        telebot.types.InlineKeyboardButton(L("❌ Nein, weiter"), callback_data=f"dtp_no_{deal_id}")
                    )
                    msg = (
                        f"🎯 TÄGLICHES ATR-ZIEL ERREICHT ({DAILY_TP_ATR_PERIOD}-Tage)\n"
                        f"{instrument} ({direction})\n\n"
                        f"Einstieg: {entry:.5f}\n"
                        f"Aktuell: {current:.5f}\n"
                        f"Gewinn (Preis): +{kar_fiyat:.5f}\n"
                        f"Gewinn (EUR): {upl:+.2f}\n\n"
                        f"Ø-Tagesbewegung ({DAILY_TP_ATR_PERIOD}T): {atr_fiyat:.5f} (%{atr_pct:.2f})\n"
                        f"Ziel (%{int(DAILY_TP_ATR_ORAN*100)} davon): {hedef:.5f}\n\n"
                        f"Willst du jetzt verkaufen?"
                    )
                    try:
                        bot.send_message(MY_CHAT_ID, msg, reply_markup=markup)
                    except Exception as se:
                        logging.warning(f"Daily-TP Nachricht fehlgeschlagen: {se}")
                        continue

                    state[deal_id] = {"notified_date": bugun, "notified_price": current}
                    degisti = True

                except Exception as pe:
                    logging.warning(f"Daily-TP Pozisyon hatasi: {pe}")

            if degisti:
                _save_daily_tp_state(state)

        except Exception as e:
            logging.error(f"Daily-TP watcher hatasi: {e}")

        time.sleep(900)  # 15 dakika


@bot.callback_query_handler(func=lambda call: call.data.startswith("dtp_"))
def handle_daily_tp_callback(call):
    """Gunluk ATR-TP sorusuna kullanici cevabi: Ja (verkaufen) / Nein (weiterlaufen)."""
    try:
        _, action, deal_id = call.data.split("_", 2)
    except Exception:
        bot.answer_callback_query(call.id, "Ungueltige Anfrage")
        return

    with daily_tp_lock:
        state = _load_daily_tp_state()

        if action == "yes":
            try:
                h = capital_session.get_headers()
                r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                if r.status_code == 200:
                    bot.answer_callback_query(call.id, "Position geschlossen")
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id, message_id=call.message.message_id,
                            text=call.message.text + "\n\n>> VERKAUFT (auf deine Bestätigung hin)"
                        )
                    except: pass
                    logging.info(f"Daily-TP: Position via Nutzer-Bestaetigung geschlossen, dealId={deal_id}")
                else:
                    bot.answer_callback_query(call.id, f"Fehler beim Schließen ({r.status_code})", show_alert=True)
            except Exception as e:
                bot.answer_callback_query(call.id, "Fehler: " + str(e), show_alert=True)
            state.pop(deal_id, None)
            _save_daily_tp_state(state)
        else:
            bot.answer_callback_query(call.id, "Position läuft weiter")
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id, message_id=call.message.message_id,
                    text=call.message.text + "\n\n>> WEITER (normale Logik läuft unverändert)"
                )
            except: pass
            if deal_id in state:
                state[deal_id]["dismissed"] = True
            _save_daily_tp_state(state)


def build_fallback_prompt(h):
    """
    v15.10: Prompt fuer den KI-Fallback (Gemini-Quota voll).
    Enthaelt ausschliesslich echte Daten: die Gate-Keeper-Kandidaten dieses
    Zyklus und deren Live-Kurse von Capital.com.

    Rueckgabe: (system, prompt, erlaubte_signale)
      erlaubte_signale = {SYMBOL: "BUY"/"SELL"} - nur diese Trades fuehrt
                         execute_nexus_trade im Fallback aus.
      prompt ist None, wenn es nichts zu entscheiden gibt.
    """
    erlaubte_signale = {}
    zeilen = []
    for sym, skor in dict(gemini_kandidaten).items():
        signal = str(skor.get("signal", "")).upper()
        cfg = MARKET_CONFIG.get(sym)
        if signal not in ("BUY", "SELL") or not cfg:
            continue
        try:
            r = requests.get(f"{CAPITAL_URL}/markets/{cfg['epic']}", headers=h, timeout=10)
            snap = r.json().get("snapshot", {}) if r.status_code == 200 else {}
            bid = float(snap.get("bid", 0) or 0)
            ask = float(snap.get("offer", 0) or 0)
        except Exception as e:
            logging.warning(f"Fallback-Kurs {sym}: {e}")
            continue
        if bid <= 0 or ask <= 0:
            continue
        erlaubte_signale[sym] = signal
        zeilen.append(
            f"{sym}: Python-Signal={signal} | Score={skor.get('score', 0)}/{skor.get('max_score', 5)} | "
            f"Gremium={skor.get('gremium_ja', 0)}/5 JA | BID={bid} | ASK={ask}"
        )

    if not zeilen:
        return None, None, erlaubte_signale

    system = (
        "Du bist der Fallback-Analyst von NEXUS. Der Python Gate-Keeper und das Gremium "
        "haben die Kandidaten unten bereits geprueft und freigegeben.\n"
        "REGELN:\n"
        "1. Nur die gelisteten Symbole, nur in der angegebenen Richtung (Python-Signal).\n"
        "2. Erfinde keine Kurse. SL und TP muessen sich auf BID/ASK aus der Liste beziehen.\n"
        "   BUY: SL unter BID, TP ueber ASK. SELL: SL ueber ASK, TP unter BID.\n"
        "3. SIZE ist immer 0 - die Groesse berechnet Python aus der .env.\n"
        "4. Pro Kandidat genau EINE Zeile, exakt in diesem Format:\n"
        "TRADE: [SYMBOL] | SIDE: [BUY/SELL] | SIZE: 0 | SL: [Preis] | TP: [Preis] | PYRAMIDING: 0\n"
        "   oder wenn du den Trade ablehnst:\n"
        "ISLEM YOK: [SYMBOL] - [kurzer Grund]\n"
        "Kein weiterer Text."
    )
    prompt = (
        f"Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
        f"Wochenende: {'JA' if is_weekend() else 'NEIN'}\n\n"
        "FREIGEGEBENE KANDIDATEN (Live-Kurse Capital.com):\n"
        + "\n".join(zeilen)
    )
    return system, prompt, erlaubte_signale


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
                try: bot.send_message(MY_CHAT_ID, f"⚠️ NEXUS NATURE v12.0: API bağlantı hatası! Yeniden deneniyor... (Döngü #{dongu_sayaci})")
                except: pass
                time.sleep(60)
                continue

            # Volatilite kontrol: Schutz-Thread (alle 5 Min)
            # Hier nicht mehr nötig - läuft separat ohne Quota

            # Pozisyon raporu: sadece her 12. dongude (6 saatte bir)
            # Önceden her döngüde → spam
            if dongu_sayaci % 12 == 1:
                try:
                    h_rap = capital_session.get_headers()
                    if h_rap:
                        pos_rap = get_positions(h_rap)
                        if pos_rap is not None:
                            logging.info(f"Pozisyon raporu: {len(pos_rap)} açık pozisyon")
                except:
                    pass

            # Spread alle 3 Zyklen (alle 90 Minuten) in Config schreiben
            if spread_scan_counter >= 3:
                spread_scan_counter = 0
                logging.info("🔄 Automatischer Spread-Scan...")
                scan_and_write_spreads()

            # Pyramiding-JSON VOR jeder KI-Analyse abgleichen
            sync_result = sync_pyramiding_from_capital()
            logging.info(f"Pyramiding-Sync: {sync_result}")
            # v12.1: Senkron mesajı sadece düzeltme olduğunda (her döngüde değil)
            if "korrigiert" in sync_result or "korrektur" in sync_result.lower():
                try: bot.send_message(MY_CHAT_ID, f"🔄 Piramiding Düzeltme:\n{sync_result}")
                except: pass

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
                    try: bot.send_message(MY_CHAT_ID, msg)
                    except: pass
                    time.sleep(SCAN_INTERVAL_SEC)
                    continue

            # ── Daily Drawdown Check ─────────────────────────────────
            daily_status, daily_msg = check_daily_limits()
            if daily_status == "TARGET_REACHED":
                if dongu_sayaci % 12 == 0:
                    try: bot.send_message(MY_CHAT_ID, f"🎯 {daily_msg} — Trading pausiert bis morgen")
                    except: pass
                time.sleep(SCAN_INTERVAL_SEC)
                continue
            if daily_status == "MAX_LOSS":
                try: bot.send_message(MY_CHAT_ID, f"🛑 {daily_msg} — Trading gestoppt!")
                except: pass
                time.sleep(3600)
                continue

            # ── Strategische Analyse ──────────────────────────────────
            _fallback_signale = None  # v15.10: nur im KI-Fallback gesetzt
            if gremium_aktiv():
                # v16.0: 11 Mentoren stimmen ab; nur ihre Beschluesse (Symbol + Richtung) duerfen ausgefuehrt werden
                try:
                    analysis, _fallback_signale = gremium_zyklus()
                except Exception as _gz_e:
                    logging.error(f"GREMIUM Zyklus: {_gz_e}", exc_info=True)
                    analysis, _fallback_signale = "GREMIUM: Fehler", {}
            else:
                analysis = fetch_strategic_response("AUTONOMOUS")

            if "QUOTA_FULL_ALL" in analysis:
                # Gemini Quota leer → Groq direkt nutzen
                # Meldung max. 1x pro 30 Minuten
                global _quota_msg_ts
                if quota_meldung():  # v15.18: nur bei geaendertem Grund, sonst hoechstens alle 6 h
                    _quota_msg_ts = time.time()

                if GROQ_KEYS or QWEN_API_KEY:
                    # v15.10: Fallback NUR mit echten Daten (Gate-Keeper-Kandidaten
                    # + Live-Kurse). Vorher bekam die KI keinerlei Marktdaten und
                    # hat Symbole, Groessen und Preise erfunden.
                    try:
                        _fb_system, _groq_prompt, _fallback_signale = build_fallback_prompt(h)
                        if _groq_prompt is None:
                            # Kein freigegebener Kandidat -> keine KI fragen, kein Trade
                            analysis = "FALLBACK: Gate-Keeper 0 aday - bu dongude islem yok (KI cagrilmadi)"
                        else:
                            analysis = call_ai(
                                _groq_prompt,
                                system=_fb_system,
                                use_grounding=False
                            )
                        logging.info(f"Groq/Qwen fallback analiz: {len(analysis)} karakter")
                        Health.report("call_ai_fallback", True, "Groq/Qwen OK")
                    except Exception as _fb_e:
                        Health.report("call_ai_fallback", False, str(_fb_e))
                        time.sleep(SCAN_INTERVAL_SEC)
                        continue
                else:
                    # Kein Fallback verfügbar
                    time.sleep(SCAN_INTERVAL_SEC)
                    continue

            if "API Bağlantı" in analysis:
                time.sleep(60)
                continue

            # HEARTBEAT
            if "TRADE:" not in analysis:
                # v12.1: Heartbeat sadece her 3 döngüde bir (90 dk) → Telegram quota tasarrufu
                if dongu_sayaci % 6 == 0:  # v14.0: alle 3h statt 90min
                    status_msg = f"🟢 {datetime.now().strftime('%d.%m %H:%M')} | NEXUS NATURE v12.0 Tarama #{dongu_sayaci} tamamlandı.\nBu döngüde trade sinyali yok.\nPiyasa izlenmeye devam ediyor."
                    try: bot.send_message(MY_CHAT_ID, status_msg)
                    except: pass
            elif SCAN_MELDUNGEN == "alle":  # v15.18: sonst schickt scan_meldungen() sie - nur wenn gehandelt wurde
                try: bot.send_message(MY_CHAT_ID, analysis[:4000])
                except: pass

            # Wochenende: max 3 Krypto-Positionen
            if is_weekend():
                h_check = capital_session.get_headers()
                if h_check:
                    alle_pos = get_positions(h_check)
                    # Krypto-Limit am Wochenende entfernt
                    # krypto_pos = [p for p in alle_pos if is_crypto(p['market']['epic'])]
                    # if len(krypto_pos) >= 3:
                    #     try: bot.send_message(MY_CHAT_ID, f"⚠️ Haftasonu kripto limiti")
                    #     except: pass
            res = execute_nexus_trade(analysis, erlaubte_signale=_fallback_signale)
            if res:  # v15.21: vorher stand das Ergebnis nur in Telegram - fuer die Diagnose auch ins Log
                for _erg_z in str(res).splitlines():
                    if _erg_z.strip():
                        logging.info(f"Trade-Ergebnis: {_erg_z}")
            if scan_meldungen(analysis, res):  # v15.18: True = es wurde gehandelt
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

            time.sleep(SCAN_INTERVAL_SEC)  # FIX: 6 Stunden statt 30 Minuten

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
            ["pgrep", "-f", "nexus_nature.py"],
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

    _ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    # Trading-Assets aus .env oder capital_markets_config.py
    _trading_assets_env = os.getenv("TRADING_ASSETS", "").strip()
    if _trading_assets_env:
        trading_assets_info = f"  ✅ TRADING_ASSETS (.env): {_trading_assets_env}"
    else:
        trading_assets_info = f"  ℹ️  TRADING_ASSETS nicht in .env → alle aus capital_markets_config.py: {', '.join(MARKET_CONFIG.keys())}"

    # Trading-Assets aus .env oder capital_markets_config.py
    _trading_assets_env = os.getenv("TRADING_ASSETS", "").strip()
    if _trading_assets_env:
        _trading_assets_info = f"  ✅ TRADING_ASSETS (.env): {_trading_assets_env}"
    else:
        _trading_assets_info = f"  ℹ️  TRADING_ASSETS nicht in .env → alle aus capital_markets_config.py: {', '.join(MARKET_CONFIG.keys())}"
    
    baslanis_mesaji = f"""🕐 {_ts} | NEXUS NATURE {NEXUS_VERSION} - BRIDGEWATER EDITION Baslatildi
Mod: Rogers Filter + Gremium 5 + MA/ADX/RSI/BB/FIB/EMA200
Interval: {SCAN_INTERVAL_SEC / 3600:g}h (Macro-Scan) | Max Positionen: {MAX_POSITIONEN}
Kara Kuğu Koruması (3 Seviye):
  -%8  Gemini Acil Karar
  -%12 Otomatik Kapat
  -%18 ACIL TUM POZİSYONLARI KAPAT
Koruma-Thread: 5 Dakika (Quota yok)
Haber-Thread: 60 Dakika (RSS + X/Nitter, Quota yok)
Alternatif Veri: 31 Cargo Airline + 18 Gemi Bolgesi + BDI
  GDACS + NHC Kasirga + HDD/CDD + AB Gaz Deposu + ECMWF + NOAA
Haber Geçmişi: 14 Gün
Pyramiding: Sinir yok (min %2 kar per seviye) | EXIT: Gemini veya Trailing SL %5
Stop Loss: min. {SL_ATR_MULT:g} × Tagesspanne (Tages-ATR), max. {SL_MAX_PCT:g}% | /sl_weiten
Wiedereinstieg: frühestens {WIEDEREINSTIEG_SPERRE_STD:g} h nach einer Schließung | Scan-Meldungen: {SCAN_MELDUNGEN}
Gremium: Cihat/Rogers/Dalio/Taleb/Soros ({os.getenv('GREMIUM_MIN_JA', '4')}/5 JA gerekli, Krypto {os.getenv('GREMIUM_MIN_JA_KRYPTO', '3')}/5)
Spread Filter: Max {MAX_SPREAD} | Auto-Config: AKTİF
Haftasonu: ALLE Assets AKTIF (Krypto gleich wie andere behandelt)
Aşama 1 Filtre (Bollinger+Fib): AKTİF
Google Search Grounding: DEAKTIF (GDELT + AlphaVantage aktif)\nSQLite Hafıza: AKTİF\nKelly-Kriteri: AKTİF\nEconomic Calendar: AKTIF\nHava Durumu API: AKTİF\nKaynak Güvenilirliği: AKTİF

Komutlar: /help

🔧 TRADING ASSETS:
{_trading_assets_info}"""

    # .env Konfig-Check beim Start
    konfig_uyarilar = []
    if not GEMINI_MODELS:
        konfig_uyarilar.append("❌ GEMINI_MODEL_1 eksik! .env dosyasına GEMINI_MODEL_1=gemini-3.5-flash ekle.")
    else:
        konfig_uyarilar.append(f"✅ Gemini modeller: {', '.join(GEMINI_MODELS[:3])}{'...' if len(GEMINI_MODELS)>3 else ''}")
    valid_gem = [k for k in GEMINI_KEYS if k]
    if not valid_gem:
        konfig_uyarilar.append("❌ GEMINI_KEYS eksik! .env dosyasına GEMINI_KEYS=key1,key2 ekle.")
    else:
        konfig_uyarilar.append(f"✅ Gemini keys: {len(valid_gem)} adet")
    if not GROQ_KEYS:
        konfig_uyarilar.append("⚠️ GROQ_KEYS yok (opsiyonel fallback)")
    if gremium_aktiv():  # v16.0
        konfig_uyarilar.append(f"🏛️ Gremium: 11 Mentoren, Mehrheit {GREMIUM_MEHRHEIT:g}/11 (Krypto am Wochenende {GREMIUM_MEHRHEIT_KRYPTO:g}/11), "
                               f"höchstens {GREMIUM_MAX_KANDIDATEN} Märkte je Scan - /gremium")
    elif GREMIUM_MODUS == "ki":
        konfig_uyarilar.append("⚠️ Gremium: nexus_gremium.py fehlt - alter Ablauf aktiv")
    else:
        konfig_uyarilar.append("🏛️ Gremium: alter Ablauf (GREMIUM_MODUS=regeln)")
    # Provider-Anzeige mit Key-Anzahl (Merge aus Qwen-Session)
    _prov_display = []
    for _prov in PROVIDER_ORDER:
        if _prov == "gemini":
            _cnt = len(valid_gem) if valid_gem else 0
        elif _prov == "groq":
            _cnt = len(GROQ_KEYS) if GROQ_KEYS else 0
        elif _prov == "qwen":
            _cnt = len(_AI_KEYS["qwen"])  # v15.22: alle Keys zaehlen
        elif _prov == "nvidia":
            _cnt = len(_AI_KEYS["nvidia"])  # v15.22
        else:
            _cnt = 1 if os.getenv(f"{_prov.upper()}_API_KEY", "").strip() else 0
        _prov_display.append(f"{_prov}({_cnt})")
    konfig_uyarilar.append(f"Provider sırası: {', '.join(_prov_display)}")
    baslanis_mesaji += "\n\n🔧 Konfig:\n" + "\n".join(konfig_uyarilar)

    try: bot.send_message(MY_CHAT_ID, baslanis_mesaji)
    except Exception as e: logging.error(f"Başlangıç mesajı hatası: {e}")
    # v15.19: Beim ersten Start (BOT_LANGUAGE fehlt in der .env) nach der Sprache fragen.
    # Der Bot arbeitet waehrenddessen normal weiter und sendet bis zur Wahl die Originaltexte.
    if _NL is not None and BOT_LANGUAGE not in ("de", "en", "tr", "orig") and MY_CHAT_ID:
        send_language_chooser()

    sync_bericht = sync_pyramiding_from_capital()
    logging.info(sync_bericht)
    try: bot.send_message(MY_CHAT_ID, f"Başlangıç Senkronu:\n{sync_bericht}")
    except: pass

    # BotFather menu - "/" yazinca komutlar gorunsun
    try:
        from telebot.types import BotCommand
        bot.set_my_commands([
            BotCommand("status",      "Tam quant analiz + Gremium oylama"),
            BotCommand("pozisyon",    "Acik pozisyonlar, PnL, Pyramiding"),
            BotCommand("kapat",       "Kapat: /kapat GOLD | /kapat ALLE"),
            BotCommand("manuell",     "Manuel trade: /manuell GOLD BUY 100"),
            BotCommand("ma",          "MA9/26 + ADX + RSI sinyalleri"),
            BotCommand("volatilite",  "Volatilite + Kara Kugu kontrolu"),
            BotCommand("spread",      "Spread tarama + config guncelleme"),
            BotCommand("backtest",    "Backtest: /backtest GOLD 200"),
            BotCommand("deepdive",    "Derin analiz: /deepdive GOLD HOUR_4 30"),
            BotCommand("stats",       "Trade istatistikleri + performans"),
            BotCommand("news",        "Haberler: /news OIL 7"),
            BotCommand("newscollect", "Manuel haber toplama: RSS + Grounding"),
            BotCommand("sources",     "Kaynak guvenilirlik skorlari"),
            BotCommand("kayip",       "Bugunun kayip/zarar sayaci"),
            BotCommand("bloklar",     "Aktif HARD BLOCK listesi"),
            BotCommand("dbtemizle",   "Eski/bozuk haberleri DB'den sil"),
            BotCommand("unut",        "Kaydedilen kullanici notlarini sil"),
            BotCommand("help",        "Tum komutlar ve kullanim rehberi"),
        ])
        logging.info("Telegram menu (BotCommand) ayarlandi")
    except Exception as e:
        logging.warning("BotCommand ayar hatasi: " + str(e))
    apply_language_ui(mit_tasten=False)  # v15.19: ueberschreibt das Menue oben, wenn eine Sprache gewaehlt ist

    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    threading.Thread(target=schutz_loop, daemon=True).start()
    threading.Thread(target=news_collector_loop, daemon=True).start()
    threading.Thread(target=_gemini_modelupdate_loop, daemon=True).start()  # v15.15: Gemini-Modellliste aktuell halten
    threading.Thread(target=_ai_modelupdate_loop, daemon=True).start()      # v15.22: Groq/Qwen/Nvidia-Modelle aktuell halten

    threading.Thread(target=exit_monitor_loop, daemon=True).start()
    logging.info("✅ Exit-Monitor Thread gestartet")

    threading.Thread(target=daily_tp_watcher_loop, daemon=True).start()
    logging.info("✅ Gunluk-TP-Bant Hatirlatma Thread gestartet")

    # Meta-Learning: wöchentlich Montag 06:00 ausführen
    def _meta_learn_scheduler():
        while True:
            now = datetime.now()
            if now.weekday() == 0 and now.hour == 6 and now.minute < 5:
                result = meta_learn_weekly()
                logging.info(f"Meta-Learn: {result}")
            time.sleep(300)  # alle 5 Min prüfen
    threading.Thread(target=_meta_learn_scheduler, daemon=True).start()
    logging.info("Koruma-Thread: 5 Dak | Haber-Thread: 60 Dak (Quota yok)")
    main_loop()
