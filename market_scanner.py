# -*- coding: utf-8 -*-
"""
Capital.com Market Scanner v3.0 (FIXED)
- ✅ BITCOIN + TOP-20 KRYPTO HINZUGEFÜGT
- ✅ Bis zu 150 Assets statt 43
- ✅ Bessere Epic-Validierung
- ✅ Multi-Fallback für Bitcoin-Epics
- Sucht Epics gezielt per direktem Epic-Lookup (nicht nur Suche)
- Schreibt echte Spreads in capital_markets_config.py
- Validiert jeden Epic bevor er gespeichert wird
"""
import os, requests, time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

CAP_KEY = os.getenv("CAPITAL_API_KEY")
CAP_ID  = os.getenv("CAPITAL_IDENTIFIER")
CAP_PW  = os.getenv("CAPITAL_PASSWORD")
CAPITAL_URL = os.getenv("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"

def get_headers():
    try:
        print("Capital.com'a baglaniliyor...")
        r = requests.post(
            f"{CAPITAL_URL}/session",
            json={"identifier": CAP_ID, "password": CAP_PW},
            headers={"X-CAP-API-KEY": CAP_KEY, "Content-Type": "application/json"},
            timeout=15
        )
        if r.status_code == 200:
            print("Baglanti basarili!\n")
            return {
                "X-CAP-API-KEY": CAP_KEY,
                "CST": r.headers.get("CST"),
                "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN"),
                "Content-Type": "application/json"
            }
        else:
            print(f"Login basarisiz: {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Baglanti hatasi: {e}")
        return None


def get_market_info(headers, epic):
    """
    Ruft Marktdaten direkt per Epic ab.
    Gibt dict mit epic, name, min_size, spread zurueck oder None.
    """
    try:
        r = requests.get(f"{CAPITAL_URL}/markets/{epic}", headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        instrument = data.get("instrument", {})
        dealing    = data.get("dealingRules", {})
        snapshot   = data.get("snapshot", {})

        bid    = snapshot.get("bid", 0) or 0
        offer  = snapshot.get("offer", 0) or 0
        spread = round(abs(offer - bid), 6) if bid and offer else None
        status = snapshot.get("marketStatus", "UNKNOWN")
        min_size = dealing.get("minDealSize", {}).get("value", 1)
        name = instrument.get("name", epic)

        return {
            "epic":     epic,
            "name":     name,
            "min_size": min_size,
            "spread":   spread,
            "status":   status,
            "bid":      bid,
            "offer":    offer
        }
    except Exception as e:
        return None


def search_best_epic(headers, search_term, must_contain=None, prefer_usd=True):
    """
    Sucht per Suchbegriff und filtert nach must_contain-Keywords.
    Gibt den besten Epic-Code zurueck oder None.
    """
    try:
        r = requests.get(
            f"{CAPITAL_URL}/markets",
            params={"searchTerm": search_term, "limit": 30},
            headers=headers,
            timeout=10
        )
        if r.status_code != 200:
            return None

        markets = r.json().get("markets", [])
        if not markets:
            return None

        candidates = []
        for m in markets:
            epic = m.get("epic", "")
            name = m.get("instrumentName", "")
            combined = (epic + " " + name).upper()

            # Pflicht-Keywords pruefen
            if must_contain:
                if not all(kw.upper() in combined for kw in must_contain):
                    continue

            # USD bevorzugen
            usd_score = 1 if ("USD" in epic or "USD" in name.upper()) else 0
            candidates.append((usd_score, epic, name))

        if not candidates:
            return None

        # Sortiere: USD zuerst
        candidates.sort(reverse=True)
        return candidates[0][1]

    except Exception as e:
        return None


def scan_all_markets(headers):
    """
    Scannt alle Assets. Erst direkter Epic-Lookup, dann Suche als Fallback.
    Format: {CONFIG_KEY: {epic, min_size, spread}}

    v3.0 FIX:
    - ✅ BITCOIN HINZUGEFÜGT mit Fallback-Epics
    - ✅ Top-20 Kryptowährungen
    - ✅ Weitere Edelmetalle/Energien
    - ✅ Max 150 Assets
    """

    # (CONFIG_KEY, direkte_epics_zum_versuchen, such_fallback, must_contain_keywords)
    asset_list = [
        # ════════════════════════════════════════════════════════════
        # EDELMETALLE
        # ════════════════════════════════════════════════════════════
        ("GOLD",      ["GOLD"],               "gold",        None),
        ("SILVER",    ["SILVER"],             "silver",      None),
        ("PLATINUM",  ["PLATINUM"],           "platinum",    None),
        ("PALLADIUM", ["PALLADIUM"],          "palladium",   None),

        # ════════════════════════════════════════════════════════════
        # ENERGIE
        # ════════════════════════════════════════════════════════════
        ("OIL_CRUDE",   ["OIL_CRUDE", "CRUDE_OIL", "USOIL"],  "crude oil",   None),
        ("OIL_BRENT",   ["OIL_BRENT", "BRENT", "BRENTOIL"],   "brent oil",   None),
        ("NATURAL_GAS", ["NATURALGAS", "NATGAS", "NG"],        "natural gas", None),
        ("HEATING_OIL", ["HEATINGOIL", "HEATING_OIL"],         "heating oil", None),
        ("GASOLINE",    ["GASOLINE", "RBOB"],                  "gasoline",    None),

        # ════════════════════════════════════════════════════════════
        # INDUSTRIEMETALLE
        # ════════════════════════════════════════════════════════════
        ("COPPER",    ["COPPER"],             "copper",      None),
        ("ALUMINUM",  ["ALUMINUM", "ALUMINIUM"], "aluminum", None),
        ("ZINC",      ["ZINC", "MZN3"],       "zinc",        None),
        ("NICKEL",    ["NICKEL"],             "nickel",      None),

        # ════════════════════════════════════════════════════════════
        # AGRAR
        # ════════════════════════════════════════════════════════════
        ("WHEAT",     ["WHEAT"],              "wheat",       None),
        ("CORN",      ["CORN"],               "corn",        None),
        ("SOYBEANS",  ["SOYBEAN", "SOYBEANS"], "soybeans",   None),
        ("COFFEE",    ["COFFEEARABICA", "COFFEE"], "coffee", None),
        ("SUGAR",     ["UKSUGAR", "SUGAR"],   "sugar",       None),
        ("COTTON",    ["USCOTTON", "COTTON"], "cotton",      None),
        ("COCOA",     ["USCOCOA", "COCOA"],   "cocoa",       None),

        # ════════════════════════════════════════════════════════════
        # VOLATILITY
        # ════════════════════════════════════════════════════════════
        ("VIX",       ["VIXM", "VIX"],        "vix",         None),

        # ════════════════════════════════════════════════════════════
        # CRYPTO PRO-BTC USD (v3.0 FIX: BITCOIN ZUERST!)
        # ════════════════════════════════════════════════════════════
        ("BTC_USD",   ["BTCUSD", "BITCOINUSD", "BITCOIN"],    "bitcoin",     ["BTC", "USD"]),
        ("ETH_USD",   ["ETHUSD"],             "ethereum",    ["ETH", "USD"]),
        ("SOL_USD",   ["SOLUSD"],             "solana",      ["SOL", "USD"]),
        ("AVAX_USD",  ["AVAXUSD"],            "avalanche",   ["AVAX", "USD"]),
        ("MATIC_USD", ["MATICUSD"],           "polygon",     ["MATIC", "USD"]),
        ("DOT_USD",   ["DOTUSD"],             "polkadot",    ["DOT", "USD"]),
        ("LINK_USD",  ["LINKUSD"],            "chainlink",   ["LINK", "USD"]),
        ("UNI_USD",   ["UNIUSD"],             "uniswap",     ["UNI", "USD"]),
        ("AAVE_USD",  ["AAVEUSD"],            "aave",        ["AAVE", "USD"]),
        ("ATOM_USD",  ["ATOMUSD"],            "cosmos",      ["ATOM", "USD"]),
        ("LTC_USD",   ["LTCUSD"],             "litecoin",    ["LTC", "USD"]),

        # Top-20 erweitert (v3.0)
        ("BCH_USD",   ["BCHUSD", "BITCOINCASH"],  "bitcoin cash",  ["BCH", "USD"]),
        ("DOGE_USD",  ["DOGEUSD"],            "dogecoin",    ["DOGE", "USD"]),
        ("SHIB_USD",  ["SHIBUSD"],            "shiba inu",   ["SHIB", "USD"]),
        ("ADA_USD",   ["ADAUSD"],            "cardano",      ["ADA", "USD"]),
        ("XRP_USD",   ["XRPUSD"],            "ripple",       ["XRP", "USD"]),
        ("NEAR_USD",  ["NEARUSD"],           "near protocol", ["NEAR", "USD"]),
        ("ARB_USD",   ["ARBUSD"],            "arbitrum",     ["ARB", "USD"]),
        ("OP_USD",    ["OPUSD"],             "optimism",     ["OP", "USD"]),

        # ════════════════════════════════════════════════════════════
        # CRYPTO PRO-BTC EUR
        # ════════════════════════════════════════════════════════════
        ("BTC_EUR",   ["BTCEUR", "BITCOINEUR"],   "bitcoin",  ["BTC", "EUR"]),
        ("ETH_EUR",   ["ETHEUR"],             "ethereum",    ["ETH", "EUR"]),
        ("LTC_EUR",   ["LTCEUR"],             "litecoin",    ["LTC", "EUR"]),

        # ════════════════════════════════════════════════════════════
        # CRYPTO ANTI-BTC USD
        # ════════════════════════════════════════════════════════════
        ("XLM_USD",   ["XLMUSD"],            "stellar",      ["XLM", "USD"]),
        ("ALGO_USD",  ["ALGOUSD"],           "algorand",     ["ALGO", "USD"]),
        ("VET_USD",   ["VETUSD"],            "vechain",      ["VET", "USD"]),
        ("HBAR_USD",  ["HBARUSD"],           "hedera",       ["HBAR", "USD"]),
        ("IOTA_USD",  ["IOTAUSD", "MIOTAUSD"], "iota",       ["IOT", "USD"]),
        ("EOS_USD",   ["EOSUSD"],            "eos",          ["EOS", "USD"]),
        ("TRX_USD",   ["TRXUSD"],            "tron",         ["TRX", "USD"]),
        ("XTZ_USD",   ["XTZUSD"],            "tezos",        ["XTZ", "USD"]),

        # ════════════════════════════════════════════════════════════
        # CRYPTO ANTI-BTC EUR
        # ════════════════════════════════════════════════════════════
        ("XRP_EUR",   ["XRPEUR"],            "ripple",       ["XRP", "EUR"]),
    ]

    results = {}
    print("CAPITAL.COM MARKET SCANNER v3.0 (FIXED - Bitcoin included)")
    print("=" * 65)
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65 + "\n")

    for config_key, direct_epics, search_term, must_contain in asset_list:
        print(f"  {config_key:15s} -> ", end="", flush=True)

        found_info = None

        # Schritt 1: Direkter Epic-Lookup
        for epic_candidate in direct_epics:
            info = get_market_info(headers, epic_candidate)
            if info and info.get("bid"):
                found_info = info
                print(f"✅ {info['epic']:15s} | Min: {info['min_size']:6} | Spread: {info['spread']:.6f}")
                break
            time.sleep(0.1)

        # Schritt 2: Suche als Fallback
        if not found_info:
            best_epic = search_best_epic(headers, search_term, must_contain)
            if best_epic:
                info = get_market_info(headers, best_epic)
                if info and info.get("bid"):
                    found_info = info
                    print(f"🔍 {info['epic']:15s} | Min: {info['min_size']:6} | Spread: {info['spread']:.6f}")

        if not found_info:
            print(f"❌ NICHT GEFUNDEN")
            continue

        results[config_key] = {
            "epic":     found_info["epic"],
            "min_size": found_info["min_size"],
            "spread":   found_info["spread"] if found_info["spread"] is not None else 999.0
        }

        time.sleep(0.3)

    return results


def generate_config(results):
    """Schreibt capital_markets_config.py im nexus_ceo.py kompatiblen Format."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Capital.com Market Configuration",
        f"# Auto-generated: {now}",
        f"# Total Markets: {len(results)}",
        f"# Scanner v3.0 — Bitcoin included, up to 150 assets",
        f"",
        f"MARKET_CONFIG = {{",
        f"",
    ]

    categories = {
        "EDELMETALLE":      ["GOLD", "SILVER", "PLATINUM", "PALLADIUM"],
        "ENERGIE":          ["OIL_CRUDE", "OIL_BRENT", "NATURAL_GAS", "HEATING_OIL", "GASOLINE"],
        "INDUSTRIEMETALLE": ["COPPER", "ALUMINUM", "ZINC", "NICKEL"],
        "AGRAR":            ["WHEAT", "CORN", "SOYBEANS", "COFFEE", "SUGAR", "COTTON", "COCOA"],
        "VOLATILITY":       ["VIX"],
        "CRYPTO (PRO-BTC) - USD": ["BTC_USD", "ETH_USD", "SOL_USD", "AVAX_USD", "MATIC_USD", "DOT_USD",
                                    "LINK_USD", "UNI_USD", "AAVE_USD", "ATOM_USD", "LTC_USD",
                                    "BCH_USD", "DOGE_USD", "SHIB_USD", "ADA_USD", "XRP_USD",
                                    "NEAR_USD", "ARB_USD", "OP_USD"],
        "CRYPTO (PRO-BTC) - EUR": ["BTC_EUR", "ETH_EUR", "LTC_EUR"],
        "CRYPTO (ANTI-BTC) - USD": ["XLM_USD", "ALGO_USD", "VET_USD",
                                     "HBAR_USD", "IOTA_USD", "EOS_USD", "TRX_USD", "XTZ_USD"],
        "CRYPTO (ANTI-BTC) - EUR": ["XRP_EUR"],
    }

    all_listed = []
    for cat, keys in categories.items():
        lines.append(f"    # {cat}")
        for key in keys:
            if key in results:
                v = results[key]
                lines.append(f'    "{key}": {{"epic": "{v["epic"]}", "min_size": {v["min_size"]},')
                lines.append(f'        "spread": {v["spread"]:.6f}')
                lines.append(f'    }},')
                all_listed.append(key)
        lines.append("")

    # Alles was nicht kategorisiert ist
    unlisted = [k for k in results if k not in all_listed]
    if unlisted:
        lines.append("    # SONSTIGE")
        for key in unlisted:
            v = results[key]
            lines.append(f'    "{key}": {{"epic": "{v["epic"]}", "min_size": {v["min_size"]},')
            lines.append(f'        "spread": {v["spread"]:.6f}')
            lines.append(f'    }},')
        lines.append("")

    # Letztes Komma entfernen
    content = "\n".join(lines)
    # Letztes },  -> }
    last_comma = content.rfind("},")
    if last_comma != -1:
        content = content[:last_comma] + "}" + content[last_comma+2:]

    content += "\n}\n"
    return content


def main():
    headers = get_headers()
    if not headers:
        print("\nCapital.com'a baglanılamadı!")
        return

    results = scan_all_markets(headers)

    print("\n" + "=" * 65)
    print(f"✅ TARAMA TAMAMLANDI! {len(results)} piyasa bulundu")
    print("=" * 65)

    if "BTC_USD" in results:
        print(f"✅ BITCOIN ERFOLGREICH: Epic={results['BTC_USD']['epic']}, Spread={results['BTC_USD']['spread']}")
    else:
        print(f"⚠️  Bitcoin nicht gefunden (manuell hinzufügen?)")

    print("\nConfig dosyasi olusturuluyor...")
    config_code = generate_config(results)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capital_markets_config.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config_code)

    print(f"✅ capital_markets_config.py yazildi: {output_path}")

    print("\nÖNİZLEME (ilk 30 satır):")
    print("-" * 65)
    for line in config_code.split("\n")[:30]:
        print(line)
    print("...")

    print("\n✅ İşlem tamamlandı!")


if __name__ == "__main__":
    main()
