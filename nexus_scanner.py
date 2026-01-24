# -*- coding: utf-8 -*-
import os, requests, json, time
from dotenv import load_dotenv

load_dotenv()

CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW = os.getenv("CAPITAL_PASSWORD")
URL = "https://api-capital.backend-capital.com/api/v1"

def deep_scan_full_report():
    print("--- 🛰️ NEXUS FULL REPORT: HESAP + TUM PIYASALAR ---")
    session_data = {"identifier": CAP_ID, "password": CAP_PW}
    headers_init = {"X-CAP-API-KEY": CAP_KEY, "Content-Type": "application/json"}
    
    try:
        # 1. Login ve Oturum Bilgileri
        r = requests.post(f"{URL}/session", json=session_data, headers=headers_init, timeout=20)
        if r.status_code != 200:
            print(f"❌ Login Hatasi: {r.status_code}")
            return

        auth_h = {
            "X-CAP-API-KEY": CAP_KEY,
            "CST": r.headers.get("CST"),
            "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN"),
            "Content-Type": "application/json"
        }

        # 2. HESAP VERILERINI CEK (KOCUM Hesabı)
        print("💰 Hesap bilgileri aliniyor...")
        account_res = requests.get(f"{URL}/accounts", headers=auth_h).json()
        positions_res = requests.get(f"{URL}/positions", headers=auth_h).json()

        # 3. TUM PIYASALARI TARA (Hierarchical Scan)
        print("🌍 Küresel piyasa agaci taraniyor (Bu biraz sürebilir)...")
        top_nodes = requests.get(f"{URL}/marketnavigation", headers=auth_h).json()
        
        all_markets = []
        if 'nodes' in top_nodes:
            for node in top_nodes['nodes']:
                print(f"📦 Kategoride derinlesiliyor: {node['name']}")
                # Alt kategorilere gir
                sub_res = requests.get(f"{URL}/marketnavigation/{node['id']}", headers=auth_h).json()
                if 'nodes' in sub_res:
                    for s_node in sub_res['nodes']:
                        # Piyasa detaylarini al
                        m_res = requests.get(f"{URL}/marketnavigation/{s_node['id']}", headers=auth_h).json()
                        if 'markets' in m_res:
                            all_markets.extend(m_res['markets'])
                        time.sleep(0.2) # Ban yememek icin kısa bekleme

        # 4. OZEL EMTHIALAR (Kahve, Kakao, Bakir, Pamuk, Seker)
        print("🌾 Özel emtialar (Coffee, Cocoa, Copper, Cotton) kontrol ediliyor...")
        special_terms = ["COFFEE", "COCOA", "COPPER", "COTTON", "SUGAR", "WHEAT"]
        for term in special_terms:
            s_res = requests.get(f"{URL}/markets?searchTerm={term}", headers=auth_h).json()
            if 'markets' in s_res:
                all_markets.extend(s_res['markets'])

        # 5. Mukerrer Kayitlari Temizle
        unique_markets = {m['epic']: m for m in all_markets}.values()

        # 6. HEPSINI BIRLESTIR VE KAYDET
        final_report = {
            "report_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "my_account": account_res, # Hesap bakiyen ve ID'lerin
            "my_active_positions": positions_res, # Açık işlemlerin
            "market_catalog": {
                "total_count": len(unique_markets),
                "instruments": list(unique_markets)
            }
        }

        with open('market_data.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ ISLEM TAMAMLANDI!")
        print(f"📊 Toplam {len(unique_markets)} varlik ve hesap bilgileriniz 'market_data.json' icine kaydedildi.")

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

if __name__ == "__main__":
    deep_scan_full_report()
