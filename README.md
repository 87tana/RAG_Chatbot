# RAG_Chatbot

Adaptive Retrieval-Augmented Generation (RAG) Chatbot

Live Demo: [azureragchatbotapp.azurewebsites.net]

This repository contains a Streamlit-based application that uses Azure OpenAI and Azure Cognitive Search (or Chroma) to semantically ingest, index, and query text datasets (e.g., CSV files) stored in Azure Blob Storage, delivering context-rich, on-demand insights.

## Featues:

- Semantic Ingestion: Automatically load and deduplicate text entries from CSV files in Azure Blob Storage.

- Dynamic Indexing: Monitor CSV additions, modifications, and deletions and sync changes to Azure Cognitive Search or a local Chroma DB.

- RAG QA Pipeline: Use LangChain’s RetrievalQA with Azure OpenAI for context-aware question answering.

- Interactive UI: User-friendly chat interface built with Streamlit.

- Flexible Vector Store: Switch between Azure Cognitive Search and Chroma via a single environment variable.

## Architecture:
    Data Source: CSV files residing in an Azure Blob Storage container, each containing a content column.

    Indexing Module: indexing_utils.py monitors blob storage, computes file hashes, and updates the vector index.

    Embedding Service: Azure OpenAI Embeddings generate semantic vectors for ingested text.

    Vector Store: Azure Cognitive Search or Chroma serves as the retrieval backend.

    QA Chain: LangChain’s RetrievalQA composes retrieval and Azure Chat OpenAI to answer queries.

    Streamlit UI: app.py stitches everything into an interactive chat experience.

## Prerequisites & Installation:

- Python 3.8 or higher

- Azure account with:

    - Blob Storage account and container for CSV files

    - Azure OpenAI resource with deployed models for embeddings and chat

    - Azure Cognitive Search service (if using vector_db_type=azure)

- Azure CLI

## Running the App & Usage: 
- Start the Streamlit application:  streamlit run app.py

## Usage

    - Enter questions in the chat input box related to your ingested documents.

    - The app maintains a conversation history during your session.

    - If no CSV files are found, a dummy document is loaded to keep the chatbot functional.

## Using Your Own Data

- To test the RAG Chatbot with your own documents (for example, research papers):

    - Prepare Your Data: Export your papers or sections (e.g., abstracts, full text) into one or more CSV files, each with a content column.

    - Upload to Blob Storage: Place these CSV files into your configured Azure Blob Storage container. The app will automatically pick up new or updated files when you restart or invoke reindexing.

    - Run the App: Start the Streamlit app (streamlit run app.py) and navigate to the UI. Your uploaded documents will be ingested and indexed on launch.

    - Query: Ask questions naturally—e.g., “Summarize the methodology of paper X” or “What are the key findings across all uploaded papers?”

- Tip: For quick local testing without Azure, set VECTOR_DB_TYPE=chroma, place your CSV files under a ./data folder, and adjust the ingestion code to read from local files instead of Blob Storage.

## Vector Store Options 

- azure: Uses Azure Cognitive Search with semantic search capabilities.

- chroma: Uses a local Chroma vector database persisted under ./chroma_db.

## How It Works:

- Blob Loading: app.py fetches all CSV blobs, extracts the content column, and deduplicates entries.

- Index Sync: reindex_if_blob_changed checks for file changes, computes hashes, and updates the vector index accordingly.

- Embedding: Text documents are converted to semantic vectors via Azure OpenAI Embeddings.

- Retrieval: A retriever pulls top-k relevant documents for each query.

- Generation: Azure Chat OpenAI LLM crafts a response based on retrieved context.

- Display: Streamlit chat UI renders the conversation.

## Deployment

- Azure App Service: Containerize with Docker or use Python runtime.

- Streamlit Cloud: Directly deploy your repo, set environment variables in the dashboard.

## Docker:

- Create a Dockerfile with Python and Streamlit dependencies.

- Build and push to a container registry.

- Deploy to your chosen service.