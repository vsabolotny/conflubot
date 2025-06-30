import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# .env laden
load_dotenv()

# Konfiguration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "confluence_knowledge")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240620")

# Initialisierung
app = FastAPI(title="Claude Confluence Bot API")
embedder = SentenceTransformer("paraphrase-MiniLM-L6-v2")
qdrant = QdrantClient(url=f"http://{QDRANT_HOST}:{QDRANT_PORT}")
anthropic = Anthropic(api_key=CLAUDE_API_KEY)

# Datamodelle
class AskRequest(BaseModel):
    question: str
    top_k: int = 3

class AskResponse(BaseModel):
    answer: str
    context_used: list

# Hilfsfunktionen
def get_context(query: str, top_k: int):
    """
    Findet die relevantesten Text-Chunks für eine gegebene Anfrage.
    """
    query_embedding = embedder.encode(query).tolist()
    
    # FIX: The keyword argument is 'query', not 'vector'.
    search_result = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        with_payload=True
    )
    return search_result.points

def build_prompt(query: str, context_chunks):
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"Dokument {i+1} (Titel: {chunk.payload.get('title', 'ohne Titel')}):\n{chunk.payload.get('text', '')}\n\n"
    return (
        f"{HUMAN_PROMPT} Du bist ein hilfreicher Assistent, der Fragen auf Basis interner Wissensdokumente beantwortet. "
        f"Nutze nur den folgenden Kontext. Wenn die Antwort nicht enthalten ist, sage \"Ich weiß es nicht.\"\n\n"
        f"{context_text}\n"
        f"Frage: {query}\n"
        f"{AI_PROMPT}"
    )

def ask_claude(user_prompt: str) -> str:
    """
    Fragt das Claude-Modell mit dem bereitgestellten Prompt über die Messages API.
    """
    # FIX: Use the Messages API for Claude 3.5 Sonnet
    system_prompt = "Du bist ein hilfreicher Assistent, der Fragen auf Basis interner Wissensdokumente beantwortet. Wenn die Antwort nicht im Kontext enthalten ist, sage ehrlich 'Ich weiß es nicht.'"
    
    response = anthropic.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.content[0].text.strip()

# API-Endpunkte
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        context_chunks = get_context(req.question, req.top_k)
        
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            source = chunk.payload.get('source', 'Unbekannte Quelle')
            page = chunk.payload.get('page', '?')
            text = chunk.payload.get('text', '')
            context_text += f"Dokument {i+1} (Quelle: {source}, Seite: {page}):\n{text}\n\n"

        user_prompt = (
            f"Bitte beantworte die folgende Frage nur auf Basis des bereitgestellten Kontexts.\n\n"
            f"--- BEGINN KONTEXT ---\n{context_text}--- ENDE KONTEXT ---\n\n"
            f"Frage: {req.question}"
        )

        answer = ask_claude(user_prompt)
        
        context_list = [chunk.payload for chunk in context_chunks]
        return AskResponse(answer=answer, context_used=context_list)

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")