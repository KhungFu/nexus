# -*- coding: utf-8 -*-
# NEXUS CEO v9.0 - Hibrit Gremium + MA 9/26 Multi-Timeframe + Volatilite Koruma
import os, time, requests, telebot, re, logging, json, threading
from google import genai
from google.genai import types
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- KONFIGURASYON ---
TG_TOKEN = os.getenv("TG_TOKEN") or os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")
GEMINI_KEYS = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 7)]
CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW = os.getenv("CAPITAL_PASSWORD")
CAPITAL_URL = os.getenv("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"

# --- GEMINI MODELLER VE ROTASYON ---
GEMINI_MODELS = [
    "gemini-3-flash-preview",       # Overgeordnet - En guclu
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

# --- MARKET LISTESI ---
MARKET_CONFIG = {
    "EURUSD":  {"epic": "EURUSD",  "min_size": 1000.0},
    "XRP_EUR": {"epic": "XRP_EUR", "min_size": 1.0},
    "XRP_USD": {"epic": "XRP_USD", "min_size": 1.0},
    "SOL_EUR": {"epic": "SOL_EUR", "min_size": 0.1},
    "SOL_USD": {"epic": "SOL_USD", "min_size": 0.1},
    "ADA_EUR": {"epic": "ADA_EUR", "min_size": 1.0},
    "ADA_USD": {"epic": "ADA_USD", "min_size": 1.0},
    "LTC_EUR": {"epic": "LTC_EUR", "min_size": 0.1},
    "LTC_USD": {"epic": "LTC_USD", "min_size": 0.1},
}

# --- PYRAMIDING TAKIP ---
# {epic: pyramiding_stufe (0-4)}
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
# CAPITAL.COM HELPERS
# ============================================================

def get_headers():
    try:
        r = requests.post(
            f"{CAPITAL_URL}/session",
            json={"identifier": CAP_ID, "password": CAP_PW},
            headers={"X-CAP-API-KEY": CAP_KEY},
            timeout=15
        )
        if r.status_code == 200:
            return {
                "X-CAP-API-KEY": CAP_KEY,
                "CST": r.headers.get("CST"),
                "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN"),
                "Content-Type": "application/json"
            }
    except Exception as e:
        logging.error(f"Session hatasi: {e}")
    return None

def get_positions(h):
    try:
        return requests.get(f"{CAPITAL_URL}/positions", headers=h, timeout=10).json().get('positions', [])
    except:
        return []

def get_account_info(h):
    try:
        acc_req = requests.get(f"{CAPITAL_URL}/accounts", headers=h, timeout=10).json()
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

# ============================================================
# MA 9/26 HESAPLAMA - MULTI TIMEFRAME
# ============================================================

def hesapla_ma(prices, period):
    """Basit hareketli ortalama hesapla"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def get_candles(epic, resolution, max_candles=30):
    """Capital.com'dan mum verisi al"""
    h = get_headers()
    if not h:
        return []
    try:
        url = f"{CAPITAL_URL}/prices/{epic}?resolution={resolution}&max={max_candles}"
        r = requests.get(url, headers=h, timeout=15)
        if r.status_code == 200:
            prices_data = r.json().get('prices', [])
            # Kapanış fiyatlarını al
            closes = []
            for p in prices_data:
                close = p.get('closePrice', {}).get('bid', None)
                if close:
                    closes.append(float(close))
            return closes
    except Exception as e:
        logging.warning(f"Mum verisi alinamadi {epic}/{resolution}: {e}")
    return []

def ma_cross_signal(epic):
    """
    MA 9/26 Cross - Multi Timeframe Analizi
    4H = Giris sinyali
    D1 = Orta vade filtre
    W1 = Uzun vade filtre
    
    Donus: (sinyal, guc, aciklama)
    sinyal: "BUY", "SELL", "NOTR"
    guc: 1-3 (kac timeframe uyusuyor)
    """
    sonuclar = {}
    
    # Capital.com resolution degerleri
    timeframes = {
        "4H": "HOUR_4",
        "D1": "DAY",
        "W1": "WEEK"
    }
    
    for tf_adi, tf_kod in timeframes.items():
        closes = get_candles(epic, tf_kod, 30)
        if len(closes) < 26:
            sonuclar[tf_adi] = "NOTR"
            continue
        
        ma9  = hesapla_ma(closes, 9)
        ma26 = hesapla_ma(closes, 26)
        
        if ma9 is None or ma26 is None:
            sonuclar[tf_adi] = "NOTR"
            continue
        
        if ma9 > ma26:
            sonuclar[tf_adi] = "BUY"
        elif ma9 < ma26:
            sonuclar[tf_adi] = "SELL"
        else:
            sonuclar[tf_adi] = "NOTR"
    
    # 4H sinyal yoksa NOTR
    if sonuclar.get("4H", "NOTR") == "NOTR":
        return "NOTR", 0, "4H sinyali yok"
    
    ana_sinyal = sonuclar["4H"]
    guc = sum(1 for s in sonuclar.values() if s == ana_sinyal)
    
    aciklama = f"4H:{sonuclar.get('4H','?')} D1:{sonuclar.get('D1','?')} W1:{sonuclar.get('W1','?')}"
    
    # Minimum 2/3 timeframe uyumlu olmali
    if guc < 2:
        return "NOTR", guc, f"Zayif sinyal - {aciklama}"
    
    return ana_sinyal, guc, aciklama

# ============================================================
# VOLATILITE KORUMA - KARA KUĞU ALARMI
# ============================================================

def volatilite_kontrol(h):
    """
    Tum acik pozisyonlari kontrol et.
    Bir pozisyon %10+ duserse HEMEN kapat + Telegram alarmi.
    """
    pozisyonlar = get_positions(h)
    kapatilanlar = []
    
    for p in pozisyonlar:
        try:
            epic = p['market']['epic']
            upl = float(p['position']['upl'])
            level = float(p['position']['level'])  # giris fiyati
            current_bid = float(p['market'].get('bid', level))
            direction = p['position']['direction']
            deal_id = p['position']['dealId']
            instrument = p['market']['instrumentName']
            
            # Fiyat degisim yuzdesi hesapla
            if level > 0:
                if direction == "BUY":
                    degisim_pct = ((current_bid - level) / level) * 100
                else:
                    degisim_pct = ((level - current_bid) / level) * 100
                
                # -10% veya daha kotu = KARA KUĞU
                if degisim_pct <= -10:
                    logging.warning(f"KARA KUĞU: {instrument} {degisim_pct:.1f}% - Kapatiliyor!")
                    
                    # Pozisyonu kapat
                    r = requests.delete(
                        f"{CAPITAL_URL}/positions/{deal_id}",
                        headers=h,
                        timeout=10
                    )
                    
                    if r.status_code == 200:
                        kapatilanlar.append(f"🔴 {instrument}: {degisim_pct:.1f}% kaybetti - KAPATILDI")
                        reset_pyramiding_stufe(epic)
                    else:
                        kapatilanlar.append(f"⚠️ {instrument}: Kapatma HATASI - {r.text[:100]}")
        except Exception as e:
            logging.error(f"Volatilite kontrol hatasi: {e}")
    
    if kapatilanlar:
        alarm_mesaj = "⚠️ KARA KUĞU ALARMI!\n\n" + "\n".join(kapatilanlar)
        alarm_mesaj += "\n\nTaleb Kurali: Hayatta kalmak kazanmaktan önce gelir!"
        try:
            bot.send_message(MY_CHAT_ID, alarm_mesaj)
        except:
            pass
    
    return kapatilanlar

# ============================================================
# PYRAMIDING KONTROL
# ============================================================

def pyramiding_kontrol(h, epic, instrument):
    """
    Mevcut pyramiding seviyesini kontrol et.
    4 stufe dolmus mu? Pozisyon %2+ karda mi?
    """
    stufe = get_pyramiding_stufe(epic)
    
    if stufe >= 4:
        return False, f"{instrument} maks 4 pyramiding seviyesine ulasti"
    
    # Mevcut pozisyonlari kontrol et
    pozisyonlar = get_positions(h)
    epic_pozisyonlar = [p for p in pozisyonlar if p['market']['epic'] == epic]
    
    if not epic_pozisyonlar:
        # Ilk giris - serbest
        return True, "Ilk giris"
    
    # En son pozisyonun karini kontrol et
    for p in epic_pozisyonlar:
        upl = float(p['position']['upl'])
        level = float(p['position']['level'])
        size = float(p['position']['size'])
        
        # Kucuk pozisyonlarda yuzde hesabi zor, UPL pozitif mi yeterli
        if level > 0 and size > 0:
            # Yaklasik maliyet
            maliyet = level * size
            if maliyet > 0:
                kar_pct = (upl / maliyet) * 100
                if kar_pct >= 2.0:
                    return True, f"Pozisyon %{kar_pct:.1f} karda - Pyramiding izinli"
                else:
                    return False, f"Pozisyon sadece %{kar_pct:.1f} karda - Min %2 gerekli"
    
    return False, "Pyramiding icin yeterli kar yok"

# ============================================================
# GREMIUM - 11 MENTOR OYLAMA SISTEMI
# ============================================================

def gremium_oylama(sinyal, guc, epic, instrument, upl_toplam, saat):
    """
    11 mentor demokratik oylama.
    Her mentor kendi doktrinine gore oy verir.
    """
    oylar = {}
    
    is_krypto = any(k in epic.upper() for k in ["XRP", "SOL", "ADA", "LTC", "BTC", "ETH"])
    is_gece = 23 <= saat or saat < 6
    
    # 1. Cihat Çiçek - Gold ve hard assets, enflasyon savunmasi
    if sinyal in ["BUY", "SELL"] and guc >= 2:
        oylar["Cihat"] = "JA"
    else:
        oylar["Cihat"] = "NEIN"
    
    # 2. Ray Dalio - Zayif sinyal ve gece kriptoda NEIN
    if guc >= 2 and not (is_krypto and is_gece and guc < 3):
        oylar["Dalio"] = "JA"
    else:
        oylar["Dalio"] = "NEIN"
    
    # 3. Kiyosaki - Cashflow odakli, her sinyale EVET
    oylar["Kiyosaki"] = "JA" if sinyal != "NOTR" else "NEIN"
    
    # 4. Graham - Margin of safety, sadece guclu sinyalde
    oylar["Graham"] = "JA" if guc == 3 else "NEIN"
    
    # 5. Buffett - Economic moat, uzun vadeli trend lazim
    oylar["Buffett"] = "JA" if guc >= 2 else "NEIN"
    
    # 6. Beate Sander - Antisiklist, toplam zarar cok mu?
    if upl_toplam < -30:
        oylar["Sander"] = "NEIN"  # Hesap zor durumda
    else:
        oylar["Sander"] = "JA" if sinyal != "NOTR" else "NEIN"
    
    # 7. Kostolany - Herkes aliyorsa sat! Gece kriptoya dikkat
    if is_krypto and is_gece:
        oylar["Kostolany"] = "NEIN"
    else:
        oylar["Kostolany"] = "JA" if guc >= 2 else "NEIN"
    
    # 8. Lynch - Anlasilan varliklar, iyi bilinenler
    oylar["Lynch"] = "JA" if sinyal != "NOTR" else "NEIN"
    
    # 9. Taleb - Anti-fragil, zayif sinyalde asla
    if guc < 2 or (is_krypto and is_gece):
        oylar["Taleb"] = "NEIN"
    else:
        oylar["Taleb"] = "JA"
    
    # 10. Munger - Disiplin, sadece net sinyaller
    oylar["Munger"] = "JA" if guc >= 2 else "NEIN"
    
    # 11. Druckenmiller - Trend doneminde agresif
    oylar["Druckenmiller"] = "JA" if guc == 3 else ("NEIN" if guc < 2 else "JA")
    
    ja_sayisi = sum(1 for v in oylar.values() if v == "JA")
    nein_sayisi = len(oylar) - ja_sayisi
    
    karar = ja_sayisi >= 6
    
    return karar, ja_sayisi, nein_sayisi, oylar

# ============================================================
# ANA GEMINI ANALIZ
# ============================================================

def fetch_strategic_response(prompt_type="AUTONOMOUS", extra_data=None):
    h = get_headers()
    if not h:
        return "API Baglanti Hatasi"
    
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)
    
    portfolio = []
    for p in pozisyonlar:
        stufe = get_pyramiding_stufe(p['market']['epic'])
        portfolio.append({
            "asset": p['market']['instrumentName'],
            "epic": p['market']['epic'],
            "upl": p['position']['upl'],
            "size": p['position']['size'],
            "dir": p['position']['direction'],
            "level": p['position'].get('level', 0),
            "pyramiding_stufe": stufe
        })
    
    # MA Cross sinyallerini topla
    ma_sinyaller = {}
    for k, v in MARKET_CONFIG.items():
        sinyal, guc, aciklama = ma_cross_signal(v['epic'])
        ma_sinyaller[k] = {"sinyal": sinyal, "guc": guc, "aciklama": aciklama}
    
    market_intel = {}
    for k, v in MARKET_CONFIG.items():
        try:
            p_res = requests.get(f"{CAPITAL_URL}/markets/{v['epic']}", headers=h, timeout=10).json()
            snapshot = p_res.get('snapshot', {})
            bid = snapshot.get('bid', 0)
            offer = snapshot.get('offer', 0)
            spread = round(abs(offer - bid), 5) if offer and bid else 999
            market_intel[k] = {"price": bid, "spread": spread}
        except:
            market_intel[k] = {"price": 0, "spread": 999}
    
    current_model = get_next_model()
    saat = datetime.now().hour
    
    system_prompt = f"""Sen NEXUS CEO v9.0 - Hibrit Gremium modundasin.
Konusma tarzi: Cihat E. Cicek gibi - direkt, ogretici, Turkce terimler kullan.
Fiat para = "kagit para", Enflasyon = "sistematik hirsizlik"
Mevcut Model: {current_model}

KRITIK KURALLAR:
1. MA 9/26 Cross BIRINCIL STRATEJI - 4H giris, D1+W1 filtre
2. En az 2/3 timeframe uyumlu olmali - aksi halde TRADE YOK
3. Pyramiding: Maks 4 seviye, her seviye min %2 karda
4. Volatilite: Tek mumda -%10 = HEMEN KAP
5. Gece (23-06): Kripto sadece 3/3 sinyal uyumunda
6. Her karar 11 mentordan 6+ JA oyu almali

GREMIUM (11 Mentor):
Cihat Cicek | Ray Dalio | Kiyosaki | Graham | Buffett
Beate Sander | Kostolany | Lynch | Taleb | Munger | Druckenmiller

FORMAT (KESINLIKLE KOR):
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
MA_CROSS_SINYALLER: {json.dumps(ma_sinyaller, ensure_ascii=False)}
MARKET (Fiyat/Spread): {json.dumps(market_intel)}
EXTRA: {json.dumps(extra_data) if extra_data else 'Yok'}
KOMUT: MA 9/26 sinyallerini degerlendir, Gremium oylama yap, uygun ise trade uret."""

    client_key_list = [k for k in GEMINI_KEYS if k]
    if not client_key_list:
        return "GEMINI_KEY_EKSIK"
    
    client_key = client_key_list[int(time.time() / 3600) % len(client_key_list)]
    client = genai.Client(api_key=client_key)
    
    # Tum model ve key kombinasyonlarini dene
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
            time.sleep(2)  # Kisa bekleme
    
    # Tum modeller ve keyler denendi, hepsi bitti
    logging.error("Tum Gemini modelleri ve keyler quota dolu!")
    return "QUOTA_FULL_ALL"

# ============================================================
# TRADE EXECUTION - PYRAMIDING KONTROL ILE
# ============================================================

def execute_nexus_trade(analysis):
    pattern = r"TRADE:\s*([\w\._]+)\s*\|\s*SIDE:\s*(BUY|SELL)\s*\|\s*SIZE:\s*([\d\.]+)\s*\|\s*SL:\s*([\d\.]+)\s*\|\s*TP:\s*([\d\.]+)"
    matches = re.findall(pattern, analysis)
    if not matches:
        return None
    
    h = get_headers()
    if not h:
        return "❌ API baglanti hatasi"
    
    results = []
    
    for sym, side, size, sl, tp in matches:
        sym = sym.upper().strip()
        if sym not in MARKET_CONFIG:
            continue
        
        cfg = MARKET_CONFIG[sym]
        epic = cfg["epic"]
        
        # Pyramiding kontrol
        izinli, neden = pyramiding_kontrol(h, epic, sym)
        if not izinli:
            results.append(f"⏸️ {sym} Pyramiding beklemede: {neden}")
            continue
        
        # Mevcut SL senkronize et (trailing)
        try:
            pozisyonlar = get_positions(h)
            for p in pozisyonlar:
                if p['market']['epic'] == epic:
                    deal_id = p['position']['dealId']
                    current_sl = p['position'].get('stopLevel', 0)
                    new_sl = float(sl)
                    
                    # SL sadece kar yonunde hareket etmeli
                    direction = p['position']['direction']
                    if direction == "BUY" and new_sl > (current_sl or 0):
                        requests.put(
                            f"{CAPITAL_URL}/positions/{deal_id}",
                            json={"stopLevel": new_sl, "profitLevel": float(tp)},
                            headers=h,
                            timeout=10
                        )
                    elif direction == "SELL" and new_sl < (current_sl or 999999):
                        requests.put(
                            f"{CAPITAL_URL}/positions/{deal_id}",
                            json={"stopLevel": new_sl, "profitLevel": float(tp)},
                            headers=h,
                            timeout=10
                        )
        except Exception as e:
            logging.warning(f"SL sync hatasi {sym}: {e}")
        
        # Yeni islem ac
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
            results.append(f"✅ {sym} Pyramiding Seviye {stufe}/4 - {side}")
        else:
            error_text = r.text[:150]
            results.append(f"❌ {sym} Hata: {error_text}")
            logging.error(f"Trade hatasi {sym}: {error_text}")
    
    return "\n".join(results) if results else None

# ============================================================
# TELEGRAM KOMUTLAR
# ============================================================

@bot.message_handler(commands=['status'])
def handle_status(message):
    bot.send_message(MY_CHAT_ID, "🔍 NEXUS CEO v9.0 - Analiz yapiliyor...")
    analysis = fetch_strategic_response("STATUS_REQUEST")
    bot.send_message(MY_CHAT_ID, analysis[:4000])

@bot.message_handler(commands=['pozisyon'])
def handle_pozisyon(message):
    h = get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API baglantisi kurulamadi")
        return
    
    acc = get_account_info(h)
    pozisyonlar = get_positions(h)
    
    mesaj = f"📊 NEXUS POZISYON RAPORU\n"
    mesaj += f"Nakit: {acc['nakit']:.2f} EUR\n"
    mesaj += f"UPL: {acc['upl']:.2f} EUR\n"
    mesaj += f"Marjin: {acc['marjin']:.2f} EUR\n\n"
    
    if pozisyonlar:
        for p in pozisyonlar:
            epic = p['market']['epic']
            stufe = get_pyramiding_stufe(epic)
            mesaj += f"• {p['market']['instrumentName']}: {p['position']['direction']} "
            mesaj += f"UPL:{p['position']['upl']:.2f} Pyr:{stufe}/4\n"
    else:
        mesaj += "Acik pozisyon yok."
    
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['ma'])
def handle_ma(message):
    mesaj = "📈 MA 9/26 SINYALLER\n\n"
    for k, v in MARKET_CONFIG.items():
        sinyal, guc, aciklama = ma_cross_signal(v['epic'])
        emoji = "🟢" if sinyal == "BUY" else "🔴" if sinyal == "SELL" else "⚪"
        mesaj += f"{emoji} {k}: {sinyal} ({guc}/3) - {aciklama}\n"
    bot.send_message(MY_CHAT_ID, mesaj)

@bot.message_handler(commands=['volatilite'])
def handle_volatilite(message):
    h = get_headers()
    if not h:
        bot.send_message(MY_CHAT_ID, "❌ API baglantisi kurulamadi")
        return
    bot.send_message(MY_CHAT_ID, "🔍 Volatilite kontrolu yapiliyor...")
    kapatilanlar = volatilite_kontrol(h)
    if not kapatilanlar:
        bot.send_message(MY_CHAT_ID, "✅ Tum pozisyonlar normal aralıkta")

@bot.message_handler(commands=['help'])
def handle_help(message):
    mesaj = """🦞 NEXUS CEO v9.0 Komutlar:

/status - Tam analiz ve gremium oylama
/pozisyon - Acik pozisyon raporu
/ma - MA 9/26 multi-timeframe sinyaller
/volatilite - Volatilite kontrolu
/help - Bu menu"""
    bot.send_message(MY_CHAT_ID, mesaj)

# ============================================================
# ANA DONGU
# ============================================================

def main_loop():
    dongu_sayaci = 0
    
    while True:
        try:
            dongu_sayaci += 1
            h = get_headers()
            
            if not h:
                logging.error("API baglantisi yok, 60s bekleniyor")
                time.sleep(60)
                continue
            
            # Her dongude volatilite kontrol
            volatilite_kontrol(h)
            
            # Her 30 dakikada bir tam analiz
            analysis = fetch_strategic_response("AUTONOMOUS")
            
            if "QUOTA_FULL_ALL" in analysis:
                logging.warning("TUM modeller quota dolu! 60 dakika bekleniyor")
                try:
                    pass
                except:
                    pass
                time.sleep(3600)
                continue

            
            if "API Baglanti" in analysis:
                time.sleep(60)
                continue
            
            # Telegram'a gonder (maks 4000 karakter)
            bot.send_message(MY_CHAT_ID, analysis[:4000])
            
            # Trade varsa calistir
            res = execute_nexus_trade(analysis)
            if res:
                bot.send_message(MY_CHAT_ID, f"📋 Islem Bildirimi:\n{res}")
            
            # Her 6. dongude (3 saatte bir) pyramiding ozet
            if dongu_sayaci % 6 == 0:
                ozet = "📊 Pyramiding Ozet:\n"
                for k, v in MARKET_CONFIG.items():
                    stufe = get_pyramiding_stufe(v['epic'])
                    if stufe > 0:
                        ozet += f"• {k}: Seviye {stufe}/4\n"
                if "Seviye" in ozet:
                    bot.send_message(MY_CHAT_ID, ozet)
            
            time.sleep(1800)  # 30 dakika
            
        except Exception as e:
            logging.error(f"Ana dongu hatasi: {e}")
            time.sleep(60)

# ============================================================
# BASLANGIC
# ============================================================

if __name__ == "__main__":
    baslanis_mesaji = """🦞 NEXUS CEO v9.0 Baslatildi

Mod: Hibrit Gremium + MA 9/26 Multi-Timeframe
Interval: 30 dakika
Volatilite Koruma: AKTIF (%10 Kara Kuğu)
Pyramiding: Maks 4 seviye (min %2 kar)
Gremium: 11 Mentor (6+ JA gerekli)

Komutlar: /help"""
    
    try:
        bot.send_message(MY_CHAT_ID, baslanis_mesaji)
    except Exception as e:
        logging.error(f"Baslangic mesaji hatasi: {e}")
    
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    main_loop()
