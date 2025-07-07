import os
import traceback
import time
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

def ask_claude(user_prompt: str, max_retries: int = 3):
    """
    Sends a prompt to the Anthropic Claude model with retry logic for overloaded errors.
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempting to call Claude API (Attempt {attempt + 1}/{max_retries})...")
            message = anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except APIStatusError as e:
            # Check if the error is due to the service being overloaded (status code 529)
            if e.status_code == 529 and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2, 4 seconds
                print(f"Claude API is overloaded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"An unrecoverable API error occurred after retries or for a non-retriable status: {e}")
                raise e # Re-raise the exception

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
        # 1. Search for relevant context in Qdrant
        context_results = search_qdrant(request.question, request.top_k)
        
        if not context_results:
            return AskResponse(answer="I couldn't find any relevant information in the knowledge base to answer your question.", sources=[])

        # 2. Build the prompt for Claude
        context = "\n\n".join([f"Source: {res['url']}\nContent: {res['text']}" for res in context_results])
        
        user_prompt = f"""{HUMAN_PROMPT}
        Based on the following context from our knowledge base, please answer the user's question.
        Answer in the same language as the user's question.
        Cite the sources you used in your answer using markdown links like [Source Title](URL).

        Context:
        {context}

        Question: {request.question}
        {AI_PROMPT}
        """

        # 3. Get the answer from Claude
        answer = ask_claude(user_prompt)

        # 4. Format and return the response
        sources = [{"title": res["title"], "url": res["url"]} for res in context_results]
        return AskResponse(answer=answer, sources=sources)

    except APIStatusError as e:
        # Specifically handle API errors after retries
        if e.status_code == 529:
            raise HTTPException(status_code=503, detail="The service is temporarily overloaded. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"An unexpected API error occurred: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        # The generic exception handler will catch this and return a 500 error
        raise e

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/version")
def get_version():
    return {"version": "1.0.0"}