import requests

url = "https://bpbd.jakarta.go.id/waterlevel"
r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})

print("Status:", r.status_code)
print("Ada Angke?", "Angke" in r.text)

from bs4 import BeautifulSoup

soup = BeautifulSoup(r.text, "html.parser")

for row in soup.find_all("tr"):
    cells = row.find_all("td")
    if cells and "Angke Hulu" in cells[0].text:
        latest = None
        for cell in cells[1:]:              # lewati kolom nama pos
            if cell.get_text(strip=True):   # hanya kolom yang ada isinya
                latest = cell

        text = latest.get_text(strip=True)  # "40 cm (T)"
        cuaca = text[-2]                    # "T"
        siaga = latest.get("class")[0]      # "siaga4"
        print("Teks:", text)
        print("Kode cuaca:", cuaca)
        print("Status:", siaga)