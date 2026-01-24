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
        
        # Intervalle gemäß deiner Anweisung
        self.base_interval = 1800  # 30 Min Standard
        self.error_interval = 3600 # 60 Min Pause bei API-Limit
        self.budget_limit = 100.0
        
        # Marktfilter
        self.survival_keywords = ["GOLD", "SILVER", "OIL", "BRENT", "COPPER", "GAS"]
        self.crypto_keywords = ["BTC", "ETH", "XRP", "LTC", "SOL", "DOGE"]

    def load_doctrine_and_intel(self):
        doctrine_text = "Standard Doktrin: Handle vorsichtig."
        if os.path.exists("mentor_name.txt"):
            with open("mentor_name.txt", "r", encoding="utf-8", errors="ignore") as f: 
                doctrine_text = f.read()
        return doctrine_text

    def filter_market_data(self, mode):
        if not os.path.exists('market_data.json'): return "Keine Marktdaten."
        try:
            with open('market_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            instruments = data.get('market_catalog', {}).get('instruments', [])
            valid = []
            for inst in instruments:
                name, epic = inst.get('instrumentName', '').upper(), inst.get('epic', '')
                if mode == "CRYPTO_ONLY" and any(x in name or x in epic for x in self.crypto_keywords):
                    valid.append(f"{name} ({epic})")
                elif mode == "SURVIVAL" and any(x in name or x in epic for x in self.survival_keywords):
                    valid.append(f"{name} ({epic})")
                elif mode == "NORMAL":
                    valid.append(f"{name} ({epic})")
            return "\n".join(valid[:100])
        except: return "Filterfehler."

    def run_business_cycle(self):
        try:
            print(f"\n⏰ --- ZYKLUS START: {datetime.datetime.now().strftime('%H:%M')} ---")
            
            # 1. STATUS HOLEN
            state = self.ops.get_state()
            if not state:
                print(f"❌ API Fehler. Pause {self.error_interval//60} Min.")
                time.sleep(self.error_interval)
                return
            
            equity = float(state['balance'].get('amount', 0))
            positions = state['positions']
            is_weekend = datetime.datetime.today().weekday() >= 5
            
            # 2. MODUS BESTIMMEN
            if is_weekend:
                mode = "CRYPTO_ONLY" if equity > 0 else "IDLE"
            elif equity < self.budget_limit:
                mode = "SURVIVAL"
            else:
                mode = "NORMAL"

            if mode == "IDLE": return

            # 3. ANALYSE VORBEREITEN
            deep_scan_full_report()
            market_menu = self.filter_market_data(mode)
            doctrine = self.load_doctrine_and_intel()
            
            prompt = (
                f"DU BIST DER NEXUS STRATEGE. MODUS: {mode}\n"
                f"EQUITY: {equity} EUR\nOFFENE POSITIONEN: {json.dumps(positions)}\n"
                f"DOKTRIN: {doctrine[:1000]}\n"
                f"MÄRKTE:\n{market_menu}\n"
                "Antworte NUR JSON: {\"summary\": \"...\", \"actions\": [{\"type\": \"OPEN/CLOSE\", ...}]}"
            )

            # 4. 🛡️ KI-KILL-SWITCH (NO-GEMINI-NO-TRADE)
            print("🧠 Gemini entscheidet...")
            res = self.strategy.get_analysis(prompt)
            
            if not res or "Analiz su an yapilamiyor" in res or len(res) < 5:
                # KI-AUSFALL LOGIK
                msg = "🚨 KI-NOTAUS: Gemini antwortet nicht! (Token leer?)."
                print(msg)
                
                if positions:
                    print("📉 Schließe sofort ALLE Positionen zur Sicherheit...")
                    for pos in positions:
                        self.ops.close_position(pos.get('dealId'))
                    self.comm.send_report(f"{msg}\n🛑 Alle Trades wurden ZWANGSGESCHLOSSEN.")
                else:
                    self.comm.send_report(f"{msg}\n🚫 Handel gestoppt.")
                
                time.sleep(self.error_interval) # 60 Min warten
                return

            # 5. AUSFÜHRUNG BEI ERFOLGREICHER KI-ANTWORT
            try:
                data = json.loads(res.replace("```json", "").replace("```", "").strip())
                ops_log = []
                for act in data.get('actions', []):
                    if act['type'] == 'OPEN':
                        ok, m = self.ops.place_order(act['epic'], act['dir'], act['size'], act.get('sl'), act.get('tp'))
                        ops_log.append(f"OPEN {act['epic']}: {'✅' if ok else '❌'}")
                    elif act['type'] == 'CLOSE':
                        ok, m = self.ops.close_position(act['dealId'])
                        ops_log.append(f"CLOSE {act['dealId']}: {'✅' if ok else '❌'}")
                
                if ops_log: self.comm.send_report(f"📊 ZYKLUS-BERICHT\nEquity: {equity}€\n" + "\n".join(ops_log))
            except Exception as e:
                nexus_logger.log_error("JSON_ERR", f"{e}\nRes: {res}")

        except Exception as e:
            nexus_logger.log_error("CEO_CRASH", traceback.format_exc())

    def run(self):
        print("🚀 NEXUS CEO ONLINE")
        while True:
            self.run_business_cycle()
            time.sleep(self.base_interval)

if __name__ == "__main__":
    NexusCEO().run()
