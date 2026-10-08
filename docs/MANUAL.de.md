# NEXUS CEO – Betriebsanleitung (v15.23)

NEXUS CEO ist ein Telegram-Bot, der über die Capital.com-API selbstständig CFD-Positionen auf Rohstoffe und Krypto eröffnet, absichert und in Stufen wieder verkauft. Diese Anleitung beschreibt den Stand v15.23 so, wie er im Code steht. Sie beschreibt die Technik und ist keine Anlageempfehlung. CFD-Handel kann zum Verlust des eingesetzten Geldes führen; nutze zuerst ein Demo-Konto.

Am Ende stehen drei Anhänge: Spread-Tabelle (A), Kurzreferenz für den Alltag (B) und Glossar (C). Wenn du das Handbuch mit `/handbuch` in Telegram abrufst, hängt der Bot außerdem Anhang L an: deine Einstellungen von jetzt.

Andere Sprachen: [English](MANUAL.en.md) · [Türkçe](MANUAL.tr.md)

## 1. Erste Einrichtung

Du brauchst einen Rechner, der dauernd läuft (zum Beispiel einen Raspberry Pi), Python 3.10 oder neuer (getestet mit 3.11), ein Capital.com-Konto und einen eigenen Telegram-Bot.

1. Dateien in einen Ordner legen, zum Beispiel `~/nexus/`: `nexus_ceo.py`, `nexus_lang.py`, `nexus_diagnose.py`, `requirements.txt`, `.env.example`. Freiwillig dazu: `capital_markets_config.py` mit der Liste deiner Märkte. Fehlt sie, handelt der Bot eine eingebaute Liste mit neun Märkten (EUR/USD, Gold, Silber, Crude, Brent, BTC, ETH, XRP, SOL).
2. Python-Pakete installieren: `pip install -r requirements.txt`
3. Telegram-Bot anlegen: in Telegram mit `@BotFather` schreiben, `/newbot` senden, den Token aufheben.
4. Capital.com: im Konto unter den Einstellungen einen API-Key erzeugen. Dabei vergibst du ein eigenes Passwort für den Key. In die `.env` gehören der Key (`CAPITAL_API_KEY`), deine Anmelde-E-Mail (`CAPITAL_IDENTIFIER`) und das Passwort (`CAPITAL_PASSWORD`). Welches Passwort Capital.com hier erwartet (das des Keys oder das des Kontos), steht in der API-Anleitung von Capital.com; lehnt der Bot die Anmeldung ab, das andere versuchen. Für den Anfang das Demo-Konto verwenden.
5. Im Capital.com-Konto den Hedging-Modus ausschalten. Sonst kann der Bot keine Teilverkäufe machen.
6. Mindestens einen Gemini-Key (Google AI Studio) und am besten einen Groq-Key als Ersatz besorgen.
7. `.env.example` nach `.env` kopieren und die Zugangsdaten eintragen: `cp .env.example .env`, dann `chmod 600 .env`.
8. Bot starten: `python3 nexus_ceo.py`
9. Dem Bot in Telegram irgendetwas schreiben. Solange `MY_CHAT_ID` leer ist, antwortet er nur mit deiner Chat-ID. Diese Zahl als `MY_CHAT_ID` in die `.env` eintragen und den Bot neu starten.
10. Beim nächsten Start fragt der Bot nach der Sprache. Sprache antippen, bestätigen. Der Bot schreibt `BOT_LANGUAGE` selbst in die `.env`.

Für den Dauerbetrieb den Bot als systemd-Dienst einrichten; eine Vorlage liegt in `systemd/nexus_ceo.service.example`.

Die `.env` enthält alle Zugangsdaten. Gib sie nie weiter und lade sie nie hoch. Die Datei `.gitignore` im Paket sorgt dafür, dass Git sie ignoriert.

## 2. Sprache

Der Bot spricht Deutsch, Englisch und Türkisch. Die Texte stehen in `nexus_lang.py`; der Bot übersetzt jede Nachricht erst beim Senden.

- **Erster Start:** Steht kein `BOT_LANGUAGE` in der `.env`, schickt der Bot drei Tasten: Deutsch, English, Türkçe. Nach dem Antippen fragt er nach, erst die Bestätigung speichert die Wahl.
- **Später ändern:** `/sprache` senden. Oder in der `.env` `BOT_LANGUAGE=de`, `en` oder `tr` eintragen und neu starten.
- **Befehle:** Jeder Befehl hat in jeder Sprache einen Namen. Alle Namen funktionieren immer, egal welche Sprache eingestellt ist. Die türkischen Namen sind die ursprünglichen.
- **KI-Texte:** Die KI bekommt den Auftrag, in der gewählten Sprache zu schreiben. Die TRADE-Zeilen bleiben in ihrem festen Format.
- **Fehlende Übersetzung:** Texte ohne Regel sendet der Bot im Original und schreibt sie in `nexus_lang_missing.log`. Eine Übersetzung trägst du in `nexus_lang.py` unter `RULES` nach; `python3 nexus_lang.py` prüft die Datei.
- `BOT_LANGUAGE=orig` schaltet die Übersetzung ab.

## 3. Starten, stoppen, prüfen

Als systemd-Dienst `nexus_ceo.service`:

| Aufgabe | Befehl |
| --- | --- |
| Neu starten (nach jeder Änderung an `.env` oder Code) | `sudo systemctl restart nexus_ceo.service` |
| Stoppen | `sudo systemctl stop nexus_ceo.service` |
| Starten | `sudo systemctl start nexus_ceo.service` |
| Läuft er? | `sudo systemctl status nexus_ceo.service --no-pager \| head -10` |
| Letzte Zeilen des Dienstes | `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Log mitlesen | `tail -f nexus_ceo.log` |
| Code vor dem Start prüfen | `python3 -m py_compile nexus_ceo.py` |

Nach jedem Start schickt der Bot eine Startmeldung. Darin stehen die Version, das Scan-Intervall, die Stop-Regel und die Wiedereinstiegs-Sperre. Stimmt ein Wert nicht mit der `.env` überein, wurde die Datei nicht gelesen oder der Dienst nicht neu gestartet.

Änderungen an der `.env` wirken erst nach einem Neustart. Ein gestoppter Bot zieht keine Stops nach und verkauft keine Stufen; die bei Capital.com hinterlegten Stop-Loss- und Take-Profit-Kurse gelten aber weiter.

## 4. Telegram-Befehle

Der Bot nimmt Befehle, Text und Tasten nur aus dem Chat `MY_CHAT_ID` an. Nachrichten aus anderen Chats ignoriert er.

### Stand und Analyse

| Befehl | Taste | Was passiert |
| --- | --- | --- |
| `/position` | 📍 Positionen | Positionsbericht: je Position Größe, Einstieg, Kurs, Stop Loss, Take Profit, Tagesspanne, Tagesziel, Stop-Abstand in Tagesspannen und Mirror-TP-Stufen mit Status |
| `/status` | 📊 Status | Volle KI-Analyse mit Gremium-Abstimmung. Verbraucht eine Gemini-Anfrage |
| `/signale` | 📈 Signale | Technische Signale (MA 9/26, ADX, RSI) |
| `/stats` | 🧮 Statistik | Trade-Statistik und Ergebnis je Asset aus der Bot-Datenbank |
| `/verluste` | 💸 Verluste | Verlustzähler von heute je Symbol |
| `/sperren` | 🔒 Sperren | Aktive Handelssperren |
| `/volatilitaet` | – | Schwarzer-Schwan-Prüfung jetzt ausführen |
| `/update_models` | – | KI-Modelle prüfen: Gemini-Kette und abgelehnte Keys, dazu Modell, Kette und Sperren von Groq, Qwen und Nvidia. `/update_models best` wechselt auf das größte Modell, das die Prüfung besteht |
| `/diagnose` | 🔎 Diagnose | Diagnose der letzten 7 Tage: Kurzfassung als Nachricht, ganzer Bericht als Textdatei. `/diagnose 3` = nur 3 Tage. Nur lesend |
| `/handbuch` | – | Das komplette Handbuch als Datei in deiner Sprache, am Ende mit den Einstellungen, mit denen der Bot jetzt läuft. `/handbuch en` = Englisch, `de` = Deutsch, `tr` = Türkisch. Fehlt die Datei neben dem Bot, lädt er sie von GitHub |
| `/sprache` | – | Sprache wählen |
| `/hilfe` | 📋 Menü | Befehlsübersicht |

### Positionen steuern

| Befehl | Was passiert |
| --- | --- |
| `/schliessen GOLD` | Schließt alle Positionen dieses Symbols sofort |
| `/schliessen ALLE` | Fragt nach; erst `/schliessen ALLE BESTAETIGEN` schließt wirklich alle Positionen |
| `/manuell GOLD BUY 100` | Eröffnet sofort eine Position über 100 EUR, ohne Gate-Keeper und Gremium. Stop und Ziel setzt der Bot selbst |
| `/manuell GOLD BUY 100 1900 2100` | Dasselbe mit eigenem Stop Loss (1900) und Take Profit (2100) |
| `/sl_weiten` | Zeigt, welche Stops offener Positionen im Tagesrauschen liegen. Ändert nichts |
| `/sl_weiten ja` | Setzt diese Stops auf den Mindestabstand. Nur weiter weg, nie enger; der Take Profit bleibt |

### Recherche und Pflege

| Befehl | Was passiert |
| --- | --- |
| `/backtest GOLD 200` | Backtest für ein Symbol über 200 Tage |
| `/deepdive GOLD HOUR_4 30` | Detailanalyse für Symbol, Zeitrahmen und Tage |
| `/nachrichten OIL 7` | Gesammelte Nachrichten zu einem Symbol aus den letzten 7 Tagen (Taste 📰 Nachrichten) |
| `/news_sammeln` | Nachrichten jetzt sammeln |
| `/quellen` | Zuverlässigkeits-Werte der Nachrichtenquellen |
| `/spread` | Spreads aller Märkte messen und in die Markt-Konfiguration schreiben |
| `/db_bereinigen` | Alte oder kaputte Nachrichten aus der Datenbank löschen |
| `/vergessen` | Deine gespeicherten Notizen löschen |

### Text ohne Befehl

Alles, was du ohne Schrägstrich schreibst, speichert der Bot als Notiz für die KI-Analyse. Die Hilfe des Bots nennt 48 Stunden Gültigkeit. Die KI liest die Notiz mit; sie ist ein Hinweis, keine Anweisung, an die sich der Bot halten muss.

**Handelssperre per Text funktioniert derzeit nicht.** Der Code sieht vor, dass ein Satz wie `Gold nicht handeln` das Symbol sofort sperrt. Wegen eines Fehlers erkennt der Bot das Symbol im Satz aber nie (siehe Abschnitt 15). Verlass dich nicht darauf. Wenn der Bot ein Symbol nicht handeln soll, trage in `TRADING_ASSETS` nur die Symbole ein, die er handeln darf, und starte neu. Wenn er gar nicht handeln soll, stoppe den Dienst.

## 5. Wie der Bot handelt

Der Bot handelt in Scans. Zwischen zwei Scans liegen `SCAN_INTERVAL_SEC` Sekunden (Standard 21600, also 6 Stunden). Ein Scan läuft so ab:

1. **Abgleich.** Der Bot gleicht seine Merker mit den offenen Positionen bei Capital.com ab und prüft den Tages-Verlust-Stopp.
2. **Gate-Keeper.** Für jedes Symbol berechnet Python fünf technische Punkte: MA-Kreuz 9/26, ADX über 15, RSI passend zur Richtung, Bollinger-Lage, Nähe zu einem Fibonacci-Niveau. Rohstoffe können einen sechsten Punkt bekommen (Rogers-Filter, EMA 50/200). Weiter kommt nur, wer mindestens 5 Punkte hat. Krypto braucht damit 5 von 5.
3. **Gremium.** Fünf feste Regelsätze (Cihat, Rogers, Dalio, Taleb, Soros) stimmen mit JA oder NEIN. Nötig sind 4 von 5, bei Krypto 3 von 5.
4. **KI-Analyse.** Gemini bekommt die Kandidaten samt Nachrichten, Wetter- und Makrodaten und antwortet mit TRADE-Zeilen. Liefert Gemini nicht, formatiert ein Ersatz-Anbieter nur die vom Gate-Keeper freigegebenen Kandidaten.
5. **Prüfungen vor der Order.** Jede TRADE-Zeile läuft durch die Sperren aus Abschnitt 8. Im Ersatzbetrieb darf nur das Symbol und die Richtung durch, die der Gate-Keeper in diesem Scan freigegeben hat.
6. **Order.** Der Bot berechnet die Größe selbst, schiebt den Stop auf den Mindestabstand, schickt die Order und prüft nach 8 Sekunden, ob die Position wirklich im Depot steht.

Die Signale für Rohstoffe kommen aus Tageskerzen. Sie ändern sich im Lauf eines Tages kaum, deshalb liefert jeder Scan meist dieselben Kandidaten.

### Was bei einer schon offenen Position passiert

- **Gleiche Richtung:** Der Bot stockt nur auf, wenn die Position mindestens 2 % im Gewinn ist (Pyramiding). Sonst steht im Protokoll „… Pyramiding übersprungen: …“.
- **Gegenrichtung:** Kommt im Scan eine TRADE-Zeile, deren Richtung der offenen Position widerspricht (Position BUY, Zeile SELL oder umgekehrt), schließt der Bot alle Positionen dieses Symbols. Eine Gegenposition eröffnet er nicht.

So läuft das ab:

1. Die Zeile muss durch die Sperren aus Abschnitt 8: Tages-Verlust-Stopp, weniger als `MAX_POSITIONEN` offene Positionen, Markt offen, Spread, Verlust-Sperre.
2. Der Bot schließt alle Positionen des Symbols. Jede geschlossene Position, die im Minus war, zählt als Verlust für die Verlust-Sperre.
3. Im Protokoll steht „↩️ …: Gegensignal …->… - nur geschlossen, keine Gegenposition“. Schlägt das Schließen fehl, steht dort der Grund.

Bleibt das Gegensignal bestehen, eröffnet der nächste Scan die neue Richtung als normale Position, mit allen Prüfungen. Bis v15.20 schickte der Bot sofort eine Gegen-Order ohne diese Prüfungen.

Auf ein Gegensignal reagiert nur der Scan. Der Exit-Monitor schließt nach seinen eigenen Regeln.

### Was daneben ständig läuft

| Takt | Aufgabe |
| --- | --- |
| alle 5 Minuten | Schutz-Lauf: Schwarzer Schwan, Breakeven, Mirror-TP, Trailing-Stop, Meldung geschlossener Positionen |
| alle 15 Minuten | Tagesziel-Wächter: fragt mit Ja/Nein-Tasten, ob eine Position am Tagesziel verkauft werden soll |
| alle 30 Minuten | Exit-Monitor: schließt bei `AUTO_EXIT=true` eine Position, wenn 3 von 5 Exit-Regeln zustimmen |
| alle 60 Minuten | Nachrichten sammeln (RSS, X) |
| alle 6 Stunden | Gemini-Modellliste aktualisieren |

Diese Läufe brauchen kein KI-Kontingent.

## 6. Positionsgröße

Bei automatischen Trades bestimmt allein die `.env` die Größe; die Zahl, die die KI hinter SIZE schreibt, wird nicht verwendet.

1. Basis = Depot × `POSITION_SIZE_PCT`, mindestens `MIN_POSITION_EUR`.
2. Obergrenze = der kleinste dieser drei Werte: `MAX_POSITION_EUR` (wenn gesetzt), die Risk-Parity-Grenze (zwei Drittel des Depots) und 50 % des Depots.
3. Bei Epics mit BTC, ETH, SOL oder XRP im Namen wird der Betrag halbiert.
4. Der Betrag wird mit dem Live-Kurs und dem EUR/USD-Kurs in Einheiten umgerechnet.
5. Liegt das Ergebnis unter der Mindestgröße der Börse, nimmt der Bot die Mindestgröße. Kostet schon die Mindestgröße mehr als die Obergrenze, gibt es keinen Trade.

Kann der Bot Depot oder Kurs nicht lesen, eröffnet er bei automatischen Trades nichts.

Beim manuellen Trade gilt dein EUR-Betrag. Er wird auf `MIN_POSITION_EUR` angehoben und bei 50 % des Depots gekappt; `MAX_POSITION_EUR` greift dort nicht. Die Halbierung aus Schritt 3 gilt auch manuell.

## 7. Stop Loss und Gewinnmitnahme

Jede Position bekommt bei der Eröffnung einen Stop Loss und einen Take Profit bei Capital.com. Danach verwaltet der Schutz-Lauf sie alle 5 Minuten.

### Stop Loss beim Einstieg

Die KI schlägt einen Stop vor; der Bot schiebt ihn auf einen Mindestabstand, wenn er zu nah am Kurs liegt.

- **Mindestabstand** = Tagesspanne (Tages-ATR über 14 Tage) × `SL_ATR_MULT` (Standard 1.0).
- **Untergrenze:** nie näher als 1,5 % (Krypto am Wochenende 3,75 %). Dieser Wert gilt auch, wenn die Tagesspanne nicht abrufbar ist.
- **Obergrenze:** höchstens `SL_MAX_PCT` (Standard 6 %), damit der Stop vor der Schwarzer-Schwan-Schwelle greift.
- Liegt der KI-Stop weiter weg als der Mindestabstand, bleibt er. Liegt er mehr als 8 % weg, wird er ersetzt.

Die Regel gilt für automatische Trades. Der manuelle Trade setzt ohne eigene Angabe den Stop auf 2 × Stunden-ATR und das Ziel auf das Dreifache dieses Abstands.

### Take Profit beim Einstieg

Der Take Profit kommt von der KI. Fehlt er oder liegt er näher als 0,3 % am Kurs, setzt der Bot 90 % der Tagesspanne.

### Was nach dem Einstieg passiert

| Auslöser | Was der Bot tut |
| --- | --- |
| Kurs erreicht Einstieg ± 0,5 × Stunden-ATR | Mirror-TP Stufe 1: verkauft 25 % der ursprünglichen Größe |
| Kurs erreicht ± 1,0 × Stunden-ATR | Mirror-TP Stufe 2: weitere 25 % |
| Kurs erreicht ± 1,5 × Stunden-ATR | Mirror-TP Stufe 3: weitere 25 % |
| Gewinn ab 1,0 % | Breakeven: Stop auf den Einstiegskurs (plus 0,03 %) |
| Gewinn ab 1,5 % | Trailing-Stop: 5 % hinter dem besten Kurs, wird nur enger gezogen |
| Gewinn ab 2 % bei mehreren Positionen im selben Symbol | Schließt die kleinste Position |
| Gewinn erreicht 90 % der Tagesspanne | Tagesziel: der Bot fragt mit Ja/Nein-Tasten, ob er verkaufen soll |
| Kurs erreicht den Take Profit | Capital.com schließt den Rest |

Ein Stunden-ATR ist bei Rohstoffen etwa ein Fünftel der Tagesspanne. Die drei Stufen liegen damit bei etwa 0,1, 0,2 und 0,3 Tagesspannen, der Stop bei einer ganzen. Gewinne je Stufe sind deshalb deutlich kleiner als ein Verlust am Stop.

### Regeln für den Teilverkauf

- Verkauft wird mindestens die Mindestgröße der Börse, auch wenn 25 % kleiner wären.
- Bliebe danach weniger als die Mindestgröße übrig, verkauft der Bot den ganzen Rest. Eine kleine Position kann deshalb schon mit Stufe 2 komplett geschlossen sein.
- Teilverkäufe funktionieren nur, wenn der Hedging-Modus im Capital.com-Konto ausgeschaltet ist.
- Bei jeder Stop-Änderung sendet der Bot den Take Profit mit. Sonst löscht Capital.com ihn.

### Stops offener Positionen

Neue Werte für `SL_ATR_MULT` gelten nur für neue Positionen. `/sl_weiten` zeigt, welche offenen Stops näher liegen als der Mindestabstand, `/sl_weiten ja` setzt sie weiter weg. Enger stellen geht nur von Hand in der Capital-App.

## 8. Schutzregeln und Sperren

Diese Regeln prüft Python selbst; keine KI kann sie übergehen. „Fest im Code“ heißt: nicht über die `.env` einstellbar.

### Vor einer neuen Position

| Regel | Schwelle | Wirkung | Stellschraube |
| --- | --- | --- | --- |
| Maximale Positionen | 5 offene Positionen | Keine neue Position. Bei 5 oder mehr auch kein Aufstocken und kein Drehen | `MAX_POSITIONEN` |
| Wiedereinstiegs-Sperre | 6 Stunden nach einer Schließung | Kein neuer Einstieg in dasselbe Symbol in derselben Richtung | `WIEDEREINSTIEG_SPERRE_STD` |
| Verlust-Sperre | 3 Stop-Loss-Verluste je Symbol und Tag | Symbol für heute gesperrt; ab dem ersten Verlust eine Warnung. Ein Stop am Einstieg zählt nicht | `MAX_VERLUSTE_PRO_TAG` |
| Tages-Verlust-Stopp | Depotwert 5 % oder 40 EUR unter dem Tageshoch | Heute keine neuen Trades | fest im Code |
| Spread | Live-Spread über `MAX_SPREAD` | Trade abgelehnt | `MAX_SPREAD` |
| Markt geschlossen | laut Capital.com | Keine Order, Meldung mit Öffnungszeit | – |
| Margin | Trade bräuchte mehr als 90 % des verfügbaren Geldes | Trade abgelehnt | fest im Code |
| Plausibilität | Stop oder Ziel auf der falschen Seite des Kurses, oder kein Live-Kurs | Trade verworfen | – |
| Handelssperre | Wochen-Lernlauf (montags 6 Uhr): Symbol, Richtung und Wochentag mit Trefferquote unter 33 % | Symbol gesperrt bis zum Neustart. Wirkt nur bei Symbolen ohne Unterstrich im Namen (GOLD ja, OIL_CRUDE nein) | fest im Code |
| Wochenende | Samstag und Sonntag | Nur Krypto, höchstens 3 Krypto-Positionen | fest im Code |
| Krypto-Nachtsperre | 23 bis 6 Uhr | Standard: aus | `KRYPTO_NACHT_SPERRE` |

### Für offene Positionen

| Regel | Schwelle | Wirkung | Stellschraube |
| --- | --- | --- | --- |
| Schwarzer Schwan Stufe 1 | Position 8 % im Minus | KI-Notfallentscheidung: halten oder schließen | fest im Code |
| Schwarzer Schwan Stufe 2 | Position 12 % im Minus | Position wird automatisch geschlossen | fest im Code |
| Schwarzer Schwan Stufe 3 | Eine Position 18 % im Minus | Alle Positionen werden geschlossen | fest im Code |
| Auto-Exit | 3 von 5 Exit-Regeln (Signalwechsel, stark negative Nachrichten, Risk-off) | Position wird geschlossen | `AUTO_EXIT` |

Mit `AUTO_EXIT=false` schließt der Exit-Monitor nicht selbst, sondern schickt nur eine Empfehlung.

## 9. KI-Anbieter

Die Hauptanalyse macht Gemini. Liefert Gemini nichts, übernimmt ein Ersatz-Anbieter, der aber nur die vom Gate-Keeper freigegebenen Kandidaten in TRADE-Zeilen fassen darf.

### Gemini-Modellkette

Jede Anfrage läuft über höchstens 4 Modelle (`GEMINI_CHAIN_MAX`): zuerst das Modell aus `GEMINI_MODEL_1`, dann die aktuellen Flash-Modelle aus Googles Live-Liste. Je Modell probiert der Bot alle nutzbaren Keys.

| Antwort von Google | Was der Bot tut |
| --- | --- |
| 401, Key ungültig | Key wird 6 Stunden nicht mehr benutzt; nächster Key |
| 429 Tageslimit | Nächster Key. Sind alle gültigen Keys am Limit, ruht das Modell bis zum Reset (Mitternacht US-Pazifikzeit) und das nächste Modell rückt in die Kette |
| 429 Minutenlimit, 403 | Nächster Key |
| 503 überlastet | Ein zweiter Versuch nach 6 Sekunden (`GEMINI_503_PAUSE`), dann nächstes Modell |
| 404 oder kein Gratis-Kontingent | Modell 24 Stunden gesperrt, Modellliste wird neu geholt |
| anderer Fehler | Gemini für diese Anfrage aufgegeben |

Die Modellliste aktualisiert sich alle 6 Stunden selbst; `/update_models` holt sie sofort und zeigt abgelehnte Keys mit den letzten vier Zeichen.

Keys aus demselben Google-Projekt teilen sich ein Kontingent; mehrere Keys aus einem Projekt bringen nicht mehr Anfragen als einer. Das Gratis-Kontingent ist klein. Je kürzer das Scan-Intervall, desto öfter läuft der Bot über den Ersatz-Anbieter.

### Ersatz-Anbieter

Die Reihenfolge steht in `PROVIDER_ORDER`. Das lokale Ollama-Modell steuert `OLLAMA_PRIORITY`:

- `last`: Ollama nur, wenn alle Cloud-Anbieter ausfallen.
- `first`: Ollama antwortet vor allen anderen, sobald es auf dem Rechner läuft.
- `only`: nur Ollama.

Im Ersatzbetrieb legt die KI nur Stop und Ziel fest oder lehnt einen Kandidaten ab. Symbol und Richtung kommen vom Gate-Keeper, die Größe aus der `.env`, und der Stop wird auf den Mindestabstand geschoben. Die Telegram-Meldung nennt immer „Groq“, auch wenn ein anderer Anbieter geantwortet hat; welcher es war, steht im Log als `[OK] ...`.

### Modelle der Ersatz-Anbieter (ab v15.22)

Groq, OpenRouter und Nvidia nehmen Modelle immer wieder aus dem Programm. Bis v15.21 lief jeder Anbieter mit dem einen Modell aus der `.env` und fiel aus, sobald es das Modell nicht mehr gab. Jetzt hält der Bot die Modelle selbst aktuell, nach demselben Verfahren wie swarm.py:

- **Kette je Anfrage.** Der Bot fragt zuerst das Modell aus der `.env`, danach bis zu drei Ersatzmodelle aus der Modellliste des Anbieters (`AI_CHAIN_MAX`). Bei 401, 403 oder 429 wechselt er den Key; sind alle Keys durch, das Modell. Bei Überlastung oder leerer Antwort wechselt er sofort das Modell.
- **Totes Modell.** Meldet der Anbieter, dass es das Modell nicht mehr gibt (404, 410, „does not exist“, „No endpoints found“), sperrt der Bot es für 24 Stunden und stößt eine Prüfung an.
- **Ersatz.** Die Prüfung holt die Modellliste, sortiert Nicht-Chat-Modelle aus und testet die besten Kandidaten mit einem kurzen echten Aufruf. Das erste Modell, das antwortet, wird Hauptmodell: Der Bot schreibt es in die `.env`, benutzt es sofort und meldet den Wechsel in Telegram. Das bisherige Modell fragt er vorher selbst: Er ersetzt es nur, wenn es wirklich nicht mehr antwortet. Bleibt die Prüfung ohne Ergebnis (Limit, Netz), ändert er nichts.
- **Wann geprüft wird.** 75 Sekunden nach dem Start, danach alle `MODEL_AUTOUPDATE_HOURS` Stunden und fünf Minuten nach einem Ausfall.

Vor dem Schreiben legt der Bot die Sicherung `.env.modelupdate.bak` an. Danach liest er die `.env` zur Kontrolle; stimmt ein Wert nicht, stellt er den alten Inhalt wieder her. Kommentare und alle anderen Zeilen bleiben, wie sie sind.

`/update_models` prüft sofort und zeigt je Anbieter Modell, Kette und gesperrte Modelle. Ein Modell, das antwortet, bleibt dabei stehen. `/update_models best` wechselt zusätzlich auf das größte Modell, das die Prüfung besteht. Mit `MODEL_AUTOUPDATE_PIN=GROQ_MODEL` (auch `QWEN_MODEL`, `NVIDIA_MODEL`, kommagetrennt) fasst der Bot das Modell eines Anbieters nie an.

- **Qwen:** Der Bot nimmt nur Gratis-Modelle von OpenRouter, zuerst die Qwen-Modelle. Besteht keines die Prüfung, springt ein anderes Gratis-Modell ein. Ein bezahltes Modell, das du selbst eingetragen hast, bleibt stehen. Zeigt `QWEN_BASE_URL` nicht auf OpenRouter, wechselt der Bot dort nichts.
- **Kosten:** Jede Prüfung kostet bei Groq und Nvidia einen kurzen Aufruf, bei einem Wechsel bis zu sechs weitere.
- **Denk-Text:** Was ein Modell zwischen `<think>` und `</think>` schreibt, entfernt der Bot aus der Antwort.

## 10. Meldungen verstehen

Die Tabellen nennen den Anfang der Meldung, wie er in dieser Sprache im Chat steht. „…“ steht für Werte wie Symbol, Kurs oder Uhrzeit.

### Rund um einen Scan

| Meldung | Bedeutung | Was du tun musst |
| --- | --- | --- |
| „🕐 … \| NEXUS … gestartet“ | Bot ist gestartet | Version und Werte kurz prüfen |
| `TRADE: OIL_CRUDE \| SIDE: SELL \| SIZE: 0 ...` | Rohzeilen der KI. SIZE 0 ist richtig, die Größe rechnet der Bot. Kommt nur, wenn gehandelt wurde | Nichts |
| „✅ POSITION BESTÄTIGT: …“ | Order ausgeführt, Position steht im Depot | Nichts |
| „⚠️ POSITION NICHT BESTÄTIGT: …“ | Order gesendet, Position nach 8 Sekunden nicht sichtbar | In der Capital-App nachsehen |
| „🔔 Handelsmeldung:“ | Protokoll des Scans: neue Position, Stop-Korrektur mit Grund, übersprungene Symbole | Lesen |
| „🔔 Scan ohne neuen Trade:“ | Nichts eröffnet, mit Gründen. Kommt nur, wenn sich die Gründe ändern, sonst alle 6 Stunden | Nichts |
| „DEPOT NACH DEM TRADE:“ | Depot nach dem Trade: Kontostand, verfügbares Geld, offener Gewinn/Verlust (UPL) | Nichts |
| „🟢 … \| NEXUS NATURE v12.0 Scan #… abgeschlossen.“ | Lebenszeichen: Scan ohne Signal | Nichts |
| „INFO … \| Gemini-Quota erschöpft → weiter mit Groq“ | Gemini hat nicht geliefert, Ersatz-Anbieter übernimmt. Darunter der Grund je Modell | Abgelehnte Keys ersetzen; beim Tageslimit warten |
| „🤖 Gemini-Kette aktualisiert:“ | Modellliste hat sich geändert | Nichts |

### Abgelehnte Trades (Zeilen im Protokoll)

| Zeile | Bedeutung |
| --- | --- |
| „⏳ … : vor … min geschlossen - Wiedereinstieg gesperrt, noch … h … min (WIEDEREINSTIEG_SPERRE_STD=… )“ | Symbol wurde vor weniger als 6 Stunden geschlossen |
| „⛔ …: MAX POSITIONEN …/… erreicht - nicht eröffnet“ | Obergrenze offener Positionen erreicht |
| „… Pyramiding übersprungen: …“ | Position offen, aber noch keine 2 % im Gewinn |
| „⚠️ WARNUNG …: Heute …x Verlust - Gremium soll vorsichtig sein“ | Warnung: heute schon ein Stop-Loss-Verlust in diesem Symbol |
| „🔴 HARD BLOCK (Handelssperre) …: Heute …x Verlust (Limit=…) - Trade gestoppt“ | Verlust-Sperre für heute |
| „⛔ HARD BLOCK (Handelssperre) … (…): Benutzeranweisung aktiv — …“ | Handelssperre aus dem Wochen-Lernlauf |
| „⛔ SPREAD-BLOCK …: Live-Spread … > MAX_SPREAD … (.env) - TRADE ABGELEHNT, auch wenn Gemini ihn empfiehlt“ | Spread über `MAX_SPREAD` |
| „⏰ MARKT GESCHLOSSEN: …“ | Markt geschlossen |
| „⛔ FALLBACK-BLOCK … (…): nicht vom Gate-Keeper freigegeben (erlaubt: …)“ | Ersatz-KI wollte etwas handeln, das der Gate-Keeper nicht freigegeben hat |
| „⛔ … : SL/TP unplausibel (Kurs … , SL … , TP … ) -> Trade verworfen“ | Stop oder Ziel auf der falschen Seite des Kurses |
| „Margin-SPERRE: …“ | Zu wenig verfügbares Geld |
| „DEPOT-DD-ALARM! Heute KEIN neuer Trade.“ | Tages-Verlust-Stopp: heute keine neuen Trades |

### Offene Positionen

| Meldung | Bedeutung | Was du tun musst |
| --- | --- | --- |
| „🎯 MIRROR-TP Level … : …“ | Stufe verkauft; zeigt Menge, Kurs und Rest | Nichts |
| „Teilverkauf nicht möglich: Im Capital.com-Konto ist der Hedging-Modus eingeschaltet. Bitte dort ausschalten, dann verkauft der Bot in Stufen.“ | Teilverkauf ging nicht, weil das Konto im Hedging-Modus ist | Hedging-Modus bei Capital.com ausschalten |
| „Breakeven: … +… % → SL=…“ | Stop liegt jetzt am Einstieg | Nichts |
| „Teilausstieg: … +… % \| … Einheiten gesichert“ | Kleinste von mehreren Positionen eines Symbols geschlossen | Nichts |
| „… POSITION GESCHLOSSEN: … (…)“ | Capital.com hat geschlossen (Stop Loss, Take Profit oder Broker); mit Grund, Ergebnis und Verlustzähler | Nichts |
| „… Geschlossen (Bot/Hand): … \| … → … \| Größe … \| Ergebnis …“ | Vom Bot (Mirror-TP, Exit) oder von dir geschlossen; eine Zeile mit Ergebnis | Nichts |
| „🎯 TÄGLICHES ATR-ZIEL ERREICHT (…-Tage)“ | Position hat 90 % der Tagesspanne erreicht | Ja oder Nein drücken |
| „🔍 EXIT-EMPFEHLUNG: …“ | 3 von 5 Exit-Regeln stimmen zu; mit `AUTO_EXIT=true` schließt der Bot selbst | Nichts |
| „SCHWARZER SCHWAN (…%)“ | Position mindestens 8 % im Minus, KI-Notfallentscheidung | Position ansehen |
| „SCHWARZER-SCHWAN-ALARM!“ | Position automatisch geschlossen (ab 12 % Minus) | Depot prüfen |
| „SCHWARZER SCHWAN NOTFALL!“ | Eine Position 18 % im Minus: alle Positionen werden geschlossen | Depot prüfen |
| „🔄 Pyramiding-Korrektur:“ | Buchhaltung: Merker an das echte Depot angepasst | Nichts |
| „⚠️ NEXUS NATURE v12.0: API-Verbindungsfehler! Neuer Versuch... (Durchlauf #…)“ | Capital.com nicht erreichbar oder Login abgelehnt | Siehe Fehlersuche |

Steht bei einer Schließung der Zusatz „(aus den Kursen gerechnet, ohne Gebühren)“, hat der Bot die Buchung nicht gefunden und das Ergebnis aus Einstieg, Ausstieg und Größe berechnet, in der Währung des Instruments.

## 11. Einstellungen in der .env

Die Datei liegt neben `nexus_ceo.py`. Änderungen wirken nach einem Neustart. Kommentare gehören in eine eigene Zeile über dem Eintrag. Jeder Name darf nur einmal vorkommen; steht er doppelt da, zählt der letzte.

### Handel

| Eintrag | Standard | Bedeutung |
| --- | --- | --- |
| `BOT_LANGUAGE` | leer | `de`, `en` oder `tr`; leer = der Bot fragt beim Start; `orig` = nie übersetzen |
| `SCAN_INTERVAL_SEC` | 21600 | Sekunden zwischen zwei Scans |
| `TRADING_ASSETS` | leer | Leer = alle Symbole aus `capital_markets_config.py`; sonst kommagetrennte Liste |
| `POSITION_SIZE_PCT` | 10.0 | Positionsgröße in Prozent des Depots |
| `MIN_POSITION_EUR` | 50.0 | Mindestbetrag je Position |
| `MAX_POSITION_EUR` | leer | Feste Obergrenze je Position; leer = nur Risk-Parity-Grenze |
| `MAX_POSITIONEN` | 5 | Höchstzahl offener Positionen |
| `MAX_SPREAD` | 0.5 | Höchster Spread als Preisabstand (Ask minus Bid), kein Prozentwert; leer = kein Limit |
| `GREMIUM_MIN_JA` | 4 | Nötige JA-Stimmen von 5 |
| `GREMIUM_MIN_JA_KRYPTO` | 3 | Dasselbe für Krypto |
| `KRYPTO_NACHT_SPERRE` | false | true = Krypto von 23 bis 6 Uhr gesperrt |
| `AUTO_EXIT` | false | true = Exit-Monitor schließt selbst; false = nur Empfehlung |

### Stop Loss, Gewinnmitnahme, Sperren

| Eintrag | Standard | Bedeutung |
| --- | --- | --- |
| `SL_ATR_MULT` | 1.0 | Mindestabstand des Stops in Tagesspannen. 0 = fester Abstand 1,5 % |
| `SL_MAX_PCT` | 6.0 | Obergrenze für diesen Abstand in Prozent |
| `ATR_DAILY_PERIOD` | 14 | Tage für die durchschnittliche Tagesspanne |
| `ATR_DAILY_ORAN` | 0.90 | Tagesziel als Anteil der Tagesspanne |
| `MIRROR_TP_ENABLED` | true | Stufenverkauf an oder aus |
| `MIRROR_TP_LEVEL_1_MULT`, `_2_`, `_3_` | 0.5, 1.0, 1.5 | Abstand der drei Stufen in Stunden-ATR |
| `MIRROR_TP_CLOSE_PCT` | 25.0 | Anteil der Position je Stufe |
| `MAX_VERLUSTE_PRO_TAG` | 3 | Stop-Loss-Verluste je Symbol und Tag bis zur Sperre; 0 = aus |
| `WIEDEREINSTIEG_SPERRE_STD` | 6 | Stunden bis zum Wiedereinstieg nach einer Schließung; 0 = aus |

### KI und Meldungen

| Eintrag | Standard | Bedeutung |
| --- | --- | --- |
| `GEMINI_KEYS` | – | Kommagetrennt; jeder Key nur einmal |
| `GEMINI_MODEL_1` | – | Erstes Modell der Kette |
| `GEMINI_CHAIN_MAX` | 4 | Höchstzahl Modelle je Anfrage |
| `GEMINI_503_PAUSE` | 6 | Sekunden bis zum zweiten Versuch bei Überlastung; 0 = keiner |
| `MODEL_AUTOUPDATE`, `_HOURS`, `_NOTIFY` | true, 6, true | Modelle selbst aktuell halten (Gemini-Liste und Ersatz-Anbieter), Abstand in Stunden, Meldung bei Änderung |
| `MODEL_AUTOUPDATE_PIN` | – | Anbieter, deren Modell der Bot nie ersetzt, z. B. `GROQ_MODEL,NVIDIA_MODEL` |
| `AI_CHAIN_MAX` | 4 | Höchstzahl Modelle je Anfrage bei Groq, Qwen und Nvidia |
| `PROVIDER_ORDER` | gemini,groq,qwen,nvidia | Reihenfolge der Ersatz-Anbieter |
| `GROQ_KEYS`, `GROQ_MODEL` | – | Groq. Das Modell ersetzt der Bot selbst, wenn es wegfällt |
| `QWEN_KEYS`, `QWEN_MODEL`, `QWEN_BASE_URL` | – | Qwen über einen OpenAI-kompatiblen Zugang. Bei OpenRouter ersetzt der Bot das Modell selbst |
| `NVIDIA_KEYS`, `NVIDIA_MODEL` | – | Nvidia NIM. Das Modell ersetzt der Bot selbst, wenn es wegfällt |
| `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_PRIORITY` | localhost, –, last | Lokales Modell; `first`, `last` oder `only` |
| `SCAN_MELDUNGEN` | neu | `neu` = Scan ohne Trade nur bei Änderung melden; `alle` = bei jedem Scan |

### Zugang und Datenquellen

| Eintrag | Bedeutung |
| --- | --- |
| `TG_TOKEN` | Token des Telegram-Bots |
| `MY_CHAT_ID` | Dein Chat; nur von dort nimmt der Bot Befehle an |
| `CAPITAL_API_KEY`, `CAPITAL_IDENTIFIER`, `CAPITAL_PASSWORD` | Zugang zu Capital.com |
| `CAPITAL_URL` | Demo- oder Live-Adresse. Mit der Live-Adresse handelt der Bot echtes Geld |
| `FRED_API_KEY`, `EIA_API_KEY`, `X_API_BEARER` | Makro-, Energie- und X-Daten für die Analyse (freiwillig) |

## 12. Dateien des Bots

Die Merker-Dateien schreibt der Bot selbst; bearbeite sie nicht von Hand, solange er läuft.

| Datei | Inhalt | Darf man sie löschen? |
| --- | --- | --- |
| `nexus_ceo.py` | Das Programm | Nein |
| `nexus_lang.py` | Texte in Deutsch, Englisch, Türkisch | Nein; ohne sie sendet der Bot die Originaltexte |
| `nexus_diagnose.py` | Diagnose-Skript, nur lesend. Läuft über `/diagnose` oder im Terminal mit `python3 nexus_diagnose.py` | Ja; `/diagnose` meldet dann, dass die Datei fehlt |
| `.env` | Einstellungen und Zugangsdaten | Nein |
| `.env.modelupdate.bak` | Sicherung der `.env` vor dem letzten automatischen Modellwechsel. Enthält dieselben Zugangsdaten | Ja |
| `capital_markets_config.py` | Symbole, Epics, Mindestgrößen, Spreads (freiwillig) | Ja; der Bot handelt dann die eingebaute Liste mit neun Märkten |
| `nexus_ceo.log` | Log. Wechselt um Mitternacht, 7 Tage bleiben erhalten | Ja, alte Tage |
| `nexus_quant.db` | Datenbank: Nachrichten, deine Notizen, Trades, Statistik | Nein, sonst sind Notizen und Statistik weg |
| `trailing_sl_state.json` | Beste Kurse für den Trailing-Stop und welche Mirror-TP-Stufen schon verkauft sind | Nicht, solange Positionen offen sind |
| `positions_seen.json` | Zuletzt gesehene Positionen und Schließzeiten für die Wiedereinstiegs-Sperre | Ja; die Sperre vergisst dann bisherige Schließungen |
| `pyramiding_state.json` | Zahl der Positionen je Symbol; wird bei jedem Scan mit dem Depot abgeglichen | Ja |
| `daily_loss_counter.json` | Verlustzähler von heute | Ja; hebt die Verlust-Sperre für heute auf |
| `depot_dd_tracker.json` | Tageshoch des Depots und Tages-Verlust-Stopp | Ja; hebt den Stopp für heute auf |
| `daily_tp_state.json` | Welche Tagesziel-Fragen schon gestellt wurden | Ja |
| `nexus_lang_missing.log` | Texte, für die es keine Übersetzung gab | Ja |

### Listen aus GitHub

Drei Listen lädt der Bot bei Bedarf aus dem öffentlichen Repository `KhungFu/kisilerim`, nicht aus dem eigenen Ordner: `mentor_name.txt` (Handels-Doktrin; die ersten 3000 Zeichen gehen in den KI-Auftrag), `toplam_egitim.txt` und `Abfrage_Quellen.txt` (Nachrichtenseiten und X-Konten für die Nachrichtensammlung). Jede Installation benutzt damit dieselben Listen. Ist GitHub nicht erreichbar, arbeitet der Bot ohne sie weiter. Gepflegt werden die Listen im Repository `nexus`; `kisilerim` holt sie von dort einmal pro Stunde.

## 13. Update und Rollback

Ein Update besteht aus `nexus_ceo.py`, `nexus_lang.py` und `nexus_diagnose.py`. Die drei gehören zusammen; die Befehle unten gelten für jede der Dateien.

```bash
cp nexus_ceo.py nexus_ceo.py.bak
cp nexus_lang.py nexus_lang.py.bak
# neue Dateien in den Ordner kopieren, dann:
python3 -m py_compile nexus_ceo.py && python3 nexus_lang.py && sudo systemctl restart nexus_ceo.service
```

Der Neustart läuft nur, wenn beide Dateien fehlerfrei sind. In der Startmeldung die Version prüfen.

Zurück zum alten Stand:

```bash
cp nexus_ceo.py.bak nexus_ceo.py
cp nexus_lang.py.bak nexus_lang.py
sudo systemctl restart nexus_ceo.service
```

Merker-Dateien bleiben bei Updates erhalten. Handelssperren gehen bei jedem Neustart verloren.

## 14. Fehlersuche

| Symptom | Wahrscheinliche Ursache | Abhilfe |
| --- | --- | --- |
| Keine Startmeldung nach dem Neustart | Dienst läuft nicht, meist ein Fehler in Code oder `.env`, oder `MY_CHAT_ID` fehlt | `sudo systemctl status nexus_ceo.service` und `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Bot antwortet nur mit einer Chat-ID | `MY_CHAT_ID` ist leer | Zahl in die `.env` eintragen, neu starten |
| Bot antwortet gar nicht | Dienst gestoppt, Token falsch, oder du schreibst aus einem anderen Chat als `MY_CHAT_ID` | Status prüfen; `TG_TOKEN` und `MY_CHAT_ID` prüfen |
| Nachrichten kommen in der falschen Sprache oder gemischt | `BOT_LANGUAGE` falsch, `nexus_lang.py` fehlt, oder für einen Text gibt es keine Regel | `/sprache` senden; `nexus_lang_missing.log` ansehen |
| Der Bot eröffnet nichts | Eine Sperre greift, oder der Gate-Keeper findet keinen Kandidaten | Meldung „🔔 Scan ohne neuen Trade:“ lesen; `/position`, `/verluste`, `/sperren`; am Wochenende nur Krypto |
| „INFO … \| Gemini-Quota erschöpft → weiter mit Groq“ bei jedem Scan | Keys abgelehnt, Tageslimit erreicht oder zu viele Scans für das Gratis-Kontingent | `/update_models`; abgelehnte Keys ersetzen; Scan-Intervall verlängern |
| Im Log steht bei jedem Scan `Groq key 1 hata: ...` (oder Qwen, Nvidia) | Modell beim Anbieter abgeschaltet, Key abgelehnt oder Limit erreicht | `/update_models` zeigt Modell, Kette und Sperren; `/diagnose` nennt die häufigste Fehlermeldung je Anbieter |
| Stufen werden nicht verkauft | Hedging-Modus im Konto an, `MIRROR_TP_ENABLED=false`, oder Stunden-ATR nicht abrufbar | Hedging ausschalten; `.env` prüfen |
| Positionsbericht zeigt keinen Take Profit | Take Profit fehlt bei Capital.com | In der Capital-App nachtragen |
| Positionsbericht warnt vor dem Tagesrauschen | Stop liegt näher als der Mindestabstand | `/sl_weiten`, dann `/sl_weiten ja` |
| Position ohne Meldung verschwunden | Schließ-Meldung kommt erst mit dem nächsten 5-Minuten-Lauf | Warten; sonst die Historie in der Capital-App ansehen |
| „⚠️ NEXUS NATURE v12.0: API-Verbindungsfehler! Neuer Versuch... (Durchlauf #…)“ | Capital.com nicht erreichbar oder Login abgelehnt | Zugangsdaten in der `.env` prüfen, neu starten |
| Symbol unbekannt | Symbol fehlt in `capital_markets_config.py` oder in der eingebauten Liste | Symbol mit Epic und Mindestgröße in `capital_markets_config.py` eintragen, neu starten |

Nützliche Log-Abfragen:

```bash
# Was ist mit Stops, Stufen und Schließungen passiert?
grep -E "Breakeven|MIRROR|Trailing SL|Schliess-Melder|KARA" nexus_ceo.log | tail -40

# Warum liefert Gemini nicht, und wer hat stattdessen geantwortet?
grep -E "Gemini .*: (tot|tageslimit|key|keytot|modell|abbruch)|\[OK\]" nexus_ceo.log | tail -40

# Was wurde abgelehnt?
grep -E "MAX POSITIONEN|Wiedereinstieg|HARD BLOK|SPREAD BLOK|KAPALI|FALLBACK-BLOCK|unplausibel" nexus_ceo.log | tail -40

# Fehler
grep -E "ERROR|Traceback" nexus_ceo.log | tail -20
```

Das Log bleibt in der Originalsprache (Deutsch und Türkisch gemischt); übersetzt werden nur die Telegram-Nachrichten.

## 15. Bekannte Grenzen

### Fehler und Eigenheiten im Code

- **Gasoline zählt als Krypto.** Der Name GASOLINE enthält „SOL“. Der Bot halbiert deshalb die Positionsgröße, verlangt nur 3 von 5 Gremium-Stimmen und wendet die Krypto-Regeln an, auch am Wochenende.
- **Halbierung nur für vier Coins.** Halbiert wird bei BTC, ETH, SOL und XRP. Andere Coins laufen mit voller Größe.
- **Zwölf Coins gelten nicht als Krypto.** Der Bot erkennt Krypto an einer festen Namensliste. AAVE, BCH, NEAR, ARB, OP, XLM, ALGO, VET, HBAR, IOTA, TRX und XTZ aus der mitgelieferten Marktliste stehen nicht darauf. Für sie gelten die Regeln für Rohstoffe: 4 von 5 Gremium-Stimmen und kein Handel am Wochenende.
- **Korrelation wird nicht geprüft.** Verwandte Märkte wie Crude, Heating Oil und Gasoline gelten als unabhängige Positionen.
- **Ab 5 Positionen wirkt kein Gegensignal.** Bei 5 oder mehr offenen Positionen bricht der Bot vor jeder Prüfung ab. Ein Gegensignal schließt dann auch keine bestehende Position.
- **Statistik und Tagesziel aus der Bot-Datenbank sind unvollständig.** Die Datenbank kennt nur Schließungen, die der Bot selbst ausgelöst hat. Maßgeblich ist die Auswertung in der Capital-App.
- **Der manuelle Trade** nutzt weder den Rausch-Schutz noch `MAX_POSITION_EUR`.
- **Handelssperre per Text wirkt nicht.** Die Tabelle, die Wörter wie „gold“ einem Symbol zuordnet, wird weiter unten im Code von einer zweiten Tabelle gleichen Namens (`ASSET_KEYWORDS`, für die Nachrichten) überschrieben. Der Bot erkennt deshalb in keinem Satz ein Symbol und setzt nie eine Sperre. Der Fehler ist absichtlich nicht behoben: Mit der Reparatur würde ein Satz mit „sell“, „close“, „verkaufen“ oder „kapat“ und einem Symbolnamen sofort die Positionen dieses Symbols schließen.
- **Sperren aus dem Wochen-Lernlauf** greifen nur bei Symbolen ohne Unterstrich im Namen.
- **Die Rangfolge der Ersatzmodelle** richtet sich nach Größe, Kontextlänge und Alter des Modells, nicht nach der Güte der Analyse. Ein automatisch gewähltes Modell kann schwächer urteilen als das alte. Der Bot meldet jeden Wechsel; das Modell lässt sich in der `.env` wieder festlegen und mit `MODEL_AUTOUPDATE_PIN` halten.

### Grenzen der Schutzfunktionen

- **Schließ-Meldung:** Eine Position, die innerhalb von 5 Minuten eröffnet und wieder geschlossen wird, sieht der Bot nicht.
- **Handelssperren** liegen nur im Arbeitsspeicher und überleben keinen Neustart.
- **Gestoppter Bot:** Kein Breakeven, kein Stufenverkauf, kein Trailing. Nur Stop und Ziel bei Capital.com wirken weiter.
- **Gewinne und Verluste sind ungleich groß.** Die Stufen liegen bei etwa 0,1 bis 0,3 Tagesspannen, der Stop bei einer ganzen. Eine hohe Trefferquote allein reicht deshalb nicht für einen Gewinn.

### Grenzen der Übersetzung

- Übersetzt werden die Telegram-Nachrichten, nicht das Log.
- KI-Texte kommen in der Sprache, die die KI wählt; der Bot bittet sie nur um die eingestellte Sprache.
- Nachrichten-Schlagzeilen bleiben in der Sprache der Quelle.

### Was geprüft ist

Die Funktionen sind gegen nachgebaute Capital.com-, Telegram-, Gemini-, Groq-, OpenRouter- und Nvidia-Antworten getestet, nicht gegen ein echtes Live-Konto. Der Modellwechsel der Ersatz-Anbieter ist mit den Fehlermeldungen aus einem echten Log geprüft, aber nicht gegen die echten Modelllisten der Anbieter. Lass den Bot mindestens eine Woche im Demo-Konto laufen, bevor du `CAPITAL_URL` auf die Live-Adresse stellst.

---

## Anhang A – Spread-Tabelle (Preisabstand Ask minus Bid)

`MAX_SPREAD` vergleicht den Live-Spread mit dem eingestellten Wert. Ist er größer, meldet der Bot „⛔ SPREAD BLOK" und eröffnet nicht.

| Markt | Spread | Bei `MAX_SPREAD=2` |
| --- | --- | --- |
| Zink | 18,7 | gesperrt |
| Aluminium | 29,4 | gesperrt |
| Nickel | 65 | gesperrt |
| Rohöl | 0,04 | frei |
| Heizöl, Benzin | 0,002 | frei |
| Weizen | 0,8 | frei |
| Platin, Palladium, BTC, ETH_EUR, Kakao | über 2 | gesperrt |
| Sojabohnen, AAVE, ETH_USD, BCH | grenznah | je nach Tageswert |

Werte stammen aus `capital_markets_config.py` bzw. der Diagnose und schwanken im Tagesverlauf.

---

## Anhang B – Kurzreferenz für den Alltag

**Jeden Tag**
- `/status` – Konto, Positionen, Bot-Zustand
- `/position` – offene Positionen mit Stop, Stufen, Gewinn
- `/diagnose 1` – Diagnose-Bericht (Fehler, Zähler, Einstellungen, ohne Schlüssel)

**Wenn etwas hakt**
1. `/diagnose 1` aufrufen und den Bericht ansehen.
2. KI antwortet nicht: `/update_models` (prüft und ersetzt tote Modelle).
3. Bot reagiert gar nicht: `sudo systemctl restart nexus_ceo`, dann `journalctl -u nexus_ceo -n 50`.
4. Nach einem Update schiefgelaufen: Rollback laut Kapitel 13.

**Einstellung ändern**
1. `.env` öffnen, genau einen Eintrag ändern (jeder Name nur einmal).
2. Speichern, Bot neu starten.
3. Mit `/diagnose 1` prüfen, dass der Wert übernommen wurde.

**Verlustbegrenzung, in dieser Reihenfolge**
1. Positionsgröße senken (`POSITION_SIZE_PCT`, `MAX_POSITION_EUR`).
2. Weniger Positionen (`MAX_POSITIONEN`).
3. Enge Märkte erzwingen (`MAX_SPREAD`).
4. Tageslimit (`MAX_VERLUSTE_PRO_TAG`) und Wiedereinstiegssperre (`WIEDEREINSTIEG_SPERRE_STD`).

**Sicherheit**
- `.env` niemals hochladen oder weitergeben; nach jedem Teilen alle Schlüssel erneuern.
- Zuerst Demo-Konto; `CAPITAL_URL` erst nach mindestens einer Woche Demo auf Live stellen.

---

## Anhang C – Glossar

- **ATR** – durchschnittliche Tagesspanne (Average True Range); Basis für Stop und Stufen.
- **Breakeven** – Stop wird auf den Einstieg gezogen, sobald +1 % erreicht sind.
- **CFD** – Differenzkontrakt; Hebelprodukt, Totalverlust des Einsatzes möglich.
- **Gate-Keeper** – Vorprüfung (Spread, Sperren, Limits) vor dem Gremium.
- **Gremium** – fünf KI-Mentoren; 4 von 5 JA nötig (Krypto 3 von 5).
- **Kara Kuğu** – Schutzregel gegen plötzliche Extremereignisse („Schwarzer Schwan").
- **Mirror-TP** – Teilverkauf in drei Stufen (je 25 %) bei 0,5 / 1,0 / 1,5 × Stunden-ATR.
- **Schutz-Schleife** – prüft alle 5 Minuten die offenen Positionen.
- **Spread** – Abstand zwischen Kauf- und Verkaufskurs; kostet beim Einstieg sofort Geld.
- **Trailing** – nachgezogener Stop, 5 % ab +1,5 %.
- **Wiedereinstiegssperre** – Stunden, in denen ein soeben geschlossener Markt nicht erneut eröffnet wird.


Die Tabelle „Anhang L“ mit deinen aktuellen Einstellungen hängt der Bot nur an, wenn du das Handbuch mit `/handbuch` abrufst.

