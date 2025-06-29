from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 1. Textdaten vorbereiten
texts = [
    "Ich liebe Pizza.",
    "Katzen sind tolle Haustiere.",
    "Der Himmel ist blau.",
    "Ich mag Pasta und italienisches Essen.",
    "Hunde sind sehr loyal."
]

# 2. Embedding-Modell laden
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# 3. Texte in Vektoren umwandeln
embeddings = model.encode(texts)

# 4. FAISS Index erstellen (für cosine similarity normalisieren wir)
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # IP = inner product = cosine similarity (nach Normalisierung)
faiss.normalize_L2(embeddings)        # Wichtig für cosine similarity
index.add(embeddings)                 # Vektoren speichern

# 5. Beispielabfrage
query = "Ich esse gern italienisch."
query_embedding = model.encode([query])
faiss.normalize_L2(query_embedding)

# 6. Suche starten (Top 3 ähnliche Texte)
k = 3
distances, indices = index.search(query_embedding, k)

# 7. Ausgabe
print(f"Query: {query}\n")
print("Top 3 ähnliche Sätze:")
for i in range(k):
    print(f"{i+1}. {texts[indices[0][i]]} (Score: {distances[0][i]:.2f})")