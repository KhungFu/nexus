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
        
        # Abteilungsleiter initialisieren
        self.ops = CapitalManager()      # COO (Ausführung)
        self.strategy = GeminiAnalyst()  # CSO (Strategie/KI)
        self.comm = TelegramBot()        # PR (Kommunikation)
        
        # Konfiguration
        self.base_interval = 1800  # 30 Minuten Standard
        self.error_interval = 3600 # 60 Minuten bei API Limit
        self.survival_limit = 100.0 # Euro Grenze
        
        # DEFINITION DER SICHEREN HÄFEN (SURVIVAL ASSETS)
        # Hier wurden GOLD, SILVER, OIL und COPPER hinzugefügt
        self.survival_assets = [
            "GOLD", "SILVER", "OIL", "USOIL", "BRENT",  # Edelmetalle & Energie
            "COPPER", "NATURAL GAS",                    # Industriemetalle & Gas
            "COTTON", "SUGAR", "COFFEE", "WHEAT"        # Agrar-Rohstoffe
        ]

    def load_doctrine_and_intel(self):
        """Lädt die Doktrin (Gesetz) und Informationsquellen."""
        doctrine_text = ""
        info_text = ""
        
        # 1. Die Haupt-Doktrin
        if os.path.exists("mentor_name.txt"):
            with open("mentor_name.txt", "r", encoding="utf-8", errors="ignore") as f:
                doctrine_text = f.read()
        else:
            doctrine_text = "WARNUNG: Keine Doktrin gefunden. Handle konservativ."

        # 2. Andere .txt Informationsquellen & Links
        files = glob.glob("*.txt")
        for file in files:
            if file == "mentor_name.txt": continue # Wurde schon geladen
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                info_text += f"\n--- QUELLE: {file} ---\n{content}\n"
                
        return doctrine_text, info_text

    def check_trading_hours(self):
        """Prüft, ob Wochenende ist."""
        # 0=Montag, 6=Sonntag
        weekday = datetime.datetime.today().weekday()
        is_weekend = weekday >= 5
        return is_weekend

    def run_business_cycle(self):
        """Der Hauptgeschäftszyklus."""
        try:
            print(f"\n⏰ --- NEUER GESCHÄFTSZYKLUS: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
            
            # 1. STATUS BERICHT
            state = self.ops.get_state()
            if not state:
                raise Exception("Kritischer Fehler: Keine Verbindung zu Capital.com (Operations down).")
            
            balance = float(state['balance'].get('amount', 0))
            open_positions = state.get('positions', [])
            
            print(f"💰 Kassenstand: {balance:.2f} EUR | Offene Positionen: {len(open_positions)}")

            # 2. SURVIVAL MODE CHECK (< 100 EUR)
            is_survival = balance < self.survival_limit
            target_sector_instruction = ""
            
            if is_survival:
                print("⚠️ SURVIVAL MODE AKTIV: Budget < 100€. Nur Rohstoffe/Edelmetalle erlaubt.")
                assets_str = ", ".join(self.survival_assets)
                target_sector_instruction = (
                    f"ACHTUNG: KONTOSTAND KRITISCH ({balance} EUR). "
                    f"ERLAUBT SIND AUSSCHLIESSLICH ROHSTOFFE: {assets_str}. "
                    "KEINE AKTIEN, KEIN CRYPTO, KEIN FOREX."
                )
            else:
                target_sector_instruction = "KONTOSTAND STABIL. Freie Marktwahl (Aktien, Forex, Rohstoffe, Crypto)."

            # 3. MARKTFORSCHUNG BEAUFTRAGEN
            is_weekend = self.check_trading_hours()
            if is_weekend:
                print("🌴 Wochenende. Märkte eingeschränkt (nur Crypto/Otc).")
            
            print("🕵️ Beauftrage Deep Scan...")
            deep_scan_full_report() 
            
            market_data = {}
            if os.path.exists('market_data.json'):
                with open('market_data.json', 'r', encoding='utf-8') as f:
                    market_data = json.load(f)

            # 4. STRATEGIE BRIEFING
            doctrine, intel = self.load_doctrine_and_intel()
            
            prompt = f"""
            DU BIST: Der Head of Strategy der Nexus Capital Corp.
            
            --- DEINE DOKTRIN (Gesetz) ---
            {doctrine}
            
            --- ZUSÄTZLICHE INTELLIGENZ ---
            {intel}
            
            --- AKTUELLE LAGE ---
            KONTOSTAND: {balance} EUR
            MODUS: {target_sector_instruction}
            OFFENE POSITIONEN (Prüfe ob Schließung/Änderung nötig): {json.dumps(open_positions, default=str)}
            MARKT DATEN (Auszug): {str(market_data.get('market_catalog', {}).get('instruments', []))[:12000]} 
            
            --- AUFGABE ---
            1. Analysiere offene Positionen: Halten, Schließen oder Trailing SL anpassen?
            2. Suche neue Chancen. Du kannst LONG (Buy) oder SHORT (Sell) gehen.
            3. Beachte strikt den MODUS (Survival Mode erlaubt nur bestimmte Assets).
            
            --- FORMAT BEFEHL (WICHTIG) ---
            Antworte AUSSCHLIESSLICH in validem JSON Format.
            {{
                "analysis_summary": "Kurze Begründung...",
                "actions": [
                    {{
                        "action": "OPEN", 
                        "epic": "EPIC_CODE", 
                        "direction": "BUY" oder "SELL", 
                        "size": 0.1, 
                        "stop_loss_distance": 10, 
                        "take_profit_distance": 20
                    }},
                    {{
                        "action": "CLOSE",
                        "dealId": "DEAL_ID"
                    }}
                ]
            }}
            """

            # 5. ENTSCHEIDUNG EINHOLEN
            print("🧠 Konsultiere Strategieabteilung (Gemini)...")
            decision_text = self.strategy.get_analysis(prompt)
            
            if "API KEY EKSIK" in decision_text or "Analiz" in decision_text and "fehler" in decision_text.lower():
                 print("⚠️ API Fehler bei Strategie.")
                 return

            # 6. AUSFÜHRUNG
            try:
                clean_json = decision_text.replace("```json", "").replace("```", "").strip()
                decision_data = json.loads(clean_json)
                
                actions = decision_data.get("actions", [])
                summary = decision_data.get("analysis_summary", "Keine Analyse.")
                
                execution_report = []
                
                print(f"📝 Strategie-Analyse: {summary}")
                
                for act in actions:
                    if act['action'] == "OPEN":
                        success, msg = self.ops.place_order(
                            epic=act['epic'],
                            side=act['direction'],
                            size=act['size'],
                            sl=act['stop_loss_distance'],
                            tp=act['take_profit_distance']
                        )
                        status = "✅ EROFFNET" if success else f"❌ FEHLER: {msg}"
                        execution_report.append(f"{act['direction']} {act['epic']} -> {status}")
                        
                    elif act['action'] == "CLOSE":
                        execution_report.append(f"CLOSE ORDER für {act.get('dealId')} notiert (Funktion folgt in Capital.py).")

                # 7. BERICHTERSTATTUNG
                if execution_report:
                    full_report = f"🏢 **NEXUS CEO REPORT**\n\n📊 **Analyse:** {summary}\n\n🛠 **Operations:**\n" + "\n".join(execution_report)
                    full_report += f"\n\n💵 Saldo: {balance:.2f} EUR"
                    self.comm.send_report(full_report)
                    print("📨 Bericht gesendet.")
                else:
                    print("💤 Keine Handelsaktivität notwendig.")

            except json.JSONDecodeError:
                print("❌ Fehler: Strategieabteilung hat kein valides JSON geliefert.")
                nexus_logger.log_error("STRATEGY_JSON", decision_text)

        except Exception as e:
            error_msg = str(e)
            print(f"🔥 KRITISCHER FEHLER: {error_msg}")
            nexus_logger.log_error("CEO_CRASH", error_msg)
            try:
                self.comm.send_report(f"🚨 **ALARM: SYSTEM CRASH** 🚨\n\nFehler: `{error_msg}`\nBitte `error_log.json` prüfen.")
            except:
                pass

    def run(self):
        """Die Endlosschleife."""
        print("🚀 Nexus Capital Corp operativ.")
        self.comm.send_report("🏛 **NEXUS CEO:** System gestartet. Übernehme Kontrolle.")
        
        while True:
            start_time = time.time()
            self.run_business_cycle()
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.base_interval - elapsed)
            
            print(f"⏳ CEO geht in Pause für {sleep_time/60:.1f} Minuten...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    ceo = NexusCEO()
    ceo.run()
