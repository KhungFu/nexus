# -*- coding: utf-8 -*-
import time
import json
import glob
import os
import datetime
import traceback

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
        self.budget_limit = 100.0
        
        # Listen für Filterung
        self.survival_keywords = ["GOLD", "SILVER", "OIL", "BRENT", "COPPER", "GAS", "COTTON", "SUGAR", "COFFEE", "WHEAT"]
        self.crypto_keywords = ["BITCOIN", "ETHEREUM", "RIPPLE", "LITECOIN", "DOGE", "BTC", "ETH", "XRP", "LTC", "SOL"]

    def load_doctrine_and_intel(self):
        doctrine_text = "Standard Doktrin."
        info_text = ""
        if os.path.exists("mentor_name.txt"):
            with open("mentor_name.txt", "r", encoding="utf-8", errors="ignore") as f: doctrine_text = f.read()
        
        files = glob.glob("*.txt")
        for file in files:
            if file == "mentor_name.txt": continue
            with open(file, "r", encoding="utf-8", errors="ignore") as f: info_text += f"\nSOURCE {file}: {f.read()[:5000]}\n"
        return doctrine_text, info_text

    def filter_market_data(self, mode):
        """
        Erstellt eine 'Speisekarte' für Gemini, um Token zu sparen und Fehler zu vermeiden.
        Gibt nur Epics zurück, die zum aktuellen Modus passen.
        """
        if not os.path.exists('market_data.json'): return "Keine Marktdaten."
        
        with open('market_data.json', 'r', encoding='utf-8') as f:
            full_data = json.load(f)
            
        instruments = full_data.get('market_catalog', {}).get('instruments', [])
        valid_list = []
        
        for inst in instruments:
            name = inst.get('instrumentName', '').upper()
            epic = inst.get('epic', '')
            
            # FILTER LOGIK
            if mode == "SURVIVAL":
                # Nur Rohstoffe erlauben
                if any(x in name for x in self.survival_keywords) or any(x in epic for x in self.survival_keywords):
                    valid_list.append(f"{name} (EPIC: {epic})")
                    
            elif mode == "CRYPTO_ONLY":
                # Nur Crypto erlauben
                if any(x in name for x in self.crypto_keywords) or "USD" in epic and ("BTC" in epic or "ETH" in epic):
                    valid_list.append(f"{name} (EPIC: {epic})")
            
            else: # NORMAL MODE
                # Alles erlauben, aber Liste begrenzen um Token zu sparen (z.B. Top 100)
                valid_list.append(f"{name} (EPIC: {epic})")

        # Begrenzung auf max 4000 Zeichen String-Länge für die Liste, damit Prompt nicht platzt
        return "\n".join(valid_list)[:8000]

    def run_business_cycle(self):
        try:
            print(f"\n⏰ --- ZYKLUS START: {datetime.datetime.now().strftime('%H:%M')} ---")
            
            # 1. STATUS & ZEIT
            state = self.ops.get_state()
            if not state: raise Exception("Operations (Capital) nicht erreichbar.")
            
            balance = float(state['balance'].get('amount', 0))
            positions = state['positions']
            
            weekday = datetime.datetime.today().weekday()
            is_weekend = weekday >= 5
            
            # 2. MODUS BESTIMMEN
            mode = "NORMAL"
            
            if is_weekend:
                if balance > self.budget_limit:
                    mode = "CRYPTO_ONLY"
                    print(f"🎰 WOCHENENDE + GUTHABEN ({balance}€): Crypto-Modus aktiviert.")
                else:
                    print(f"🛌 WOCHENENDE + WENIG GUTHABEN ({balance}€): Ruhemodus. Kein Handel.")
                    return # Zyklus beenden, schlafen gehen
            
            elif balance < self.budget_limit:
                mode = "SURVIVAL"
                print(f"⚠️ SURVIVAL MODE ({balance}€ < {self.budget_limit}€): Nur Rohstoffe.")
            
            else:
                print(f"🚀 NORMALER MARKT ({balance}€): Voller Zugriff.")

            # 3. SCANNER (Nur wenn nötig)
            # Um API Limits beim Scannen zu schonen: Scan nur alle paar Zyklen oder wenn Datei alt ist?
            # Hier: Immer scannen für Aktualität, aber Scanner hat sleep integriert.
            deep_scan_full_report()
            
            # 4. DATEN FILTERN
            market_menu = self.filter_market_data(mode)
            if not market_menu:
                print("❌ Keine passenden Märkte für diesen Modus gefunden.")
                return

            # 5. STRATEGIE PROMPT
            doctrine, intel = self.load_doctrine_and_intel()
            
            prompt = f"""
            ROLLE: Head of Strategy, Nexus Corp.
            MODUS: {mode} (Halte dich STRIKT daran!)
            KONTO: {balance} EUR
            
            --- DOKTRIN ---
            {doctrine[:2000]}
            
            --- ZUSATZ WISSEN ---
            {intel[:2000]}

            --- DEIN MARKT-MENÜ (NUR DIESE EPICS SIND GÜLTIG) ---
            {market_menu}
            
            --- OFFENE POSITIONEN ---
            {json.dumps(positions, default=str)}
            
            AUFGABE:
            1. Prüfe offene Positionen: Schließen (CLOSE) oder Laufen lassen?
            2. Suche NEUE Einstiege basierend auf dem Menü. (OPEN)
            
            FORMAT (JSON ONLY):
            {{
                "summary": "Grund...",
                "actions": [
                    {{ "type": "OPEN", "epic": "GENAUER_EPIC_AUS_MENU", "dir": "BUY/SELL", "size": 0.1, "sl": 10, "tp": 20 }},
                    {{ "type": "CLOSE", "dealId": "DEAL_ID_VON_POSITION" }}
                ]
            }}
            """
            
            # 6. ENTSCHEIDUNG
            print("🧠 Strategie wird berechnet...")
            res = self.strategy.get_analysis(prompt)
            
            if "API KEY EKSIK" in res: return

            # 7. EXECUTION
            try:
                clean = res.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean)
                
                ops_log = []
                print(f"Analyse: {data.get('summary')}")
                
                for act in data.get('actions', []):
                    if act['type'] == 'OPEN':
                        ok, msg = self.ops.place_order(act['epic'], act['dir'], act['size'], act.get('sl'), act.get('tp'))
                        ops_log.append(f"OPEN {act['epic']}: {'✅' if ok else '❌ ' + str(msg)}")
                    
                    elif act['type'] == 'CLOSE':
                        ok, msg = self.ops.close_position(act['dealId'])
                        ops_log.append(f"CLOSE {act['dealId']}: {'✅' if ok else '❌ ' + str(msg)}")
                
                # Bericht senden wenn was passiert ist
                if ops_log:
                    self.comm.send_report(f"📊 **NEXUS REPORT**\nModus: {mode}\n\n" + "\n".join(ops_log))
                    
            except Exception as e:
                print(f"JSON Fehler: {e}")
                nexus_logger.log_error("STRATEGY_PARSE", res)

        except Exception as e:
            err = traceback.format_exc()
            print(f"CRASH: {e}")
            nexus_logger.log_error("CEO_CRASH", err)
            self.comm.send_report(f"🚨 CEO CRASH: {e}")

    def run(self):
        print("🚀 NEXUS CEO ONLINE")
        self.comm.send_report("🏛 CEO ist online.")
        while True:
            self.run_business_cycle()
            time.sleep(self.base_interval)

if __name__ == "__main__":
    NexusCEO().run()