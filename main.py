import os
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


# ===== Fungsi-fungsi =====

# Sumber 1: prakiraan cuaca dari BMKG
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


# Sumber 2: tinggi air terbaru dari BPBD Jakarta
def get_bpbd():
    url = "https://bpbd.jakarta.go.id/waterlevel"
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if cells and BPBD_POS in cells[0].text:
            # Cari kolom terakhir yang ada isinya (data terbaru)
            latest = None
            for cell in cells[1:]:
                if cell.get_text(strip=True):
                    latest = cell

            if latest is None:
                return []  # baris ada, tapi belum ada data

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

    return []  # pos tidak ditemukan


# Sumber 3: data uji dari dummy site
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


# Cek apakah ada kata hujan/gerimis/banjir di daftar prakiraan
def is_rain(forecasts):
    for forecast in forecasts:
        desc = forecast["desc"].lower()
        if any(word in desc for word in KEYWORDS):
            return True
    return False


# Kirim pesan ke Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=30)
    print("Telegram:", r.status_code)


# ===== Program utama =====

lines = ["Cuaca Kalideres, Jakarta Barat, DKI Jakarta"]

# Sumber 1: BMKG
bmkg = get_bmkg()
lines.append("")
lines.append("[BMKG]")
for forecast in bmkg:
    lines.append(f"{forecast['jam']} - {forecast['desc']}")
rain_expected = is_rain(bmkg)

# Sumber 2: BPBD Jakarta
bpbd = get_bpbd()
lines.append("")
lines.append(f"[BPBD - Pos {BPBD_POS}]")
for forecast in bpbd:
    lines.append(f"{forecast['jam']} - {forecast['desc']}")
if is_rain(bpbd):
    rain_expected = True

# Sumber 3: Dummy (data uji)
if USE_DUMMY:
    dummy = get_dummy()
    lines.append("")
    lines.append("[Dummy - data uji]")
    for forecast in dummy:
        lines.append(f"{forecast['jam']} - {forecast['desc']}")
    if is_rain(dummy):
        rain_expected = True

# Saran sesuai aturan
if rain_expected:
    suggestion = "☔ Bawa payung dan pakai sunscreen"
else:
    suggestion = "☀️ Pakai sunscreen"

lines.append("")
lines.append(f"Saran: {suggestion}")
lines.append("Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika), BPBD (Badan Penanggulangan Bencana Daerah) DKI Jakarta")

message = "\n".join(lines)
print(message)
send_telegram(message)