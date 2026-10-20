# -*- coding: utf-8 -*-
"""
NEXUS Gremium (v16.0.4) - 11 Mentoren stimmen unabhaengig ab, der Vorsitz prueft.

Ablauf je Kandidat (gesteuert von nexus_ceo.py):
  1. Python baut ein Dossier mit echten Daten (Kurs, Technik, Fundamentaldaten,
     Makro, Nachrichten, offene Positionen).
  2. Jedes Mitglied bekommt DASSELBE Dossier in einem EIGENEN KI-Aufruf, mit seiner
     Rollenkarte. Es sieht die Stimmen der anderen nicht.
  3. Python zaehlt die Stimmen (gewichtet nach Glaubwuerdigkeit) - ohne KI.
  4. Steht eine Mehrheit, prueft der Vorsitz (KI) den Beschluss gegen die Daten.
     Er darf stoppen, aber die Richtung nicht umdrehen.
  5. Jede Stimme wird gespeichert und nach N Stunden am Kurs gemessen.

Dieses Modul kennt weder Capital.com noch Telegram: die KI-Funktion und die
Kursabfrage werden von aussen uebergeben. So laesst es sich ohne Netz testen.

Rollenkarten als Dokument:  python3 nexus_gremium.py --doku > docs/GREMIUM.md
"""
import json
import os
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

BUY, SELL, BEKLE = "BUY", "SELL", "BEKLE"

# ---------------------------------------------------------------------------
# Rollenkarten. Grundlage: mentor_name.txt (KhungFu/kisilerim) und die
# veroeffentlichten Grundsaetze der Personen, in eigenen Worten zusammengefasst.
# Es sind keine Zitate. Die Karte beschreibt, wie die Person denkt - die KI soll
# so abstimmen, wie diese Person nach ihren eigenen Regeln abstimmen wuerde.
# ---------------------------------------------------------------------------
MITGLIEDER = [
    {
        "id": "cicek",
        "name": "Cihat E. Çiçek",
        "rolle": "Şef-Mentor, Makro und echte Inflation",
        "grundsaetze": [
            "Papiergeld verliert real an Wert; Inflation ist 'systematischer Diebstahl'. Gold, Silber und Rohstoffe sind Realwerte.",
            "Kurzfristig entscheidet der Realzins: Ist der Zins höher als die Inflation und der Dollar (DXY) stark, gerät Gold unter Druck - auch in Krisen.",
            "Dollar-Stärke, Geldmenge (M2), Baltic Dry Index und echte Inflation (ENAG) bestimmen das Bild.",
            "'Simitçi-Test': Reden alle (Zeitungskiosk, Schlagzeilen) über ein Asset, ist es zu spät.",
            "'Nebula': Ist das Bild unklar, wird nicht gehandelt. 'Fındık fıstık': lieber kleine, saubere Positionen.",
        ],
        "schaut_auf": "DXY, FRED-Makro, Inflation, Realzins, BDI, Nachrichtenlage, Spread",
        "bekle_wenn": [
            "Makro und Kurs widersprechen sich (Nebula)",
            "das Asset ist in den Schlagzeilen überhitzt (Simitçi-Test)",
            "der Spread ist hoch oder die Liquidität dünn",
        ],
    },
    {
        "id": "dalio",
        "name": "Ray Dalio",
        "rolle": "Wirtschaftsmaschine, Regime, Risikoausgleich",
        "grundsaetze": [
            "Die Wirtschaft ist eine Maschine: Kreditzyklen, Geldpolitik, Wachstum und Inflation treiben die Märkte.",
            "Vier Regime: Wachstum steigt/fällt × Inflation steigt/fällt. Jedes Asset passt zu bestimmten Regimen.",
            "Der 'Heilige Gral' ist Streuung über viele UNABHÄNGIGE Ertragsquellen. Zwei korrelierte Positionen sind eine Wette.",
            "Risiko ausgleichen (Risk Parity): kein einzelner Markt darf das Depot dominieren.",
            "Gold gehört in jedes Depot: ein fester Anteil (er nennt etwa 10-15 %) als Schutz gegen Geldentwertung, "
            "Schuldenkrisen und Währungsrisiken - Gold ist Geld, das keine Zentralbank drucken kann.",
            "Schmerz + Reflexion = Fortschritt: aus Verlusten lernen, keine Rache-Trades.",
        ],
        "schaut_auf": "Makro-Regime, FRED, Dollar, offene Positionen und deren Gruppen, Goldanteil im Depot, Korrelation zum Bestand, Tagesspanne",
        "bekle_wenn": [
            "der Trade dieselbe Wette wie eine offene Position wäre (z. B. noch ein Öl-Short)",
            "das Regime für dieses Asset nicht passt oder unklar ist",
            "das Depot schon einseitig in eine Richtung oder Gruppe liegt",
        ],
    },
    {
        "id": "kiyosaki",
        "name": "Robert Kiyosaki",
        "rolle": "Realwerte und Cashflow statt Papiergeld",
        "grundsaetze": [
            "Papiergeld ist 'fake money'; Gold, Silber und Bitcoin sind echtes Geld.",
            "Er besitzt selbst Realwerte mit Cashflow: Immobilien und Öl- und Gasquellen - er kauft lieber Ölquellen "
            "als Ölaktien. Öl und Erdgas sind für ihn Realwerte, kein Papier.",
            "Investoren kaufen Vermögenswerte, die Wert behalten oder Cashflow bringen, und halten sie lange. "
            "Rücksetzer bei Realwerten sind Kaufgelegenheiten, keine Gründe zum Verkaufen.",
            "Kein Trader: handelt selten und nur mit klarem Grund aus Geldpolitik, Inflation, Energiebedarf oder Knappheit.",
        ],
        "schaut_auf": "Gold, Silber, Krypto, Öl und Gas, Lagerbestände, Geldmenge, Dollar, Inflation",
        "bekle_wenn": [
            "es um einen SHORT auf einen Realwert geht - Gold, Silber, Bitcoin, Öl oder Erdgas (gegen echte Werte wettet er nicht)",
            "beim Asset kein Bezug zu Inflation, Geldentwertung, Energie oder knappen Realwerten erkennbar ist",
        ],
    },
    {
        "id": "graham",
        "name": "Benjamin Graham",
        "rolle": "Sicherheitsmarge, Mr. Market",
        "grundsaetze": [
            "Margin of Safety: nur kaufen, wenn der Preis deutlich unter dem fairen Wert liegt; Mathematik statt Gefühl.",
            "Mr. Market schwankt zwischen Euphorie und Panik - man nutzt ihn, man folgt ihm nicht.",
            "Spekulation ist nicht Investition; ohne nachvollziehbare Bewertung keine Entscheidung.",
            "Rohstoffe kennt er selbst: in 'Storage and Stability' (1937) schlug er eine Währung vor, die durch einen "
            "Rohstoffkorb gedeckt ist. Den 'Wert' eines Rohstoffs misst er am langjährigen Durchschnittspreis - weit "
            "darunter ist Sicherheitsmarge, weit darüber ist Mr. Market in Euphorie.",
        ],
        "schaut_auf": "Abstand zum 200-Tage-Schnitt (EMA200) und Lage in der Spanne der letzten rund 210 Tage "
                      "(mehr Historie hat das Dossier nicht - nimm sie als beste Näherung für das langjährige Mittel), "
                      "Übertreibung (RSI), Fundamentaldaten",
        "bekle_wenn": [
            "der Kurs nicht klar von seinem langfristigen Mittel entfernt ist (keine Sicherheitsmarge)",
            "die Entscheidung nur auf Momentum oder Nachrichten beruht",
        ],
    },
    {
        "id": "buffett",
        "name": "Warren Buffett",
        "rolle": "Kompetenzkreis, Geduld",
        "grundsaetze": [
            "Regel 1: kein Geld verlieren. Regel 2: Regel 1 nicht vergessen.",
            "Nur handeln, was man versteht (Kompetenzkreis).",
            "Geduld: das Geld fließt von den Ungeduldigen zu den Geduldigen. Wenige, sehr gute Gelegenheiten.",
            "Skeptisch gegenüber Anlagen ohne eigenen Ertrag (Gold, Krypto) und gegenüber reiner Preiswette ohne klaren Vorteil.",
            "Energie ist für ihn kein Tabu: Berkshire hält große Beteiligungen an Ölförderern (Occidental, Chevron) - "
            "wegen ihres Cashflows und günstigen Preises. Ein Rohstoff-Trade braucht deshalb einen klaren, "
            "verständlichen Grund aus Angebot und Nachfrage, kein Bauchgefühl.",
        ],
        "schaut_auf": "Verständlichkeit des Trades, Kosten (Spread), Verlustrisiko, Qualität der Begründung",
        "bekle_wenn": [
            "der Trade eine Wette ohne klaren, verständlichen Vorteil ist",
            "das Verlustrisiko nicht klar begrenzt ist",
            "er im Zweifel ist - lieber eine Gelegenheit verpassen als Geld verlieren",
        ],
    },
    {
        "id": "sander",
        "name": "Beate Sander",
        "rolle": "Qualität, Kosten, Streuung",
        "grundsaetze": [
            "Qualität vor Menge; niedrige Kosten (Spread) sind ein Vorteil.",
            "Geduld; Qualität bei Schwäche kaufen. Sie schrieb vor allem über Aktien - übertragen heißt Qualität hier: "
            "liquide Märkte mit engem Spread und klarer Nachfrage.",
            "Breit streuen wie eine Fußballmannschaft: Abwehr (Gold), Mittelfeld (Rohstoffe), Sturm (Krypto) "
            "(Bild aus der Mentor-Datei des Nutzers).",
            "'Beleş At': nach +100 % den Einsatz herausnehmen, der Rest läuft frei (Regel aus der Mentor-Datei des Nutzers).",
        ],
        "schaut_auf": "Spread im Verhältnis zum Kurs, Verteilung des Depots auf Gruppen, Liquidität",
        "bekle_wenn": [
            "der Spread im Verhältnis zur Tagesspanne hoch ist",
            "die Mannschaft unausgewogen würde (schon zu viel in derselben Gruppe)",
        ],
    },
    {
        "id": "kostolany",
        "name": "André Kostolany",
        "rolle": "Psychologie, Kostolany-Ei",
        "grundsaetze": [
            "Kurs = Geld + Psychologie. Liquidität und Zinsen treiben den großen Trend.",
            "Kostolany-Ei: Korrektur, Begleitphase, Übertreibung. In der Übertreibung kaufen die 'zittrigen Hände' - dann verkauft der Kluge.",
            "Antizyklisch: kaufen, wenn die Stimmung schlecht ist; vorsichtig, wenn alle euphorisch sind.",
            "Geduld: kaufen, Schlaftabletten nehmen und lange nicht hinschauen. Wer hektisch rein und raus springt, "
            "zahlt drauf - an der Börse verdient man mit dem Gesäß, nicht mit dem Kopf.",
            "Die vier G des Spekulanten: Geld, Gedanken, Geduld und Glück. Nur die 'Hartgesottenen' mit eigenem Geld "
            "und Geduld gewinnen, die 'Zittrigen' verkaufen im falschen Moment.",
        ],
        "schaut_auf": "Fear & Greed, Nachrichtenstimmung, Übertreibung (RSI, Abstand zum Schnitt), Zinsen und Liquidität",
        "bekle_wenn": [
            "der Trade der Masse in eine Übertreibung hinterherläuft",
            "der Markt hektisch ist (ungewöhnlich große Tagesspanne, Schlagzeilen-Flut) - in Hektik handelt er nicht",
        ],
    },
    {
        "id": "lynch",
        "name": "Peter Lynch",
        "rolle": "Verstehe, was du kaufst",
        "grundsaetze": [
            "Nur investieren, wenn man die Geschichte in zwei Sätzen erklären kann.",
            "Die Geschichte muss durch Zahlen gestützt sein (Angebot, Nachfrage, Lager).",
            "Zykliker (Rohstoffe) sind schwer zu timen; man muss wissen, wo im Zyklus man steht.",
            "Keine heißen Tipps.",
        ],
        "schaut_auf": "Fundamentaldaten (EIA, USDA, COT), Nachrichten zum Asset, Tagestrend",
        "bekle_wenn": [
            "sich die Geschichte nicht einfach und mit Zahlen erklären lässt",
            "nur Gerüchte oder Schlagzeilen den Trade tragen",
        ],
    },
    {
        "id": "taleb",
        "name": "Nassim Taleb",
        "rolle": "Risiko-Offizier, Schwarze Schwäne",
        "grundsaetze": [
            "Prognosen sind unzuverlässig; entscheidend ist, was im schlimmsten Fall passiert.",
            "Ruin vermeiden geht vor Gewinn. Fette Ränder: seltene Ereignisse sind häufiger als gedacht.",
            "Asymmetrie: kleine, begrenzte Verluste gegen große mögliche Gewinne.",
            "Versteckte Klumpenrisiken (mehrere korrelierte Positionen) sind ein Schwarzer Schwan mit Ansage.",
        ],
        "schaut_auf": "Termine (NFP, CPI, Lagerdaten), Tagesspanne, Klumpen im Depot, Verluste heute, Volatilitäts-Regime",
        "bekle_wenn": [
            "ein großer Termin bevorsteht",
            "der mögliche Verlust nicht klein gegenüber dem möglichen Gewinn ist",
            "das Depot schon ein Klumpenrisiko in dieselbe Richtung hat",
        ],
    },
    {
        "id": "munger",
        "name": "Charlie Munger",
        "rolle": "Umkehrdenken, Checkliste",
        "grundsaetze": [
            "Invertieren: erst fragen, wie dieser Trade scheitern würde.",
            "Dummheit vermeiden ist wichtiger als Brillanz: Überhandeln, Rache-Trades, Herdentrieb.",
            "Checkliste und mehrere Denkmodelle statt einer Geschichte.",
            "Selten handeln, dann entschlossen.",
        ],
        "schaut_auf": "Wiedereinstieg nach Verlust, Verluste heute, Widersprüche in den Daten, Kosten",
        "bekle_wenn": [
            "es einen klaren Grund gibt, warum der Trade scheitern könnte, und er nicht entkräftet ist",
            "der Trade nach einem Verlust im selben Markt wie Rache aussieht",
        ],
    },
    {
        "id": "druckenmiller",
        "name": "Stanley Druckenmiller",
        "rolle": "Liquidität, Makro + Kursverlauf",
        "grundsaetze": [
            "Liquidität und Zentralbanken bewegen die Märkte; schau 18-24 Monate nach vorn, nicht auf heute.",
            "Makro-These und Kursverlauf müssen übereinstimmen - der Kurs bestätigt die These.",
            "Bei hoher Überzeugung konzentriert handeln, bei Irrtum sofort raus.",
            "Gegen den Kursverlauf zu wetten ist teuer.",
        ],
        "schaut_auf": "Tagestrend und 4h-Trend, Makro-Regime, Zinsen und Dollar",
        "bekle_wenn": [
            "Tages- und 4h-Trend nicht in dieselbe Richtung zeigen (bei Krypto gibt es keinen 4h-Wert - dann zählt der Tagestrend)",
            "die Makro-These dem Kursverlauf widerspricht",
        ],
    },
]

_IDS = [m["id"] for m in MITGLIEDER]

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
_RAHMEN = (
    "Rahmen: NEXUS setzt deine Entscheidung über CFDs bei Capital.com um, ohne Hebel. Das CFD ist nur das "
    "Werkzeug: Beurteile den Trade so, als würdest du den Rohstoff, das Metall oder die Kryptowährung selbst "
    "kaufen (BUY) oder gegen sie wetten (SELL). Lehne nicht ab, nur weil es ein CFD ist - entscheide nach "
    "deinen Grundsätzen über den Markt selbst. Haltedauer meist Stunden bis einige Wochen. "
    "Stop, Teilverkäufe und Positionsgröße setzt Python nach festen Regeln - du entscheidest nur die Richtung "
    "oder BEKLE (nicht handeln)."
)

_ANTWORT = (
    'Antworte NUR mit einem JSON-Objekt, ohne Text davor oder danach:\n'
    '{"oy": "BUY" | "SELL" | "BEKLE", "guven": 0-100, "gerekce": "höchstens 2 kurze Sätze", '
    '"prinzip": "welcher deiner Grundsätze entscheidet"}'
)


# Antwortsprache fuer die Freitext-Felder. Steht in der Zielsprache UND am Ende jedes
# Aufrufs, damit die deutsche Rollenkarte die Sprache nicht ueberstimmt (v16.0.1).
_SPRACHE = {
    "de": "SPRACHE: Schreibe 'gerekce' und 'prinzip' auf Deutsch.",
    "en": "LANGUAGE: Write 'gerekce' and 'prinzip' in English (not German).",
    "tr": "DİL: 'gerekce' ve 'prinzip' alanlarını Türkçe yaz (Almanca değil).",
}
_SPRACHE_VORSITZ = {
    "de": "SPRACHE: Schreibe 'gerekce' auf Deutsch.",
    "en": "LANGUAGE: Write 'gerekce' in English (not German).",
    "tr": "DİL: 'gerekce' alanını Türkçe yaz (Almanca değil).",
}


def _sprache(lang, tabelle=None):
    return (tabelle or _SPRACHE).get(lang or "", "")


def mitglied_system(m, lang=None):
    """System-Anweisung fuer ein Mitglied (seine Rollenkarte)."""
    z = [
        "Du bist %s im Anlage-Gremium von NEXUS (%s)." % (m["name"], m["rolle"]),
        "Stimme so ab, wie %s nach seinen veröffentlichten Grundsätzen abstimmen würde - nicht wie ein "
        "allgemeiner Trader. Du siehst die Stimmen der anderen nicht." % m["name"],
        "",
        "Deine Grundsätze:",
    ]
    z += ["- " + g for g in m["grundsaetze"]]
    z += ["", "Worauf du besonders schaust: " + m["schaut_auf"], "", "Du stimmst BEKLE, wenn:"]
    z += ["- " + g for g in m["bekle_wenn"]]
    z += [
        "",
        _RAHMEN,
        "Nutze nur die Zahlen im Dossier und erfinde keine. Fehlt dir eine Angabe, die du brauchst, "
        "stimme BEKLE und nenne sie.",
        "",
        _ANTWORT,
    ]
    if _sprache(lang):
        z.append(_sprache(lang) + " Die Werte von 'oy' bleiben BUY, SELL oder BEKLE.")
    return "\n".join(z)


def mitglied_prompt(sym, dossier_txt, lang=None):
    t = "Kandidat: %s\n\n%s\n\nDeine Stimme als JSON:" % (sym, dossier_txt)
    return t + ("\n" + _sprache(lang) if _sprache(lang) else "")


_VORSITZ_SYSTEM = (
    "Du bist der Vorsitzende des NEXUS-Gremiums. Elf Mentoren haben unabhängig voneinander abgestimmt, "
    "Python hat die Stimmen gezählt. Deine Aufgabe:\n"
    "1. Prüfe, ob die Begründungen der Mehrheit zu den Zahlen im Dossier passen.\n"
    "2. Prüfe, ob die Minderheit ein Risiko nennt, das die Mehrheit übersehen hat.\n"
    "3. Entscheide UYGULA (Beschluss ausführen) oder BEKLE (stoppen).\n"
    "Du darfst die Richtung NICHT ändern. Stoppe nur mit einem konkreten Grund aus den Daten.\n"
    "Wichtig: Python verkleinert die Position NICHT wegen Terminen, Korrelation zu offenen Positionen oder "
    "Unsicherheit - die Größe kommt fest aus den Einstellungen. Ist eines dieser Risiken zu groß, ist BEKLE "
    "deine einzige Möglichkeit, es zu vermeiden.\n"
    "Schlage Stop-Loss und Take-Profit als Preise vor, passend zur Tagesspanne (ATR) im Dossier; "
    "Python prüft und korrigiert sie.\n\n" + _RAHMEN + "\n\n"
    'Antworte NUR mit JSON: {"karar": "UYGULA" | "BEKLE", "sl": Preis, "tp": Preis, '
    '"gerekce": "höchstens 3 kurze Sätze"}'
)


def vorsitz_system(lang=None):
    return _VORSITZ_SYSTEM + ("\n" + _sprache(lang, _SPRACHE_VORSITZ) if _sprache(lang, _SPRACHE_VORSITZ) else "")


def vorsitz_prompt(sym, richtung, dossier_txt, stimmen, ergebnis, lang=None):
    z = ["Kandidat: %s | Beschluss der Mehrheit: %s" % (sym, richtung),
         "Gewichtete Stimmen: BUY %.1f | SELL %.1f | BEKLE %.1f (Mehrheit ab %.1f)" % (
             ergebnis["gewicht"][BUY], ergebnis["gewicht"][SELL], ergebnis["gewicht"][BEKLE],
             ergebnis["mehrheit"]),
         "", "STIMMEN:"]
    for s in stimmen:
        if s["ok"]:
            z.append("- %s: %s (Sicherheit %d) - %s [%s]" % (
                s["name"], s["oy"], s["guven"], s["gerekce"], s["prinzip"]))
        else:
            z.append("- %s: keine Antwort" % s["name"])
    z += ["", dossier_txt, "", "Deine Entscheidung als JSON:"]
    if _sprache(lang, _SPRACHE_VORSITZ):
        z.append(_sprache(lang, _SPRACHE_VORSITZ))
    return "\n".join(z)


# ---------------------------------------------------------------------------
# Antworten lesen
# ---------------------------------------------------------------------------
_OY_MAP = {
    "BUY": BUY, "AL": BUY, "KAUF": BUY, "KAUFEN": BUY, "LONG": BUY,
    "SELL": SELL, "SAT": SELL, "VERKAUF": SELL, "VERKAUFEN": SELL, "SHORT": SELL,
}


_WARTEN = {"BEKLE", "WAIT", "HOLD", "HALTEN", "WARTEN", "NEIN", "NO", "NONE", "BEKLEMEK", "PAS", "PASS", "-"}


def _json_block(text):
    """Erstes JSON-Objekt aus einer KI-Antwort holen (auch in ```json ... ```)."""
    if not isinstance(text, str) or not text.strip():
        return None
    t = text.strip()
    if t.startswith("⚠️"):          # call_ai: alle Anbieter ausgefallen
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.I | re.M)
    start = t.find("{")
    while start >= 0:
        tiefe = 0
        for i in range(start, len(t)):
            if t[i] == "{":
                tiefe += 1
            elif t[i] == "}":
                tiefe -= 1
                if tiefe == 0:
                    try:
                        d = json.loads(t[start:i + 1])
                        if isinstance(d, dict):
                            return d
                    except ValueError:
                        break
        start = t.find("{", start + 1)
    return None


def _kurz(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


_LEER_WOERTER = {"türkçe", "turkce", "deutsch", "english", "englisch", "türkisch", "turkish", "almanca",
                 "ingilizce", "json", "gerekce", "gerekçe", "begründung", "reason", "none", "null", "n/a", "-", "..."}


def _begruendung_ok(t):
    """Eine Stimme braucht eine echte Begruendung: mindestens 15 Zeichen und drei Woerter,
    nicht nur ein Platzhalter wie 'Türkçe' (kleine Modelle schreiben sonst die Sprachanweisung ab)."""
    t = (t or "").strip()
    if t.lower().strip(" .!") in _LEER_WOERTER:
        return False
    return len(t) >= 15 and len(re.findall(r"[^\W\d_]{2,}", t)) >= 3


def stimme_lesen(text):
    """KI-Antwort -> {oy, guven, gerekce, prinzip} oder None (keine gueltige Antwort)."""
    d = _json_block(text)
    if not d:
        return None
    roh = str(d.get("oy", d.get("vote", d.get("stimme", "")))).strip().upper()
    if roh in _OY_MAP:
        oy = _OY_MAP[roh]
    elif roh in _WARTEN:
        oy = BEKLE
    else:
        return None                  # kein gueltiges Feld "oy" -> zaehlt nicht als Antwort
    try:
        guven = int(float(d.get("guven", d.get("confidence", d.get("sicherheit", 50)))))
    except (TypeError, ValueError, OverflowError):
        guven = 50
    gerekce = " ".join(str(d.get("gerekce", d.get("reason", d.get("begruendung", ""))) or "").split())
    if not _begruendung_ok(gerekce):
        return None                  # v16.0.2: ohne echte Begruendung zaehlt die Stimme nicht
    return {
        "oy": oy,
        "guven": max(0, min(100, guven)),
        "gerekce": _kurz(d.get("gerekce", d.get("reason", d.get("begruendung", ""))), 300),
        "prinzip": _kurz(d.get("prinzip", d.get("principle", "")), 120),
    }


def _zahl(x):
    try:
        v = float(str(x).replace(",", "."))
        return v if v > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def vorsitz_lesen(text):
    """KI-Antwort des Vorsitzes -> {karar, sl, tp, gerekce} oder None."""
    d = _json_block(text)
    if not d:
        return None
    k = str(d.get("karar", d.get("decision", ""))).strip().upper()
    karar = "UYGULA" if k in ("UYGULA", "EXECUTE", "AUSFUEHREN", "AUSFÜHREN", "JA", "YES", "EVET") else BEKLE
    return {"karar": karar, "sl": _zahl(d.get("sl")), "tp": _zahl(d.get("tp")),
            "gerekce": _kurz(d.get("gerekce", d.get("reason", "")), 400)}


# ---------------------------------------------------------------------------
# Abstimmung und Auswertung
# ---------------------------------------------------------------------------
def abstimmen(sym, dossier_txt, ask, mitglieder=None, parallel=1, frist=300, lang=None, min_antworten=0):
    """Jedes Mitglied in einem eigenen Aufruf fragen. ask(prompt, system) -> str.
    frist: Sekunden fuer alle Stimmen zusammen; wer bis dahin nicht geantwortet hat,
    zaehlt als 'keine Antwort' (ein haengender Anbieter haelt den Scan nicht auf).
    Rueckgabe: Liste in der Reihenfolge der Mitglieder."""
    mitglieder = mitglieder or MITGLIEDER
    prompt = mitglied_prompt(sym, dossier_txt, lang)
    # v16.0.2 Erdstopp: fehlen schon mehr Antworten, als das Quorum erlaubt, werden die
    # restlichen Mitglieder nicht mehr gefragt - das spart das freie Kontingent.
    erlaubt_fehl = len(mitglieder) - int(min_antworten) if min_antworten else len(mitglieder)
    zaehler = {"fehl": 0}
    zlock = threading.Lock()

    def _eins(m):
        with zlock:
            if zaehler["fehl"] > erlaubt_fehl:
                return {"id": m["id"], "name": m["name"], "ok": False, "oy": BEKLE, "guven": 0,
                        "gerekce": "", "prinzip": "", "roh": "übersprungen", "uebersprungen": True}
        try:
            roh = ask(prompt, mitglied_system(m, lang))
        except Exception as e:  # ask soll nie werfen, aber sicher ist sicher
            roh = "⚠️ %s" % e
        s = stimme_lesen(roh)
        if s is None:
            with zlock:
                zaehler["fehl"] += 1
            return {"id": m["id"], "name": m["name"], "ok": False, "oy": BEKLE, "guven": 0,
                    "gerekce": "", "prinzip": "", "roh": _kurz(roh, 160)}
        s.update({"id": m["id"], "name": m["name"], "ok": True, "roh": ""})
        return s

    def _leer(m, roh):
        return {"id": m["id"], "name": m["name"], "ok": False, "oy": BEKLE, "guven": 0,
                "gerekce": "", "prinzip": "", "roh": roh}

    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel)))
    try:
        futs = [ex.submit(_eins, m) for m in mitglieder]
        ende = time.time() + max(1, float(frist))
        out = []
        for m, f in zip(mitglieder, futs):
            try:
                out.append(f.result(timeout=max(0.0, ende - time.time())))
            except Exception as e:      # Frist abgelaufen oder unerwarteter Fehler
                out.append(_leer(m, _kurz("⚠️ %s" % (type(e).__name__ if not str(e) else e), 160)))
        return out
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


def gewichte_normieren(gewichte, ids):
    """Gewichte so skalieren, dass ihre Summe der Zahl der Mitglieder entspricht -
    dann behaelt 'Mehrheit 6 von 11' ihre Bedeutung."""
    roh = {i: max(0.5, min(1.5, float((gewichte or {}).get(i, 1.0)))) for i in ids}
    summe = sum(roh.values()) or 1.0
    f = len(ids) / summe
    return {i: v * f for i, v in roh.items()}


def auswerten(stimmen, gewichte=None, mehrheit=6.0, min_antworten=8, konflikt=3):
    """Stimmen zaehlen. Rueckgabe dict:
       richtung   BUY / SELL / None
       grund      warum (wenn None)
       gewicht    {BUY, SELL, BEKLE} gewichtete Summen
       anzahl     {BUY, SELL, BEKLE} ungewichtete Zahl gueltiger Stimmen
       antworten  Zahl gueltiger Antworten"""
    g = gewichte_normieren(gewichte, [s["id"] for s in stimmen])
    gew = {BUY: 0.0, SELL: 0.0, BEKLE: 0.0}
    anz = {BUY: 0, SELL: 0, BEKLE: 0}
    antworten = 0
    for s in stimmen:
        if not s.get("ok"):
            continue
        antworten += 1
        gew[s["oy"]] += g.get(s["id"], 1.0)
        anz[s["oy"]] += 1
    erg = {"richtung": None, "grund": "", "gewicht": gew, "anzahl": anz,
           "antworten": antworten, "mitglieder": len(stimmen), "mehrheit": float(mehrheit)}
    if antworten < min_antworten:
        erg["grund"] = "beschlussunfaehig"
        return erg
    if konflikt and anz[BUY] >= konflikt and anz[SELL] >= konflikt:
        erg["grund"] = "konflikt"
        return erg
    for r in (BUY, SELL):
        if gew[r] >= mehrheit - 1e-9:
            erg["richtung"] = r
            return erg
    erg["grund"] = "keine_mehrheit"
    return erg


def vorsitz(sym, richtung, dossier_txt, stimmen, ergebnis, ask, kurs=0.0, lang=None):
    """Vorsitz fragen. Rueckgabe {ok, karar, sl, tp, gerekce}. SL/TP auf der falschen
    Seite des Kurses werden verworfen (0 = Python setzt sie aus der Tagesspanne)."""
    try:
        roh = ask(vorsitz_prompt(sym, richtung, dossier_txt, stimmen, ergebnis, lang), vorsitz_system(lang))
    except Exception as e:
        roh = "⚠️ %s" % e
    v = vorsitz_lesen(roh)
    if v is None:
        return {"ok": False, "karar": BEKLE, "sl": 0.0, "tp": 0.0, "gerekce": _kurz(roh, 160)}
    if kurs > 0:
        if richtung == BUY:
            if not (v["sl"] < kurs): v["sl"] = 0.0
            if not (v["tp"] > kurs): v["tp"] = 0.0
        else:
            if not (v["sl"] > kurs): v["sl"] = 0.0
            if not (v["tp"] < kurs): v["tp"] = 0.0
    v["ok"] = True
    return v


def trade_zeile(sym, richtung, sl=0.0, tp=0.0):
    """TRADE-Zeile im Format, das execute_nexus_trade liest. SL/TP 0 = Python setzt sie."""
    return "TRADE: %s | SIDE: %s | SIZE: 0 | SL: %s | TP: %s | PYRAMIDING: 0" % (
        sym, richtung, _preis_text(sl), _preis_text(tp))


def _kurs_text(x):
    """Kurs fuer Menschen: rund 6 gueltige Stellen (3.2904999999999998 -> 3.2905)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "?"
    if not x > 0 or x != x or x == float("inf"):
        return "?"
    t = "%.6g" % x
    if "e" in t:
        t = ("%.12f" % x).rstrip("0").rstrip(".")
    return t


def _preis_text(x):
    """Preis ohne e-Notation (execute_nexus_trade liest nur Ziffern und Punkt); 0 = Python setzt ihn."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "0"
    if not x > 0 or x != x or x == float("inf"):
        return "0"
    stellen = max(2, 8 - len(str(int(x))))          # rund 8 gueltige Stellen, auch fuer 0.000012
    t = ("%.*f" % (stellen if x >= 1 else 12, x)).rstrip("0").rstrip(".")
    return t or "0"


# ---------------------------------------------------------------------------
# Gedaechtnis: Stimmen, Bewertung, Glaubwuerdigkeit, Beschluesse
# ---------------------------------------------------------------------------
class Gedaechtnis:
    def __init__(self, pfad):
        self.pfad = pfad
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS stimmen (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, sym TEXT, epic TEXT,
                mitglied TEXT, oy TEXT, guven INTEGER, preis REAL, atr_pct REAL,
                bewertet INTEGER DEFAULT 0, richtig INTEGER, rendite REAL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS beschluesse (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, sym TEXT, richtung TEXT,
                karar TEXT, grund TEXT, buy REAL, sell REAL, bekle REAL, antworten INTEGER)""")
            c.execute("CREATE INDEX IF NOT EXISTS ix_st_offen ON stimmen(bewertet, ts)")
            c.execute("CREATE INDEX IF NOT EXISTS ix_be_sym ON beschluesse(sym, ts)")

    @contextmanager
    def _conn(self):
        """Verbindung oeffnen, am Ende speichern und schliessen."""
        c = sqlite3.connect(self.pfad, timeout=10)
        try:
            with c:
                yield c
        finally:
            c.close()

    def speichern(self, sym, epic, stimmen, preis, atr_pct, ergebnis, karar, grund="", ts=None):
        ts = time.time() if ts is None else ts
        with self._lock, self._conn() as c:
            for s in stimmen:
                if s.get("ok"):
                    c.execute("INSERT INTO stimmen (ts, sym, epic, mitglied, oy, guven, preis, atr_pct) "
                              "VALUES (?,?,?,?,?,?,?,?)",
                              (ts, sym, epic, s["id"], s["oy"], s["guven"], float(preis or 0), float(atr_pct or 0)))
            c.execute("INSERT INTO beschluesse (ts, sym, richtung, karar, grund, buy, sell, bekle, antworten) "
                      "VALUES (?,?,?,?,?,?,?,?,?)",
                      (ts, sym, ergebnis.get("richtung") or "", karar, grund,
                       ergebnis["gewicht"][BUY], ergebnis["gewicht"][SELL], ergebnis["gewicht"][BEKLE],
                       ergebnis["antworten"]))

    def letzter_beschluss(self, sym, std):
        """Juengster Beschluss zu sym innerhalb der letzten std Stunden, sonst None."""
        if std <= 0:
            return None
        with self._conn() as c:
            r = c.execute("SELECT ts, richtung, karar, grund FROM beschluesse WHERE sym=? AND ts>=? "
                          "ORDER BY ts DESC LIMIT 1", (sym, time.time() - std * 3600)).fetchone()
        return None if not r else {"ts": r[0], "richtung": r[1], "karar": r[2], "grund": r[3]}

    def bewerten(self, preis_fn, std=24.0, faktor=0.25, jetzt=None):
        """Richtungs-Stimmen, die aelter als std Stunden sind, am heutigen Kurs messen.
        richtig = Kurs lief in Stimmrichtung weiter als faktor x Tagesspanne,
        falsch  = genauso weit dagegen, sonst unentschieden (zaehlt nicht).
        BEKLE-Stimmen werden nicht bewertet. Rueckgabe: Zahl bewerteter Stimmen."""
        jetzt = time.time() if jetzt is None else jetzt
        with self._conn() as c:
            offen = c.execute("SELECT id, epic, oy, preis, atr_pct FROM stimmen WHERE bewertet=0 AND ts<=?",
                              (jetzt - std * 3600,)).fetchall()
        if not offen:
            return 0
        kurse, n = {}, 0
        for sid, epic, oy, p0, atr in offen:
            if epic not in kurse:
                try:
                    kurse[epic] = float(preis_fn(epic) or 0)
                except Exception:
                    kurse[epic] = 0.0
            p1 = kurse[epic]
            if oy == BEKLE or not p0 or p0 <= 0:
                upd = (1, None, None, sid)
            elif p1 <= 0:
                continue                     # Kurs gerade nicht lesbar -> spaeter nochmal
            else:
                ret = (p1 - p0) / p0 * 100
                schwelle = max(0.1, faktor * float(atr or 0))
                gut = ret if oy == BUY else -ret
                richtig = 1 if gut > schwelle else (0 if gut < -schwelle else None)
                upd = (1, richtig, round(ret, 3), sid)
            with self._lock, self._conn() as c:
                c.execute("UPDATE stimmen SET bewertet=?, richtig=?, rendite=? WHERE id=?", upd)
            n += 1
        return n

    def bilanz(self):
        """{mitglied: (richtig, falsch)} aus allen bewerteten Richtungs-Stimmen."""
        with self._conn() as c:
            rows = c.execute("SELECT mitglied, SUM(richtig=1), SUM(richtig=0) FROM stimmen "
                             "WHERE bewertet=1 AND richtig IS NOT NULL GROUP BY mitglied").fetchall()
        return {m: (int(r or 0), int(f or 0)) for m, r, f in rows}

    def gewichte(self, ids=None):
        """Glaubwuerdigkeit 0.5 ... 1.5. Ohne Bilanz 1.0; Startwert zaehlt wie 10 Stimmen
        (5 richtig, 5 falsch), damit wenige Zufallstreffer das Gewicht kaum bewegen."""
        b = self.bilanz()
        out = {}
        for i in (ids or _IDS):
            r, f = b.get(i, (0, 0))
            out[i] = 0.5 + (r + 5.0) / (r + f + 10.0)
        return out


# ---------------------------------------------------------------------------
# Telegram-Bericht (direkt in der Bot-Sprache; KI-Begruendungen kommen schon in
# dieser Sprache, weil call_ai die Sprachanweisung anhaengt)
# ---------------------------------------------------------------------------
_TXT = {
    "de": {"titel": "🏛️ GREMIUM: {sym}", "kurs": "Kurs {kurs} | Technik Tag: {tech}",
           "stimmen": "Stimmen", "keine": "keine Antwort", "skip": "nicht gefragt (Quorum schon verfehlt)", "gew": "Gewichtet: BUY {b} · SELL {s} · BEKLE {w} (Mehrheit ab {m}, Antworten {a}/{n})",
           "beschluss": "✅ Beschluss: {r}", "vorsitz_ok": "👔 Vorsitz: ausführen", "vorsitz_stop": "👔 Vorsitz: gestoppt",
           "vorsitz_fehl": "👔 Vorsitz: keine Antwort - kein Trade",
           "beschlussunfaehig": "⏸️ Nicht beschlussfähig: nur {a} von {n} Antworten (mindestens {min})",
           "konflikt": "⏸️ Kein Trade: Gremium gespalten ({b}× BUY, {s}× SELL) - Senaryo 4",
           "keine_mehrheit": "⏸️ Keine Mehrheit - kein Trade",
           "w_kopf": "🏛️ GREMIUM - Glaubwürdigkeit (Stimmen nach {std} h am Kurs gemessen)",
           "w_zeile": "{name}: Gewicht {g} | richtig {r} / falsch {f}",
           "w_leer": "Noch keine bewerteten Stimmen - alle Gewichte 1.0.",
           "b_kopf": "Letzte Beschlüsse:",
           "s_kopf": "🏛️ NEXUS STATUS (Gremium entscheidet) | {zeit}",
           "s_konto": "Konto: {gesamt} EUR | verfügbar {frei} EUR | offen {upl} EUR | Positionen {npos}",
           "s_beschl": "Gremiumsbeschlüsse der letzten {std} h:",
           "s_leer": "Noch kein Beschluss in den letzten {std} h. Nächster Scan in etwa {naechst}.",
           "s_zeile": "{zeit} {sym}: {ergebnis} | BUY {b} · SELL {s} · BEKLE {w} | Antworten {a}/11",
           "s_fuss": "Gehandelt wird nur nach Gremiums-Mehrheit + Vorsitz. Einzelne Stimmen: /gremium",
           "erg_trade": "✅ {r} ausgeführt", "erg_vstop": "👔 {r} vom Vorsitz gestoppt", "erg_vfehlt": "👔 {r}, Vorsitz ohne Antwort",
           "erg_keine": "⏸️ keine Mehrheit", "erg_konflikt": "⏸️ gespalten", "erg_quorum": "⏸️ zu wenige Antworten",
           "budget": "🏛️ GREMIUM: {sym} nicht beraten - KI-Budget fast aufgebraucht ({n}/{max} Aufrufe in der letzten Stunde, je Markt nötig: {need}). Nächster Versuch beim nächsten Scan."},
    "en": {"titel": "🏛️ COMMITTEE: {sym}", "kurs": "Price {kurs} | Daily technicals: {tech}",
           "stimmen": "Votes", "keine": "no answer", "skip": "not asked (quorum already missed)", "gew": "Weighted: BUY {b} · SELL {s} · WAIT {w} (majority from {m}, answers {a}/{n})",
           "beschluss": "✅ Decision: {r}", "vorsitz_ok": "👔 Chair: execute", "vorsitz_stop": "👔 Chair: stopped",
           "vorsitz_fehl": "👔 Chair: no answer - no trade",
           "beschlussunfaehig": "⏸️ No quorum: only {a} of {n} answers (at least {min})",
           "konflikt": "⏸️ No trade: committee split ({b}× BUY, {s}× SELL) - scenario 4",
           "keine_mehrheit": "⏸️ No majority - no trade",
           "w_kopf": "🏛️ COMMITTEE - believability (votes measured against the price after {std} h)",
           "w_zeile": "{name}: weight {g} | right {r} / wrong {f}",
           "w_leer": "No rated votes yet - all weights 1.0.",
           "b_kopf": "Latest decisions:",
           "s_kopf": "🏛️ NEXUS STATUS (the committee decides) | {zeit}",
           "s_konto": "Account: {gesamt} EUR | available {frei} EUR | open {upl} EUR | positions {npos}",
           "s_beschl": "Committee decisions in the last {std} h:",
           "s_leer": "No decision in the last {std} h. Next scan in about {naechst}.",
           "s_zeile": "{zeit} {sym}: {ergebnis} | BUY {b} · SELL {s} · WAIT {w} | answers {a}/11",
           "s_fuss": "Trades only after a committee majority + chair. Single votes: /committee",
           "erg_trade": "✅ {r} executed", "erg_vstop": "👔 {r} stopped by the chair", "erg_vfehlt": "👔 {r}, chair did not answer",
           "erg_keine": "⏸️ no majority", "erg_konflikt": "⏸️ split", "erg_quorum": "⏸️ too few answers",
           "budget": "🏛️ COMMITTEE: {sym} not discussed - AI budget almost used up ({n}/{max} calls in the last hour, needed per market: {need}). Next try at the next scan."},
    "tr": {"titel": "🏛️ KURUL: {sym}", "kurs": "Fiyat {kurs} | Günlük teknik: {tech}",
           "stimmen": "Oylar", "keine": "yanıt yok", "skip": "sorulmadı (yeter sayı zaten tutmuyor)", "gew": "Ağırlıklı: BUY {b} · SELL {s} · BEKLE {w} (çoğunluk {m}, yanıt {a}/{n})",
           "beschluss": "✅ Karar: {r}", "vorsitz_ok": "👔 Başkan: uygula", "vorsitz_stop": "👔 Başkan: durdurdu",
           "vorsitz_fehl": "👔 Başkan: yanıt yok - işlem yok",
           "beschlussunfaehig": "⏸️ Karar yeter sayısı yok: {n} üyeden yalnızca {a} yanıt (en az {min})",
           "konflikt": "⏸️ İşlem yok: kurul bölündü ({b}× BUY, {s}× SELL) - Senaryo 4",
           "keine_mehrheit": "⏸️ Çoğunluk yok - işlem yok",
           "w_kopf": "🏛️ KURUL - güvenilirlik (oylar {std} sa sonra fiyatla ölçülür)",
           "w_zeile": "{name}: ağırlık {g} | doğru {r} / yanlış {f}",
           "w_leer": "Henüz değerlendirilmiş oy yok - tüm ağırlıklar 1.0.",
           "b_kopf": "Son kararlar:",
           "s_kopf": "🏛️ NEXUS DURUM (kararı kurul verir) | {zeit}",
           "s_konto": "Hesap: {gesamt} EUR | kullanılabilir {frei} EUR | açık {upl} EUR | pozisyon {npos}",
           "s_beschl": "Son {std} saatin kurul kararları:",
           "s_leer": "Son {std} saatte karar yok. Sonraki tarama yaklaşık {naechst} sonra.",
           "s_zeile": "{zeit} {sym}: {ergebnis} | BUY {b} · SELL {s} · BEKLE {w} | yanıt {a}/11",
           "s_fuss": "İşlem yalnızca kurul çoğunluğu + başkan onayıyla açılır. Tek tek oylar: /kurul",
           "erg_trade": "✅ {r} uygulandı", "erg_vstop": "👔 {r} başkan durdurdu", "erg_vfehlt": "👔 {r}, başkan yanıt vermedi",
           "erg_keine": "⏸️ çoğunluk yok", "erg_konflikt": "⏸️ kurul bölündü", "erg_quorum": "⏸️ yeter sayı yok",
           "budget": "🏛️ KURUL: {sym} görüşülmedi - yapay zekâ bütçesi neredeyse doldu (son bir saatte {n}/{max} çağrı, piyasa başına gereken: {need}). Bir sonraki taramada yeniden denenecek."},
}
_EMOJI = {BUY: "🟢", SELL: "🔴", BEKLE: "⚪"}


def _t(lang):
    return _TXT.get(lang, _TXT["tr"])


def bericht(sym, stimmen, ergebnis, vorsitz_erg=None, lang="tr", kurs=0, tech="", min_antworten=8):
    T = _t(lang)
    z = [T["titel"].format(sym=sym)]
    if kurs or tech:
        z.append(T["kurs"].format(kurs=_kurs_text(kurs), tech=tech or "-"))
    z.append("")
    for s in stimmen:
        if s["ok"]:
            z.append("%s %s: %s (%d) - %s" % (_EMOJI[s["oy"]], s["name"], s["oy"], s["guven"], _kurz(s["gerekce"], 160)))
        elif s.get("uebersprungen"):
            z.append("⚫ %s: %s" % (s["name"], T["skip"]))
        else:
            z.append("⚫ %s: %s" % (s["name"], T["keine"]))
    g = ergebnis["gewicht"]
    z += ["", T["gew"].format(b="%.1f" % g[BUY], s="%.1f" % g[SELL], w="%.1f" % g[BEKLE],
                              m="%.1f" % ergebnis["mehrheit"], a=ergebnis["antworten"], n=ergebnis["mitglieder"])]
    if ergebnis["richtung"]:
        z.append(T["beschluss"].format(r=ergebnis["richtung"]))
        if vorsitz_erg is not None:
            if not vorsitz_erg.get("ok"):
                z.append(T["vorsitz_fehl"])
            else:
                z.append((T["vorsitz_ok"] if vorsitz_erg["karar"] == "UYGULA" else T["vorsitz_stop"])
                         + (" - " + vorsitz_erg["gerekce"] if vorsitz_erg.get("gerekce") else ""))
            if vorsitz_erg.get("wer"):
                z[-1] = z[-1].replace(":", " (%s):" % vorsitz_erg["wer"], 1)
    else:
        grund = ergebnis.get("grund") or "keine_mehrheit"
        z.append(T[grund].format(a=ergebnis["antworten"], n=ergebnis["mitglieder"], min=min_antworten,
                                 b=ergebnis["anzahl"][BUY], s=ergebnis["anzahl"][SELL]))
    return "\n".join(z)


def status_bericht(gd, konto=None, lang="tr", std=48, letzte=12, naechst="?", extra=""):
    """v16.0.4: /status im Gremium-Modus - Konto + letzte Beschluesse. Kein KI-Aufruf."""
    T = _t(lang)
    z = [T["s_kopf"].format(zeit=time.strftime("%d.%m %H:%M"))]
    if konto:
        z.append(T["s_konto"].format(**konto))
    with gd._conn() as c:
        rows = c.execute("SELECT ts, sym, richtung, karar, grund, buy, sell, bekle, antworten FROM beschluesse "
                         "WHERE ts>=? ORDER BY ts DESC LIMIT ?", (time.time() - std * 3600, int(letzte))).fetchall()
    z.append("")
    if not rows:
        z.append(T["s_leer"].format(std=int(std), naechst=naechst))
    else:
        z.append(T["s_beschl"].format(std=int(std)))
        for ts, sym, ri, ka, gr, b, s_, w, a in rows:
            if ka == "UYGULA":
                erg = T["erg_trade"].format(r=ri)
            elif gr == "vorsitz_stop":
                erg = T["erg_vstop"].format(r=ri)
            elif gr == "vorsitz_fehlt":
                erg = T["erg_vfehlt"].format(r=ri)
            elif gr == "konflikt":
                erg = T["erg_konflikt"]
            elif gr == "beschlussunfaehig":
                erg = T["erg_quorum"]
            else:
                erg = T["erg_keine"]
            z.append(T["s_zeile"].format(zeit=time.strftime("%d.%m %H:%M", time.localtime(ts)), sym=sym, ergebnis=erg,
                                         b="%.1f" % (b or 0), s="%.1f" % (s_ or 0), w="%.1f" % (w or 0), a=a or 0))
    if extra:
        z += ["", extra]
    z += ["", T["s_fuss"]]
    return "\n".join(z)


def budget_zeile(sym, n, maxi, need, lang="tr"):
    return _t(lang)["budget"].format(sym=sym, n=n, max=maxi, need=need)


def gewichte_bericht(gd, lang="tr", std=24, letzte=8):
    T = _t(lang)
    z = [T["w_kopf"].format(std=int(std) if float(std).is_integer() else std), ""]
    b = gd.bilanz()
    gw = gd.gewichte()
    if not b:
        z.append(T["w_leer"])
    for m in MITGLIEDER:
        r, f = b.get(m["id"], (0, 0))
        z.append(T["w_zeile"].format(name=m["name"], g="%.2f" % gw[m["id"]], r=r, f=f))
    with gd._conn() as c:
        rows = c.execute("SELECT ts, sym, richtung, karar, grund FROM beschluesse ORDER BY ts DESC LIMIT ?",
                         (int(letzte),)).fetchall()
    if rows:
        z += ["", T["b_kopf"]]
        for ts, sym, ri, ka, gr in rows:
            z.append("%s %s %s %s%s" % (time.strftime("%d.%m %H:%M", time.localtime(ts)), sym, ri or "-", ka,
                                        (" (%s)" % gr) if gr else ""))
    return "\n".join(z)


# ---------------------------------------------------------------------------
# Rollenkarten als Dokument
# ---------------------------------------------------------------------------
def doku():
    z = ["# NEXUS Gremium – Rollenkarten (v16.0.4)", "",
         "Diese Datei wird aus `nexus_gremium.py` erzeugt (`python3 nexus_gremium.py --doku > docs/GREMIUM.md`). "
         "Genau dieser Text geht als Anweisung an die KI. Wer eine Karte ändern will, ändert `MITGLIEDER` in "
         "`nexus_gremium.py` und erzeugt die Datei neu.", "",
         "Grundlage: `mentor_name.txt` (KhungFu/kisilerim) und die veröffentlichten Grundsätze der Personen, "
         "in eigenen Worten zusammengefasst – keine Zitate.", "",
         "## Ablauf", "",
         "1. Python sucht Kandidaten über alle Märkte und baut für jeden ein Dossier mit echten Daten.",
         "2. Jedes Mitglied bekommt dasselbe Dossier in einem eigenen KI-Aufruf und sieht die anderen Stimmen nicht.",
         "3. Python zählt: Mehrheit 6 von 11 (Krypto am Wochenende 5 von 11), gewichtet nach Glaubwürdigkeit. "
         "Mindestens 8 gültige Antworten. Stimmen 3 oder mehr für BUY und 3 oder mehr für SELL, wird nicht gehandelt (Senaryo 4).",
         "4. Der Vorsitz prüft den Beschluss gegen die Daten: ausführen oder stoppen, die Richtung darf er nicht ändern.",
         "5. Python-Sperren (Stop, Gruppen-Limit, Spread, Max. Positionen, Wiedereinstieg) gelten immer.",
         "6. Jede Stimme wird nach 24 h am Kurs gemessen; daraus entsteht das Gewicht 0,5 bis 1,5.", "",
         "## Rahmen für alle Mitglieder", "", _RAHMEN, ""]
    for m in MITGLIEDER:
        z += ["## %s – %s" % (m["name"], m["rolle"]), "", "**Grundsätze**", ""]
        z += ["- " + g for g in m["grundsaetze"]]
        z += ["", "**Schaut auf:** " + m["schaut_auf"], "", "**Stimmt BEKLE, wenn:**", ""]
        z += ["- " + g for g in m["bekle_wenn"]]
        z.append("")
    z += ["## Vorsitz", "", "```", _VORSITZ_SYSTEM, "```", ""]
    return "\n".join(z)


if __name__ == "__main__":
    if "--doku" in sys.argv:
        print(doku())
    else:
        print(__doc__)
