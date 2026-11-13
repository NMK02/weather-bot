# Weather Forecast-based Daily Suggestion System

Know what to do each day depending on the weather.

Every morning the bot checks the weather for **Kalideres, West Jakarta**, decides whether you need an umbrella, sends the suggestion to **Telegram**, and keeps a daily record in **Excel**. It runs automatically on **GitHub Actions**, so no computer needs to be switched on.

---

## 1. How it works

```
BMKG (forecast)    ─┐
BPBD (water level)  ├─▶ check rule ─▶ Telegram message
Dummy (test data)  ─┘        │
                             └──────▶ Excel log (daily record + backup)
```

1. Fetch data from each source.
2. If a source fails or is offline, use the last data saved in Excel instead (see section 6).
3. Check the rule (section 3) and build one Telegram message.
4. Save the fresh data to `weather_log.xlsx`, then send the message.

---

## 2. Data sources

| # | Source | What is used | How it is read |
|---|---|---|---|
| 1 | **BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika), open forecast API | 3-hourly forecast for today, area code `31.73.06.1001` (Kalideres) | JSON via `requests` |
| 2 | **BPBD DKI Jakarta** (Badan Penanggulangan Bencana Daerah), `bpbd.jakarta.go.id/waterlevel` | Latest water level, weather code and alert status at **Pos Angke Hulu** | HTML table via BeautifulSoup |
| 3 | **Dummy site**, `dummy/index.html` (in this repo) | Test forecasts you can edit freely | HTML via BeautifulSoup |

The dummy site is only included when `USE_DUMMY = True` (default `False`), so test data never affects real messages.

**BPBD weather codes:** T = Terang (clear), MT = Mendung Tipis (thin clouds), M = Mendung (cloudy), G = Gerimis (drizzle), H = Hujan (rain)
**BPBD alert status:** Siaga 4 (normal) to Siaga 1 (danger)

---

## 3. The rule

| Condition | Suggestion |
|---|---|
| Any source contains **"hujan"**, **"gerimis"** or **"banjir"** | ☔ Bawa payung dan pakai sunscreen *(bring an umbrella and wear sunscreen)* |
| Otherwise | ☀️ Pakai sunscreen *(wear sunscreen)* |

- BPBD codes **H** and **G** count as rain.
- BPBD **Siaga 1 or 2** adds "waspada banjir" (flood alert), so it also triggers the umbrella suggestion.
- Backup data older than **24 hours** is shown but **not** used for the suggestion.

---

## 4. Output

### Telegram message (example)

```
Cuaca Kalideres, Jakarta Barat, DKI Jakarta
(2026-11-12 15:47 WIB)

[BMKG]
16:00 - Cerah
19:00 - Hujan Ringan
22:00 - Cerah

[BPBD - Pos Angke Hulu]
terbaru - Terang, 40 cm, Siaga 4

Saran: ☔ Bawa payung dan pakai sunscreen
Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika), BPBD DKI Jakarta (Badan Penanggulangan Bencana Daerah)
```

### Excel log: `weather_log.xlsx`

One row per forecast. New rows are added at the bottom on every run.

| Column | Meaning |
|---|---|
| `waktu_jalan` | When the bot ran (WIB) |
| `sumber` | Source name |
| `jam` | Forecast time (`terbaru` = latest reading for BPBD) |
| `desc` | Weather description |
| `saran` | Suggestion sent that run |

---

## 5. Schedule (GitHub Actions)

- Runs **every day at 05:00 WIB** (`cron: "0 22 * * *"`, 22:00 UTC). GitHub may start it 5–30 minutes late when busy (the first scheduled run arrived at 05:30 WIB).
- After each run, the updated `weather_log.xlsx` is committed back to the repo by `github-actions`.
- **Manual run:** GitHub → **Actions** → **Daily weather** → **Run workflow**.
- Run history: green = success, red = failed (GitHub also emails the owner on failure).

Workflow file: `.github/workflows/daily.yml`

---

## 6. Offline backup

If a source fails (site down, blocked, timeout), the bot does **not** stop:

1. It uses that source's most recent rows from `weather_log.xlsx`.
2. The message shows `⚠️ Situs offline, memakai data tersimpan <time>` (site offline, using saved data).
3. If that saved data is **older than 24 hours**, the message adds a second warning and the data is ignored for the suggestion.
4. Backup data is never saved to Excel again, so every row in the log is real data from that time.
5. If there is no saved data at all, the section shows `Data tidak tersedia` (data not available).

Saving to Excel and sending to Telegram are also protected: if one fails, the other still runs.

---

## 7. Known limitation: BPBD blocks GitHub servers

The BPBD Jakarta website rejects connections from servers outside Indonesia (`Connection reset by peer`). GitHub Actions servers are overseas, so **on the daily automatic run, BPBD always uses backup data**. BMKG is not affected.

**To refresh BPBD data**, run the bot once from a computer in Indonesia:

1. **Sync** in VS Code (get the latest `weather_log.xlsx` from GitHub).
2. Run `python main.py`. BPBD should appear without ⚠️.
3. **Immediately** commit `weather_log.xlsx` (e.g. `Refresh BPBD data from local`) and **Sync**.

Avoid doing this around 05:00 WIB, when the automatic run also writes to the same file.

---

## 8. Setup

### Run on your own computer (Windows)

```
git clone <https://github.com/NMK02/weather-bot.git>
cd weather-bot
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a file named `.env` in the project folder (never commit it; it is already in `.gitignore`):

```
TELEGRAM_TOKEN=<token from @BotFather>
TELEGRAM_CHAT_ID=<your chat id>
```

Then run:

```
python main.py
```

### Run on GitHub Actions

In the repo: **Settings → Secrets and variables → Actions → New repository secret**, add `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` with the same values as `.env`.

---

## 9. Settings (top of `main.py`)

| Setting | Default | Meaning |
|---|---|---|
| `ADM4` | `"31.73.06.1001"` | BMKG area code (Kalideres) |
| `DAY` | `0` | 0 = today, 1 = tomorrow |
| `KEYWORDS` | `["hujan", "gerimis", "banjir"]` | Words that mean "rain expected" |
| `BPBD_POS` | `"Angke Hulu"` | BPBD monitoring post to read |
| `CUACA_BPBD` | T / MT / M / G / H | BPBD weather code meanings |
| `USE_DUMMY` | `False` | `True` = include dummy test data |
| `EXCEL_FILE` | `"weather_log.xlsx"` | Log / backup file |

---

## 10. Notes for developers

- **Sync at the start of every session**, because GitHub Actions adds a commit every day.
- `weather_log.xlsx` is owned by GitHub Actions. After local test runs, **Discard Changes** on it before committing (Git cannot merge Excel files). The only exception is the BPBD refresh in section 7.
- Close Excel before running the bot locally, otherwise Windows locks the file.
- Use the dummy site to test the rule: edit `dummy/index.html`, set `USE_DUMMY = True`, run, then set it back to `False`.

### Project structure

```
weather-bot/
├── .github/workflows/daily.yml   # daily schedule
├── dummy/index.html              # dummy site (test data)
├── main.py                       # the bot
├── weather_log.xlsx              # daily record + backup
├── requirements.txt              # Python packages
├── README.md                     # user manual (Indonesian / English)
├── TESTING.md                    # test checklist (Indonesian / English)
├── bmkg.py, dummy.py, demo.py    # early learning scripts (not used by the bot)
└── .env                          # secrets (local only, not on GitHub)
```

---

## Data attribution

Weather data: **BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)**.
Water level data: **BPBD DKI Jakarta (Badan Penanggulangan Bencana Daerah)**.
