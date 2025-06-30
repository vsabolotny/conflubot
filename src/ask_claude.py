import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from anthropic import Anthropic
from anthropic._exceptions import OverloadedError

# .env laden
load_dotenv()

# Konfiguration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "confluence_knowledge")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")  # Updated default model

# Initialisierung
client = QdrantClient(url=f"http://{QDRANT_HOST}:{QDRANT_PORT}")
embedder = SentenceTransformer("paraphrase-MiniLM-L6-v2")
anthropic = Anthropic(api_key=CLAUDE_API_KEY)

def get_context(query: str, top_k=3):
    """
    Findet die relevantesten Text-Chunks für eine gegebene Anfrage
    mithilfe von Vektor-Ähnlichkeitssuche in Qdrant.
    """
    query_embedding = embedder.encode(query).tolist()

    # Use query_points instead of the deprecated search method
    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        with_payload=True
    )
    # The result object is now in search_result.points
    return search_result.points

def build_prompt(query: str, context_chunks):
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"Dokument {i+1} (Quelle: {chunk.payload.get('source', 'Unbekannte Quelle')}, Seite: {chunk.payload.get('page', '?')}):\n{chunk.payload.get('text', '')}\n\n"
    
    # The prompt for the Messages API is just the user's request.
    # The system prompt will be handled separately.
    user_prompt = (
        f"Bitte beantworte die folgende Frage nur auf Basis des bereitgestellten Kontexts.\n\n"
        f"--- BEGINN KONTEXT ---\n{context_text}--- ENDE KONTEXT ---\n\n"
        f"Frage: {query}"
    )
    return user_prompt

def ask_claude(prompt: str, max_retries=3):
    # System prompt defines the AI's role and rules.
    system_prompt = "Du bist ein hilfreicher Assistent, der Fragen auf Basis interner Wissensdokumente beantwortet. Wenn die Antwort nicht im Kontext enthalten ist, sage ehrlich 'Ich weiß es nicht.'"
    
    for attempt in range(max_retries):
        try:
            # Use the Messages API for Claude 3 models
            response = anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            # The response content is in a different location in the Messages API
            return response.content[0].text.strip()
        except OverloadedError as e:
            if attempt < max_retries - 1:
                # Use exponential backoff for retries (e.g., 1s, 2s, 4s)
                wait_time = 2 ** attempt
                print(f"Server is overloaded. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print("Server is still overloaded after multiple retries. Please try again later.")
                raise e # Re-raise the exception if all retries fail

if __name__ == "__main__":
    frage = input("❓ Deine Frage: ")

    print("🔍 Suche nach relevantem Kontext...")
    context_chunks = get_context(frage)

    print("🧠 Erzeuge Prompt und frage Claude...")
    prompt = build_prompt(frage, context_chunks)
    antwort = ask_claude(prompt)

    print("\n💬 Antwort von Claude:")
    print(antwort)