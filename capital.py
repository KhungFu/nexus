# -*- coding: utf-8 -*-
import requests
import os
import json
from logger import nexus_logger

class CapitalManager:
    def __init__(self):
        self.api_key = os.getenv("CAPITAL_API_KEY")
        self.identifier = os.getenv("CAPITAL_IDENTIFIER")
        self.password = os.getenv("CAPITAL_PASSWORD")
        self.url = "https://api-capital.backend-capital.com/api/v1"
        self.headers = None

    def get_headers(self):
        """Erstellt die Session und holt CST/Security Token."""
        try:
            payload = {"identifier": self.identifier, "password": self.password}
            headers_init = {"X-CAP-API-KEY": self.api_key, "Content-Type": "application/json"}
            r = requests.post(f"{self.url}/session", json=payload, headers=headers_init, timeout=15)
            
            if r.status_code == 200:
                self.headers = {
                    "X-CAP-API-KEY": self.api_key,
                    "CST": r.headers.get("CST"),
                    "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN"),
                    "Content-Type": "application/json"
                }
                return self.headers
            return None
        except Exception as e:
            nexus_logger.log_error("CAPITAL_AUTH", e)
            return None

    def get_state(self):
        """
        Unterscheidet zwischen 'Balance' (Bargeld) und 'Equity' (Gesamtwert).
        Greift exakt auf die Felder aus deiner market_data.json zu.
        """
        if not self.headers: self.get_headers()
        try:
            acc_res = requests.get(f"{self.url}/accounts", headers=self.headers, timeout=15)
            acc_data = acc_res.json()
            
            if 'errorCode' in acc_data:
                self.get_headers()
                acc_res = requests.get(f"{self.url}/accounts", headers=self.headers, timeout=15)
                acc_data = acc_res.json()

            # Datenextraktion aus deinem 'KOCUM' Konto
            main_acc = acc_data['accounts'][0]
            balance_info = main_acc.get('balance', {})

            # 1. Reines Bargeld (Balance)
            cash_balance = float(balance_info.get('balance', 0))
            
            # 2. Gesamtwert des Depots (Equity = Balance + P/L)
            # In der API oft auch als 'available' oder berechnet aus balance + profitLoss
            pl = float(balance_info.get('profitLoss', 0))
            equity = cash_balance + pl
            
            # Wir nutzen für den CEO die Equity, da dies die reale Kaufkraft ist
            current_funds = equity if equity > 0 else cash_balance

            # 3. Offene Positionen holen
            pos_res = requests.get(f"{self.url}/positions", headers=self.headers, timeout=15)
            pos_data = pos_res.json()
            
            return {
                "balance": {"amount": current_funds}, # CEO arbeitet mit diesem Wert
                "cash_only": cash_balance,            # Nur zur Info
                "positions": pos_data.get('positions', [])
            }
        except Exception as e:
            nexus_logger.log_error("CAPITAL_STATE", e)
            return None

    def place_order(self, epic, side, size, sl=None, tp=None):
        if not self.headers: self.get_headers()
        try:
            payload = {"epic": epic, "direction": side, "size": size, "type": "MARKET"}
            if sl: payload["stopDistance"] = sl
            if tp: payload["profitDistance"] = tp
            r = requests.post(f"{self.url}/positions", json=payload, headers=self.headers)
            return (True, r.json().get('dealReference')) if r.status_code == 200 else (False, r.text)
        except Exception as e:
            return False, str(e)

    def close_position(self, deal_id):
        if not self.headers: self.get_headers()
        try:
            r = requests.delete(f"{self.url}/positions/{deal_id}", headers=self.headers)
            return (True, "Closed") if r.status_code == 200 else (False, r.text)
        except Exception as e:
            return False, str(e)
