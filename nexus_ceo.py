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
        
        # Zeit-Intervalle (Personalisiert nach deinen Vorgaben)
        self.base_interval = 1800  # 30 Minuten (Normaler autonomer Intervall)
        self.error_interval = 3600 # 60 Minuten (Erhöhte Pause bei API-Limit)
        
        self.budget_limit = 100.0  # Grenze für Survival Mode
        
        # Keywords für die Markt-Filterung
        self.survival_keywords = ["GOLD", "SILVER", "OIL", "BRENT", "COPPER", "GAS", "COTTON"]
        self.crypto_keywords = ["BTC", "ETH", "XRP", "LTC", "SOL", "DOGE", "BITCOIN", "ETHEREUM"]

    def load_doctrine_and_intel(self):
        """Lädt die zentrale Doktrin aus mentor_name.txt und weitere Intel-Quellen."""
        doctrine_text = "Standard Doktrin: Handle vorsichtig und otonom."
        
        # Prüfung auf mentor_name.txt (wie von dir gewünscht)
        if os.path.exists("mentor_name.txt"):
            with open("mentor_name.txt", "r", encoding="utf-8", errors="ignore") as f: 
                doctrine_text = f.read()
        
        info_text = ""
        files = glob.glob("*.txt")
        for file in files:
            if file == "mentor_name.txt": continue
            with open(file, "r", encoding="utf-8", errors="ignore") as f: 
                info_text += f"\nSOURCE {file}: {f.read()[:2000]}\n"
        return doctrine_text, info_text

    def filter_market_data(self, mode):
        """Filtert die Marktdaten, um Token bei Gemini zu sparen."""
        if not os.path.exists('market_data.json'): return "Keine Marktdaten vorhanden."
        try:
            with open('market_data.json', 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            instruments = full_data.get('market_catalog', {}).get('instruments', [])
            valid_list = []
            
            for inst in instruments:
                name = inst.get('instrumentName', '').upper()
                epic = inst.get('epic', '')
                
                if mode == "SURVIVAL":
                    if any(x in name or x in epic for x in self.survival_keywords):
                        valid_list.append(f"{name} (EPIC: {epic})")
                elif mode == "CRYPTO_ONLY":
                    if any(x in name or x in epic for x in self.crypto_keywords):
                        valid_list.append(f"{name} (EPIC: {epic})")
                else:
                    valid_list.append(f"{name} (EPIC: {epic})")

            return "\n".join(valid_list[:100])
        except Exception as e:
            return f"Fehler beim Filtern: {e}"

    def run_business_cycle(self):
        try:
            print(f"\n⏰ --- ZYKLUS START: {datetime.datetime.now().strftime('%H:%M')} ---")
            
            # 1. STATUS HOLEN (Equity Check)
            state = self.ops.get_state()
            if not state: 
                print(f"❌ API-Fehler oder Limit erreicht. Erhöhe Pause auf {self.error_interval//60} Min.")
                time.sleep(self.error_interval)
                return
            
            # Nutzt Equity (Bargeld + Gewinn/Verlust)
            balance = float(state['balance'].get('amount', 0))
            positions = state['positions']
            
            is_weekend = datetime.datetime.today().weekday() >= 5
            
            # 2. MODUS BESTIMMEN
            if is_weekend:
                if balance > 0:
                    mode = "CRYPTO_ONLY"
                    print(f"🎰 WOCHENENDE: Crypto-Modus aktiv (Equity: {balance}€).")
                else:
                    print(f"🛌 WOCHENENDE: Kein Guthaben ({balance}€). Ruhemodus.")
                    return
            elif balance < self.budget_limit:
                mode = "SURVIVAL"
                print(f"⚠️ SURVIVAL MODE: Equity {balance}€ unter {self.budget_limit}€. Nur Rohstoffe.")
            else:
                mode = "NORMAL"
                print(f"🚀 NORMALBETRIEB: Equity {balance}€.")

            # 3. SCANNER AUSFÜHREN
            deep_scan_full_report()
            
            # 4. DATEN FÜR GEMINI VORBEREITEN
            market_menu = self.filter_market_data(mode)
            doctrine, intel = self.load_doctrine_and_intel()
            
            prompt = (
                f"DU BIST DER NEXUS STRATEGE. MODUS: {mode}\n"
                f"DEPOTWERT (EQUITY): {balance} EUR\n"
                f"OFFENE POSITIONEN: {json.dumps(positions)}\n\n"
                f"MENTOR DOKTRIN (WICHTIG):\n{doctrine[:1500]}\n\n"
                f"AKTUELLE MÄRKTE:\n{market_menu}\n\n"
                "ENTSCHEIDUNG: Antworte NUR im JSON Format:\n"
                "{\"summary\": \"Grund\", \"actions\": [{\"type\": \"OPEN\", \"epic\": \"...\", \"dir\": \"BUY/SELL\", \"size\": 0.1}, {\"type\": \"CLOSE\", \"dealId\": \"...\"}]}"
            )

            # 5. KI-ANALYSE MIT MAXIMALEM KILL-SWITCH
            print("🧠 Gemini analysiert die Lage...")
            res = self.strategy.get_analysis(prompt)
            
            # 🛡️ NO-GEMINI-NO-TRADE SPERRE (KILL-SWITCH)
            if not res or "Analiz su an yapilamiyor" in res or len(res) < 10:
                warning = "🚨 KRITISCHER KI-AUSFALL: Gemini antwortet nicht (Token leer?)."
                print(warning)
                
                if positions:
                    print("📉 NOT-STOPP: Schließe sofort alle Positionen...")
                    for pos in positions:
                        self.ops.close_position(pos.get('dealId'))
                    self.comm.send_report(f"{warning}\n🛑 Alle Positionen wurden zur Sicherheit GESCHLOSSEN.")
                else:
                    self.comm.send_report(f"{warning}\n🚫 Handel ausgesetzt, bis KI verfügbar.")
                
                time.sleep(self.error_interval)
                return

            # 6. AUSFÜHRUNG
            try:
                clean_res = res.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_res)
                
                ops_log = []
                for act in data.get('actions', []):
                    if act['type'] == 'OPEN':
                        ok, msg = self.ops.place_order(act['epic'], act['dir'], act['size'], act.get('sl'), act.get('tp'))
                        ops_log.append(f"OPEN {act['epic']}: {'✅' if ok else '❌'}")
                    elif act['type'] == 'CLOSE':
                        ok, msg = self.ops.close_position(act['dealId'])
                        ops_log.append(f"CLOSE {act['dealId']}: {'✅' if ok else '❌'}")
                
                if ops_log:
                    self.comm.send_report(f"📊 **NEXUS ZYKLUS BERICHT**\nEquity: {balance}€\nModus: {mode}\n\n" + "\n".join(ops_log))

            except Exception as e:
                print(f"Fehler beim Verarbeiten der KI-Antwort: {e}")
                nexus_logger.log_error("CEO_PARSE_ERROR", res)

        except Exception as e:
            nexus_logger.log_error("CEO_CRASH", traceback.format_exc())

    def run(self):
        print("🚀 NEXUS CEO ONLINE")
        while True:
            self.run_business_cycle()
            time.sleep(self.base_interval)

if __name__ == "__main__":
    ceo = NexusCEO()
    # Support für Einzeldurchlauf (GitHub Actions) oder Dauerbetrieb
    if "--single-cycle" in sys.argv:
        ceo.run_business_cycle()
    else:
        ceo.run()
