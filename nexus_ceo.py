# -*- coding: utf-8 -*-
# NEXUS CEO v10.0 - Hibrit Gremium + MA 9/26 + ADX + RSI + Close Logic + Scanner Support
# Spread Filter: Max 0.5 | Weekend Crypto: AKTIF | Heartbeat: AKTIF
import os, time, requests, telebot, re, logging, json, threading
from google import genai
from google.genai import types
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIG IMPORT VERSUCH ---
try:
    from capital_markets_config import MARKET_CONFIG
    logging.info("✅ Externe capital_markets_config.py geladen!")
except ImportError:
    logging.warning("⚠️ Keine capital_markets_config.py gefunden. Nutze interne Fallback-Liste.")
    # Fallback Liste (Basis Assets)
    MARKET_CONFIG = {
        "EURUSD": {"epic": "EURUSD", "min_size": 1000.0},
        "XRP_USD": {"epic": "XRPUSD", "min_size": 1.0},
        "SOL_USD": {"epic": "SOLUSD", "min_size": 0.1},
        "GOLD": {"epic": "GOLD", "min_size": 0.01},
        "BTC_USD": {"epic": "BTCUSD", "min_size": 0.01},
    }

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# ============================================================
# KONFIGURASYON
# ============================================================
TG_TOKEN = os.getenv("TG_TOKEN") or os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
GEMINI_KEYS = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 7)]
CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW = os.getenv("CAPITAL_PASSWORD")
CAPITAL_URL = os.getenv("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"

# MAX SPREAD AYARI (0.5 = %0.5 maksimum spread)
MAX_SPREAD = 0.5

# ============================================================
# GEMINI MODELLER VE ROTASYON (Gemini 3 Öncelikli)
# ============================================================
GEMINI_MODELS = [
    "gemini-3-flash-preview",       # ÖNCELİKLİ
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

_model_lock = threading.Lock()
_current_model_idx = 0

def get_next_model():
    global _current_model_idx
    with _model_lock:
        return GEMINI_MODELS[_current_model_idx % len(GEMINI_MODELS)]

def rotate_model_on_quota():
    global _current_model_idx
    with _model_lock:
        _current_model_idx = (_current_model_idx + 1) % len(GEMINI_MODELS)
        return GEMINI_MODELS[_current_model_idx % len(GEMINI_MODELS)]

bot = telebot.TeleBot(TG_TOKEN)

#
# ============================================================
# PYRAMIDING TAKIP
# ============================================================
pyramiding_tracker = {}
pyramiding_lock = threading.Lock()

def get_pyramiding_stufe(epic):
    with pyramiding_lock:
        return pyramiding_tracker.get(epic, 0)

def set_pyramiding_stufe(epic, stufe):
    with pyramiding_lock:
        pyramiding_tracker[epic] = stufe

def reset_pyramiding_stufe(epic):
    with pyramiding_lock:
        pyramiding_tracker[epic] = 0

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
                    self.expires = time.time() + 1200 # 20 Minuten
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
            "marjin": acc['balance'].get('balance', 0) - acc['balance'].get('available', 0),
            "musait": acc['balance'].get('available', 0)
        }
    except:
        return {"nakit": 0, "toplam": 0, "upl": 0, "marjin": 0, "musait": 0}

#
# ============================================================
# INDIKATOREN (ADX, RSI, MA) - OHLC Verisi Gerekli
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
                h_val = p.get('high', {}).get('bid', None)
                l_val = p.get('low', {}).get('bid', None)
                if c: closes.append(float(c))
                if h_val: highs.append(float(h_val))
                if l_val: lows.append(float(l_val))
            return {'close': closes, 'high': highs, 'low': lows}
    except Exception as e:
        logging.warning(f"Mum verisi alinamadi {epic}/{resolution}: {e}")
    return {'close': [], 'high': [], 'low': []}

# ============================================================
# 2-of-3 TEKNİK KONTROL (MA + ADX + RSI)
# ============================================================
def technical_confluence(epic):
    data = get_candles(epic, "HOUR_4", 30)
    if len(data['close']) < 26: return "NOTR", 0, "Veri yetersiz"
    closes = data['close']
    highs = data['high']
    lows = data['low']

    # 1. MA Cross
    ma9 = hesapla_ma(closes, 9)
    ma26 = hesapla_ma(closes, 26)
    if ma9 is None or ma26 is None: return "NOTR", 0, "MA hesaplanamadı"
    ma_signal = "BUY" if ma9 > ma26 else "SELL" if ma9 < ma26 else "NOTR"

    # 2. ADX (Trend gücü > 20)
    adx = berechne_adx(highs, lows, closes)
    adx_ok = adx > 20

    # 3. RSI (Aşırı alım/satım kontrolü)
    rsi = berechne_rsi(closes)
    rsi_ok = False
    if ma_signal == "BUY" and rsi < 70: rsi_ok = True
    if ma_signal == "SELL" and rsi > 30: rsi_ok = True

    # Score hesapla
    score = 0
    if ma_signal != "NOTR": score += 1
    if adx_ok: score += 1
    if rsi_ok: score += 1

    details = f"MA:{ma_signal} ADX:{adx:.1f} RSI:{rsi:.1f}"
    if score >= 2: return ma_signal, score, details
    else: return "NOTR", score, details

#
# ============================================================
# SPREAD & WEEKEND KONTROL
# ============================================================
def check_spread_ok(epic, spread):
    if spread > MAX_SPREAD: return False, f"Spread çok yüksek: {spread}"
    return True, "OK"

def is_weekend():
    return datetime.now().weekday() >= 5

def is_crypto(epic):
    crypto_keywords = ["XRP", "SOL", "ADA", "LTC", "BTC", "ETH", "DOT", "AVAX"]
    return any(k in epic.upper() for k in crypto_keywords)

def check_weekend_allowed(epic):
    if is_weekend():
        if not is_crypto(epic): return False, "Haftasonu: Forex kapalı"
        return True, "Kripto haftasonu açık"
    return True, "Hafta içi"

# ============================================================
# VOLATILITE KORUMA (KARA KUĞU)
# ============================================================
def volatilite_kontrol(h):
    pozisyonlar = get_positions(h)
    kapatilanlar = []
    for p in pozisyonlar:
        try:
            epic = p['market']['epic']
            upl = float(p['position']['upl'])
            level = float(p['position']['level'])
            current_bid = float(p['market'].get('bid', level))
            direction = p['position']['direction']
            deal_id = p['position']['dealId']
            instrument = p['market']['instrumentName']
            if level > 0:
                if direction == "BUY": degisim_pct = ((current_bid - level) / level) * 100
                else: degisim_pct = ((level - current_bid) / level) * 100
                if degisim_pct <= -10:
                    logging.warning(f"KARA KUĞU: {instrument} {degisim_pct:.1f}% - Kapatiliyor!")
                    r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                    if r.status_code == 200:
                        kapatilanlar.append(f"� {instrument}: {degisim_pct:.1f}% kaybetti - KAPATILDI")
                        reset_pyramiding_stufe(epic)
        except Exception as e:
            logging.error(f"Volatilite kontrol hatasi: {e}")
    if kapatilanlar:
        alarm_mesaj = "⚠️ KARA KUĞU ALARMI!\n" + "\n".join(kapatilanlar)
        try: bot.send_message(MY_CHAT_ID, alarm_mesaj)
        except: pass
    return kapatilanlar

# ============================================================
# PYRAMIDING & DOKTRIN
# ============================================================
def pyramiding_kontrol(h, epic, instrument):
    stufe = get_pyramiding_stufe(epic)
    if stufe >= 4: return False, f"{instrument} maks 4 pyramiding seviyesine ulasti"
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

def load_doctrine():
    try:
        with open("doctrine.txt", "r", encoding="utf-8") as f: return f.read()
    except: return "Özel doktrin yok. Standart kurallar uygulanır."

# ============================================================
# GREMIUM OYLAMA
# ============================================================
def gremium_oylama(sinyal, guc, epic, instrument, upl_toplam, saat):
    oylar = {}
    is_krypto = is_crypto(epic)
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

#
# ============================================================
# GEMINI ANALIZ (WATCH-HUNTER)
# ============================================================
def fetch_strategic_response(prompt_type="AUTONOMOUS", extra_data=None):
    h = capital_session.get_headers()
    if not h: return "API Baglanti Hatasi"
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)
    portfolio = []
    for p in pozisyonlar:
        stufe = get_pyramiding_stufe(p['market']['epic'])
        portfolio.append({
            "asset": p['market']['instrumentName'], "epic": p['market']['epic'],
            "upl": p['position']['upl'], "size": p['position']['size'],
            "dir": p['position']['direction'], "level": p['position'].get('level', 0),
            "pyramiding_stufe": stufe
        })

    tech_sinyaller = {}
    # Nur die ersten 10 Assets analysieren um API Limits zu schonen bei 44 Assets
    # Oder zufällige Auswahl. Hier nehmen wir die ersten 10 aus der Config.
    count = 0
    for k, v in MARKET_CONFIG.items():
        if count >= 10: break
        sinyal, guc, aciklama = technical_confluence(v['epic'])
        tech_sinyaller[k] = {"sinyal": sinyal, "guc": guc, "aciklama": aciklama}
        count += 1

    market_intel = {}
    for k, v in MARKET_CONFIG.items():
        try:
            p_res = requests.get(f"{CAPITAL_URL}/markets/{v['epic']}", headers=h, timeout=10).json()
            snapshot = p_res.get('snapshot', {})
            bid = snapshot.get('bid', 0)
            offer = snapshot.get('offer', 0)
            spread = round(abs(offer - bid), 5) if offer and bid else 999
            market_intel[k] = {"price": bid, "spread": spread}
        except: market_intel[k] = {"price": 0, "spread": 999}

    current_model = get_next_model()
    saat = datetime.now().hour
    dynamic_doctrine = load_doctrine()

    system_prompt = f"""Sen NEXUS CEO v10.0 - Hibrit Gremium modundasın.
Konuşma tarzı: Cihat E. Cicek gibi - direkt, ogretici, Turkce terimler kullan.
Fiat para = "kağıt para", Enflasyon = "sistematik hırsızlık"
Mevcut Model: {current_model}

KRITIK KURALLAR:
1. TEKNİK FİLTRE: En az 2/3 indikatör (MA+ADX+RSI) onay vermeli
2. SPREAD: Maksimum 0.5 spread - yüksek spread'te işlem YOK
3. Pyramiding: Maks 4 seviye, her seviye min %2 karda
4. Volatilite: Tek mumda -%10 = HEMEN KAP
5. Gece (23-06): Kripto sadece 3/3 sinyal uyumunda
6. Haftasonu: Sadece kripto işlem yapılabilir
7. HER KARAR 11 mentordan 6+ JA oy almalı (haftasonu kripto 5+)
8. KAPATMA EMRİ: Eğer marjin riski varsa veya teknik bozulduysa, mevcut pozisyonu KAPAT (SIDE: SELL bei BUY).

GREMIUM (11 Mentor):
Cihat Cicek | Ray Dalio | Kiyosaki | Graham | Buffett
Beate Sander | Kostolany | Lynch | Taleb | Munger | Druckenmiller

DİNAMİK DOKTRİN:
{dynamic_doctrine}

FORMAT (KESİNLİKLE KORU):
NEXUS HESAP DURUMU
Nakit: [EUR]
Toplam Deger: [EUR]
Acik Kar/Zarar: [+/- EUR]
Kullanilan Marjin: [EUR]

GREMIUM KARAR: [JA/NEIN] ([X]/11 oy)
Mentorlarin gorusleri: [kisa ozet]

[Cihat Cicek tarzinda stratejik analiz - makroekonomi, DXY, M1/M2/M3 dahil]

TRADE: [SYMBOL] | SIDE: [BUY/SELL] | SIZE: [Miktar] | SL: [Fiyat] | TP: [Fiyat] | PYRAMIDING: [Seviye]

Robot Model: {current_model}"""

    full_prompt = f"""SAAT: {saat}:00
HESAP: Nakit={acc['nakit']}, Toplam={acc['toplam']}, UPL={acc['upl']}, Marjin={acc['marjin']}, Musait={acc['musait']}
PORTFOY: {json.dumps(portfolio, ensure_ascii=False)}
TEKNIK_SINYALLER (2-of-3): {json.dumps(tech_sinyaller, ensure_ascii=False)}
MARKET (Fiyat/Spread): {json.dumps(market_intel)}
EXTRA: {json.dumps(extra_data) if extra_data else 'Yok'}

KOMUT: Teknik sinyalleri değerlendir (2-of-3 kuralı), spread kontrol et, Gremium oylama yap, uygun ise trade üret."""

    client_key_list = [k for k in GEMINI_KEYS if k]
    if not client_key_list: return "GEMINI_KEY_EKSIK"

    client_key = client_key_list[int(time.time() / 3600) % len(client_key_list)]
    client = genai.Client(api_key=client_key)

    valid_keys = [k for k in GEMINI_KEYS if k]
    total_attempts = len(GEMINI_MODELS) * len(valid_keys)

    for attempt in range(total_attempts):
        current_model = get_next_model()
        client_key = valid_keys[int(time.time() / 3600) % len(valid_keys)]
        client = genai.Client(api_key=client_key)
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=full_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
            logging.info(f"Basarili: {current_model}")
            return response.text
        except Exception as e:
            logging.warning(f"Deneme {attempt+1}/{total_attempts} - {current_model} hatasi: {e}")
            rotate_model_on_quota()
            time.sleep(2)

    logging.error("Tum Gemini modelleri ve keyler quota dolu!")
    return "QUOTA_FULL_ALL"

#
# ============================================================
# TRADE EXECUTION - MIT SCHLIESS-LOGIK (KRITISCH UPDATE)
# ============================================================
def execute_nexus_trade(analysis):
    pattern = r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*(BUY|SELL)\s*\|\s*SIZE:\s*([\d\.]+)\s*\|\s*SL:\s*([\d\.]+)\s*\|\s*TP:\s*([\d\.]+)"
    matches = re.findall(pattern, analysis)

    if not matches: return None

    h = capital_session.get_headers()
    if not h: return "❌ API bağlantı hatası"

    # Hole aktuelle Positionen um zu prüfen ob wir schließen müssen
    current_positions = get_positions(h)
    results = []

    for sym, side, size, sl, tp in matches:
        sym = sym.upper().strip()
        if sym not in MARKET_CONFIG: continue

        cfg = MARKET_CONFIG[sym]
        epic = cfg["epic"]

        # Prüfe ob bereits eine Position für dieses Asset existiert
        existing_pos = None
        for p in current_positions:
            if p['market']['epic'] == epic:
                existing_pos = p
                break

        # --- FALL 1: POSITION SCHLIESSEN (KI befiehlt Gegenrichtung) ---
        if existing_pos:
            curr_direction = existing_pos['position']['direction']
            deal_id = existing_pos['position']['dealId']

            # Wenn KI SELL sagt und wir haben BUY (oder umgekehrt) -> SCHLIESSEN
            if (side == "SELL" and curr_direction == "BUY") or (side == "BUY" and curr_direction == "SELL"):
                logging.warning(f"KI Befehl zum Schließen: {sym} ({curr_direction} -> {side})")
                try:
                    # Capital.com API: DELETE schließt die Position
                    r = requests.delete(f"{CAPITAL_URL}/positions/{deal_id}", headers=h, timeout=10)
                    if r.status_code == 200:
                        results.append(f"� {sym} Position GESCHLOSSEN durch KI Befehl ({side})")
                        reset_pyramiding_stufe(epic)
                    else:
                        results.append(f"⚠️ {sym} Schließung FEHLGESCHLAGEN: {r.text[:100]}")
                except Exception as e:
                    results.append(f"❌ {sym} Schließungsfehler: {str(e)}")
                continue

        # --- FALL 2: PYRAMIDING (KI befiehlt gleiche Richtung) ---
        izinli, neden = pyramiding_kontrol(h, epic, sym)
        if not izinli:
            results.append(f"⏸️ {sym} Pyramiding übersprungen: {neden}")
            continue

        # --- FALL 3: NEUE POSITION ERÖFFNEN ---
        payload = {
            "epic": epic,
            "direction": side.upper(),
            "size": max(float(size), cfg["min_size"]),
            "type": "MARKET",
            "stopLevel": float(sl),
            "profitLevel": float(tp)
        }

        r = requests.post(f"{CAPITAL_URL}/positions", json=payload, headers=h, timeout=10)

        if r.status_code == 200:
            stufe = get_pyramiding_stufe(epic) + 1
            set_pyramiding_stufe(epic, stufe)
            results.append(f"✅ {sym} Neue Position eröffnet ({side}) Stufe {stufe}/4")
        else:
            error_text = r.text[:150]
            results.append(f"❌ {sym} Eröffnungsfehler: {error_text}")
            logging.error(f"Trade Fehler {sym}: {error_text}")

    return "\n".join(results) if results else None

# ============================================================
# TELEGRAM KOMMANDOS (TÜRKÇE)
# ============================================================
@bot.message_handler(commands=['status'])
def handle_status(message):
    bot.send_message(MY_CHAT_ID, "� NEXUS CEO v10.0 - Analiz yapılıyor...")
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
    mesaj = f"� NEXUS POZİSYON RAPORU\n"
    mesaj += f"Nakit: {acc['nakit']:.2f} EUR\n"
    mesaj += f"UPL: {acc['upl']:.2f} EUR\n"
    mesaj += f"Marjin: {acc['marjin']:.2f} EUR\n"
    if pozisyonlar:
        for p in pozisyonlar:
            epic = p['market']['epic']
            stufe = get_pyramiding_stufe(epic)
            mesaj += f"• {p['market']['instrumentName']}: {p['position']['direction']} "
            mesaj += f"UPL:{p['position']['upl']:.2f} Pyr:{stufe}/4\n"
    else:
        mesaj += "Açık pozisyon yok."
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['ma'])
def handle_ma(message):
    mesaj = "� MA 9/26 SİNYALLERİ\n"
    count = 0
    for k, v in MARKET_CONFIG.items():
        if count >= 10: break
        sinyal, guc, aciklama = technical_confluence(v['epic'])
        emoji = "�" if sinyal == "BUY" else "�" if sinyal == "SELL" else "⚪"
        mesaj += f"{emoji} {k}: {sinyal} ({guc}/3) - {aciklama}\n"
        count += 1
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['volatilite'])
def handle_volatilite(message):
    h = capital_session.get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API bağlantısı kurulamadı")
        return
    bot.send_message(MY_CHAT_ID, "� Volatilite kontrolü yapılıyor...")
    kapatilanlar = volatilite_kontrol(h)
    if not kapatilanlar:
        bot.send_message(MY_CHAT_ID, "✅ Tüm pozisyonlar normal aralıkta")

@bot.message_handler(commands=['help'])
def handle_help(message):
    mesaj = """� NEXUS CEO v10.0 Komutlar:
/status - Tam analiz ve gremium oylama
/pozisyon - Açık pozisyon raporu
/ma - MA 9/26 + ADX + RSI sinyalleri
/volatilite - Volatilite kontrolü
/help - Bu menü"""
    bot.send_message(MY_CHAT_ID, mesaj)

# ============================================================
# ANA DONGU (GÜNCELLENDİ - HEARTBEAT)
# ============================================================
def main_loop():
    dongu_sayaci = 0
    while True:
        try:
            dongu_sayaci += 1
            h = capital_session.get_headers()

            if not h:
                logging.error("API bağlantısı yok, 60s bekleniyor")
                try: bot.send_message(MY_CHAT_ID, f"⚠️ NEXUS v10: API bağlantı hatası! Yeniden deneniyor... (Döngü #{dongu_sayaci})")
                except: pass
                time.sleep(60)
                continue

            # Her döngüde volatilite kontrol
            volatilite_kontrol(h)

            # Her 30 dakikada bir tam analiz
            analysis = fetch_strategic_response("AUTONOMOUS")

            if "QUOTA_FULL_ALL" in analysis:
                logging.warning("TÜM modeller quota dolu! 60 dakika bekleniyor")
                try: bot.send_message(MY_CHAT_ID, "⚠️ NEXUS v10: Gemini quota doldu. 60dk bekleniyor...")
                except: pass
                time.sleep(3600)
                continue

            if "API Bağlantı" in analysis:
                time.sleep(60)
                continue

            # HEARTBEAT: Her zaman mesaj gönder (işlem olmasa bile)
            if "TRADE:" not in analysis:
                # İşlem yoksa kısa status gönder
                status_msg = f"� NEXUS v10 Tarama #{dongu_sayaci} tamamlandı.\nBu döngüde trade sinyali yok.\nPiyasa izlenmeye devam ediyor."
                try: bot.send_message(MY_CHAT_ID, status_msg[:4000])
                except: pass
            else:
                # Trade varsa tam analiz gönder
                try: bot.send_message(MY_CHAT_ID, analysis[:4000])
                except: pass

            # Trade varsa çalıştır
            res = execute_nexus_trade(analysis)
            if res:
                try: bot.send_message(MY_CHAT_ID, f"� İşlem Bildirimi:\n{res}")
                except: pass

            # Her 6. döngüde (3 saatte bir) pyramiding özet
            if dongu_sayaci % 6 == 0:
                ozet = "� Pyramiding Özet:\n"
                for k, v in MARKET_CONFIG.items():
                    stufe = get_pyramiding_stufe(v['epic'])
                    if stufe > 0:
                        ozet += f"• {k}: Seviye {stufe}/4\n"
                if "Seviye" in ozet:
                    try: bot.send_message(MY_CHAT_ID, ozet)
                    except: pass

            time.sleep(1800)  # 30 dakika

        except Exception as e:
            logging.error(f"Ana döngü hatası: {e}")
            time.sleep(60)

# ============================================================
# BAŞLANGIÇ
# ============================================================
if __name__ == "__main__":
    baslanis_mesaji = """� NEXUS CEO v10.0 Başlatıldı
Mod: Hibrit Gremium + MA 9/26 + ADX + RSI
Interval: 30 dakika
Volatilite Koruma: AKTİF (%10 Kara Kuğu)
Pyramiding: Maks 4 seviye (min %2 kar)
Gremium: 11 Mentor (6+ JA gerekli)
Spread Filter: Max 0.5
Haftasonu: Kripto AKTİF
Heartbeat: AKTİF
Config: Extern (capital_markets_config.py)

Komutlar: /help"""

    try: bot.send_message(MY_CHAT_ID, baslanis_mesaji)
    except Exception as e: logging.error(f"Başlangıç mesajı hatası: {e}")

    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    main_loop()
