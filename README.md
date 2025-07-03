# Confluence Q&A with Claude & Qdrant

This project provides a question-answering system that uses a Large Language Model (Claude 3.5 Sonnet) to answer questions based on knowledge stored in a Confluence space. It uses Qdrant as a vector database to perform efficient similarity searches for relevant context.

---

## ✨ Features

-   **Data Ingestion**: Fetches pages from a specified Confluence space.
-   **Vector Embeddings**: Converts document chunks into vector embeddings using `sentence-transformers`.
-   **Vector Storage**: Stores and indexes embeddings in a Qdrant collection for fast retrieval.
-   **RAG Pipeline**: Implements a Retrieval-Augmented Generation (RAG) pipeline.
-   **Question Answering**: Uses Anthropic's Claude 3.5 Sonnet model to generate answers based on the retrieved context.

---

## 🚀 Getting Started

### 1. Prerequisites

-   Python 3.10+
-   Access to a Confluence space with an API token.
-   An Anthropic API key.
-   Docker and Docker Compose (for running Qdrant).

### 2. Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd vektor-exp
    ```

2.  **Set up Qdrant:**
    The easiest way to run Qdrant is with Docker.
    ```bash
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
    Your Qdrant dashboard will be available at [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

3.  **Create and configure the environment file:**
    Copy the template to a new `.env` file and fill in your credentials.
    ```bash
    cp .env.template .env
    ```
    Now edit `.env` with your details:
    ```properties
    # Confluence configuration
    CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
    CONFLUENCE_SPACE=YOURSPACEKEY
    CONFLUENCE_EMAIL=your-email@example.com
    CONFLUENCE_API_TOKEN=your-confluence-api-token

    # Qdrant configuration
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    QDRANT_COLLECTION=confluence_knowledge

    # Anthropic configuration
    ANTHROPIC_API_KEY=your-anthropic-api-key
    CLAUDE_MODEL=claude-3-5-sonnet-20240620
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Usage

1.  **Start Qdrant (Vector Database):**
    The easiest way to run Qdrant is with Docker:
    ```bash
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
    The Qdrant dashboard will be available at [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

2.  **Ingest Data:**
    Run the `ingest.py` script to fetch documents from Confluence, create embeddings, and load them into Qdrant.
    ```bash
    python src/ingest.py
    ```

3.  **Ask Questions:**
    Run the `ask_claude.py` script to start the interactive Q\&A session.
    ```bash
    python src/ask_claude.py
    ```

4.  **Start the API:**
    If you want to run the FastAPI app (e.g., in `main.py`), use:
    ```bash
    uvicorn main:app --reload
    ```
    This will start the API locally with hot-reloading. Make sure `uvicorn` is installed (`pip install uvicorn`).

---

## 📝 Lizenz

This project is licensed under the MIT License.


## AWS 

aws ecr create-repository --repository-name claude-confluence-bot --region us-east-1

aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 456359847368.dkr.ecr.eu-central-1.amazonaws.com

aws ecr describe-repositories

## Push build to AWS

docker build -t claude-bot .
docker tag claude-bot 456359847368.dkr.ecr.eu-central-1.amazonaws.com/claude-confluence-bot:latest

aws ecr get-login-password --region eu-central-1 | \
docker login --username AWS --password-stdin 456359847368.dkr.ecr.eu-central-1.amazonaws.com
                             
docker push 456359847368.dkr.ecr.eu-central-1.amazonaws.com/claude-confluence-bot:latest


