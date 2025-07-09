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
    cd conflubot
    ```
2.  **Create and configure the environment file:**
    Copy the template to a new `.env` file and fill in your credentials.
    ```bash
    cp .env.template .env
    ```
    Now edit `.env` with your details.

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---
## 🐳 Running with Docker

This project is fully containerized. You can run the Qdrant vector database and the FastAPI application using Docker.

### 1. Start Qdrant Database
You can start the Qdrant service using the provided Docker Compose file:
```bash
docker-compose up -d qdrant
```
The Qdrant dashboard will be available at [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

### 2. Build the Application Image
Build the Docker image for the FastAPI application using the Dockerfile:
```bash
docker build -t conflubot .
```

### 3. Run the Application Container
Run the application container, making sure to pass the environment variables from your .env file.
```bash
docker run --rm -p 8000:8000 --env-file .env conflubot
```
*Note: `--network=host` is used here to allow the application container to connect to Qdrant running on `localhost`. For more robust setups, consider using a shared Docker network.*

The API will be available at http://localhost:8000.

---

## ⚙️ Usage

### 1. Ingest Data
Run the 

embed_to_qdrant.py

 script to fetch documents from Confluence, create embeddings, and load them into Qdrant.
```bash
python src/embed_to_qdrant.py
```

### 2. Ask Questions (Interactive)
Run the 

ask_claude.py

 script to start an interactive Q&A session in your terminal.
```bash
python src/ask_claude.py
```

### 3. Start the API (Local Development)
If you are not using Docker, you can run the FastAPI app directly with `uvicorn` for local development with hot-reloading.
```bash
uvicorn main:app --reload
```

---
## ☁️ AWS Deployment

The following commands outline the process for pushing the application's Docker image to Amazon ECR.

1.  **Create ECR Repository (private):**
    ```bash
    aws ecr create-repository --repository-name conflubot --region eu-central-1
    ```
    Or you can create a public repository:
    ```bash
    aws ecr-public create-repository --repository-name conflubot --region us-east-1
    ```

2.  **Login to ECR:**
    ```bash
    aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <your_aws_account_id>.dkr.ecr.eu-central-1.amazonaws.com
    ```
3.  **Tag and Push the Image:**
    ```bash
    docker tag conflubot:latest <your_aws_account_id>.dkr.ecr.eu-central-1.amazonaws.com/conflubot:latest
    docker push <your_aws_account_id>.dkr.ecr.eu-central-1.amazonaws.com/conflubot:latest
    ```

---
## 📝 License

This project is licensed under the MIT License.
