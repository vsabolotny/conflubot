import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import uuid

# Load environment variables from .env file
load_dotenv()

BASE_URL = os.getenv("CONFLUENCE_URL")
SPACE_KEY = os.getenv("CONFLUENCE_SPACE")
EMAIL = os.getenv("CONFLUENCE_EMAIL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "confluence_knowledge")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = { "Accept": "application/json" }

# Qdrant configuration
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_use_ssl = os.getenv("QDRANT_USE_SSL", "false").lower() == "true"

# Initialize Qdrant client based on configuration
if qdrant_api_key:
    # Production setup with API key
    qdrant_client = QdrantClient(
        host=qdrant_host,
        port=qdrant_port,
        api_key=qdrant_api_key,
        https=qdrant_use_ssl,
    )
    print("Connecting to Qdrant Cloud with API key.")
else:
    # Local setup without API key
    qdrant_client = QdrantClient(
        host=qdrant_host, 
        port=qdrant_port,
        https=qdrant_use_ssl
    )
    print("Connecting to local Qdrant instance.")

# Seiten abrufen
def get_pages(limit=10):
    url = f"{BASE_URL}/rest/api/content"
    params = {
        "limit": limit,
        "spaceKey": SPACE_KEY,
        "expand": "body.storage"
    }
    response = requests.get(url, headers=headers, auth=auth, params=params)
    if response.status_code != 200:
        raise Exception(f"Fehler bei Anfrage: {response.status_code} - {response.text}")
    return response.json().get("results", [])

# HTML zu Text
def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

# Text chunken
def chunk_text(text, max_words=100):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words) if len(words[i:i+max_words]) > 5]

# Collection initialisieren oder ersetzen
def init_collection(dim):
    if qdrant_client.collection_exists(COLLECTION_NAME):
        qdrant_client.delete_collection(COLLECTION_NAME)

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "size": dim,
            "distance": "Cosine"
        }
    )

# Embedding und Upload
def embed_and_upload(chunks, metadaten):
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    vectors = model.encode(chunks)
    init_collection(vectors.shape[1])

    points = []
    for i, (vec, meta) in enumerate(zip(vectors, metadaten)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload=meta
        )
        points.append(point)

    qdrant_client.upload_points(
        collection_name=COLLECTION_NAME,
        points=points,
    )
    print(f"✅ {len(points)} Chunks gespeichert in Qdrant (Collection: {COLLECTION_NAME})")

# Hauptprozess
if __name__ == "__main__":
    print("🔍 Lade Confluence Seiten ...")
    pages = get_pages()

    all_chunks = []
    all_meta = []

    for page in pages:
        title = page["title"]
        html = page["body"]["storage"]["value"]
        url = f"{BASE_URL}/pages/viewpage.action?pageId={page['id']}"
        text = html_to_text(html)
        chunks = chunk_text(text)

        for chunk in chunks:
            all_chunks.append(chunk)
            all_meta.append({
                "title": title,
                "url": url,
                "text": chunk
            })

        print(f"📄 {title}: {len(chunks)} Chunks")

    print(f"📦 Gesamt: {len(all_chunks)} Chunks")
    embed_and_upload(all_chunks, all_meta)