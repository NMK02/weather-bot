import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ADM4 = "31.73.06.1001"  # Kalideres, Jakarta Barat
KEYWORDS = ["hujan", "banjir"]  # kata yang dianggap "hujan"

# 1. Ambil data dari BMKG
url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={ADM4}"
data = requests.get(url, timeout=30).json()
lokasi = data["lokasi"]
today = data["data"][0]["cuaca"][0]

# 2. Cek aturan: ada kata "hujan"/"banjir" di prakiraan hari ini?
rain_expected = False
for forecast in today:
    desc = forecast["weather_desc"].lower()
    if any(word in desc for word in KEYWORDS):
        rain_expected = True

if rain_expected:
    suggestion = "☔ Bawa payung dan pakai sunscreen"
else:
    suggestion = "☀️ Pakai sunscreen"

# 3. Susun pesan
lines = [f"Cuaca {lokasi['desa']}, {lokasi['kotkab']}, {lokasi['provinsi']}"]
for forecast in today:
    jam = forecast["local_datetime"][11:16]  # ambil "22:00" saja
    lines.append(f"{jam} - {forecast['weather_desc']}, {forecast['t']}°C")
lines.append("")
lines.append(f"Saran: {suggestion}")
lines.append("Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)")
message = "\n".join(lines)
print(message)

# 4. Kirim ke Telegram
tg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
r = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": message}, timeout=30)
print("Telegram:", r.status_code)