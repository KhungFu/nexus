#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXUS - Diagnose fuer v15.16 bis v15.24   (NUR LESEND)

Das Skript aendert nichts: Es liest nexus_ceo.py, die .env, die Logdateien und holt
von Capital.com nur Daten ab (GET). Es eroeffnet, aendert und schliesst keine Position.
Schluessel, Passwoerter und Token gibt es nie aus.

Was es beantwortet:
  0) Welcher Stand laeuft, mit welchen Einstellungen?
  1) Was hat der Bot laut Log getan (Scans, Orders, Sperren, Stops, Stufen, KI, Fehler)?
  2) Was steht bei Capital.com: offene Positionen, Buchungen, Ergebnis JE POSITION
     (Capital.com zaehlt jeden Teilverkauf als eigenen Trade - das schoent die Gewinnquote),
     Wiedereinstiege nach einer Schliessung.
  3) Sind die Listen aus GitHub erreichbar?

Aufruf (im Bot-Ordner):
    python3 nexus_diagnose.py              # letzte 7 Tage
    python3 nexus_diagnose.py --days 3
    python3 nexus_diagnose.py --no-api     # ohne Capital.com und GitHub
    python3 nexus_diagnose.py --dir /pfad/zum/bot
    python3 nexus_diagnose.py --lang en    # Kurzfassung am Ende auf de, en oder tr

Ab NEXUS v15.20 ruft der Bot dieses Skript auf, wenn du in Telegram /diagnose sendest:
die Kurzfassung kommt als Nachricht, der ganze Bericht als Datei.
"""
import argparse
import glob
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "8 (fuer NEXUS v16.0)"

K = {}          # Kennzahlen fuer die Kurzfassung am Ende (auch fuer /diagnose in Telegram)
KURZ_MARKE = "KURZFASSUNG"

# .env-Eintraege, die gezeigt werden duerfen (keine Zugangsdaten)
ZEIGEN = [
    "BOT_LANGUAGE", "SCAN_INTERVAL_SEC", "TRADING_ASSETS", "POSITION_SIZE_PCT", "MIN_POSITION_EUR",
    "MAX_POSITION_EUR", "MAX_POSITIONEN", "MAX_SPREAD", "GREMIUM_MODUS", "GREMIUM_MEHRHEIT", "GREMIUM_MEHRHEIT_KRYPTO",
    "GREMIUM_MIN_ANTWORTEN", "GREMIUM_MAX_KANDIDATEN", "GREMIUM_GUELTIG_STD", "GREMIUM_PARALLEL", "GREMIUM_BEWERTUNG_STD",
    "GREMIUM_GEWICHTUNG", "GREMIUM_MIN_JA", "GREMIUM_MIN_JA_KRYPTO",
    "KRYPTO_NACHT_SPERRE", "AUTO_EXIT", "SL_ATR_MULT", "SL_MAX_PCT", "STOP_LEITER", "MAX_JE_GRUPPE", "ATR_DAILY_PERIOD", "ATR_DAILY_ORAN",
    "MIRROR_TP_ENABLED", "MIRROR_TP_LEVEL_1_MULT", "MIRROR_TP_LEVEL_2_MULT", "MIRROR_TP_LEVEL_3_MULT",
    "MIRROR_TP_CLOSE_PCT", "MAX_VERLUSTE_PRO_TAG", "WIEDEREINSTIEG_SPERRE_STD", "SCAN_MELDUNGEN",
    "PROVIDER_ORDER", "OLLAMA_PRIORITY", "OLLAMA_MODEL", "GEMINI_MODEL_1", "GEMINI_CHAIN_MAX",
    "GEMINI_503_PAUSE", "GEMINI_USE_INTERACTIONS_API", "MODEL_AUTOUPDATE", "MODEL_AUTOUPDATE_HOURS",
    "MODEL_AUTOUPDATE_PIN", "AI_CHAIN_MAX", "GROQ_MODEL", "QWEN_MODEL", "NVIDIA_MODEL", "CAPITAL_URL",
]
SCHLUESSEL_LISTEN = ["GEMINI_KEYS", "GROQ_KEYS", "QWEN_KEYS", "NVIDIA_KEYS"]
PFLICHT = ["TG_TOKEN", "MY_CHAT_ID", "CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD"]

# (Name, Suchtext oder Regex)  - gezaehlt wird je Logzeile hoechstens einmal je Name
EREIGNISSE = [
    ("Bot gestartet", "Log gestartet"),
    ("Order eroeffnet und bestaetigt", re.compile(r"Post-Order Verify \S+: OK")),
    ("Order gesendet, Position NICHT gefunden", re.compile(r"Post-Order Verify \S+: NICHT")),
    ("Order abgelehnt", "Trade Fehler"),
    ("Gegensignal (EXIT)", re.compile(r"EXIT: \S+ (BUY|SELL)->(BUY|SELL)")),
    ("Stop auf Mindestabstand geschoben", re.compile(r"SL (düzeltildi|güncellendi)")),
    ("Breakeven gesetzt", "Breakeven-SL:"),
    ("Mirror-TP Stufe 1", "MIRROR-TP L1"),
    ("Mirror-TP Stufe 2", "MIRROR-TP L2"),
    ("Mirror-TP Stufe 3", "MIRROR-TP L3"),
    ("Trailing-Stop wirklich nachgezogen", re.compile(r"Trailing SL: .* Sv:\d+ Peak:.*->")),
    ("Trailing-Stop fehlgeschlagen", "Trailing SL basarisiz"),
    ("Teilausstieg bei mehreren Positionen", "Partial Exit:"),
    ("Stop-Leiter nachgezogen", re.compile(r"Stop-Leiter: .* Stufe \d SL ")),
    ("Stop-Leiter abgelehnt", re.compile(r"Stop-Leiter .* abgelehnt: ")),
    ("Schwarzer Schwan", "KARA KUGU"),
    ("Sperre: Wiedereinstieg", "Wiedereinstieg gesperrt"),
    ("Sperre: maximale Positionen", "MAX POSITIONEN"),
    ("Sperre: Gruppen-Limit", "Gruppen-Limit "),
    ("Sperre: Verluste des Tages", "HARD BLOK"),
    ("Sperre: Spread", "SPREAD BLOK"),
    ("Sperre: Markt geschlossen", re.compile(r"\bKAPALI \S+")),
    ("Sperre: Ersatz-KI ohne Freigabe", "FALLBACK-BLOCK"),
    ("Sperre: Stop/Ziel unplausibel", "unplausibel"),
    ("Sperre: Margin", "Margin ENGEL"),
    ("Sperre: Tages-Verlust-Stopp", "DEPOT DD"),
    ("KI: Gemini hat geantwortet", "[OK] Başarılı"),
    ("KI: Ersatz Groq", "[OK] Groq"),
    ("KI: Ersatz Qwen", "[OK] Qwen"),
    ("KI: Ersatz Nvidia", "[OK] Nvidia"),
    ("KI: Ersatz Ollama (lokal)", "[OK] Ollama"),
    ("KI: Ersatzmodell der Kette sprang ein", re.compile(r"Hauptmodell \S+ ausgefallen -> ")),
    ("KI: Modell automatisch ersetzt", "Modell ersetzt: "),
    ("KI: kein Ersatzmodell bestand die Pruefung", "kein Ersatz hat die Prüfung bestanden"),
    ("Ersatzbetrieb im Scan", "fallback analiz"),
    ("KI: Gemini-Kette ohne Antwort", "kombinasyonları quota dolu"),
    ("KI: alle Ersatz-Anbieter ausgefallen", "Tüm AI provider başarısız"),
    ("Warnung im Stop-Lauf (Trailing SL epic)", "Trailing SL epic"),
    ("Gremium beraten", re.compile(r"GREMIUM \S+: (BUY|SELL|-) \| (UYGULA|BEKLE)")),
    ("Gremium: Beschluss ausgefuehrt", re.compile(r"GREMIUM \S+: (BUY|SELL) \| UYGULA")),
    ("Gremium: Vorsitz gestoppt", "BEKLE vorsitz_stop"),
    ("Gremium: Vorsitz ohne Antwort", "BEKLE vorsitz_fehlt"),
    ("Gremium: nicht beschlussfaehig", "BEKLE beschlussunfaehig"),
    ("Gremium: gespalten (Senaryo 4)", "BEKLE konflikt"),
    ("Gremium: keine Mehrheit", "BEKLE keine_mehrheit"),
    ("Gremium: kein Kandidat im Scan", "GREMIUM: kein Kandidat"),
    ("Sprache gesetzt", "Sprache gesetzt"),
]

_MASKEN = [
    (re.compile(r"bot\d{6,}:[A-Za-z0-9_\-]{20,}"), "bot<token>"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{30,}\b"), "<telegram-token>"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), "<google-key>"),
    (re.compile(r"gsk_[0-9A-Za-z]{16,}"), "<groq-key>"),
    (re.compile(r"sk-[0-9A-Za-z\-_]{16,}"), "<key>"),
    (re.compile(r"nvapi-[0-9A-Za-z_\-]{16,}"), "<nvidia-key>"),
    (re.compile(r"(key=\.\.\.)\S+"), r"\1<…>"),
    (re.compile(r"(?i)((?:api[_-]?key|token|password|passwort|secret|bearer)\s*[=:]\s*)\S+"), r"\1<…>"),
    (re.compile(r"[\w.\-]+@[\w\-]+\.[a-z]{2,}"), "<e-mail>"),
]


def mask(text):
    """Alles entfernen, was wie ein Schluessel, Token, Passwort oder eine E-Mail aussieht."""
    for rx, ers in _MASKEN:
        text = rx.sub(ers, text)
    return text


def titel(text):
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


def read_env(path):
    """.env lesen. Rueckgabe: (werte, doppelte_namen)."""
    env, zahl = {}, Counter()
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if v[:1] in ("'", '"') and v[-1:] == v[:1]:
                v = v[1:-1]
            elif " #" in v or v.startswith("#"):
                v = v.split("#", 1)[0].strip()
            env[k] = v
            zahl[k] += 1
    except Exception as e:
        print("  .env nicht lesbar: %s" % e)
    return env, sorted(k for k, n in zahl.items() if n > 1)


def lokal(ts_utc):
    """UTC-Zeit (naiv) -> Ortszeit des Rechners (naiv)."""
    return ts_utc.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)


def zeit(text):
    """'2026-10-05T08:26:15.274' -> datetime (naiv) oder None."""
    try:
        return datetime.strptime(str(text)[:19], "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError):
        return None


def zahl(x, standard=0.0):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return standard


def konto_art(url):
    if not url or "demo-api-capital" in url:
        return "Demo"
    if "api-capital.backend-capital.com" in url:
        return "LIVE - echtes Geld"
    return "unbekannte Adresse"


WOCHENTAG = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def dauer(sek):
    sek = int(max(0, sek))
    return "%d h %02d min" % (sek // 3600, sek % 3600 // 60)


# ---------------------------------------------------------------------------------------
# TEIL 0: Stand und Einstellungen
# ---------------------------------------------------------------------------------------
def teil0(bot_dir, env, doppelt):
    titel("TEIL 0: Stand und Einstellungen")
    code = bot_dir / "nexus_ceo.py"
    stand = "nexus_ceo.py fehlt"
    if code.is_file():
        src = code.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^NEXUS_VERSION\s*=\s*"([^"]+)"', src, re.M)
        if m:
            stand = m.group(1)
        elif "def sl_min_distance(" in src:
            stand = "v15.17 oder neuer (ohne Versionszeile)"
        elif "def build_fallback_prompt(" in src:
            stand = "v15.10 bis v15.15"
        else:
            stand = "aelter als v15.10"
        merkmale = [("Gremium 11 Mentoren (v16.0)", "def gremium_zyklus("), ("Stop-Leiter/Gruppen-Limit (v15.24)", "def gruppen_belegt("), ("Modell-Schleife Ersatz-KI (v15.22)", "def ai_chain_call("), ("Sprachen (v15.19)", "def set_language("), ("Wiedereinstiegs-Sperre (v15.18)", "def letzte_schliessung("),
                    ("Stop aus der Tagesspanne (v15.17)", "def sl_min_distance("), ("Schliess-Melder (v15.16)", "def closed_position_watch(")]
        K["stand"] = stand
        print("  Code-Stand: %s   (%d Zeilen, geaendert %s)" % (
            stand, src.count("\n") + 1, datetime.fromtimestamp(code.stat().st_mtime).strftime("%d.%m. %H:%M")))
        print("  Enthalten: " + " | ".join("%s: %s" % (n, "ja" if t in src else "NEIN") for n, t in merkmale))
    else:
        print("  " + stand)

    lang = bot_dir / "nexus_lang.py"
    if lang.is_file():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("nexus_lang_diag", str(lang))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            probe = mod.translate("Kayit hatasi: Test", "de")
            print("  nexus_lang.py: %d Regeln, %d Befehle, Sprachen %s | kurze Bausteine: %s" % (
                len(mod.RULES), len(mod.COMMANDS), "/".join(mod.LANGS),
                "ok" if probe.startswith("Fehler beim Speichern") else "ALTE FASSUNG (bitte die neue aus dem Repo nehmen)"))
        except Exception as e:
            print("  nexus_lang.py: NICHT ladbar: %s" % mask(str(e))[:150])
    else:
        print("  nexus_lang.py: FEHLT - der Bot sendet die Originaltexte")

    try:
        aus = subprocess.run(["systemctl", "show", "nexus_ceo.service", "-p", "ActiveState", "-p", "SubState",
                              "-p", "NRestarts", "-p", "ActiveEnterTimestamp"],
                             capture_output=True, text=True, timeout=6).stdout
        werte = dict(z.split("=", 1) for z in aus.strip().splitlines() if "=" in z)
        if werte.get("ActiveState"):
            K["dienst"] = (werte.get("ActiveState"), werte.get("NRestarts", "?"))
            print("  Dienst nexus_ceo.service: %s/%s | Neustarts durch systemd: %s | laeuft seit: %s" % (
                werte.get("ActiveState"), werte.get("SubState"), werte.get("NRestarts", "?"),
                werte.get("ActiveEnterTimestamp") or "-"))
    except Exception:
        print("  Dienst: nicht abfragbar (kein systemd?)")

    print()
    print("  Einstellungen (.env) - leer = Standard aus dem Code:")
    zeile = []
    for k in ZEIGEN:
        if env.get(k, "") != "":
            zeile.append("%s=%s" % (k, env[k]))
            if len(zeile) == 4:
                print("    " + " | ".join(zeile))
                zeile = []
    if zeile:
        print("    " + " | ".join(zeile))
    ohne = [k for k in ZEIGEN if env.get(k, "") == ""]
    if ohne:
        print("    nicht gesetzt (Standard gilt): " + ", ".join(ohne))
    for k in SCHLUESSEL_LISTEN:
        if env.get(k):
            teile = [t.strip() for t in env[k].split(",") if t.strip()]
            print("    %s: %d Eintraege, %d verschiedene%s" % (
                k, len(teile), len(set(teile)), "   <-- doppelte Keys" if len(set(teile)) < len(teile) else ""))
    fehlt = [k for k in PFLICHT if not env.get(k) and not (k == "TG_TOKEN" and env.get("TELEGRAM_TOKEN"))
             and not (k == "MY_CHAT_ID" and env.get("TELEGRAM_CHAT_ID"))]
    print("    Pflicht-Eintraege: %s" % ("alle gesetzt" if not fehlt else "FEHLEN: " + ", ".join(fehlt)))
    if doppelt:
        print("    Namen stehen MEHRFACH in der .env (der letzte zaehlt): " + ", ".join(doppelt))
    print("    Konto: %s" % konto_art(env.get("CAPITAL_URL", "")))
    K["sprache"] = env.get("BOT_LANGUAGE") or "-"


# ---------------------------------------------------------------------------------------
# TEIL 1: Log
# ---------------------------------------------------------------------------------------
def teil1(bot_dir, days):
    titel("TEIL 1: Bot-Log der letzten %d Tage" % days)
    files = sorted(glob.glob(str(bot_dir / "nexus_ceo.log*")), key=lambda f: Path(f).stat().st_mtime)
    if not files:
        print("  keine nexus_ceo.log* in %s gefunden" % bot_dir)
        return
    jetzt = datetime.now()
    ab = jetzt - timedelta(days=days)
    heute, gestern = jetzt.date(), (jetzt - timedelta(days=1)).date()
    cnt_all, cnt_heute, cnt_gestern, cnt_24 = Counter(), Counter(), Counter(), Counter()
    letzte = defaultdict(list)
    gem_art, sl_mult = Counter(), Counter()
    fehler, schliess, ergebnisse = Counter(), [], []
    fehler_bsp = {}
    anbieter, exits = defaultdict(Counter), []
    erste, letzte_ts, zeilen = None, None, 0
    for f in files:
        try:
            if datetime.fromtimestamp(Path(f).stat().st_mtime) < ab:
                continue
            ts = None
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    kopf = line[:19]
                    if len(kopf) == 19 and kopf[4] == "-" and kopf[13] == ":":
                        try:
                            ts = datetime.strptime(kopf, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            pass
                    if ts is None or ts < ab:
                        continue
                    zeilen += 1
                    erste = ts if erste is None or ts < erste else erste
                    letzte_ts = ts if letzte_ts is None or ts > letzte_ts else letzte_ts
                    for name, pat in EREIGNISSE:
                        if (pat in line) if isinstance(pat, str) else pat.search(line):
                            cnt_all[name] += 1
                            if ts >= jetzt - timedelta(hours=24):
                                cnt_24[name] += 1
                            if ts.date() == heute:
                                cnt_heute[name] += 1
                            elif ts.date() == gestern:
                                cnt_gestern[name] += 1
                            letzte[name].append((ts, line.rstrip()))
                            del letzte[name][:-3]
                    m = re.search(r"Gemini (\S+) key=\.\.\.\S+: (\w+) \|", line)
                    if m:
                        gem_art[(m.group(1), m.group(2))] += 1
                    m = re.search(r"\b(Groq|Qwen|Nvidia|Ollama)(?: key \d+)? hata: (.*)", line)
                    if m:
                        anbieter[m.group(1)][re.sub(r"\d+(?:[.,]\d+)?", "#", mask(m.group(2).strip()))[:120]] += 1
                    m = re.search(r"EXIT: (\S+) (BUY|SELL)->(BUY|SELL)", line)
                    if m:
                        exits.append((ts, m.group(1), m.group(2), m.group(3)))
                    m = re.search(r"minimum mesafe: ([\d.]+) × Tagesspanne", line)
                    if m:
                        sl_mult[m.group(1)] += 1
                    if "Trade-Ergebnis: " in line:
                        ergebnisse.append((ts, line.split("Trade-Ergebnis: ", 1)[1].rstrip()))
                    if "Schliess-Melder: " in line and ("GESCHLOSSEN" in line or "Geschlossen" in line):
                        schliess.append((ts, line.split("Schliess-Melder: ", 1)[1].rstrip()))
                    if " ERROR " in line or line.startswith("ERROR:") or "Traceback" in line:
                        roh = line.split(" ERROR ", 1)[1] if " ERROR " in line else line
                        norm = re.sub(r"\d+(?:[.,]\d+)?", "#", mask(roh.strip()))[:110]
                        fehler[norm] += 1
                        fehler_bsp[norm] = ts
        except Exception as e:
            print("  %s: %s" % (Path(f).name, e))
    if erste is None:
        print("  keine Logzeilen im Zeitraum")
        return
    print("  %d Zeilen von %s bis %s" % (zeilen, erste.strftime("%d.%m. %H:%M"), letzte_ts.strftime("%d.%m. %H:%M")))
    K["heute"], K["alle"], K["fehler"] = dict(cnt_24), dict(cnt_all), sum(fehler.values())
    K["exits"] = exits
    print()
    print("  %-44s %7s %8s %8s" % ("Ereignis", "heute", "gestern", "%d Tage" % days))
    for name, _ in EREIGNISSE:
        if cnt_all[name]:
            print("  %-44s %7d %8d %8d" % (name, cnt_heute[name], cnt_gestern[name], cnt_all[name]))
    nie = [n for n, _ in EREIGNISSE if not cnt_all[n]]
    if nie:
        print("  nie im Zeitraum: " + ", ".join(nie))

    scans_gem, scans_ers = cnt_all["KI: Gemini hat geantwortet"], cnt_all["Ersatzbetrieb im Scan"]
    if scans_gem or scans_ers:
        print("\n  KI: Gemini lieferte %d-mal, der Ersatzbetrieb lief %d-mal im Scan." % (scans_gem, scans_ers))
    if gem_art:
        print("  Gemini-Fehlschlaege nach Modell und Art (tot/tageslimit/key/keytot/modell/abbruch):")
        for (modell, art), n in sorted(gem_art.items(), key=lambda x: -x[1])[:8]:
            print("    %5d x  %-28s %s" % (n, modell, art))
    if anbieter:
        print("  Ersatz-Anbieter: Fehlschlaege und haeufigste Fehlermeldung (Erfolge stehen oben als 'KI: Ersatz ...'):")
        for name in ("Groq", "Qwen", "Nvidia", "Ollama"):
            if anbieter.get(name):
                print("    %-7s %5d Fehlschlaege" % (name, sum(anbieter[name].values())))
                for text, n in anbieter[name].most_common(2):
                    print("            %5d x  %s" % (n, text))
        K["anbieter"] = {k: sum(v.values()) for k, v in anbieter.items()}
    if sl_mult:
        print("  Stop-Korrekturen nach Faktor (SL_ATR_MULT zum Zeitpunkt): " +
              ", ".join("%s x Tagesspanne: %d" % (k, n) for k, n in sorted(sl_mult.items())))

    for name in ("Order gesendet, Position NICHT gefunden", "Order abgelehnt", "Gegensignal (EXIT)",
                 "Sperre: Wiedereinstieg", "Sperre: maximale Positionen", "Sperre: Gruppen-Limit",
                 "Stop-Leiter nachgezogen", "Stop-Leiter abgelehnt", "Trailing-Stop wirklich nachgezogen", "Gremium beraten",
                 "Warnung im Stop-Lauf (Trailing SL epic)", "Schwarzer Schwan",
                 "KI: Modell automatisch ersetzt", "KI: kein Ersatzmodell bestand die Pruefung"):
        if letzte.get(name):
            print("\n  --- letzte Zeilen: %s ---" % name)
            for ts, l in letzte[name]:
                print("    " + mask(l)[:200])

    if schliess:
        print("\n  --- Schliessungen laut Bot (Schliess-Melder), letzte %d von %d ---" % (min(25, len(schliess)), len(schliess)))
        grund = Counter()
        for ts, text in schliess:
            m = re.search(r"Grund: ([^|]+)", text)
            grund[(m.group(1).strip() if m else "Bot/Hand")] += 1
        for ts, text in schliess[-25:]:
            print("    %s  %s" % (ts.strftime("%d.%m. %H:%M"), mask(text)[:170]))
        print("    nach Grund: " + ", ".join("%s: %d" % (g, n) for g, n in grund.most_common()))
    else:
        print("\n  Schliess-Melder: keine Meldung im Zeitraum")

    if ergebnisse:
        print("\n  --- Scan-Ergebnisse laut Log (ab v15.21), letzte %d von %d ---" % (min(25, len(ergebnisse)), len(ergebnisse)))
        for ts, text in ergebnisse[-25:]:
            print("    %s  %s" % (ts.strftime("%d.%m. %H:%M"), mask(text)[:170]))
    else:
        print("\n  Scan-Ergebnisse: keine Zeile 'Trade-Ergebnis' im Zeitraum (der Bot schreibt sie ab v15.21)")

    print("\n  --- Fehler im Log: %d Zeilen, %d verschiedene ---" % (sum(fehler.values()), len(fehler)))
    for norm, n in fehler.most_common(10):
        print("    %5d x  (zuletzt %s)  %s" % (n, fehler_bsp[norm].strftime("%d.%m. %H:%M"), norm))

    miss = bot_dir / "nexus_lang_missing.log"
    if miss.is_file():
        zl = [z for z in miss.read_text(encoding="utf-8", errors="replace").splitlines() if z.strip()]
        K["miss"] = len(zl)
        print("\n  --- nicht uebersetzte Telegram-Texte (nexus_lang_missing.log): %d ---" % len(zl))
        for z in zl[-15:]:
            print("    " + mask(z)[:170])
    else:
        print("\n  nexus_lang_missing.log: nicht vorhanden (bisher war jeder Text uebersetzbar oder es ist keine Sprache aktiv)")


# ---------------------------------------------------------------------------------------
# TEIL 2: Capital.com
# ---------------------------------------------------------------------------------------
def positionen_bilden(activities, offen_ids):
    """Positionen aus den POSITION-Eintraegen bilden.
    Capital.com: Der Eroeffnungs-Eintrag hat kein openPrice. Jeder Teilverkauf und die Schliessung
    tragen die dealId der Position und ein openPrice. Geschlossen ist eine Position, wenn ihre dealId
    nicht mehr unter den offenen Positionen steht.
    offen_ids = Menge der offenen dealIds oder None (dann zaehlt die verkaufte Groesse)."""
    pos = {}
    for a in activities:
        if a.get("type") != "POSITION" or str(a.get("status")).upper() != "ACCEPTED":
            continue
        det = a.get("details") or {}
        t = zeit(a.get("dateUTC") or a.get("dateUtc") or a.get("date"))
        if not t or det.get("direction") not in ("BUY", "SELL"):
            continue
        did = a.get("dealId") or "ohne-%s-%s" % (a.get("epic"), t)
        groesse = zahl(det.get("size"))
        if "openPrice" not in det:                      # Eroeffnung
            if did in pos and pos[did]["open"] is None:  # Schliessung stand vor der Eroeffnung in der Liste
                pos[did].update(open=t, groesse=groesse, einstieg=zahl(det.get("level")), dir=det["direction"])
            elif did not in pos:
                pos[did] = {"id": did, "epic": a.get("epic"), "name": det.get("marketName") or a.get("epic"),
                            "dir": det["direction"], "open": t, "close": None, "groesse": groesse,
                            "einstieg": zahl(det.get("level")), "grund": None, "teile": 0, "abbau": [], "weg": 0.0}
            else:
                pos[did]["groesse"] = (pos[did]["groesse"] or 0) + groesse     # Aufstocken unter derselben dealId
        else:                                           # Teilverkauf oder Schliessung
            if did not in pos:                          # Position wurde vor dem Zeitraum eroeffnet
                pos[did] = {"id": did, "epic": a.get("epic"), "name": det.get("marketName") or a.get("epic"),
                            "dir": "SELL" if det["direction"] == "BUY" else "BUY", "open": None, "close": None,
                            "groesse": None, "einstieg": zahl(det.get("openPrice")), "grund": None, "teile": 0,
                            "abbau": [], "weg": 0.0}
            p = pos[did]
            p["teile"] += 1
            p["weg"] += groesse
            p["abbau"].append((t, str(a.get("source") or "?").upper()))
    fertig = list(pos.values())
    for p in fertig:
        if not p["abbau"]:
            continue
        if offen_ids is not None:
            zu = p["id"] not in offen_ids
        else:
            zu = p["groesse"] is not None and p["weg"] >= p["groesse"] - 1e-9
        if zu:
            p["close"], p["grund"] = p["abbau"][-1]
    fertig.sort(key=lambda p: p["open"] or p["abbau"][0][0])
    return fertig


def buchungen_zuordnen(positionen, trades):
    """Jede TRADE-Buchung ihrer Position zuordnen: ueber die dealId der Buchung, sonst ueber
    Epic und Zeit (kurz nach einem Teilverkauf oder einer Schliessung)."""
    nach_id = {p["id"]: p for p in positionen}
    je_epic = defaultdict(list)
    for p in positionen:
        p["summe"], p["buchungen"] = 0.0, 0
        je_epic[p["epic"]].append(p)
    ohne = []
    for t, betrag, epic, did in trades:
        p = nach_id.get(did)
        if p is None:
            nah = []
            for q in je_epic.get(epic, []):
                for ab, _quelle in q["abbau"]:
                    abstand = (t - ab).total_seconds()
                    if -5 <= abstand <= 300:
                        nah.append((abs(abstand), id(q), q))
            p = min(nah, key=lambda x: x[0])[2] if nah else None
        if p is None:
            ohne.append((t, betrag, epic))
        else:
            p["summe"] += betrag
            p["buchungen"] += 1
    return ohne


def epic_von(sym, bot_dir):
    """Symbol aus dem Log (OIL_CRUDE, HEATING_OIL) -> Epic bei Capital.com (HEATINGOIL)."""
    if "cfg" not in K:
        K["cfg"] = {}
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("nexus_cfg_diag", str(Path(bot_dir) / "capital_markets_config.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            K["cfg"] = {k: v.get("epic", k) for k, v in mod.MARKET_CONFIG.items()}
        except Exception:
            pass
    return K["cfg"].get(sym, sym)


def kennzahlen(werte):
    plus = [v for v in werte if v > 0.004]
    minus = [v for v in werte if v < -0.004]
    null = len(werte) - len(plus) - len(minus)
    quote = 100.0 * len(plus) / max(1, len(plus) + len(minus))
    d_plus = sum(plus) / len(plus) if plus else 0.0
    d_minus = sum(minus) / len(minus) if minus else 0.0
    faktor = (sum(plus) / -sum(minus)) if minus else float("inf")
    noetig = 100.0 * -d_minus / (d_plus - d_minus) if (plus and minus) else None
    return {"n": len(werte), "plus": len(plus), "minus": len(minus), "null": null, "summe": sum(werte), "quote": quote,
            "d_plus": d_plus, "d_minus": d_minus, "faktor": faktor, "noetig": noetig}


def kennzahlen_zeile(name, k):
    return ("  %-26s %3d | Gewinner %3d, Verlierer %3d, +/-0: %2d | Quote %5.1f %% | Schnitt Gewinn %+6.2f, Verlust %+6.2f | "
            "Gewinnfaktor %s | Summe %+7.2f%s" % (
                name, k["n"], k["plus"], k["minus"], k["null"], k["quote"], k["d_plus"], k["d_minus"],
                ("%.2f" % k["faktor"]) if k["faktor"] != float("inf") else "-", k["summe"],
                ("" if k["noetig"] is None else " | noetige Quote fuer +/-0: %.0f %%" % k["noetig"])))


def teil2(env, days):
    titel("TEIL 2: Capital.com (nur lesend), letzte %d Tage" % days)
    try:
        import requests
    except ImportError:
        print("  Modul 'requests' fehlt fuer dieses python3 - Teil 2 uebersprungen")
        return None
    key, ident, pw = env.get("CAPITAL_API_KEY"), env.get("CAPITAL_IDENTIFIER"), env.get("CAPITAL_PASSWORD")
    url = env.get("CAPITAL_URL") or "https://demo-api-capital.backend-capital.com/api/v1"
    if not (key and ident and pw):
        print("  CAPITAL_API_KEY / CAPITAL_IDENTIFIER / CAPITAL_PASSWORD fehlen in .env")
        return None
    try:
        r = requests.post(url + "/session", json={"identifier": ident, "password": pw},
                          headers={"X-CAP-API-KEY": key}, timeout=15)
    except Exception as e:
        print("  Login fehlgeschlagen: %s" % mask(str(e))[:150])
        return None
    if r.status_code != 200:
        print("  Login fehlgeschlagen: HTTP %s %s" % (r.status_code, mask(r.text)[:150]))
        return None
    h = {"X-CAP-API-KEY": key, "CST": r.headers.get("CST"), "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN")}

    def get(path, params=None):
        for versuch in (1, 2):
            try:
                rr = requests.get(url + path, headers=h, params=params or {}, timeout=20)
                if rr.status_code == 200:
                    return rr.json()
                if rr.status_code == 429 and versuch == 1:
                    time.sleep(2)
                    continue
                return {"_error": "HTTP %s %s" % (rr.status_code, mask(rr.text)[:120])}
            except Exception as e:
                return {"_error": mask(str(e))[:120]}
        return {"_error": "unbekannt"}

    # ---- Konto ------------------------------------------------------------------------
    acc = get("/accounts")
    if "_error" in acc:
        print("  Konto nicht lesbar: %s" % acc["_error"])
    else:
        for a in acc.get("accounts", []):
            if a.get("preferred") or len(acc.get("accounts", [])) == 1:
                b = a.get("balance") or {}
                K["konto"] = (konto_art(url), zahl(b.get("balance")), zahl(b.get("available")), zahl(b.get("profitLoss")), a.get("currency", ""))
                print("  Konto (%s): Kontostand %.2f | verfuegbar %.2f | offener Gewinn/Verlust %+.2f %s" % (
                    konto_art(url), zahl(b.get("balance")), zahl(b.get("available")),
                    zahl(b.get("profitLoss")), a.get("currency", "")))
    pref = get("/accounts/preferences")
    if "_error" not in pref:
        print("  Hedging-Modus: %s" % ("AN  -> Teilverkaeufe (Mirror-TP) gehen so NICHT" if pref.get("hedgingMode")
                                      else "aus (richtig fuer Mirror-TP)"))

    # ---- offene Positionen ------------------------------------------------------------
    offen_ids = None
    pos = get("/positions")
    if "_error" in pos:
        print("  Positionen nicht lesbar: %s" % pos["_error"])
    else:
        offen = pos.get("positions", [])
        offen_ids = set((p.get("position") or {}).get("dealId") for p in offen)
        print("\n  OFFENE POSITIONEN: %d" % len(offen))
        K["offen"] = []
        for p in offen:
            pp, mm = p.get("position") or {}, p.get("market") or {}
            einstieg, sl, tp = zahl(pp.get("level")), zahl(pp.get("stopLevel")), zahl(pp.get("profitLevel"))
            kurs = zahl(mm.get("bid") if pp.get("direction") == "BUY" else mm.get("offer"))
            t = zeit(pp.get("createdDateUTC") or pp.get("createdDate"))
            K["offen"].append((str(mm.get("epic")), pp.get("direction"), zahl(pp.get("size")), zahl(pp.get("upl")),
                               (abs(sl - kurs) / kurs * 100) if sl and kurs else None, bool(tp)))
            print("    %-14s %-4s Groesse %-8g Einstieg %-10g Kurs %-10g UPL %+7.2f | SL %s | TP %s | offen seit %s" % (
                str(mm.get("epic"))[:14], pp.get("direction"), zahl(pp.get("size")), einstieg, kurs, zahl(pp.get("upl")),
                ("%g (%.2f %% vom Kurs)" % (sl, abs(sl - kurs) / kurs * 100)) if sl and kurs else "FEHLT",
                ("%g (%.2f %%)" % (tp, abs(tp - kurs) / kurs * 100)) if tp and kurs else "FEHLT",
                lokal(t).strftime("%d.%m. %H:%M") if t else "?"))

    # ---- Historie ---------------------------------------------------------------------
    activities, transactions, errors = [], [], Counter()
    jetzt = datetime.now(timezone.utc).replace(tzinfo=None)
    for d in range(days - 1, -1, -1):
        tag = jetzt.date() - timedelta(days=d)
        bis = "%sT23:59:59" % tag if d else jetzt.strftime("%Y-%m-%dT%H:%M:%S")
        p = {"from": "%sT00:00:00" % tag, "to": bis}
        a = get("/history/activity", dict(p, detailed="true"))
        if "_error" in a:
            errors["Aktivitaeten: " + a["_error"]] += 1
        else:
            activities += a.get("activities", [])
        time.sleep(0.15)
        t = get("/history/transactions", p)
        if "_error" in t:
            errors["Buchungen: " + t["_error"]] += 1
        else:
            transactions += t.get("transactions", [])
        time.sleep(0.15)
    for e, n in errors.items():
        print("  FEHLER (%dx): %s" % (n, e))
    K["api_fehler"] = sum(errors.values())
    # Capital.com liefert je Tag die NEUESTEN zuerst -> nach Zeit sortieren, Doppelte entfernen
    gesehen, akt = set(), []
    for a in activities:
        k = (a.get("dateUTC") or a.get("date"), a.get("dealId"), a.get("type"), a.get("source"))
        if k not in gesehen:
            gesehen.add(k)
            akt.append(a)
    akt.sort(key=lambda a: str(a.get("dateUTC") or a.get("date")))
    gesehen, buch = set(), []
    for t in transactions:
        k = (t.get("dateUtc") or t.get("date"), t.get("reference"), t.get("transactionType"), t.get("size"))
        if k not in gesehen:
            gesehen.add(k)
            buch.append(t)
    buch.sort(key=lambda t: str(t.get("dateUtc") or t.get("date")))

    print("\n  AKTIVITAETEN: %d | BUCHUNGEN: %d" % (len(akt), len(buch)))
    by = Counter((a.get("type"), a.get("source")) for a in akt)
    print("  nach Typ und Quelle (SL = Stop Loss, TP = Take Profit, USER = Bot oder Hand, SYSTEM = Broker): " +
          ", ".join("%s/%s: %d" % (t, s, n) for (t, s), n in sorted(by.items(), key=lambda x: -x[1])))

    trades = []
    for t in buch:
        if t.get("transactionType") == "TRADE":
            tt = zeit(t.get("dateUtc") or t.get("date"))
            if tt:
                trades.append((tt, zahl(t.get("size")), str(t.get("instrumentName")), t.get("dealId")))
    andere = Counter()
    for t in buch:
        if t.get("transactionType") != "TRADE":
            andere[t.get("transactionType")] += zahl(t.get("size"))
    if not trades:
        print("  keine TRADE-Buchungen im Zeitraum")
        return {"aktivitaeten": len(akt), "buchungen": len(buch)}

    # ---- Kennzahlen: je Buchung und je Position --------------------------------------
    positionen = positionen_bilden(akt, offen_ids)
    ohne = buchungen_zuordnen(positionen, trades)
    zu = [p for p in positionen if p["close"] is not None and p["buchungen"] > 0]
    frueher = [p for p in zu if p["open"] is None]
    print("\n  ERGEBNIS (EUR laut Buchungen)")
    K["kb"] = kennzahlen([b for _, b, _, _ in trades])
    print(kennzahlen_zeile("je Buchung (wie Capital)", K["kb"]))
    letzte24 = [b for tt, b, _, _ in trades if tt >= jetzt - timedelta(hours=24)]
    if letzte24:
        K["k24"] = kennzahlen(letzte24)
        print(kennzahlen_zeile("  davon letzte 24 h", K["k24"]))
    if zu:
        K["kp"] = kennzahlen([p["summe"] for p in zu])
        print(kennzahlen_zeile("je Position (geschlossen)", K["kp"]))
        print("  Eine Position mit drei Teilverkaeufen zaehlt bei Capital.com als drei Gewinner, ein Stop Loss als ein Verlierer.")
        if frueher:
            print("  %d dieser Positionen wurden vor dem Zeitraum eroeffnet: Teilverkaeufe von davor fehlen in ihrem Ergebnis." % len(frueher))
    if andere:
        print("  Sonstige Buchungen: " + ", ".join("%s %+.2f" % (k, v) for k, v in andere.items()))
    if ohne:
        print("  %d Buchungen ohne passende Position: Summe %+.2f" % (
            len(ohne), sum(b for _, b, _ in ohne)))

    # ---- je Tag -----------------------------------------------------------------------
    je_tag = defaultdict(lambda: [0, 0.0, 0, 0])
    for tt, betrag, _, _ in trades:
        e = je_tag[lokal(tt).date()]
        e[0] += 1
        e[1] += betrag
    for p in positionen:
        if p["open"] is not None:
            je_tag[lokal(p["open"]).date()][2] += 1
        if p["close"] is not None and p["grund"] == "SL":
            je_tag[lokal(p["close"]).date()][3] += 1
    print("\n  JE TAG (Ortszeit)        Buchungen   Summe EUR   Positionen eroeffnet   per Stop Loss geschlossen")
    for tag in sorted(je_tag):
        e = je_tag[tag]
        print("    %s %s  %10d  %+10.2f  %21d  %10d" % (WOCHENTAG[tag.weekday()], tag.strftime("%d.%m."), e[0], e[1], e[2], e[3]))

    # ---- je Symbol --------------------------------------------------------------------
    je_sym = defaultdict(lambda: [0, 0.0, 0, 0, 0])
    for _, betrag, epic, _ in trades:
        je_sym[epic][0] += 1
        je_sym[epic][1] += betrag
    for p in zu:
        e = je_sym[p["epic"]]
        e[2] += 1
        e[3] += 1 if p["summe"] > 0.004 else 0
        e[4] += 1 if p["grund"] == "SL" else 0
    print("\n  JE SYMBOL          Buchungen   Summe EUR   Positionen   davon im Plus   per Stop Loss zu")
    for epic, e in sorted(je_sym.items(), key=lambda x: x[1][1]):
        print("    %-14s %9d  %+10.2f  %11d  %14d  %16d" % (epic[:14], e[0], e[1], e[2], e[3], e[4]))

    # ---- Grund der Schliessung --------------------------------------------------------
    nach_grund = defaultdict(list)
    for p in zu:
        nach_grund[{"SL": "Stop Loss", "TP": "Take Profit", "USER": "Bot oder Hand (z.B. letzte Mirror-TP-Stufe)"}.get(
            p["grund"], "Broker (%s)" % p["grund"])].append(p)
    K["grund"] = [(p0, len(ps), sum(p["summe"] for p in ps)) for p0, ps in
                  sorted(((g, [p for p in zu if p["grund"] == g]) for g in set(p["grund"] for p in zu)), key=lambda x: -len(x[1]))]
    print("\n  WODURCH WURDE DER REST DER POSITION GESCHLOSSEN?")
    for g, ps in sorted(nach_grund.items(), key=lambda x: -len(x[1])):
        mit = [p for p in ps if p["open"] is not None]
        halten = dauer(sum((p["close"] - p["open"]).total_seconds() for p in mit) / len(mit)) if mit else "-"
        print("    %-44s %3d Positionen | Summe %+7.2f | Schnitt %+6.2f | mittlere Haltedauer %s" % (
            g, len(ps), sum(p["summe"] for p in ps), sum(p["summe"] for p in ps) / len(ps), halten))

    # ---- Liste der Positionen ---------------------------------------------------------
    print("\n  POSITIONEN (letzte %d von %d; Zeiten in Ortszeit)" % (min(40, len(positionen)), len(positionen)))
    print("    eroeffnet     Symbol         Richt.  Groesse    Einstieg    Teilverk.  geschlossen      durch   Haltedauer   Ergebnis EUR   (davor = vor dem Zeitraum eroeffnet)")
    for p in positionen[-40:]:
        print("    %-12s  %-14s %-5s %9s  %10g  %9d  %-15s  %-6s  %-11s  %s" % (
            lokal(p["open"]).strftime("%d.%m. %H:%M") if p["open"] else "davor", p["epic"][:14], p["dir"],
            ("%g" % p["groesse"]) if p["groesse"] is not None else "?", p["einstieg"],
            max(0, p["teile"] - (1 if p["close"] else 0)),
            lokal(p["close"]).strftime("%d.%m. %H:%M") if p["close"] else "noch offen",
            p["grund"] or "-", dauer((p["close"] - p["open"]).total_seconds()) if p["close"] and p["open"] else "-",
            ("%+.2f (%d Buch.)" % (p["summe"], p["buchungen"])) if p["buchungen"]
            else ("keine Buchung gefunden" if p["close"] else "-")))

    # ---- Wiedereinstiege --------------------------------------------------------------
    try:
        sperre = float(env.get("WIEDEREINSTIEG_SPERRE_STD") or 6)
    except ValueError:
        sperre = 6.0
    wieder = []
    je_epic = defaultdict(list)
    for p in positionen:
        je_epic[p["epic"]].append(p)
    for epic, ps in je_epic.items():
        for i in range(1, len(ps)):
            vor, neu = ps[i - 1], ps[i]
            if vor["close"] is not None and neu["open"] is not None and neu["dir"] == vor["dir"]:
                luecke = (neu["open"] - vor["close"]).total_seconds()
                if luecke < 24 * 3600:
                    wieder.append((neu["open"], epic, neu["dir"], luecke, vor["grund"]))
    wieder.sort()
    K["wieder"] = (len(wieder), sum(1 for w in wieder if sperre > 0 and w[3] < sperre * 3600), sperre)
    print("\n  WIEDEREINSTIEGE in dieselbe Richtung innerhalb von 24 h: %d   (Sperre laut .env: %g h; es gibt sie seit v15.18)" % (
        len(wieder), sperre))
    for t, epic, richtung, luecke, grund in wieder[-20:]:
        print("    %s  %-14s %-4s  %s nach der Schliessung (durch %s)%s" % (
            lokal(t).strftime("%d.%m. %H:%M"), epic[:14], richtung, dauer(luecke), grund,
            "   <-- kuerzer als die Sperre" if sperre > 0 and luecke < sperre * 3600 else ""))

    # ---- Drehen: ist die Gegenposition wirklich entstanden? --------------------------
    if K.get("exits"):
        print("\n  GEGENSIGNALE laut Log: %d   (ab v15.21 schliesst der Bot nur; davor schickte er eine ungepruefte Gegen-Order)" % len(K["exits"]))
        entstanden, geschl = 0, 0
        for ts, sym, von, nach in K["exits"][-15:]:
            epic = epic_von(sym, K.get("bot_dir", "."))
            zu_ok = any(q["epic"] == epic and q["dir"] == von and any(abs((lokal(ab) - ts).total_seconds()) <= 180 for ab, _ in q["abbau"])
                        for q in positionen)
            neu_ok = any(q["epic"] == epic and q["dir"] == nach and q["open"] is not None
                         and -10 <= (lokal(q["open"]) - ts).total_seconds() <= 180 for q in positionen)
            entstanden += 1 if neu_ok else 0
            geschl += 1 if zu_ok else 0
            print("    %s  %-12s %s->%s | alte Position verkleinert/geschlossen: %-4s | Gegenposition entstanden: %s" % (
                ts.strftime("%d.%m. %H:%M"), sym[:12], von, nach, "ja" if zu_ok else "NEIN", "ja" if neu_ok else "NEIN"))
        K["drehen"] = (len(K["exits"][-15:]), geschl, entstanden)

    # ---- Rohdaten zum Nachpruefen -----------------------------------------------------
    roh = [a for a in akt if a.get("type") == "POSITION"][-4:]
    if roh:
        print("\n  ROHDATEN: die 4 neuesten Positions-Eintraege und die 3 neuesten Buchungen")
        for a in roh:
            print("    " + mask(json.dumps(a, ensure_ascii=False))[:520])
        for t in buch[-3:]:
            print("    " + mask(json.dumps(t, ensure_ascii=False))[:300])
    return {"aktivitaeten": len(akt), "buchungen": len(buch), "positionen": len(positionen)}


# ---------------------------------------------------------------------------------------
# TEIL 3: Listen aus GitHub
# ---------------------------------------------------------------------------------------
def teil3():
    titel("TEIL 3: Listen aus GitHub (KhungFu/kisilerim)")
    try:
        import requests
    except ImportError:
        print("  Modul 'requests' fehlt")
        return
    for datei in ("mentor_name.txt", "toplam_egitim.txt", "Abfrage_Quellen.txt"):
        try:
            r = requests.get("https://raw.githubusercontent.com/KhungFu/kisilerim/main/" + datei, timeout=10)
            if r.status_code == 200:
                zl = [z for z in r.text.splitlines() if z.strip() and not z.strip().startswith("#")]
                x = sum(1 for z in zl if "x.com/" in z.lower() or "twitter.com/" in z.lower())
                print("  %-22s erreichbar | %7d Zeichen | %5d Zeilen | davon X-Konten: %d" % (datei, len(r.text), len(zl), x))
            else:
                print("  %-22s HTTP %s" % (datei, r.status_code))
        except Exception as e:
            print("  %-22s nicht erreichbar: %s" % (datei, mask(str(e))[:100]))


TEXTE = {
    "de": {"kopf": "🔎 NEXUS-Diagnose · {0} Tage", "stand": "Stand: {0}", "dienst": "Dienst: {0}, Neustarts: {1}", "sprache": "Sprache: {0}",
           "konto": "Konto ({0}): {1:.2f} {4} · verfügbar {2:.2f} · offen {3:+.2f}", "offen": "Offene Positionen: {0}",
           "sl": "SL {0:.2f} %", "sl_fehlt": "SL FEHLT", "tp_fehlt": "TP FEHLT",
           "kb": "Je Buchung (wie Capital)", "k24": "Letzte 24 h", "kp": "Je Position",
           "kz": "{0}: {1} · Quote {2:.0f} % · Ø {3:+.2f} / {4:+.2f} · Faktor {5} · Summe {6:+.2f}", "noetig": "Nötige Quote für ±0: {0:.0f} %",
           "grund": "Geschlossen durch", "SL": "Stop Loss", "TP": "Take Profit", "USER": "Bot/Hand", "broker": "Broker",
           "wieder": "Wiedereinstiege in 24 h: {0}, davon kürzer als die Sperre ({2:g} h): {1}",
           "heute": "Letzte 24 h im Log", "orders": "Orders", "nicht_best": "nicht bestätigt", "abgelehnt": "abgelehnt", "sl_gesch": "Stop geschoben",
           "be": "Breakeven", "mtp": "Mirror-TP", "drehen": "Gegensignale", "sperren": "Sperren ({0} Tage)", "s_wieder": "Wiedereinstieg",
           "s_max": "Max. Positionen", "s_verlust": "Verluste", "s_spread": "Spread", "s_dd": "Tages-Stopp",
           "dreh2": "Gegensignale: {0} · Position geschlossen: {1} · Gegenposition entstanden: {2}", "ki": "KI ({0} Tage): Gemini {1} · Ersatzbetrieb {2} · alle Anbieter ausgefallen {3} · Modell ersetzt {4}", "fehler": "Fehler im Log: {0} · nicht übersetzte Texte: {1}",
           "kein_log": "Kein Log im Zeitraum.", "kein_api": "Capital.com: keine Daten.", "api_fehler": "Capital.com: {0} Abfragen fehlgeschlagen.",
           "gremium": "Gremium ({0} Tage): beraten {1} · ausgeführt {2} · Vorsitz gestoppt {3} · nicht beschlussfähig {4} · gespalten {5} · keine Mehrheit {6}",
           "keine": "keine"},
    "en": {"kopf": "🔎 NEXUS diagnosis · {0} days", "stand": "Version: {0}", "dienst": "Service: {0}, restarts: {1}", "sprache": "Language: {0}",
           "konto": "Account ({0}): {1:.2f} {4} · available {2:.2f} · open {3:+.2f}", "offen": "Open positions: {0}",
           "sl": "SL {0:.2f}%", "sl_fehlt": "SL MISSING", "tp_fehlt": "TP MISSING",
           "kb": "Per booking (as Capital)", "k24": "Last 24 h", "kp": "Per position",
           "kz": "{0}: {1} · win rate {2:.0f}% · avg {3:+.2f} / {4:+.2f} · factor {5} · total {6:+.2f}", "noetig": "Win rate needed to break even: {0:.0f}%",
           "grund": "Closed by", "SL": "Stop Loss", "TP": "Take Profit", "USER": "bot/manual", "broker": "broker",
           "wieder": "Re-entries within 24 h: {0}, of which shorter than the lock ({2:g} h): {1}",
           "heute": "Last 24 h in the log", "orders": "orders", "nicht_best": "not verified", "abgelehnt": "rejected", "sl_gesch": "stop moved",
           "be": "Breakeven", "mtp": "Mirror-TP", "drehen": "opposite signals", "sperren": "Blocks ({0} days)", "s_wieder": "re-entry",
           "s_max": "max positions", "s_verlust": "losses", "s_spread": "spread", "s_dd": "daily stop",
           "dreh2": "Opposite signals: {0} · position closed: {1} · opposite position created: {2}", "ki": "AI ({0} days): Gemini {1} · fallback mode {2} · all providers failed {3} · model replaced {4}", "fehler": "Errors in the log: {0} · untranslated texts: {1}",
           "kein_log": "No log in this period.", "kein_api": "Capital.com: no data.", "api_fehler": "Capital.com: {0} requests failed.",
           "gremium": "Committee ({0} days): discussed {1} · executed {2} · chair stopped {3} · no quorum {4} · split {5} · no majority {6}",
           "keine": "none"},
    "tr": {"kopf": "🔎 NEXUS teşhisi · {0} gün", "stand": "Sürüm: {0}", "dienst": "Servis: {0}, yeniden başlatma: {1}", "sprache": "Dil: {0}",
           "konto": "Hesap ({0}): {1:.2f} {4} · müsait {2:.2f} · açık {3:+.2f}", "offen": "Açık pozisyon: {0}",
           "sl": "SL %{0:.2f}", "sl_fehlt": "SL YOK", "tp_fehlt": "TP YOK",
           "kb": "Kayıt başına (Capital gibi)", "k24": "Son 24 saat", "kp": "Pozisyon başına",
           "kz": "{0}: {1} · kazanma %{2:.0f} · ort. {3:+.2f} / {4:+.2f} · faktör {5} · toplam {6:+.2f}", "noetig": "Başabaş için gereken oran: %{0:.0f}",
           "grund": "Kapatan", "SL": "Stop Loss", "TP": "Take Profit", "USER": "bot/elle", "broker": "aracı kurum",
           "wieder": "24 saat içinde yeniden giriş: {0}, kilitten ({2:g} sa) kısa olan: {1}",
           "heute": "Son 24 saat log'da", "orders": "emir", "nicht_best": "doğrulanamadı", "abgelehnt": "reddedildi", "sl_gesch": "stop kaydırıldı",
           "be": "Breakeven", "mtp": "Mirror-TP", "drehen": "karşı sinyal", "sperren": "Engeller ({0} gün)", "s_wieder": "yeniden giriş",
           "s_max": "maks. pozisyon", "s_verlust": "kayıp", "s_spread": "spread", "s_dd": "günlük durdurma",
           "dreh2": "Karşı sinyal: {0} · pozisyon kapatıldı: {1} · karşı pozisyon oluştu: {2}", "ki": "Yapay zekâ ({0} gün): Gemini {1} · yedek mod {2} · tüm sağlayıcılar başarısız {3} · model değiştirildi {4}", "fehler": "Log'da hata: {0} · çevrilmemiş metin: {1}",
           "kein_log": "Bu dönemde log yok.", "kein_api": "Capital.com: veri yok.", "api_fehler": "Capital.com: {0} sorgu başarısız.",
           "gremium": "Kurul ({0} gün): görüşüldü {1} · uygulandı {2} · başkan durdurdu {3} · yeter sayı yok {4} · bölündü {5} · çoğunluk yok {6}",
           "keine": "yok"},
}


def kurzfassung(lang, days, mit_api):
    """Kurze Fassung fuer das Handy (und fuer /diagnose in Telegram): hoechstens rund 30 kurze Zeilen."""
    T = TEXTE.get(lang, TEXTE["de"])
    z = [T["kopf"].format(days)]
    kopf = [T["stand"].format(K.get("stand", "?"))]
    if K.get("dienst"):
        kopf.append(T["dienst"].format(*K["dienst"]))
    kopf.append(T["sprache"].format(K.get("sprache", "-")))
    z.append(" · ".join(kopf))
    if mit_api:
        if K.get("konto"):
            art = {"Demo": "Demo", "LIVE - echtes Geld": {"de": "LIVE", "en": "LIVE", "tr": "CANLI"}.get(lang, "LIVE")}.get(K["konto"][0], "?")
            z.append(T["konto"].format(art, *K["konto"][1:]))
        if "offen" in K:
            z.append(T["offen"].format(len(K["offen"])))
            for epic, richtung, groesse, upl, slp, tp in K["offen"][:8]:
                z.append(" • %s %s %g · UPL %+.2f · %s%s" % (
                    epic, richtung, groesse, upl, T["sl"].format(slp) if slp is not None else T["sl_fehlt"],
                    "" if tp else " · " + T["tp_fehlt"]))
        if not K.get("konto") and "offen" not in K and "kb" not in K:
            z.append(T["kein_api"])
        if K.get("api_fehler"):
            z.append(T["api_fehler"].format(K["api_fehler"]))

        def kz(name, k):
            return T["kz"].format(name, k["n"], k["quote"], k["d_plus"], k["d_minus"],
                                  ("%.2f" % k["faktor"]) if k["faktor"] != float("inf") else "–", k["summe"])
        for key in ("kb", "k24", "kp"):
            if key in K:
                z.append(kz(T[key], K[key]))
        if "kp" in K and K["kp"]["noetig"] is not None:
            z.append(T["noetig"].format(K["kp"]["noetig"]))
        if K.get("grund"):
            z.append(T["grund"] + ": " + " · ".join("%s %d (%+.2f)" % (T.get(g, "%s %s" % (T["broker"], g)), n, summe)
                                                     for g, n, summe in K["grund"]))
        if "wieder" in K:
            z.append(T["wieder"].format(*K["wieder"]))
        if "drehen" in K:
            z.append(T["dreh2"].format(*K["drehen"]))
    if "alle" in K:
        h, a = K["heute"], K["alle"]
        z.append("%s: %s %d · %s %d · %s %d · %s %d · %s %d · %s %d/%d/%d · %s %d" % (
            T["heute"], T["orders"], h.get("Order eroeffnet und bestaetigt", 0),
            T["nicht_best"], h.get("Order gesendet, Position NICHT gefunden", 0), T["abgelehnt"], h.get("Order abgelehnt", 0),
            T["sl_gesch"], h.get("Stop auf Mindestabstand geschoben", 0), T["be"], h.get("Breakeven gesetzt", 0),
            T["mtp"], h.get("Mirror-TP Stufe 1", 0), h.get("Mirror-TP Stufe 2", 0), h.get("Mirror-TP Stufe 3", 0),
            T["drehen"], h.get("Gegensignal (EXIT)", 0)))
        z.append("%s: %s %d · %s %d · %s %d · %s %d · %s %d" % (
            T["sperren"].format(days), T["s_wieder"], a.get("Sperre: Wiedereinstieg", 0), T["s_max"], a.get("Sperre: maximale Positionen", 0),
            T["s_verlust"], a.get("Sperre: Verluste des Tages", 0), T["s_spread"], a.get("Sperre: Spread", 0),
            T["s_dd"], a.get("Sperre: Tages-Verlust-Stopp", 0)))
        z.append(T["ki"].format(days, a.get("KI: Gemini hat geantwortet", 0), a.get("Ersatzbetrieb im Scan", 0),
                                a.get("KI: alle Ersatz-Anbieter ausgefallen", 0), a.get("KI: Modell automatisch ersetzt", 0)))
        if a.get("Gremium beraten", 0) or a.get("Gremium: kein Kandidat im Scan", 0):
            z.append(T["gremium"].format(days, a.get("Gremium beraten", 0), a.get("Gremium: Beschluss ausgefuehrt", 0),
                                         a.get("Gremium: Vorsitz gestoppt", 0) + a.get("Gremium: Vorsitz ohne Antwort", 0),
                                         a.get("Gremium: nicht beschlussfaehig", 0), a.get("Gremium: gespalten (Senaryo 4)", 0),
                                         a.get("Gremium: keine Mehrheit", 0)))
        z.append(T["fehler"].format(K.get("fehler", 0), K.get("miss", 0)))
    else:
        z.append(T["kein_log"])
    return "\n".join(z)


def sicher(name, fn, *args):
    """Einen Teil ausfuehren; ein Fehler darin beendet nicht den ganzen Bericht."""
    try:
        return fn(*args)
    except Exception as e:
        import traceback
        print("  FEHLER in %s: %s" % (name, mask(str(e))[:200]))
        print("  " + mask(traceback.format_exc().strip().splitlines()[-3])[:200])
        return None


def main():
    ap = argparse.ArgumentParser(description="NEXUS-Diagnose (nur lesend)")
    ap.add_argument("--dir", default=None, help="Bot-Ordner (Standard: Ordner dieses Skripts, sonst ~/DEXTER_SYSTEM/nexus)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--lang", default="de", choices=["de", "en", "tr"], help="Sprache der Kurzfassung")
    ap.add_argument("--no-api", action="store_true", help="ohne Capital.com und GitHub")
    a = ap.parse_args()
    if a.dir:
        bot_dir = Path(a.dir).expanduser().resolve()
    else:
        hier = Path(__file__).resolve().parent
        bot_dir = hier if (hier / "nexus_ceo.py").is_file() else Path.home() / "DEXTER_SYSTEM" / "nexus"
    days = max(1, min(a.days, 60))
    print("NEXUS-Diagnose %s | %s | Ordner: %s" % (VERSION, datetime.now().strftime("%Y-%m-%d %H:%M"), bot_dir))
    print("Nur lesend. Schluessel, Passwoerter und Token werden nicht ausgegeben.")
    env, doppelt = read_env(bot_dir / ".env")
    K["bot_dir"] = str(bot_dir)
    sicher("Teil 0", teil0, bot_dir, env, doppelt)
    sicher("Teil 1", teil1, bot_dir, days)
    if not a.no_api:
        sicher("Teil 2", teil2, env, days)
        sicher("Teil 3", teil3)
    titel(KURZ_MARKE)
    print(sicher("Kurzfassung", kurzfassung, a.lang, days, not a.no_api) or "-")
    print("\nFertig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
