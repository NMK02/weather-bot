# Test Checklist

How to use: follow the steps, compare with the expected result, and fill in **Result** (Pass / Fail) and **Date**.

Note: tests that use a fake URL or a shortened time limit must be **reverted** afterwards, and any test changes to `weather_log.xlsx` should be discarded (see README section 10).

Rule tests on 2026-11-13 were run while BMKG (Cerah Berawan, Berawan) and BPBD (Terang) showed no rain, so the suggestions were triggered by the dummy data only.

---

## A. Data sources

| ID | Test | Steps | Expected result | Result | Date |
|---|---|---|---|---|---|
| A1 | BMKG fetch | Run `python main.py` | `[BMKG]` section lists today's forecasts (time - description) | Pass | 2026-11-12 |
| A2 | BPBD fetch (from Indonesia) | Run locally | `[BPBD - Pos Angke Hulu]` shows `terbaru - <weather>, <cm>, Siaga <n>` with no ⚠️ | Pass | 2026-11-12 |
| A3 | Dummy fetch | Set `USE_DUMMY = True`, run | `[Dummy - data uji]` section lists the forecasts from `dummy/index.html` | Pass | 2026-11-13 |
| A4 | Dummy off | Set `USE_DUMMY = False`, run | No dummy section in the message | Pass | 2026-11-13 |
| A5 | BPBD 2-letter code | Check that `CUACA_BPBD` maps `MT` → Mendung Tipis; when the site shows `(MT)`, the message shows "Mendung Tipis" | Correct name, not "Terang" | | |

## B. Rule

| ID | Test | Steps | Expected result | Result | Date |
|---|---|---|---|---|---|
| B1 | Rain detected | `USE_DUMMY = True`, one dummy forecast = `Hujan Lebat`, run | Saran: ☔ Bawa payung dan pakai sunscreen | Pass | 2026-11-05 |
| B2 | No rain | `USE_DUMMY = True`, all dummy forecasts = `Cerah`, on a day BMKG/BPBD show no rain | Saran: ☀️ Pakai sunscreen | Pass | 2026-11-13 |
| B3 | "Gerimis" keyword | One dummy forecast = `Gerimis`, run | Umbrella suggestion | Pass | 2026-11-13 |
| B4 | "Banjir" keyword | One dummy forecast = `Banjir`, run | Umbrella suggestion | Pass | 2026-11-13 |
| B5 | Upper/lower case | One dummy forecast = `HUJAN`, run | Umbrella suggestion (case is ignored) | Pass | 2026-11-13 |

## C. Output

| ID | Test | Steps | Expected result | Result | Date |
|---|---|---|---|---|---|
| C1 | Telegram delivery | Run | Terminal shows `Telegram: 200`; message arrives on phone | Pass | 2026-11-12 |
| C2 | Message content | Read the message | Location, run time (WIB), each source, suggestion and full source attribution | Pass | 2026-11-12 |
| C3 | Excel created | Delete `weather_log.xlsx`, run | New file with columns `waktu_jalan, sumber, jam, desc, saran` | Pass | 2026-11-12 |
| C4 | Excel appends | Run twice | Second run's rows added below the first | Pass | 2026-11-12 |
| C5 | Excel locked | Open `weather_log.xlsx` in Excel, run | Terminal shows `Excel gagal: ... Permission denied`, Telegram still sent (`200`) | Pass | 2026-11-12 |

## D. Offline backup

| ID | Test | Steps | Expected result | Result | Date |
|---|---|---|---|---|---|
| D1 | Source offline | In `get_bpbd()` change URL to `.../waterlevelXXX`, run | BPBD shows `⚠️ Situs offline, memakai data tersimpan <time>` + saved data | Pass | 2026-11-13 |
| D2 | Backup not re-saved | After D1, open Excel | Rows for that run contain BMKG only, no BPBD | Pass | 2026-11-12 |
| D3 | Old backup ignored | Change `timedelta(hours=24)` to `timedelta(minutes=1)`, keep fake URL, run | Extra line `⚠️ Data lebih dari 24 jam, tidak dipakai untuk saran`; BPBD not used for the suggestion | Pass* | 2026-11-13 |
| D4 | No backup at all | Rename `weather_log.xlsx` temporarily, keep fake URL, run | BPBD shows `Data tidak tersedia`; bot still sends message | | |
| D5 | Telegram failure | Put a wrong token in `.env`, run | Terminal shows a non-200 status or `Telegram gagal`; Excel still saved | | |

\* D3: the warning appeared as expected (a 1-minute gap was not yet treated as old; a 2-minute gap was). Exclusion from the suggestion was not tested with backup data containing rain, because the BPBD backup at the time was "Terang".

## E. Automation (GitHub Actions)

| ID | Test | Steps | Expected result | Result | Date |
|---|---|---|---|---|---|
| E1 | Manual run | Actions → Daily weather → Run workflow | Status **Success**; message arrives | Pass | 2026-11-12 |
| E2 | Excel committed by bot | After E1, check repo commits | New commit "Update weather log" by `github-actions` | Pass | 2026-11-12 |
| E3 | Scheduled run | Wait for next morning | Message arrives around 05:00 WIB (delay up to ~30 min is normal) | Pass (05:30 WIB) | 2026-11-13 |
| E4 | BPBD on GitHub | Read message from E1/E3 | BPBD uses backup with ⚠️ (known limitation, README section 7) | Pass | 2026-11-13 |
| E5 | Secrets safe | Browse the repo and Actions logs on GitHub | No `.env` file; token not visible in code or logs (secrets shown as `***`) | Pass | 2026-11-13 |
| E6 | BPBD refresh procedure | Follow README section 7 | Next run's backup time matches the local refresh | | |
