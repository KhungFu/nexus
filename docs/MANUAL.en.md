# NEXUS CEO – Operating Manual (v16.0)

NEXUS CEO is a Telegram bot that uses the Capital.com API to open CFD positions on commodities and crypto on its own, protect them, and sell them again in levels. This manual describes v16.0 as it stands in the code. It describes the technology and is not investment advice. CFD trading can lead to the loss of the money you put in; use a demo account first.

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
| `/status` | 📊 Status | Full Gemini analysis as in the old flow (v15). The committee does not meet for it. Uses one Gemini request |
| `/signals` | 📈 Signals | Technical signals (MA 9/26, ADX, RSI) |
| `/stats` | 🧮 Stats | Trade statistics and result per asset from the bot database |
| `/losses` | 💸 Losses | Today's loss counter per symbol |
| `/blocks` | 🔒 Blocks | Active trading blocks |
| `/volatility` | – | Run the Black Swan check now |
| `/update_models` | – | Check the AI models: Gemini chain and rejected keys, plus model, chain and blocks for Groq, Qwen and Nvidia. `/update_models best` switches to the largest model that passes the check |
| `/diagnosis` | 🔎 Diagnosis | Diagnosis of the last 7 days: summary as a message, full report as a text file. `/diagnosis 3` = 3 days only. Read-only |
| `/handbook` | – | The complete manual as a file in your language, with the settings the bot is running with right now at the end. `/handbook de` = German, `en` = English, `tr` = Turkish. If the file is not next to the bot, it downloads it from GitHub |
| `/committee` | – | Committee: believability of the 11 mentors (weight, right/wrong) and the latest decisions. `/committee test` checks whether the chair (Claude) answers |
| `/language` | – | Choose the language |
| `/help` | 📋 Menu | Command overview |

### Controlling positions

| Command | What happens |
| --- | --- |
| `/close GOLD` | Closes all positions of this symbol immediately |
| `/close ALL` | Asks first; only `/close ALL CONFIRM` really closes all positions |
| `/manual GOLD BUY 100` | Opens a position of 100 EUR immediately, without the committee. The bot sets stop and target itself |
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
2. **Candidates.** Python looks at all markets in `capital_markets_config.py` (up to v15.24 the weekday scan stopped after 15 markets). The technical signal (MA 9/26, ADX, RSI on daily candles, crypto on 20 min / 45 min / 2 h) is only an attention filter: a market with signal BUY or SELL and strength 2 or more becomes a candidate. Markets that would be blocked anyway are dropped first: weekend and not crypto, `MAX_POSITIONEN` reached (then only exits from open positions), group full, losses of the day, trading block, market closed, spread above `MAX_SPREAD`, re-entry lock, adding without pyramiding permission, and markets the committee already discussed in the last `GREMIUM_GUELTIG_STD` hours. The best `GREMIUM_MAX_KANDIDATEN` by technical score move on.
3. **Dossier.** For each candidate Python puts together a dossier with real data: price and spread, daily range (ATR), daily technicals (EMA 20/50/200, change over 5/20/60 days, range of the last 210 days, RSI), the Python signal, 4h technicals (not for crypto), fundamentals of the group (EIA oil stocks, COT for oil, gold and silver, USDA for wheat, coffee and cocoa, weather), macro (regime, Fear & Greed, DXY, FRED), the next big event, news on the asset from the database (7 days), account and open positions, today's losses and the last closes.
4. **Committee.** The 11 mentors from `mentor_name.txt` (Çiçek, Dalio, Kiyosaki, Graham, Buffett, Sander, Kostolany, Lynch, Taleb, Munger, Druckenmiller) get the same dossier, each in its own AI call through the chain from `PROVIDER_ORDER`, with its role card. None of them sees the others' votes. Each answers BUY, SELL or BEKLE (do not trade), a confidence from 0 to 100 and a reason. For them the CFD is only the vehicle: they judge the market as if they bought the commodity itself or bet against it. The role cards are in `docs/GREMIUM.md`.
5. **Counting.** Python counts the votes, weighted by believability (see below). A decision needs `GREMIUM_MEHRHEIT` weighted votes out of 11 (default 6), crypto at the weekend `GREMIUM_MEHRHEIT_KRYPTO` (5). Fewer than `GREMIUM_MIN_ANTWORTEN` valid answers (8) means: no quorum. If 3 or more vote BUY and at the same time 3 or more vote SELL, there is no trade (scenario 4 from `mentor_name.txt`). The majority may also decide against the Python signal.
6. **Chair.** If there is a majority, the chair checks the decision against the data: UYGULA (execute) or BEKLE (stop). It may not change the direction. It proposes stop and target; if they are on the wrong side of the price, Python takes them from the daily range. The default is Claude through the Claude Code CLI with your Claude subscription (section 9). If the chair does not answer, there is no trade.
7. **Checks and order.** Only the symbol with the direction the committee decided may be executed. The line goes through all locks from section 8. The bot calculates the size itself, moves the stop to the minimum distance, sends the order and checks after 8 seconds whether the position is really in the account.

For every market discussed you get a message "🏛️ COMMITTEE: …" with every vote and reason (section 10). Each market discussed costs 11 AI calls for the members and one for the chair. The committee trades much less often than the old flow; several members (Buffett, Graham, Kiyosaki) are very cautious.

**Believability.** The bot measures every BUY or SELL vote against the price after `GREMIUM_BEWERTUNG_STD` hours (24): right if the price moved more than a quarter of the daily range (at least 0.1%) in the vote's direction, wrong if as far against it, otherwise it does not count. BEKLE is not rated. A member's weight lies between 0.5 and 1.5 and starts at 1.0; a few hits hardly move it. `/committee` shows the weights. `GREMIUM_GEWICHTUNG=false` turns this off.

**Old flow.** With `GREMIUM_MODUS=regeln` the bot works as up to v15.24: five fixed rules (Gate-Keeper) and one big Gemini analysis. Since v16.0 the AI gets up to 20000 characters from `mentor_name.txt` there instead of only the first 3000.

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
| every 5 minutes | Protection run: Black Swan, Breakeven, Mirror-TP, stop ladder, Trailing stop, reporting closed positions |
| every 15 minutes | Daily target watcher: asks with Yes/No buttons whether a position at the daily target should be sold |
| every 30 minutes | Exit monitor: with `AUTO_EXIT=true`, closes a position when 3 of 5 exit rules agree |
| every 60 minutes | Collect news (RSS, X) |
| every 6 hours | Update the Gemini model list |

These runs use no AI quota.

## 6. Position size

For automatic trades, the `.env` alone determines the size; the number the AI writes after SIZE is not used.

1. Base = account × `POSITION_SIZE_PCT`, at least `MIN_POSITION_EUR`.
2. Upper limit = the smallest of these three values: `MAX_POSITION_EUR` (if set), the risk-parity limit (two thirds of the account) and 50% of the account.
3. For BTC, ETH, SOL and XRP the amount is halved.
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
| A level has been sold | Stop ladder: after level 1 the stop moves to the entry (plus 0.03%), after level 2 to the sale price of level 1, after level 3 to that of level 2. The stop is only tightened, never widened. Switch `STOP_LEITER` |
| Profit from 1.0% | Breakeven: stop to the entry price (plus 0.03%) |
| Profit from 1.5% | Trailing stop: 5% behind the best price, only ever tightened |
| Profit from 2% with several positions in the same symbol | Closes the smallest position |
| Profit reaches 90% of the daily range | Daily target: the bot asks with Yes/No buttons whether to sell |
| Price reaches the Take Profit | Capital.com closes the rest |

For commodities, one hourly ATR is about a fifth of the daily range. The three levels are therefore at about 0.1, 0.2 and 0.3 daily ranges, the stop at a whole one. Profits per level are therefore much smaller than a loss at the stop.

With the stop ladder, a position that has sold level 1 can no longer close at the full stop. If the price is already beyond the new stop at the next run (for example because Capital.com rejected the stop as too close), the old stop stays until the price comes back. Positions that sold a level before v15.24 get the stop at the entry.

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
| Group limit | 2 markets per group | No new market from a group in which 2 markets are already open. Groups: energy (Crude, Brent, natural gas, heating oil, gasoline), metals (gold, silver, platinum, palladium, copper, aluminium, zinc, nickel), agriculture (wheat, corn, soybeans, coffee, sugar, cotton, cocoa) and crypto. Adding to an open market does not count | `MAX_JE_GRUPPE` |
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

In the committee (default from v16.0) the bot asks the 11 members through the chain from `PROVIDER_ORDER` (Gemini, Groq, Qwen, Nvidia, Ollama) and the chair through Claude (below). The following paragraphs on the main analysis and fallback mode apply to the old flow (`GREMIUM_MODUS=regeln`) and to `/status`.

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

### Models of the fallback providers (from v15.22)

Groq, OpenRouter and Nvidia retire models again and again. Up to v15.21 each provider ran on the one model from the `.env` and failed as soon as that model was gone. Now the bot keeps the models current by itself, using the same method as swarm.py:

- **Chain per request.** The bot first asks the model from the `.env`, then up to three backup models from the provider's model list (`AI_CHAIN_MAX`). On 401, 403 or 429 it switches the key; once all keys are used, the model. On overload or an empty answer it switches the model at once.
- **Dead model.** If the provider reports that the model no longer exists (404, 410, “does not exist”, “No endpoints found”), the bot blocks it for 24 hours and triggers a check.
- **Replacement.** The check fetches the model list, drops non-chat models and tests the best candidates with a short real call. The first model that answers becomes the main model: the bot writes it to the `.env`, uses it at once and reports the switch in Telegram. It asks the current model first and replaces it only if it really no longer answers. If the check gives no result (limit, network), it changes nothing.
- **When it checks.** 75 seconds after the start, then every `MODEL_AUTOUPDATE_HOURS` hours, and five minutes after a failure.

Before writing, the bot creates the backup `.env.modelupdate.bak`. Afterwards it reads the `.env` back to verify; if a value is wrong, it restores the old content. Comments and all other lines stay as they are.

`/update_models` checks immediately and shows model, chain and blocked models per provider. A model that answers is kept. `/update_models best` additionally switches to the largest model that passes the check. With `MODEL_AUTOUPDATE_PIN=GROQ_MODEL` (also `QWEN_MODEL`, `NVIDIA_MODEL`, comma-separated) the bot never touches that provider's model.

- **Qwen:** The bot only takes free models from OpenRouter, Qwen models first. If none passes the check, another free model steps in. A paid model you entered yourself is kept. If `QWEN_BASE_URL` does not point to OpenRouter, the bot changes nothing there.
- **Cost:** Each check costs one short call at Groq and Nvidia, and up to six more when a model is replaced.
- **Thinking text:** Whatever a model writes between `<think>` and `</think>` is removed from the answer.

### Chair through Claude Code (from v16.0)

The bot asks the 11 members through the free chain from `PROVIDER_ORDER`. By default it asks the chair through the Claude Code CLI (`claude -p`) with your own Claude subscription, model Sonnet or better (`CLAUDE_MODELL=sonnet` or `opus`; the bot raises `haiku` to `sonnet`). The call runs without tools, without a saved session, in an empty folder and without the keys from the `.env`; the dossier goes in through standard input.

Setting it up on the Raspberry Pi, as the same user the service runs as:

1. Requirements according to Anthropic: 64-bit system (ARM64), at least 4 GB RAM, a Claude Pro or Max subscription (the free plan does not include Claude Code).
2. Install: `curl -fsSL https://claude.ai/install.sh | bash`, then `claude --version`.
3. Log in: start `claude` once and follow the login link (or `claude auth login`). Check with `claude auth status`.
4. If the service cannot find the CLI (the service often does not know `~/.local/bin`), write the path from `which claude` into the `.env` as `CLAUDE_CLI`.
5. Restart the bot, then send `/committee test`. Expected: "✅ Vorsitz Claude sonnet: antwortet (…s)".

The calls count against your subscription's usage limits (one call per decision with a majority). If Claude fails (not installed, logged out, timeout after `CLAUDE_TIMEOUT` seconds), there is no trade. With `GREMIUM_VORSITZ_ERSATZ=true` the free chain decides instead; with `GREMIUM_VORSITZ=kette` it always decides.

**Free quota.** One market discussed needs about 12 calls and 20,000 to 25,000 tokens. The free tiers have limits per minute and per day (at Groq among others tokens per minute). That is why the bot asks the members one after another (`GREMIUM_PARALLEL=1`) and waits at most `GREMIUM_FRIST` seconds for all votes. If too many answers are missing after that, the committee has no quorum and there is no trade. `/diagnosis` shows how often that happens in the line "Committee (… days)".

## 10. Understanding the messages

The tables give the start of each message as it appears in the chat in this language. “…” stands for values such as symbol, price or time.

### Committee report (from v16.0)

| Line | Meaning |
| --- | --- |
| "🏛️ COMMITTEE: …" | Header: symbol, price, Python signal with strength |
| "🟢 / 🔴 / ⚪ Name: BUY / SELL / BEKLE (70) - …" | A member's vote with confidence and reason |
| "⚫ Name: no answer" | The AI call did not come back or the answer was unusable; does not count |
| "Weighted: BUY … · SELL … · WAIT … (majority from …, answers …/11)" | Weighted totals and number of valid answers |
| "✅ Decision: …" | Majority for this direction |
| "👔 Chair (Claude sonnet): execute - …" | The chair releases the decision; then the locks from section 8 apply |
| "👔 Chair …: stopped - …" | The chair stopped with a reason; no trade |
| "👔 Chair …: no answer - no trade" | Claude not reachable; `/committee test` |
| "⏸️ No quorum: only … of 11 answers" | Too few members answered (quota, network); no trade |
| "⏸️ No trade: committee split (… BUY, … SELL) - scenario 4" | At least 3 votes for each direction |
| "⏸️ No majority - no trade" | No direction reached the majority |

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
| `MAX_JE_GRUPPE` | 2 | At most this many markets per group open at the same time; 0 = off |
| `MAX_SPREAD` | 0.5 | Highest spread as a price distance (ask minus bid), not a percentage; empty = no limit |
| `GREMIUM_MIN_JA` | 4 | Only with `GREMIUM_MODUS=regeln`: YES votes needed from the 5 old rules |
| `GREMIUM_MIN_JA_KRYPTO` | 3 | The same for crypto |
| `KRYPTO_NACHT_SPERRE` | false | true = crypto locked from 23:00 to 6:00 |
| `AUTO_EXIT` | false | true = exit monitor closes itself; false = recommendation only |

### Committee (from v16.0)

| Setting | Default | Meaning |
| --- | --- | --- |
| `GREMIUM_MODUS` | ki | `ki` = committee of 11 mentors; `regeln` = old flow (v15) |
| `GREMIUM_MEHRHEIT` | 6 | Weighted votes out of 11 for a decision |
| `GREMIUM_MEHRHEIT_KRYPTO` | 5 | The same for crypto at the weekend |
| `GREMIUM_MIN_ANTWORTEN` | 8 | Fewer valid answers = no quorum |
| `GREMIUM_MAX_KANDIDATEN` | 2 | The committee discusses at most this many markets per scan (about 12 AI calls each) |
| `GREMIUM_GUELTIG_STD` | 4 | A market discussed is not discussed again for this many hours |
| `GREMIUM_PARALLEL` | 1 | AI calls at the same time; 1 spares the per-minute limits of the free providers |
| `GREMIUM_FRIST` | 420 | Seconds for all 11 votes together; a member without an answer by then counts as no answer |
| `GREMIUM_BEWERTUNG_STD` | 24 | Each vote is measured against the price after this many hours |
| `GREMIUM_GEWICHTUNG` | true | Use believability as weight; false = all 1.0 |
| `GREMIUM_VORSITZ` | claude | `claude` = Claude Code CLI with your subscription; `kette` = free chain |
| `CLAUDE_MODELL` | sonnet | `sonnet` or `opus` (or a full model name); `haiku` is raised to `sonnet` |
| `CLAUDE_CLI` | claude | Name or full path of the CLI, e.g. `/home/user/.local/bin/claude` |
| `CLAUDE_TIMEOUT` | 180 | Seconds the bot waits for the chair |
| `GREMIUM_VORSITZ_ERSATZ` | false | true = if Claude fails, the free chain decides; false = no trade |

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
| `STOP_LEITER` | true | Move the stop up after each sold level; false = off |
| `MAX_VERLUSTE_PRO_TAG` | 3 | Stop Loss losses per symbol and day until the lock; 0 = off |
| `WIEDEREINSTIEG_SPERRE_STD` | 6 | Hours until re-entry after a close; 0 = off |

### AI and messages

| Entry | Default | Meaning |
| --- | --- | --- |
| `GEMINI_KEYS` | – | Comma-separated; each key only once |
| `GEMINI_MODEL_1` | – | First model in the chain |
| `GEMINI_CHAIN_MAX` | 4 | Maximum number of models per request |
| `GEMINI_503_PAUSE` | 6 | Seconds until the second attempt on overload; 0 = none |
| `MODEL_AUTOUPDATE`, `_HOURS`, `_NOTIFY` | true, 6, true | Keep the models current automatically (Gemini list and fallback providers), interval in hours, message on change |
| `MODEL_AUTOUPDATE_PIN` | – | Providers whose model the bot never replaces, e.g. `GROQ_MODEL,NVIDIA_MODEL` |
| `AI_CHAIN_MAX` | 4 | Maximum number of models per request for Groq, Qwen and Nvidia |
| `PROVIDER_ORDER` | gemini,groq,qwen,nvidia | Order of the fallback providers |
| `GROQ_KEYS`, `GROQ_MODEL` | – | Groq. The bot replaces the model itself when it is retired |
| `QWEN_KEYS`, `QWEN_MODEL`, `QWEN_BASE_URL` | – | Qwen via an OpenAI-compatible endpoint. With OpenRouter the bot replaces the model itself |
| `NVIDIA_KEYS`, `NVIDIA_MODEL` | – | Nvidia NIM. The bot replaces the model itself when it is retired |
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
| `.env.modelupdate.bak` | Backup of the `.env` from before the last automatic model switch. Contains the same credentials | Yes |
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
| `nexus_gremium.py` | Committee: role cards, voting, counting, chair | No; without it the old flow runs and the log reports an error |
| `nexus_gremium.db` | Votes and decisions of the committee, the source of believability | Yes; the weights then start again at 1.0 |
| `docs/GREMIUM.md` | The role cards for reading, generated from `nexus_gremium.py` | Yes |

### Lists from GitHub

The bot loads three lists from the public repository `KhungFu/kisilerim` when it needs them, not from its own folder: `mentor_name.txt` (trading doctrine; in the old flow up to 20000 characters go into the AI prompt, the committee uses the role cards from `nexus_gremium.py`), `toplam_egitim.txt` and `Abfrage_Quellen.txt` (news sites and X accounts for the news collection). Every installation therefore uses the same lists. If GitHub cannot be reached, the bot carries on without them. The lists are maintained in the `nexus` repository; `kisilerim` fetches them from there once an hour.

## 13. Update and rollback

An update consists of `nexus_ceo.py`, `nexus_lang.py`, `nexus_diagnose.py` and from v16.0 `nexus_gremium.py`. The four belong together and sit in the same folder; the commands below apply to each of the files.

```bash
cp nexus_ceo.py nexus_ceo.py.bak
cp nexus_lang.py nexus_lang.py.bak
cp nexus_gremium.py nexus_gremium.py.bak 2>/dev/null
# copy the new files into the folder, then:
python3 -m py_compile nexus_ceo.py nexus_gremium.py && python3 nexus_lang.py && sudo systemctl restart nexus_ceo.service
```

The restart only runs if both files are free of errors. Check the version in the start message.

Back to the previous state:

```bash
cp nexus_ceo.py.bak nexus_ceo.py
cp nexus_lang.py.bak nexus_lang.py
sudo systemctl restart nexus_ceo.service
```

To switch off only the committee, without old files: put `GREMIUM_MODUS=regeln` into the `.env`, then restart.

State files are kept during updates. Trading blocks are lost on every restart.

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No start message after the restart | Service is not running, usually an error in the code or `.env`, or `MY_CHAT_ID` is missing | `sudo systemctl status nexus_ceo.service` and `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Bot only replies with a chat ID | `MY_CHAT_ID` is empty | Enter the number in the `.env`, restart |
| Bot does not reply at all | Service stopped, wrong token, or you are writing from a chat other than `MY_CHAT_ID` | Check the status; check `TG_TOKEN` and `MY_CHAT_ID` |
| Messages arrive in the wrong language or mixed | `BOT_LANGUAGE` wrong, `nexus_lang.py` missing, or there is no rule for a text | Send `/language`; look at `nexus_lang_missing.log` |
| The bot opens nothing | A lock is active, the committee finds no majority, has no quorum, or the chair stops | Read the “🔔 Scan without new trade:” message; `/position`, `/losses`, `/blocks`; crypto only at the weekend |
| “INFO … \| Gemini quota exhausted → continuing with Groq” on every scan | Keys rejected, daily limit reached, or too many scans for the free quota | `/update_models`; replace rejected keys; lengthen the scan interval |
| The log shows `Groq key 1 hata: ...` (or Qwen, Nvidia) on every scan | Model retired by the provider, key rejected, or limit reached | `/update_models` shows model, chain and blocks; `/diagnosis` names the most frequent error message per provider |
| Levels are not sold | Hedging mode on in the account, `MIRROR_TP_ENABLED=false`, or hourly ATR cannot be fetched | Switch off Hedging; check the `.env` |
| Position report shows no Take Profit | Take Profit is missing at Capital.com | Add it in the Capital app |
| Position report warns about the daily noise | Stop is closer than the minimum distance | `/sl_widen`, then `/sl_widen yes` |
| Position disappeared without a message | The close message only comes with the next 5-minute run | Wait; otherwise look at the history in the Capital app |
| “⚠️ NEXUS NATURE v12.0: API connection error! Retrying... (cycle #…)” | Capital.com unreachable or login rejected | Check the credentials in the `.env`, restart |
| "👔 Chair …: no answer - no trade" | Claude Code not installed, not logged in or not found by the service | `/committee test`; in the terminal `claude auth status`; set `CLAUDE_CLI` with the full path (section 9) |
| Often "No quorum" | Free quota of the members used up (per-minute or daily limit) | `/diagnosis`; more keys, `GREMIUM_MAX_KANDIDATEN=1`, longer `SCAN_INTERVAL_SEC` |
| Unknown symbol | Symbol is missing in `capital_markets_config.py` or in the built-in list | Enter the symbol with epic and minimum size in `capital_markets_config.py`, restart |

Useful log queries:

```bash
# What happened to stops, levels and closes?
grep -E "Breakeven|MIRROR|Trailing SL|Schliess-Melder|KARA" nexus_ceo.log | tail -40

# Why does Gemini not deliver, and who answered instead?
grep -E "Gemini .*: (tot|tageslimit|key|keytot|modell|abbruch)|\[OK\]" nexus_ceo.log | tail -40

# What was rejected?
grep -E "MAX POSITIONEN|Wiedereinstieg|HARD BLOK|SPREAD BLOK|KAPALI|FALLBACK-BLOCK|unplausibel" nexus_ceo.log | tail -40

# What did the committee decide, and why was there no trade?
grep -E "GREMIUM|Claude-Vorsitz" nexus_ceo.log | tail -40

# Errors
grep -E "ERROR|Traceback" nexus_ceo.log | tail -20
```

The log stays in the original language (German and Turkish mixed); only the Telegram messages are translated.

## 15. Known limits

### Bugs and quirks in the code

- **Halving for four coins only.** The amount is halved for BTC, ETH, SOL and XRP. Other coins run at full size.
- **Twelve coins do not count as crypto.** The bot recognizes crypto by a fixed list of names. AAVE, BCH, NEAR, ARB, OP, XLM, ALGO, VET, HBAR, IOTA, TRX and XTZ from the supplied market list are not on it. They follow the commodity rules: majority 6 of 11 and no trading at the weekend.
- **Correlation is only checked roughly.** The group limit counts markets per group, not direction or size. Oil and copper are in different groups, even though they often move together.
- **From `MAX_POSITIONEN` only exits.** With a full account the bot opens nothing new and does not add; an opposite signal still closes an open position (up to v15.24 it aborted before).
- **The mentors are imitations.** The role cards summarise the published principles of the people; AI models answer, not the people. Free models do not always stay in their role.
- **Believability needs time.** Only after a few weeks of rated votes do the weights differ noticeably. What is measured is the price move after 24 h, not the result of a trade.
- **The chair can only stop.** It cannot force a direction or suggest a market the committee has not discussed.
- **Quota.** With free providers, members drop out at their limits; then the bot does not trade instead of trading on half the information.
- **Statistics and daily target from the bot database are incomplete.** The database only knows closes that the bot triggered itself. The evaluation in the Capital app is authoritative.
- **The manual trade** uses neither the noise protection nor `MAX_POSITION_EUR`.
- **Trading block by text has no effect.** The table that maps words like “gold” to a symbol is overwritten further down in the code by a second table of the same name (`ASSET_KEYWORDS`, for the news). The bot therefore recognizes no symbol in any sentence and never sets a block. The bug is deliberately not fixed: with the fix, a sentence containing “sell”, “close”, “verkaufen” or “kapat” and a symbol name would immediately close the positions of that symbol.
- **Blocks from the weekly learning run** only apply to symbols without an underscore in the name.
- **The ranking of the backup models** follows size, context length and age of the model, not the quality of the analysis. A model chosen automatically can judge worse than the old one. The bot reports every switch; you can set the model again in the `.env` and keep it with `MODEL_AUTOUPDATE_PIN`.

### Limits of the protection functions

- **Close message:** The bot does not see a position that is opened and closed again within 5 minutes.
- **Trading blocks** exist only in memory and do not survive a restart.
- **Stopped bot:** No Breakeven, no level selling, no Trailing. Only stop and target at Capital.com keep working.
- **Profits and losses are unequal in size.** With the default levels (0.5 / 1.0 / 1.5) the levels are at about 0.1 to 0.3 daily ranges, the stop at a whole one. All three partial sales together then bring less than the stop on the rest costs. Larger levels (for example 1.0 / 2.0 / 3.0) and the stop ladder soften this. A high hit rate alone is not enough for a profit.

### Limits of the translation

- The Telegram messages are translated, not the log.
- AI texts come in the language the AI chooses; the bot only asks it for the configured language.
- News headlines stay in the language of the source.

### What has been tested

The functions have been tested against simulated Capital.com, Telegram, Gemini, Groq, OpenRouter and Nvidia responses, not against a real live account. The model switching of the fallback providers has been checked with the error messages from a real log, but not against the providers' real model lists. Let the bot run in the demo account for at least a week before you set `CAPITAL_URL` to the live address.
