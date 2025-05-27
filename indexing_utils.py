"""
Module: indexing_utils
Purpose: Monitor Azure Blob Storage for CSV file changes (add/update/delete) and keep Azure Cognitive Search index in sync.
"""

import os
import io
import json
import base64
import hashlib
import pandas as pd
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField
)

def compute_blob_hash(blob_data: bytes) -> str:
    """Compute SHA256 hash of blob content."""
    return hashlib.sha256(blob_data).hexdigest()

def reindex_if_blob_changed():
    """
    Reindexes Azure Cognitive Search index if any CSV blob in the container was added, updated, or deleted.
    Uses SHA256 content hash to detect changes.
    Returns True if index was modified, False otherwise.
    """
    # Load config from environment
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER")
    search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    state_file = "file_state.json"

    # Load previous state (hash + row count per file)
    old_state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                content = f.read().strip()
                if content:
                    old_state = json.loads(content)
        except Exception as e:
            print(f"⚠️ Failed to load state file: {e}")

    # Setup clients
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)
    index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))
    search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_key))

    # Get current blob state
    current_state = {}
    blobs = [b.name for b in container_client.list_blobs() if b.name.endswith(".csv")]
    for blob_name in blobs:
        blob_data = container_client.download_blob(blob_name).readall()
        content_hash = compute_blob_hash(blob_data)
        current_state[blob_name] = {
            "content_hash": content_hash,
            "row_count": old_state.get(blob_name, {}).get("row_count", 0)
        }

    # Detect changes
    changed_blobs = [name for name in blobs if old_state.get(name, {}).get("content_hash") != current_state[name]["content_hash"]]
    deleted_blobs = [name for name in old_state if name not in current_state]

    # Exit early if no changes
    if not changed_blobs and not deleted_blobs:
        return False

    # Create index if missing
    if index_name not in [i.name for i in index_client.list_indexes()]:
        index = SearchIndex(
            name=index_name,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchField(name="content", type=SearchFieldDataType.String, searchable=True)
            ]
        )
        index_client.create_index(index)

    # Delete documents from removed files
    if deleted_blobs:
        to_delete = []
        for name in deleted_blobs:
            encoded = base64.urlsafe_b64encode(name.encode()).decode().rstrip("=")
            for i in range(old_state.get(name, {}).get("row_count", 0)):
                to_delete.append({"id": f"{encoded}-{i}"})
        if to_delete:
            search_client.delete_documents(to_delete)

    # Reindex updated blobs
    for blob_name in changed_blobs:
        try:
            blob_data = container_client.download_blob(blob_name).readall()
            df = pd.read_csv(io.BytesIO(blob_data))
            if "content" not in df.columns:
                continue

            encoded = base64.urlsafe_b64encode(blob_name.encode()).decode().rstrip("=")
            docs = []
            for i, row in df.iterrows():
                docs.append({
                    "id": f"{encoded}-{i}",
                    "content": str(row["content"]),
                    "metadata": json.dumps({})
                })

            if docs:
                search_client.delete_documents([{"id": d["id"]} for d in docs])
                search_client.upload_documents(docs)
                current_state[blob_name]["row_count"] = len(docs)

        except Exception as e:
            print(f"⚠️ Failed to reindex {blob_name}: {e}")

    # Save new state
    with open(state_file, "w") as f:
        json.dump(current_state, f, indent=2)

    return True
