# NEXUS CEO

Telegram-Bot, der über die Capital.com-API CFDs auf Rohstoffe und Krypto handelt: Er scannt die Märkte, eröffnet Positionen, sichert sie mit Stop-Loss-Regeln ab und verkauft in Stufen. Nachrichten und Befehle gibt es auf **Deutsch, Englisch und Türkisch**.

English: [README.md](README.md) · Türkçe: [README.tr.md](README.tr.md)

> **Risikohinweis.** Das ist ein Hobby-Projekt, kein Finanzprodukt und keine Anlageempfehlung. Beim CFD-Handel kannst du das gesamte eingesetzte Geld verlieren. Der Code ist gegen nachgebaute Broker-Antworten getestet, nicht gegen ein Live-Konto. Lass ihn zuerst und mindestens eine Woche auf einem **Demo-Konto** laufen. Die Nutzung geschieht auf eigenes Risiko, ohne Gewähr.

## Schnellstart

1. Python 3.10 oder neuer auf einem Rechner, der dauernd läuft (Linux, zum Beispiel ein Raspberry Pi).
2. `pip install -r requirements.txt`
3. `cp .env.example .env && chmod 600 .env`, dann Telegram-Token, Capital.com-Zugangsdaten und mindestens einen Gemini-Key eintragen.
4. `python3 nexus_ceo.py`
5. Dem Bot in Telegram irgendetwas schreiben. Er antwortet mit deiner Chat-ID. Diese als `MY_CHAT_ID` in die `.env` eintragen und neu starten.
6. Beim nächsten Start fragt der Bot nach der Sprache. Antippen, bestätigen, fertig. Der Bot schreibt `BOT_LANGUAGE` selbst in die `.env`.

Die vollständige Anleitung mit allen Befehlen, Einstellungen und bekannten Grenzen steht im Handbuch:

- [Betriebsanleitung (Deutsch)](docs/MANUAL.de.md)
- [Manual (English)](docs/MANUAL.en.md)
- [Kullanım Kılavuzu (Türkçe)](docs/MANUAL.tr.md)

## Dateien

| Datei | Zweck |
| --- | --- |
| `nexus_ceo.py` | Der Bot |
| `nexus_lang.py` | Alle Telegram-Texte in Deutsch, Englisch und Türkisch |
| `.env.example` | Vorlage für deine Einstellungen. Nach `.env` kopieren |
| `requirements.txt` | Python-Pakete |
| `systemd/nexus_ceo.service.example` | Vorlage, um den Bot als Dienst zu betreiben |
| `docs/` | Handbuch in drei Sprachen |
| `capital_markets_config.py` | Marktliste: Symbole, Epics, Mindestgrößen, Spreads. Ohne sie handelt der Bot eine eingebaute Liste mit neun Märkten |
| `market_scanner.py` | Erzeugt `capital_markets_config.py` neu aus deinem eigenen Capital.com-Konto |
| `mentor_name.txt`, `toplam_egitim.txt`, `Abfrage_Quellen.txt`, `NewsVerlage.txt`, `Audiobooks.txt`, `Bot_egitim_videolari.txt` | Doktrin und Quellenlisten. Ein Workflow kopiert sie in das öffentliche Repository `KhungFu/kisilerim`; die ersten drei liest der Bot im Betrieb von dort, nicht aus seinem Ordner |

## Deine Schlüssel bleiben privat

Die `.env` enthält Passwörter und API-Keys. Die `.gitignore` schließt sie aus, Git lädt sie also nie hoch. Benenne sie nicht um, kopiere ihren Inhalt nirgends hin und sieh vor dem ersten Push mit `git status` nach.

## Sprache

Der Bot fragt beim ersten Start nach der Sprache. Später änderst du sie mit `/sprache`, `/language` oder `/dil`. Jeder Befehl hat in jeder Sprache einen Namen, und alle Namen funktionieren immer.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
