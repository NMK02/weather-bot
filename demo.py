import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"
response = requests.post(url, data={"chat_id": chat_id, "text": "Hello from weather-bot!"})
print(response.status_code, response.json())