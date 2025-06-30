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
    vector = embedder.encode(query).tolist()
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        vector=vector,
        limit=top_k,
        with_payload=True
    )
    return results

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

def ask_claude(prompt: str) -> str:
    response = anthropic.completions.create(
        model=CLAUDE_MODEL,
        max_tokens_to_sample=500,
        prompt=prompt
    )
    return response.completion.strip()

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
        context = get_context(req.question, req.top_k)
        prompt = build_prompt(req.question, context)
        answer = ask_claude(prompt)

        context_used = [
            {
                "title": c.payload.get("title", "ohne Titel"),
                "url": c.payload.get("url", ""),
                "text": c.payload.get("text", "")[:200] + "..."
            } for c in context
        ]

        return AskResponse(answer=answer, context_used=context_used)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))