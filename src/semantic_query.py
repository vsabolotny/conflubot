import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import numpy as np

# .env laden
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "confluence_knowledge")

# Initialisiere Qdrant und Embedding-Modell
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def semantic_search(query: str, top_k: int = 3):
    print(f"🔎 Frage: {query}")
    query_vector = model.encode(query).tolist()

    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True
    )

    print(f"🎯 Top {top_k} Treffer:")
    for i, hit in enumerate(search_result):
        title = hit.payload.get("title", "Ohne Titel")
        url = hit.payload.get("url", "Ohne URL")
        text = hit.payload.get("text", "")[:200].replace("\n", " ") + "..."
        print(f"\n{i+1}. 📄 {title}")
        print(f"🔗 {url}")
        print(f"🧠 {text}")

if __name__ == "__main__":
    frage = input("❓ Deine Frage: ")
    semantic_search(frage)