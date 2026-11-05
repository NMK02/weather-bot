import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== Pengaturan =====
ADM4 = "31.73.06.1001"          # Kalideres, Jakarta Barat
DAY = 0                         # 0 = hari ini, 1 = besok
KEYWORDS = ["hujan", "banjir"]  # kata yang berarti "akan hujan"
USE_DUMMY = False               # True = ikutkan data uji dari dummy site


# ===== Fungsi-fungsi =====

# Ambil prakiraan dari BMKG
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


# Ambil prakiraan dari dummy site
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


# Cek apakah ada kata hujan/banjir di daftar prakiraan
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

lines = ["Cuaca Kalideres, Jakarta Barat"]

# Sumber 1: BMKG
bmkg = get_bmkg()
lines.append("")
lines.append("[BMKG]")
for forecast in bmkg:
    lines.append(f"{forecast['jam']} - {forecast['desc']}")
rain_expected = is_rain(bmkg)

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
lines.append("Sumber: BMKG")

message = "\n".join(lines)
print(message)
send_telegram(message)