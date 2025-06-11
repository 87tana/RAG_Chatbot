# Adaptive Retrieval-Augmented Generation (RAG) Chatbot

**Live Demo**: [azureragchatbotapp.azurewebsites.net](https://azureragchatbotapp.azurewebsites.net) ([Status](https://status.azure.com) - Demo availability may depend on Azure hosting)

This repository contains a Streamlit-based application that uses Azure OpenAI and Azure Cognitive Search (or Chroma) to semantically ingest, index, and query text datasets (e.g., CSV files) stored in Azure Blob Storage, delivering context-rich, on-demand insights.

## Features:

- Semantic Ingestion: Automatically load and deduplicate text entries from CSV files in Azure Blob Storage.

- Dynamic Indexing: Monitor CSV additions, modifications, and deletions and sync changes to Azure Cognitive Search or a local Chroma DB.

- RAG QA Pipeline: Use LangChain’s RetrievalQA with Azure OpenAI for context-aware question answering.

- Interactive UI: User-friendly chat interface built with Streamlit.

- Flexible Vector Store: Switch between Azure Cognitive Search and Chroma via a single environment variable.

## Architecture: system's components, their interactions, and data flow

   - Data Source: CSV files residing in an Azure Blob Storage container, each containing a content column.

   - Indexing Module: indexing_utils.py monitors blob storage, computes file hashes, and updates the vector index.

   - Embedding Service: Azure OpenAI Embeddings generate semantic vectors for ingested text.

   - Vector Store: Azure Cognitive Search or Chroma serves as the retrieval backend.

   - QA Chain: LangChain’s RetrievalQA composes retrieval and Azure Chat OpenAI to answer queries.

   - Streamlit UI: app.py stitches everything into an interactive chat experience.

## Vector Store Options 

- azure: Uses Azure Cognitive Search with semantic search capabilities.

- chroma: Uses a local Chroma vector database persisted under ./chroma_db.

## Prerequisites & Installation:

- Python 3.8 or higher

- Azure account with:

    - Blob Storage account and container for CSV files

    - Azure OpenAI resource with deployed models for embeddings and chat

    - Azure Cognitive Search service (if using vector_db_type=azure)

- Azure CLI
- (Optional) Docker for containerized deployment

## Installation

git clone https://github.com/87tana/RAG_Chatbot.git
cd RAG_Chatbot

## Install dependencies

pip install -r requirements.txt

## Set up environment variables in a .env file:

AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_SEARCH_KEY=<your-key>
AZURE_SEARCH_ENDPOINT=<your-endpoint>
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
VECTOR_DB_TYPE=<azure|chroma>

## Running the App : 
- Start the Streamlit application:  "streamlit run app.py"

## Usage

    - Enter questions in the chat input box related to your ingested documents.

    - The app maintains a conversation history during your session.

    - If no CSV files are found, a dummy document is loaded to keep the chatbot functional.

## Using Your Own Data

- To test the RAG Chatbot with your own documents (for example, research papers or any private data):

    - Prepare Your Data: Export your document into one or more CSV files, each with a content column.

    - Upload to Blob Storage: Place these CSV files into your configured Azure Blob Storage container. The app will automatically pick up new or updated files when you restart or invoke reindexing.

    - Run the App: Start the Streamlit app (streamlit run app.py) and navigate to the UI. Your uploaded documents will be ingested and indexed on launch.

- Local Testing Tip:: Set VECTOR_DB_TYPE=chroma, place CSV files in a ./data folder, and modify ingestion code to read locally instead of from Blob Storage.

## How It Works:

- Blob Loading: app.py fetches all CSV blobs, extracts the content column, and deduplicates entries.

- Index Sync: reindex_if_blob_changed checks for file changes, computes hashes, and updates the vector index accordingly.

- Embedding: Text documents are converted to semantic vectors via Azure OpenAI Embeddings.

- Retrieval: A retriever pulls top-k relevant documents for each query.

- Generation: Azure Chat OpenAI LLM crafts a response based on retrieved context.

- Display: Streamlit chat UI renders the conversation.

## Error Handling

- Missing CSV Files: Loads a dummy document to ensure functionality.

- Invalid CSV Format: Skips files without a content column and logs an error.

- Connection Issues: Retries Azure API calls with exponential backoff.

## Performance Considerations

- CSV Size: Indexing large CSV files (>1GB) may increase processing time. Split large files for better performance.

- Indexing Time: Initial indexing depends on dataset size and Azure API latency (typically 1-5 seconds per 1000 text entries).

- Scalability: Azure Cognitive Search is recommended for large datasets; Chroma suits smaller, local deployments.

## Deployment

- Azure App Service: Containerize with Docker or use Python runtime.

- Streamlit Cloud: Directly deploy your repo, set environment variables in the dashboard.

## Docker:

1. Create a Dockerfile:

# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy your app files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

2. Build and Push

docker build -t rag-chatbot .
docker push <your-registry>/rag-chatbot