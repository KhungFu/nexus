# -*- coding: utf-8 -*-
import time
import json
import glob
import os
import datetime
import traceback
import sys

# --- ABTEILUNGEN IMPORTIEREN ---
from nexus_scanner import deep_scan_full_report
from capital import CapitalManager
from gemini import GeminiAnalyst
from telegram import TelegramBot
from logger import nexus_logger

class NexusCEO:
    def __init__(self):
        print("🏛️ NEXUS CAPITAL CORP: CEO übernimmt die Leitung.")
        
        self.ops = CapitalManager()
        self.strategy = GeminiAnalyst()
        self.comm = TelegramBot()
        
        # Einstellungen
        self.base_interval = 1800  # 30 Min
        self.error_interval = 3600 # 60 Min
        self.budget_limit = 100.0  # Grenze für Survival Mode
        
        # Keywords für die Markt-Filterung
        self.survival_keywords = ["GOLD", "SILVER", "OIL", "BRENT", "COPPER", "GAS", "COTTON", "SUGAR", "COFFEE", "WHEAT"]
        self.crypto_keywords = ["BITCOIN", "ETHEREUM", "RIPPLE", "LITECOIN", "DOGE", "BTC", "ETH", "XRP", "LTC", "SOL", "ADA", "DOT"]

    def load_doctrine_and_intel(self):
        doctrine_text = "Standard Doktrin: Handle vorsichtig."
        info_text = ""
        if os.path.exists("toplam_egitim.txt"):
            with open("toplam_egitim.txt", "r", encoding="utf-8", errors="ignore") as f: 
                doctrine_text = f.read()
        
        files = glob.glob("*.txt")
        for file in files:
            if file == "toplam_egitim.txt": continue
            with open(file, "r", encoding="utf-8", errors="ignore") as f: 
                info_text += f"\nSOURCE {file}: {f.read()[:2000]}\n"
        return doctrine_text, info_text

    def filter_market_data(self, mode):
        """Filtert die market_data.json, um Token zu sparen und Fehler zu vermeiden."""
        if not os.path.exists('market_data.json'): return "Keine Marktdaten vorhanden."
        
        try:
            with open('market_data.json', 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            instruments = full_data.get('market_catalog', {}).get('instruments', [])
            valid_list = []
            
            for inst in instruments:
                name = inst.get('instrumentName', '').upper()
                epic = inst.get('epic', '')
                status = inst.get('marketStatus', '')

                # Am Wochenende nur handelbare Märkte (Crypto) zeigen
                if status != "TRADEABLE" and mode == "CRYPTO_ONLY":
                    continue

                if mode == "SURVIVAL":
                    if any(x in name for x in self.survival_keywords) or any(x in epic for x in self.survival_keywords):
                        valid_list.append(f"{name} (EPIC: {epic})")
                elif mode == "CRYPTO_ONLY":
                    if any(x in name for x in self.crypto_keywords) or any(x in epic for x in self.crypto_keywords):
                        valid_list.append(f"{name} (EPIC: {epic})")
                else:
                    valid_list.append(f"{name} (EPIC: {epic})")

            return "\n".join(valid_list[:100]) # Top 100 zur Sicherheit
        except Exception as e:
            return f"Fehler beim Filtern: {e}"

    def run_business_cycle(self):
        try:
            print(f"\n⏰ --- ZYKLUS START: {datetime.datetime.now().strftime('%H:%M')} ---")
            
            # 1. STATUS HOLEN
            state = self.ops.get_state()
            if not state: 
                print("❌ Fehler: Konnte Kontodaten nicht abrufen.")
                return
            
            # Equity (Gesamtwert) nutzen
            balance = float(state['balance'].get('amount', 0))
            positions = state['positions']
            
            weekday = datetime.datetime.today().weekday()
            is_weekend = weekday >= 5 # 5=Samstag, 6=Sonntag
            
            # 2. MODUS BESTIMMEN
            if is_weekend:
                if balance > 0:
                    mode = "CRYPTO_ONLY"
                    print(f"🎰 WOCHENENDE: Crypto-Modus aktiv (Depotwert: {balance}€).")
                else:
                    print(f"🛌 WOCHENENDE: Kein Guthaben ({balance}€). Ruhemodus.")
                    return
            elif balance < self.budget_limit:
                mode = "SURVIVAL"
                print(f"⚠️ SURVIVAL MODE: Depotwert {balance}€ unter Limit. Nur Rohstoffe.")
            else:
                mode = "NORMAL"
                print(f"🚀 NORMALER MARKT: Depotwert {balance}€.")

            # 3. SCANNER AUSFÜHREN
            deep_scan_full_report()
            
            # 4. DATEN FÜR GEMINI VORBEREITEN
            market_menu = self.filter_market_data(mode)
            doctrine, intel = self.load_doctrine_and_intel()
            
            prompt = (
                f"DU BIST DER NEXUS STRATEGE. MODUS: {mode}\n"
                f"DEPOTWERT (EQUITY): {balance} EUR\n"
                f"OFFENE POSITIONEN: {json.dumps(positions)}\n\n"
                f"DOKTRIN:\n{doctrine[:1500]}\n\n"
                f"MARKT-OPTIONEN:\n{market_menu}\n\n"
                "AUFGABE: Entscheide über OPEN oder CLOSE. Antworte NUR im JSON Format:\n"
                "{\"summary\": \"Grund\", \"actions\": [{\"type\": \"OPEN\", \"epic\": \"...\", \"dir\": \"BUY/SELL\", \"size\": 0.1}, {\"type\": \"CLOSE\", \"dealId\": \"...\"}]}"
            )

            # 5. ANALYSE & AUSFÜHRUNG
            print("🧠 Gemini analysiert die Lage...")
            res = self.strategy.get_analysis(prompt)
            
            try:
                # JSON bereinigen
                clean_res = res.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_res)
                
                ops_log = []
                for act in data.get('actions', []):
                    if act['type'] == 'OPEN':
                        ok, msg = self.ops.place_order(act['epic'], act['dir'], act['size'], act.get('sl'), act.get('tp'))
                        ops_log.append(f"OPEN {act['epic']}: {'✅' if ok else '❌ ' + str(msg)}")
                    elif act['type'] == 'CLOSE':
                        ok, msg = self.ops.close_position(act['dealId'])
                        ops_log.append(f"CLOSE {act['dealId']}: {'✅' if ok else '❌ ' + str(msg)}")
                
                if ops_log:
                    self.comm.send_report(f"📊 **NEXUS ZYKLUS BERICHT**\nModus: {mode}\nEquity: {balance}€\n\n" + "\n".join(ops_log))
                else:
                    print("💤 Keine Aktionen empfohlen.")

            except Exception as e:
                print(f"JSON Fehler: {e}")
                nexus_logger.log_error("CEO_PARSE_ERROR", res)

        except Exception as e:
            err = traceback.format_exc()
            print(f"CRASH: {e}")
            nexus_logger.log_error("CEO_CRASH", err)

    def run(self):
        print("🚀 NEXUS CEO ONLINE")
        while True:
            self.run_business_cycle()
            time.sleep(self.base_interval)

if __name__ == "__main__":
    ceo = NexusCEO()
    if "--single-cycle" in sys.argv:
        ceo.run_business_cycle()
    else:
        ceo.run()
