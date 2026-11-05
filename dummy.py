from bs4 import BeautifulSoup

KEYWORDS = ["hujan", "banjir"]

# 1. Buka file HTML dan baca isinya sebagai teks
with open("dummy/index.html", encoding="utf-8") as f:
    html = f.read()

# 2. Ubah teks HTML menjadi objek yang bisa dicari
soup = BeautifulSoup(html, "html.parser")

# 3. Cari semua kotak prakiraan
rain_expected = False
for item in soup.find_all("div", class_="forecast"):
    jam = item.find("p", class_="time").text
    desc = item.find("p", class_="desc").text
    print(jam, "|", desc)

    if any(word in desc.lower() for word in KEYWORDS):
        rain_expected = True

print("Hujan diperkirakan:", rain_expected)