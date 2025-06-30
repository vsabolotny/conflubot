import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# .env laden
load_dotenv()

# Variablen auslesen
BASE_URL = os.getenv("CONFLUENCE_URL")
SPACE_KEY = os.getenv("CONFLUENCE_SPACE")
EMAIL = os.getenv("CONFLUENCE_EMAIL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json"
}

def get_pages(limit=5):
    url = f"{BASE_URL}/rest/api/content"
    params = {
        "limit": limit,
        "spaceKey": SPACE_KEY,
        "expand": "body.storage"
    }

    response = requests.get(url, headers=headers, auth=auth, params=params)

    if response.status_code != 200:
        raise Exception(f"Fehler bei Anfrage: {response.status_code} - {response.text}")

    data = response.json()
    return data.get("results", [])

# Beispielnutzung
if __name__ == "__main__":
    pages = get_pages()
    for page in pages:
        print(f"\n📄 {page['title']}\n")
        print(page["body"]["storage"]["value"][:500])  # Zeige ersten 500 Zeichen