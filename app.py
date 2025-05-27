"""
Streamlit app for a RAG chatbot using Azure OpenAI and Azure Cognitive Search.
Automatically reindexes CSV data stored in Azure Blob Storage using a helper module.
"""

import os
import io
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from indexing_utils import reindex_if_blob_changed  # <-- your reindexing module

# --- Load environment variables from .env file ---
load_dotenv()

# --- Configure Streamlit UI ---
st.set_page_config(page_title="RAG Chatbot", page_icon="💬", layout="wide")
st.title("💬 RAG Chatbot with Azure OpenAI")

# --- Load documents from Azure Blob CSVs ---
def load_documents_from_blob(container_name):
    """Loads unique text entries from all CSV files in the given Azure Blob container."""
    from azure.storage.blob import BlobServiceClient

    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)

    docs = []
    for blob in container_client.list_blobs():
        if blob.name.endswith(".csv"):
            blob_data = container_client.download_blob(blob.name).readall()
            df = pd.read_csv(io.BytesIO(blob_data))
            if "content" in df.columns:
                docs.extend(df["content"].dropna().astype(str).tolist())

    return list(set(docs))  # remove duplicates

# --- Load knowledge base documents ---
with st.spinner("📂 Loading knowledge base from Blob Storage..."):
    try:
        raw_texts = load_documents_from_blob(os.getenv("AZURE_STORAGE_CONTAINER"))
        if not raw_texts:
            st.error("❌ No valid 'content' columns found in any CSV files.")
            st.stop()
        documents = [Document(page_content=text) for text in raw_texts]
    except Exception as e:
        st.error(f"❌ Failed to load documents: {e}")
        st.stop()

# --- Set up Azure OpenAI Embeddings ---
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)

# --- Check for changes in Blob Storage and reindex if needed ---
with st.spinner("🔍 Checking for new or removed CSVs in Azure Blob Storage..."):
    try:
        changed = reindex_if_blob_changed()
        if changed:
            st.success("✅ Index updated from new or changed CSV files.")
    except Exception as e:
        st.error(f"❌ Failed to check blob changes: {e}")

# --- Set up Azure Cognitive Search retriever ---
azure_search = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    embedding_function=embeddings.embed_query
)
retriever = azure_search.as_retriever()

# --- Set up Azure OpenAI chat model ---
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2023-05-15",
    temperature=0
)

# --- Build RAG chain ---
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever
)

# --- Session state for persistent chat history ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Chat UI ---
query = st.chat_input("Ask a question about the documents...")

if query:
    with st.spinner("🤔 Thinking..."):
        try:
            response = qa_chain.invoke({"query": query})
            answer = response["result"]
            st.session_state.history.append((query, answer))
        except Exception as e:
            import traceback
            traceback.print_exc()
            st.session_state.history.append((query, f"⚠️ Error: {e}"))

# --- Display chat history ---
for question, answer in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        st.markdown(answer)