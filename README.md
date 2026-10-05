# NEXUS CEO

Telegram bot that trades CFDs on commodities and crypto through the Capital.com API: it scans the markets, opens positions, protects them with stop loss rules and sells in levels. Messages and commands are available in **English, German and Turkish**.

Deutsch: [README.de.md](README.de.md) · Türkçe: [README.tr.md](README.tr.md)

> **Risk warning.** This is a hobby project, not a financial product and not investment advice. CFD trading can lose all the money you put in. The code is tested against simulated broker responses, not against a live account. Run it on a **demo account** first and for at least a week. You use it at your own risk; there is no warranty.

## Quick start

1. Python 3.10 or newer on a machine that runs all the time (Linux, e.g. a Raspberry Pi).
2. `pip install -r requirements.txt`
3. `cp .env.example .env && chmod 600 .env`, then fill in the Telegram token, the Capital.com access data and at least one Gemini key.
4. `python3 nexus_ceo.py`
5. Write anything to your bot in Telegram. It answers with your chat ID. Put it into `.env` as `MY_CHAT_ID` and restart.
6. On the next start the bot asks for the language. Tap one, confirm, done. The bot writes `BOT_LANGUAGE` into `.env` itself.

Full instructions, all commands, every setting and the known limits are in the manual:

- [Manual (English)](docs/MANUAL.en.md)
- [Betriebsanleitung (Deutsch)](docs/MANUAL.de.md)
- [Kullanım Kılavuzu (Türkçe)](docs/MANUAL.tr.md)

## Files

| File | Purpose |
| --- | --- |
| `nexus_ceo.py` | The bot |
| `nexus_lang.py` | All Telegram texts in German, English and Turkish |
| `.env.example` | Template for your settings. Copy it to `.env` |
| `requirements.txt` | Python packages |
| `systemd/nexus_ceo.service.example` | Template for running the bot as a service |
| `docs/` | Manual in three languages |
| `capital_markets_config.py` | Market list: symbols, epics, minimum sizes, spreads. Without it the bot trades a built-in list of nine markets |
| `market_scanner.py` | Rebuilds `capital_markets_config.py` from your own Capital.com account |
| `mentor_name.txt`, `toplam_egitim.txt`, `Abfrage_Quellen.txt`, `NewsVerlage.txt`, `Audiobooks.txt`, `Bot_egitim_videolari.txt` | Doctrine and source lists. A workflow copies them to the public repository `KhungFu/kisilerim`; the bot reads the first three from there at runtime, not from its folder |

## Your keys stay private

`.env` contains passwords and API keys. `.gitignore` excludes it, so Git never uploads it. Do not rename it, do not paste its content anywhere, and check `git status` before your first push.

## Language

The bot asks for the language on the first start. Change it later with `/language`, `/sprache` or `/dil`. Every command has a name in each language, and all names always work.

## License

MIT, see [LICENSE](LICENSE).
