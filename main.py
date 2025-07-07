import os
import traceback
import time
import random
import anthropic
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT, APIStatusError

# Disable tokenizer parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load .env file
load_dotenv()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_USE_SSL = os.getenv("QDRANT_USE_SSL", "false").lower() == "true"
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "confluence_knowledge")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240620")
API_KEY = os.getenv("API_KEY")

# Initialization
app = FastAPI(title="Claude Confluence Bot API (with Auth)")
embedder = SentenceTransformer("paraphrase-MiniLM-L6-v2")
anthropic = Anthropic(api_key=CLAUDE_API_KEY)

# Initialize Qdrant client based on configuration
if QDRANT_API_KEY:
    # Production setup with API key
    print("QDRANT_API_KEY found, connecting with API key.")
    qdrant = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY,
        https=QDRANT_USE_SSL,
    )
else:
    # Local setup without API key
    print("QDRANT_API_KEY not found, connecting without API key.")
    qdrant = QdrantClient(
        host=QDRANT_HOST, 
        port=QDRANT_PORT,
        https=QDRANT_USE_SSL
    )

# API-Key Auth Dependency
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Data models
class AskRequest(BaseModel):
    question: str
    top_k: int = 3

class AskResponse(BaseModel):
    answer: str
    sources: list[dict]

# Helper functions
def search_qdrant(query: str, top_k: int):
    vector = embedder.encode(query).tolist()
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=top_k,
        with_payload=True
    )
    return [hit.payload for hit in hits]

def call_claude_throttled(prompt, delay=2, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(delay)  # delay between attempts
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return response.content[0].text if hasattr(response, "content") else response
        except APIStatusError as e:
            if getattr(e, "status_code", None) == 529:
                wait = delay + attempt + random.uniform(0.1, 0.5)
                print(f"Overloaded. Waiting {wait:.2f}s before retry...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Failed after retries due to overload.")

# Exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"type": "error", "error": {"type": "internal_server_error", "message": str(exc)}},
    )

# API Endpoints
@app.post("/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
def ask(request: AskRequest):
    try:
        print(f"[DEBUG] Received /ask request: question='{request.question}', top_k={request.top_k}")

        # 1. Search for relevant context in Qdrant
        context_results = search_qdrant(request.question, request.top_k)
        print(f"[DEBUG] Qdrant search returned {len(context_results) if context_results else 0} results")

        # Print up to 3 search results for debugging
        for i, res in enumerate(context_results[:3]):
            print(f"[DEBUG] Search result {i+1}: title='{res.get('title')}', url='{res.get('url')}', text='{res.get('text')[:100]}...'")

        if not context_results:
            print("[DEBUG] No relevant context found in Qdrant")
            return AskResponse(answer="I couldn't find any relevant information in the knowledge base to answer your question.", sources=[])

        # 2. Build the prompt for Claude
        context = "\n\n".join([f"Source: {res['url']}\nContent: {res['text']}" for res in context_results])
        print(f"[DEBUG] Built context for prompt with {len(context_results)} sources")

        user_prompt = f"""{HUMAN_PROMPT}
        Based on the following context from our knowledge base, please answer the user's question.
        Answer in the same language as the user's question.
        Cite the sources you used in your answer using markdown links like [Source Title](URL).

        Context:
        {context}

        Question: {request.question}
        {AI_PROMPT}
        """
        print("[DEBUG] User prompt for Claude constructed")

        # 3. Get the answer from Claude
        answer = call_claude_throttled(user_prompt)
        print("[DEBUG] Received answer from Claude")

        # 4. Format and return the response
        sources = [{"title": res["title"], "url": res["url"]} for res in context_results]
        print(f"[DEBUG] Returning response with {len(sources)} sources")
        return AskResponse(answer=answer, sources=sources)

    except APIStatusError as e:
        print(f"[ERROR] APIStatusError: {e} (status_code={e.status_code})")
        # Specifically handle API errors after retries
        if e.status_code == 529:
            raise HTTPException(status_code=503, detail="The service is temporarily overloaded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"An unexpected API error occurred: {e}")

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()
        # The generic exception handler will catch this and return a 500 error
        raise e

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/version")
def get_version():
    return {"version": "1.0.0"}