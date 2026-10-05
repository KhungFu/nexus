# NEXUS CEO – Operating Manual (v15.21)

NEXUS CEO is a Telegram bot that uses the Capital.com API to open CFD positions on commodities and crypto on its own, protect them, and sell them again in levels. This manual describes v15.21 as it stands in the code. It describes the technology and is not investment advice. CFD trading can lead to the loss of the money you put in; use a demo account first.

Other languages: [Deutsch](MANUAL.de.md) · [Türkçe](MANUAL.tr.md)

## 1. First setup

You need a computer that runs all the time (for example a Raspberry Pi), Python 3.10 or newer (tested with 3.11), a Capital.com account and your own Telegram bot.

1. Put the files in a folder, for example `~/nexus/`: `nexus_ceo.py`, `nexus_lang.py`, `nexus_diagnose.py`, `requirements.txt`, `.env.example`. Optional: `capital_markets_config.py` with the list of your markets. If it is missing, the bot trades a built-in list of nine markets (EUR/USD, Gold, Silver, Crude, Brent, BTC, ETH, XRP, SOL).
2. Install the Python packages: `pip install -r requirements.txt`
3. Create a Telegram bot: message `@BotFather` in Telegram, send `/newbot`, and keep the token.
4. Capital.com: create an API key in the account settings. You set a separate password for the key when you do this. The `.env` needs the key (`CAPITAL_API_KEY`), your login email (`CAPITAL_IDENTIFIER`) and the password (`CAPITAL_PASSWORD`). Which password Capital.com expects here (the key's or the account's) is described in the Capital.com API guide; if the bot's login is rejected, try the other one. Use the demo account to begin with.
5. Switch off Hedging mode in your Capital.com account. Otherwise the bot cannot make partial sales.
6. Get at least one Gemini key (Google AI Studio) and, ideally, a Groq key as a fallback.
7. Copy `.env.example` to `.env` and enter your credentials: `cp .env.example .env`, then `chmod 600 .env`.
8. Start the bot: `python3 nexus_ceo.py`
9. Write anything to the bot in Telegram. As long as `MY_CHAT_ID` is empty, it only replies with your chat ID. Enter this number as `MY_CHAT_ID` in the `.env` and restart the bot.
10. On the next start the bot asks for the language. Tap a language and confirm. The bot writes `BOT_LANGUAGE` to the `.env` itself.

For continuous operation, set the bot up as a systemd service; a template is in `systemd/nexus_ceo.service.example`.

The `.env` contains all your credentials. Never pass it on and never upload it. The `.gitignore` file in the package makes Git ignore it.

## 2. Language

The bot speaks German, English and Turkish. The texts are in `nexus_lang.py`; the bot translates each message only when it sends it.

- **First start:** If there is no `BOT_LANGUAGE` in the `.env`, the bot sends three buttons: Deutsch, English, Türkçe. After you tap one, it asks again; only the confirmation saves your choice.
- **Changing it later:** Send `/language`. Or enter `BOT_LANGUAGE=de`, `en` or `tr` in the `.env` and restart.
- **Commands:** Every command has a name in each language. All names always work, whichever language is set. The Turkish names are the original ones.
- **AI texts:** The AI is told to write in the chosen language. The TRADE lines keep their fixed format.
- **Missing translation:** The bot sends texts without a rule in the original and writes them to `nexus_lang_missing.log`. Add a translation in `nexus_lang.py` under `RULES`; `python3 nexus_lang.py` checks the file.
- `BOT_LANGUAGE=orig` switches translation off.

## 3. Starting, stopping, checking

As the systemd service `nexus_ceo.service`:

| Task | Command |
| --- | --- |
| Restart (after every change to `.env` or code) | `sudo systemctl restart nexus_ceo.service` |
| Stop | `sudo systemctl stop nexus_ceo.service` |
| Start | `sudo systemctl start nexus_ceo.service` |
| Is it running? | `sudo systemctl status nexus_ceo.service --no-pager \| head -10` |
| Last lines of the service | `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Follow the log | `tail -f nexus_ceo.log` |
| Check the code before starting | `python3 -m py_compile nexus_ceo.py` |

After every start the bot sends a start message. It shows the version, the scan interval, the stop rule and the re-entry lock. If a value does not match the `.env`, the file was not read or the service was not restarted.

Changes to the `.env` take effect only after a restart. A stopped bot does not trail stops and does not sell levels; the Stop Loss and Take Profit prices stored at Capital.com still apply.

## 4. Telegram commands

The bot accepts commands, text and buttons only from the chat `MY_CHAT_ID`. It ignores messages from other chats.

### Status and analysis

| Command | Button | What happens |
| --- | --- | --- |
| `/position` | 📍 Positions | Position report: for each position the size, entry, price, Stop Loss, Take Profit, daily range, daily target, stop distance in daily ranges and Mirror-TP levels with status |
| `/status` | 📊 Status | Full AI analysis with committee vote. Uses one Gemini request |
| `/signals` | 📈 Signals | Technical signals (MA 9/26, ADX, RSI) |
| `/stats` | 🧮 Stats | Trade statistics and result per asset from the bot database |
| `/losses` | 💸 Losses | Today's loss counter per symbol |
| `/blocks` | 🔒 Blocks | Active trading blocks |
| `/volatility` | – | Run the Black Swan check now |
| `/update_models` | – | Fetch the Gemini model list again; shows the chain and the keys rejected by Google |
| `/diagnosis` | 🔎 Diagnosis | Diagnosis of the last 7 days: summary as a message, full report as a text file. `/diagnosis 3` = 3 days only. Read-only |
| `/language` | – | Choose the language |
| `/help` | 📋 Menu | Command overview |

### Controlling positions

| Command | What happens |
| --- | --- |
| `/close GOLD` | Closes all positions of this symbol immediately |
| `/close ALL` | Asks first; only `/close ALL CONFIRM` really closes all positions |
| `/manual GOLD BUY 100` | Opens a position of 100 EUR immediately, without Gate-Keeper and committee. The bot sets stop and target itself |
| `/manual GOLD BUY 100 1900 2100` | The same with your own Stop Loss (1900) and Take Profit (2100) |
| `/sl_widen` | Shows which stops of open positions lie within the daily noise. Changes nothing |
| `/sl_widen yes` | Moves these stops to the minimum distance. Only further away, never tighter; the Take Profit stays |

### Research and maintenance

| Command | What happens |
| --- | --- |
| `/backtest GOLD 200` | Backtest for one symbol over 200 days |
| `/deepdive GOLD HOUR_4 30` | Detailed analysis for symbol, timeframe and days |
| `/news OIL 7` | Collected news on a symbol from the last 7 days (button 📰 News) |
| `/newscollect` | Collect news now |
| `/sources` | Reliability scores of the news sources |
| `/spread` | Measure the spreads of all markets and write them to the market configuration |
| `/db_clean` | Delete old or broken news from the database |
| `/forget` | Delete your saved notes |

### Text without a command

The bot saves everything you write without a slash as a note for the AI analysis. The bot's help says a note is valid for 48 hours. The AI reads the note along with everything else; it is a hint, not an instruction the bot has to follow.

**Trading block by text does not currently work.** The code is meant to block the symbol immediately on a sentence like `Gold nicht handeln`. Because of a bug, however, the bot never recognizes the symbol in the sentence (see section 15). Do not rely on it. If the bot should not trade a symbol, enter only the symbols it may trade in `TRADING_ASSETS` and restart. If it should not trade at all, stop the service.

## 5. How the bot trades

The bot trades in scans. There are `SCAN_INTERVAL_SEC` seconds between two scans (default 21600, that is 6 hours). A scan runs like this:

1. **Reconciliation.** The bot reconciles its state with the open positions at Capital.com and checks the daily loss stop.
2. **Gate-Keeper.** For each symbol, Python calculates five technical points: MA cross 9/26, ADX above 15, RSI matching the direction, Bollinger position, proximity to a Fibonacci level. Commodities can get a sixth point (Rogers filter, EMA 50/200). Only symbols with at least 5 points move on. Crypto therefore needs 5 of 5.
3. **Committee.** Five fixed rule sets (Cihat, Rogers, Dalio, Taleb, Soros) vote YES or NO. 4 of 5 are needed, 3 of 5 for crypto.
4. **AI analysis.** Gemini gets the candidates along with news, weather and macro data and answers with TRADE lines. If Gemini does not deliver, a fallback provider only formats the candidates approved by the Gate-Keeper.
5. **Checks before the order.** Every TRADE line goes through the locks from section 8. In fallback mode, only the symbol and the direction that the Gate-Keeper approved in this scan get through.
6. **Order.** The bot calculates the size itself, moves the stop to the minimum distance, sends the order and checks after 8 seconds whether the position is really in the account.

The signals for commodities come from daily candles. They hardly change during a day, so each scan usually delivers the same candidates.

### What happens when a position is already open

- **Same direction:** The bot only adds to the position if it is at least 2% in profit (Pyramiding). Otherwise the scan report shows “… Pyramiding skipped: …”.
- **Opposite direction:** If a scan produces a TRADE line whose direction contradicts the open position (position BUY, line SELL or the reverse), the bot closes all positions of this symbol. It does not open an opposite position.

This is how it works:

1. The line has to pass the locks from section 8: daily loss stop, fewer than `MAX_POSITIONEN` open positions, market open, spread, loss lock.
2. The bot closes all positions of the symbol. Each closed position that was at a loss counts as a loss for the loss lock.
3. The scan report shows “↩️ …: opposite signal …->… - closed only, no opposite position”. If closing fails, the report gives the reason.

If the opposite signal persists, the next scan opens the new direction as a normal position, with all checks. Up to v15.20 the bot sent an opposite order at once, without these checks.

Only the scan reacts to an opposite signal. The exit monitor closes by its own rules.

### What runs constantly alongside

| Interval | Task |
| --- | --- |
| every 5 minutes | Protection run: Black Swan, Breakeven, Mirror-TP, Trailing stop, reporting closed positions |
| every 15 minutes | Daily target watcher: asks with Yes/No buttons whether a position at the daily target should be sold |
| every 30 minutes | Exit monitor: with `AUTO_EXIT=true`, closes a position when 3 of 5 exit rules agree |
| every 60 minutes | Collect news (RSS, X) |
| every 6 hours | Update the Gemini model list |

These runs use no AI quota.

## 6. Position size

For automatic trades, the `.env` alone determines the size; the number the AI writes after SIZE is not used.

1. Base = account × `POSITION_SIZE_PCT`, at least `MIN_POSITION_EUR`.
2. Upper limit = the smallest of these three values: `MAX_POSITION_EUR` (if set), the risk-parity limit (two thirds of the account) and 50% of the account.
3. For epics with BTC, ETH, SOL or XRP in the name, the amount is halved.
4. The amount is converted into units using the live price and the EUR/USD rate.
5. If the result is below the exchange's minimum size, the bot uses the minimum size. If even the minimum size costs more than the upper limit, there is no trade.

If the bot cannot read the account or the price, it opens nothing for automatic trades.

For a manual trade, your EUR amount applies. It is raised to `MIN_POSITION_EUR` and capped at 50% of the account; `MAX_POSITION_EUR` does not apply there. The halving from step 3 also applies to manual trades.

## 7. Stop Loss and profit-taking

Every position gets a Stop Loss and a Take Profit at Capital.com when it is opened. After that, the protection run manages them every 5 minutes.

### Stop Loss at entry

The AI suggests a stop; the bot moves it to a minimum distance if it is too close to the price.

- **Minimum distance** = daily range (daily ATR over 14 days) × `SL_ATR_MULT` (default 1.0).
- **Lower limit:** never closer than 1.5% (crypto at the weekend 3.75%). This value also applies when the daily range cannot be fetched.
- **Upper limit:** at most `SL_MAX_PCT` (default 6%), so that the stop takes effect before the Black Swan threshold.
- If the AI stop is further away than the minimum distance, it stays. If it is more than 8% away, it is replaced.

The rule applies to automatic trades. Without values of your own, the manual trade sets the stop at 2 × hourly ATR and the target at three times that distance.

### Take Profit at entry

The Take Profit comes from the AI. If it is missing or closer than 0.3% to the price, the bot sets 90% of the daily range.

### What happens after entry

| Trigger | What the bot does |
| --- | --- |
| Price reaches entry ± 0.5 × hourly ATR | Mirror-TP level 1: sells 25% of the original size |
| Price reaches ± 1.0 × hourly ATR | Mirror-TP level 2: another 25% |
| Price reaches ± 1.5 × hourly ATR | Mirror-TP level 3: another 25% |
| Profit from 1.0% | Breakeven: stop to the entry price (plus 0.03%) |
| Profit from 1.5% | Trailing stop: 5% behind the best price, only ever tightened |
| Profit from 2% with several positions in the same symbol | Closes the smallest position |
| Profit reaches 90% of the daily range | Daily target: the bot asks with Yes/No buttons whether to sell |
| Price reaches the Take Profit | Capital.com closes the rest |

For commodities, one hourly ATR is about a fifth of the daily range. The three levels are therefore at about 0.1, 0.2 and 0.3 daily ranges, the stop at a whole one. Profits per level are therefore much smaller than a loss at the stop.

### Rules for the partial sale

- The bot sells at least the exchange's minimum size, even if 25% would be smaller.
- If less than the minimum size would remain afterwards, the bot sells the whole rest. A small position can therefore be completely closed as early as level 2.
- Partial sales only work if Hedging mode is switched off in the Capital.com account.
- With every stop change the bot sends the Take Profit along. Otherwise Capital.com deletes it.

### Stops of open positions

New values for `SL_ATR_MULT` only apply to new positions. `/sl_widen` shows which open stops are closer than the minimum distance, `/sl_widen yes` moves them further away. Tightening is only possible by hand in the Capital app.

## 8. Protection rules and locks

Python checks these rules itself; no AI can override them. “Hard-coded” means: cannot be set via the `.env`.

### Before a new position

| Rule | Threshold | Effect | Setting |
| --- | --- | --- | --- |
| Maximum positions | 5 open positions | No new position. At 5 or more, no adding and no reversing either | `MAX_POSITIONEN` |
| Re-entry lock | 6 hours after a close | No new entry in the same symbol in the same direction | `WIEDEREINSTIEG_SPERRE_STD` |
| Loss lock | 3 Stop Loss losses per symbol and day | Symbol locked for today; a warning from the first loss. A stop at entry does not count | `MAX_VERLUSTE_PRO_TAG` |
| Daily loss stop | Account value 5% or 40 EUR below the day's high | No new trades today | hard-coded |
| Spread | Live spread above `MAX_SPREAD` | Trade rejected | `MAX_SPREAD` |
| Market closed | according to Capital.com | No order, message with opening time | – |
| Margin | Trade would need more than 90% of the available funds | Trade rejected | hard-coded |
| Plausibility | Stop or target on the wrong side of the price, or no live price | Trade discarded | – |
| Trading block | Weekly learning run (Mondays at 6:00): symbol, direction and weekday with a hit rate below 33% | Symbol blocked until the restart. Only works for symbols without an underscore in the name (GOLD yes, OIL_CRUDE no) | hard-coded |
| Weekend | Saturday and Sunday | Crypto only, at most 3 crypto positions | hard-coded |
| Crypto night lock | 23:00 to 6:00 | Default: off | `KRYPTO_NACHT_SPERRE` |

### For open positions

| Rule | Threshold | Effect | Setting |
| --- | --- | --- | --- |
| Black Swan level 1 | Position down 8% | AI emergency decision: hold or close | hard-coded |
| Black Swan level 2 | Position down 12% | Position is closed automatically | hard-coded |
| Black Swan level 3 | One position down 18% | All positions are closed | hard-coded |
| Auto-Exit | 3 of 5 exit rules (signal change, strongly negative news, risk-off) | Position is closed | `AUTO_EXIT` |

With `AUTO_EXIT=false` the exit monitor does not close positions itself but only sends a recommendation.

## 9. AI providers

Gemini does the main analysis. If Gemini delivers nothing, a fallback provider takes over, but it may only put the candidates approved by the Gate-Keeper into TRADE lines.

### Gemini model chain

Each request runs through at most 4 models (`GEMINI_CHAIN_MAX`): first the model from `GEMINI_MODEL_1`, then the current Flash models from Google's live list. For each model the bot tries all usable keys.

| Response from Google | What the bot does |
| --- | --- |
| 401, key invalid | Key is not used for 6 hours; next key |
| 429 daily limit | Next key. If all valid keys are at the limit, the model rests until the reset (midnight US Pacific time) and the next model moves into the chain |
| 429 per-minute limit, 403 | Next key |
| 503 overloaded | A second attempt after 6 seconds (`GEMINI_503_PAUSE`), then the next model |
| 404 or no free quota | Model blocked for 24 hours, model list is fetched again |
| other error | Gemini abandoned for this request |

The model list updates itself every 6 hours; `/update_models` fetches it immediately and shows rejected keys by their last four characters.

Keys from the same Google project share one quota; several keys from one project give no more requests than one. The free quota is small. The shorter the scan interval, the more often the bot runs on the fallback provider.

### Fallback providers

The order is set in `PROVIDER_ORDER`. `OLLAMA_PRIORITY` controls the local Ollama model:

- `last`: Ollama only if all cloud providers fail.
- `first`: Ollama answers before all others as soon as it is running on the machine.
- `only`: Ollama only.

In fallback mode the AI only sets stop and target or rejects a candidate. Symbol and direction come from the Gate-Keeper, the size from the `.env`, and the stop is moved to the minimum distance. The Telegram message always says “Groq”, even if another provider answered; which one it was is in the log as `[OK] ...`.

## 10. Understanding the messages

The tables give the start of each message as it appears in the chat in this language. “…” stands for values such as symbol, price or time.

### Around a scan

| Message | Meaning | What you need to do |
| --- | --- | --- |
| “🕐 … \| NEXUS … started” | Bot has started | Briefly check version and values |
| `TRADE: OIL_CRUDE \| SIDE: SELL \| SIZE: 0 ...` | Raw lines from the AI. SIZE 0 is correct; the bot calculates the size. Only appears when a trade was made | Nothing |
| “✅ POSITION CONFIRMED: …” | Order executed, position is in the account | Nothing |
| “⚠️ POSITION NOT VERIFIED: …” | Order sent, position not visible after 8 seconds | Check in the Capital app |
| “🔔 Trade notification:” | Scan report: new position, stop correction with reason, skipped symbols | Read it |
| “🔔 Scan without new trade:” | Nothing opened, with reasons. Only appears when the reasons change, otherwise every 6 hours | Nothing |
| “ACCOUNT AFTER TRADE:” | Account after the trade: balance, available funds, open profit/loss (UPL) | Nothing |
| “🟢 … \| NEXUS NATURE v12.0 scan #… completed.” | Sign of life: scan without a signal | Nothing |
| “INFO … \| Gemini quota exhausted → continuing with Groq” | Gemini did not deliver, fallback provider takes over. Below it, the reason per model | Replace rejected keys; wait if it is the daily limit |
| “🤖 Gemini chain updated:” | Model list has changed | Nothing |

### Rejected trades (lines in the scan report)

| Line | Meaning |
| --- | --- |
| “⏳ … : closed … min ago - re-entry locked for another … h … min (WIEDEREINSTIEG_SPERRE_STD=… )” | Symbol was closed less than 6 hours ago |
| “⛔ …: MAX POSITIONS …/… reached - not opened” | Upper limit of open positions reached |
| “… Pyramiding skipped: …” | Position open but not yet 2% in profit |
| “⚠️ WARNING …: …x loss today - committee should be careful” | Warning: already one Stop Loss loss in this symbol today |
| “🔴 HARD BLOCK …: …x loss today (limit=…) - trade stopped” | Loss lock for today |
| “⛔ HARD BLOCK … (…): user instruction active — …” | Trading block from the weekly learning run |
| “⛔ SPREAD BLOCK …: live spread … > MAX_SPREAD … (.env) - TRADE REJECTED even if Gemini recommends it” | Spread above `MAX_SPREAD` |
| “⏰ MARKET CLOSED: …” | Market closed |
| “⛔ FALLBACK-BLOCK … (…): not approved by the Gate-Keeper (allowed: …)” | Fallback AI wanted to trade something the Gate-Keeper did not approve |
| “⛔ … : SL/TP implausible (price … , SL … , TP … ) -> trade discarded” | Stop or target on the wrong side of the price |
| “Margin BLOCK: …” | Not enough available funds |
| “ACCOUNT DD ALARM! NO new trade today.” | Daily loss stop: no new trades today |

### Open positions

| Message | Meaning | What you need to do |
| --- | --- | --- |
| “🎯 MIRROR-TP Level … : …” | Level sold; shows quantity, price and remainder | Nothing |
| “Partial sale not possible: Hedging mode is switched on in the Capital.com account. Please switch it off there, then the bot will sell in levels.” | Partial sale failed because the account is in Hedging mode | Switch off Hedging mode at Capital.com |
| “Breakeven: … +… % → SL=…” | Stop is now at entry | Nothing |
| “Partial exit: … +… % \| … units secured” | Smallest of several positions of a symbol closed | Nothing |
| “… POSITION CLOSED: … (…)” | Capital.com closed it (Stop Loss, Take Profit or broker); with reason, result and loss counter | Nothing |
| “… Closed (bot/manual): … \| … → … \| Size … \| Result …” | Closed by the bot (Mirror-TP, exit) or by you; one line with the result | Nothing |
| “🎯 DAILY ATR TARGET REACHED (…-day)” | Position has reached 90% of the daily range | Press Yes or No |
| “🔍 EXIT RECOMMENDATION: …” | 3 of 5 exit rules agree; with `AUTO_EXIT=true` the bot closes it itself | Nothing |
| “BLACK SWAN (…%)” | Position down at least 8%, AI emergency decision | Look at the position |
| “BLACK SWAN ALERT!” | Position closed automatically (from 12% down) | Check the account |
| “BLACK SWAN EMERGENCY!” | One position down 18%: all positions are closed | Check the account |
| “🔄 Pyramiding correction:” | Bookkeeping: state adjusted to the real account | Nothing |
| “⚠️ NEXUS NATURE v12.0: API connection error! Retrying... (cycle #…)” | Capital.com unreachable or login rejected | See Troubleshooting |

If a close carries the note “(calculated from the prices, excluding fees)”, the bot did not find the booking and calculated the result from entry, exit and size, in the currency of the instrument.

## 11. Settings in the .env

The file is next to `nexus_ceo.py`. Changes take effect after a restart. Comments belong on a line of their own above the entry. Each name may appear only once; if it appears twice, the last one counts.

### Trading

| Entry | Default | Meaning |
| --- | --- | --- |
| `BOT_LANGUAGE` | empty | `de`, `en` or `tr`; empty = the bot asks at start; `orig` = never translate |
| `SCAN_INTERVAL_SEC` | 21600 | Seconds between two scans |
| `TRADING_ASSETS` | empty | Empty = all symbols from `capital_markets_config.py`; otherwise a comma-separated list |
| `POSITION_SIZE_PCT` | 10.0 | Position size as a percentage of the account |
| `MIN_POSITION_EUR` | 50.0 | Minimum amount per position |
| `MAX_POSITION_EUR` | empty | Fixed upper limit per position; empty = risk-parity limit only |
| `MAX_POSITIONEN` | 5 | Maximum number of open positions |
| `MAX_SPREAD` | 0.5 | Highest spread as a price distance (ask minus bid), not a percentage; empty = no limit |
| `GREMIUM_MIN_JA` | 4 | YES votes needed out of 5 |
| `GREMIUM_MIN_JA_KRYPTO` | 3 | The same for crypto |
| `KRYPTO_NACHT_SPERRE` | false | true = crypto locked from 23:00 to 6:00 |
| `AUTO_EXIT` | false | true = exit monitor closes itself; false = recommendation only |

### Stop Loss, profit-taking, locks

| Entry | Default | Meaning |
| --- | --- | --- |
| `SL_ATR_MULT` | 1.0 | Minimum stop distance in daily ranges. 0 = fixed distance of 1.5% |
| `SL_MAX_PCT` | 6.0 | Upper limit for this distance in percent |
| `ATR_DAILY_PERIOD` | 14 | Days for the average daily range |
| `ATR_DAILY_ORAN` | 0.90 | Daily target as a share of the daily range |
| `MIRROR_TP_ENABLED` | true | Level selling on or off |
| `MIRROR_TP_LEVEL_1_MULT`, `_2_`, `_3_` | 0.5, 1.0, 1.5 | Distance of the three levels in hourly ATR |
| `MIRROR_TP_CLOSE_PCT` | 25.0 | Share of the position per level |
| `MAX_VERLUSTE_PRO_TAG` | 3 | Stop Loss losses per symbol and day until the lock; 0 = off |
| `WIEDEREINSTIEG_SPERRE_STD` | 6 | Hours until re-entry after a close; 0 = off |

### AI and messages

| Entry | Default | Meaning |
| --- | --- | --- |
| `GEMINI_KEYS` | – | Comma-separated; each key only once |
| `GEMINI_MODEL_1` | – | First model in the chain |
| `GEMINI_CHAIN_MAX` | 4 | Maximum number of models per request |
| `GEMINI_503_PAUSE` | 6 | Seconds until the second attempt on overload; 0 = none |
| `MODEL_AUTOUPDATE`, `_HOURS`, `_NOTIFY` | true, 6, true | Update the model list automatically, interval in hours, message on change |
| `PROVIDER_ORDER` | gemini,groq,qwen,nvidia | Order of the fallback providers |
| `GROQ_KEYS`, `GROQ_MODEL` | – | Groq |
| `QWEN_KEYS`, `QWEN_MODEL`, `QWEN_BASE_URL` | – | Qwen via an OpenAI-compatible endpoint |
| `NVIDIA_KEYS`, `NVIDIA_MODEL` | – | Nvidia NIM |
| `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_PRIORITY` | localhost, –, last | Local model; `first`, `last` or `only` |
| `SCAN_MELDUNGEN` | neu | `neu` = report a scan without a trade only on change; `alle` = on every scan |

### Access and data sources

| Entry | Meaning |
| --- | --- |
| `TG_TOKEN` | Token of the Telegram bot |
| `MY_CHAT_ID` | Your chat; the bot accepts commands only from there |
| `CAPITAL_API_KEY`, `CAPITAL_IDENTIFIER`, `CAPITAL_PASSWORD` | Access to Capital.com |
| `CAPITAL_URL` | Demo or live address. With the live address the bot trades real money |
| `FRED_API_KEY`, `EIA_API_KEY`, `X_API_BEARER` | Macro, energy and X data for the analysis (optional) |

## 12. The bot's files

The bot writes the state files itself; do not edit them by hand while it is running.

| File | Contents | Can you delete it? |
| --- | --- | --- |
| `nexus_ceo.py` | The program | No |
| `nexus_lang.py` | Texts in German, English, Turkish | No; without it the bot sends the original texts |
| `nexus_diagnose.py` | Diagnosis script, read-only. Runs through `/diagnosis` or in a terminal with `python3 nexus_diagnose.py` | Yes; `/diagnosis` then reports that the file is missing |
| `.env` | Settings and credentials | No |
| `capital_markets_config.py` | Symbols, epics, minimum sizes, spreads (optional) | Yes; the bot then trades the built-in list of nine markets |
| `nexus_ceo.log` | Log. Rotates at midnight, 7 days are kept | Yes, old days |
| `nexus_quant.db` | Database: news, your notes, trades, statistics | No, otherwise notes and statistics are gone |
| `trailing_sl_state.json` | Best prices for the Trailing stop and which Mirror-TP levels have already been sold | Not while positions are open |
| `positions_seen.json` | Last seen positions and close times for the re-entry lock | Yes; the lock then forgets previous closes |
| `pyramiding_state.json` | Number of positions per symbol; reconciled with the account on every scan | Yes |
| `daily_loss_counter.json` | Today's loss counter | Yes; lifts the loss lock for today |
| `depot_dd_tracker.json` | The account's high of the day and the daily loss stop | Yes; lifts the stop for today |
| `daily_tp_state.json` | Which daily target questions have already been asked | Yes |
| `nexus_lang_missing.log` | Texts for which there was no translation | Yes |

### Lists from GitHub

The bot loads three lists from the public repository `KhungFu/kisilerim` when it needs them, not from its own folder: `mentor_name.txt` (trading doctrine; the first 3000 characters go into the AI prompt), `toplam_egitim.txt` and `Abfrage_Quellen.txt` (news sites and X accounts for the news collection). Every installation therefore uses the same lists. If GitHub cannot be reached, the bot carries on without them. The lists are maintained in the `nexus` repository; `kisilerim` fetches them from there once an hour.

## 13. Update and rollback

An update consists of `nexus_ceo.py`, `nexus_lang.py` and `nexus_diagnose.py`. The three belong together; the commands below apply to each of the files.

```bash
cp nexus_ceo.py nexus_ceo.py.bak
cp nexus_lang.py nexus_lang.py.bak
# copy the new files into the folder, then:
python3 -m py_compile nexus_ceo.py && python3 nexus_lang.py && sudo systemctl restart nexus_ceo.service
```

The restart only runs if both files are free of errors. Check the version in the start message.

Back to the previous state:

```bash
cp nexus_ceo.py.bak nexus_ceo.py
cp nexus_lang.py.bak nexus_lang.py
sudo systemctl restart nexus_ceo.service
```

State files are kept during updates. Trading blocks are lost on every restart.

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No start message after the restart | Service is not running, usually an error in the code or `.env`, or `MY_CHAT_ID` is missing | `sudo systemctl status nexus_ceo.service` and `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Bot only replies with a chat ID | `MY_CHAT_ID` is empty | Enter the number in the `.env`, restart |
| Bot does not reply at all | Service stopped, wrong token, or you are writing from a chat other than `MY_CHAT_ID` | Check the status; check `TG_TOKEN` and `MY_CHAT_ID` |
| Messages arrive in the wrong language or mixed | `BOT_LANGUAGE` wrong, `nexus_lang.py` missing, or there is no rule for a text | Send `/language`; look at `nexus_lang_missing.log` |
| The bot opens nothing | A lock is active, or the Gate-Keeper finds no candidate | Read the “🔔 Scan without new trade:” message; `/position`, `/losses`, `/blocks`; crypto only at the weekend |
| “INFO … \| Gemini quota exhausted → continuing with Groq” on every scan | Keys rejected, daily limit reached, or too many scans for the free quota | `/update_models`; replace rejected keys; lengthen the scan interval |
| Levels are not sold | Hedging mode on in the account, `MIRROR_TP_ENABLED=false`, or hourly ATR cannot be fetched | Switch off Hedging; check the `.env` |
| Position report shows no Take Profit | Take Profit is missing at Capital.com | Add it in the Capital app |
| Position report warns about the daily noise | Stop is closer than the minimum distance | `/sl_widen`, then `/sl_widen yes` |
| Position disappeared without a message | The close message only comes with the next 5-minute run | Wait; otherwise look at the history in the Capital app |
| “⚠️ NEXUS NATURE v12.0: API connection error! Retrying... (cycle #…)” | Capital.com unreachable or login rejected | Check the credentials in the `.env`, restart |
| Symbol unknown | Symbol is missing in `capital_markets_config.py` or in the built-in list | Enter the symbol with epic and minimum size in `capital_markets_config.py`, restart |

Useful log queries:

```bash
# What happened to stops, levels and closes?
grep -E "Breakeven|MIRROR|Trailing SL|Schliess-Melder|KARA" nexus_ceo.log | tail -40

# Why does Gemini not deliver, and who answered instead?
grep -E "Gemini .*: (tot|tageslimit|key|keytot|modell|abbruch)|\[OK\]" nexus_ceo.log | tail -40

# What was rejected?
grep -E "MAX POSITIONEN|Wiedereinstieg|HARD BLOK|SPREAD BLOK|KAPALI|FALLBACK-BLOCK|unplausibel" nexus_ceo.log | tail -40

# Errors
grep -E "ERROR|Traceback" nexus_ceo.log | tail -20
```

The log stays in the original language (German and Turkish mixed); only the Telegram messages are translated.

## 15. Known limits

### Bugs and quirks in the code

- **Gasoline counts as crypto.** The name GASOLINE contains “SOL”. The bot therefore halves the position size, requires only 3 of 5 committee votes and applies the crypto rules, including at the weekend.
- **Halving for four coins only.** The amount is halved for BTC, ETH, SOL and XRP. Other coins run at full size.
- **Twelve coins do not count as crypto.** The bot recognizes crypto by a fixed list of names. AAVE, BCH, NEAR, ARB, OP, XLM, ALGO, VET, HBAR, IOTA, TRX and XTZ from the supplied market list are not on it. They follow the commodity rules: 4 of 5 committee votes and no trading at the weekend.
- **Correlation is not checked.** Related markets such as Crude, Heating Oil and Gasoline count as independent positions.
- **No opposite signal from 5 positions.** With 5 or more open positions the bot aborts before any check. An opposite signal then does not close an existing position either.
- **Statistics and daily target from the bot database are incomplete.** The database only knows closes that the bot triggered itself. The evaluation in the Capital app is authoritative.
- **The manual trade** uses neither the noise protection nor `MAX_POSITION_EUR`.
- **Trading block by text has no effect.** The table that maps words like “gold” to a symbol is overwritten further down in the code by a second table of the same name (`ASSET_KEYWORDS`, for the news). The bot therefore recognizes no symbol in any sentence and never sets a block. The bug is deliberately not fixed: with the fix, a sentence containing “sell”, “close”, “verkaufen” or “kapat” and a symbol name would immediately close the positions of that symbol.
- **Blocks from the weekly learning run** only apply to symbols without an underscore in the name.

### Limits of the protection functions

- **Close message:** The bot does not see a position that is opened and closed again within 5 minutes.
- **Trading blocks** exist only in memory and do not survive a restart.
- **Stopped bot:** No Breakeven, no level selling, no Trailing. Only stop and target at Capital.com keep working.
- **Profits and losses are unequal in size.** The levels are at about 0.1 to 0.3 daily ranges, the stop at a whole one. A high hit rate alone is therefore not enough for a profit.

### Limits of the translation

- The Telegram messages are translated, not the log.
- AI texts come in the language the AI chooses; the bot only asks it for the configured language.
- News headlines stay in the language of the source.

### What has been tested

The functions have been tested against simulated Capital.com, Telegram and Gemini responses, not against a real live account. Let the bot run in the demo account for at least a week before you set `CAPITAL_URL` to the live address.
