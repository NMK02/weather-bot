import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== Pengaturan =====
ADM4 = "31.73.06.1001"                     # Kalideres, Jakarta Barat
DAY = 0                                    # 0 = hari ini, 1 = besok
KEYWORDS = ["hujan", "gerimis", "banjir"]  # kata yang berarti "akan hujan"
BPBD_POS = "Angke Hulu"                    # pos pantau terdekat dengan Kalideres
CUACA_BPBD = {
    "T": "Terang",
    "MT": "Mendung Tipis",
    "M": "Mendung",
    "G": "Gerimis",
    "H": "Hujan",
}
USE_DUMMY = False                          # True = ikutkan data uji dari dummy site
EXCEL_FILE = "weather_log.xlsx"            # catatan harian + cadangan

# Nama sumber (dipakai di pesan dan di Excel)
BMKG_NAME = "BMKG"
BPBD_NAME = f"BPBD - Pos {BPBD_POS}"
DUMMY_NAME = "Dummy - data uji"


# ===== Sumber data =====

def get_bmkg():
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={ADM4}"
    data = requests.get(url, timeout=30).json()
    forecasts = data["data"][0]["cuaca"][DAY]

    hasil = []
    for forecast in forecasts:
        hasil.append({
            "jam": forecast["local_datetime"][11:16],
            "desc": forecast["weather_desc"],
        })
    return hasil


def get_bpbd():
    # url = "https://bpbd.jakarta.go.id/waterlevelXXX" #Contoh Kalo OFFLINE
    url = "https://bpbd.jakarta.go.id/waterlevel"
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if cells and BPBD_POS in cells[0].text:
            latest = None
            for cell in cells[1:]:
                if cell.get_text(strip=True):
                    latest = cell

            if latest is None:
                return []

            text = latest.get_text(strip=True)        # "40 cm (MT)"
            parts = text.split("(")                   # ["40 cm ", "MT)"]
            tinggi = parts[0].strip()                 # "40 cm"
            kode = parts[1].replace(")", "")          # "MT"
            cuaca = CUACA_BPBD.get(kode, kode)        # "Mendung Tipis"
            level = int(latest.get("class")[0][-1])   # "siaga4" -> 4

            desc = f"{cuaca}, {tinggi}, Siaga {level}"
            if level <= 2:
                desc += " (waspada banjir)"
            return [{"jam": "terbaru", "desc": desc}]

    return []


def get_dummy():
    with open("dummy/index.html", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    hasil = []
    for item in soup.find_all("div", class_="forecast"):
        hasil.append({
            "jam": item.find("p", class_="time").text,
            "desc": item.find("p", class_="desc").text,
        })
    return hasil


# ===== Cadangan & Excel =====

# Ambil data tersimpan terakhir untuk satu sumber (dipakai saat situs offline)
def load_backup(name):
    if not os.path.exists(EXCEL_FILE):
        return {"data": [], "saved_at": None}

    df = pd.read_excel(EXCEL_FILE)
    df = df[df["sumber"] == name]              # hanya baris sumber ini
    if df.empty:
        return {"data": [], "saved_at": None}

    last_run = df["waktu_jalan"].max()          # waktu simpan terakhir
    df = df[df["waktu_jalan"] == last_run]      # hanya baris dari waktu itu

    hasil = []
    for row in df.to_dict("records"):
        hasil.append({"jam": str(row["jam"]), "desc": str(row["desc"])})
    return {"data": hasil, "saved_at": last_run}


# Jalankan satu sumber dengan aman. Kalau gagal, pakai cadangan.
def fetch(name, get_function):
    try:
        data = get_function()
        if data:
            return {"data": data, "backup_from": None}
        print(f"{name}: tidak ada data")
    except Exception as error:
        print(f"{name} gagal: {error}")

    backup = load_backup(name)
    return {"data": backup["data"], "backup_from": backup["saved_at"]}


# Simpan data baru (bukan cadangan) ke Excel
def save_to_excel(results, run_time, suggestion):
    rows = []
    for name in results:
        result = results[name]
        if result["backup_from"] is not None:
            continue  # data cadangan tidak disimpan ulang
        for forecast in result["data"]:
            rows.append({
                "waktu_jalan": run_time,
                "sumber": name,
                "jam": forecast["jam"],
                "desc": forecast["desc"],
                "saran": suggestion,
            })

    if not rows:
        return

    df = pd.DataFrame(rows)
    if os.path.exists(EXCEL_FILE):
        old = pd.read_excel(EXCEL_FILE)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    print("Excel disimpan:", EXCEL_FILE)


# ===== Aturan & Telegram =====

def is_rain(forecasts):
    for forecast in forecasts:
        desc = forecast["desc"].lower()
        if any(word in desc for word in KEYWORDS):
            return True
    return False


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=30)
        print("Telegram:", r.status_code)
    except Exception as error:
        print("Telegram gagal:", error)


# ===== Program utama =====

run_time = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M")

results = {}
results[BMKG_NAME] = fetch(BMKG_NAME, get_bmkg)
results[BPBD_NAME] = fetch(BPBD_NAME, get_bpbd)
if USE_DUMMY:
    results[DUMMY_NAME] = fetch(DUMMY_NAME, get_dummy)

lines = ["Cuaca Kalideres, Jakarta Barat, DKI Jakarta", f"({run_time} WIB)"]
rain_expected = False

for name in results:
    result = results[name]
    lines.append("")
    lines.append(f"[{name}]")

    if not result["data"]:
        lines.append("Data tidak tersedia")
        continue

    if result["backup_from"] is not None:
        lines.append(f"⚠️ Situs offline, memakai data tersimpan {result['backup_from']}")

    for forecast in result["data"]:
        lines.append(f"{forecast['jam']} - {forecast['desc']}")

    if is_rain(result["data"]):
        rain_expected = True

if rain_expected:
    suggestion = "☔ Bawa payung dan pakai sunscreen"
else:
    suggestion = "☀️ Pakai sunscreen"

lines.append("")
lines.append(f"Saran: {suggestion}")
lines.append("Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika), BPBD DKI Jakarta (Badan Penanggulangan Bencana Daerah)")

message = "\n".join(lines)
print(message)

try:
    save_to_excel(results, run_time, suggestion)  # simpan dulu, baru kirim
except Exception as error:
    print("Excel gagal:", error)

send_telegram(message)