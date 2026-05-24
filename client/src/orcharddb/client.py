import requests

class OrchardClient:
    """
    OrchardDB Client SDK
    Provides simple, professional wrappers around vector database trial endpoints.
    """
    
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8000/api"):
        """Initializes the OrchardDB Client connection."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _handle_response(self, response: requests.Response):
        """Helper to parse API responses and raise descriptive errors on failures."""
        if response.status_code == 200:
            return response.json()
        
        # Capture backend-detailed error messages and raise them cleanly
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
            
        raise ValueError(f"OrchardDB API Error ({response.status_code}): {detail}")

    # ==========================================================================
    # Collection Management Operations (CRUD Collections)
    # ==========================================================================

    def list_collections(self) -> list:
        """Lists all vector spaces currently owned by this developer namespace."""
        url = f"{self.base_url}/vdb/collections"
        response = requests.get(url, headers=self.headers)
        data = self._handle_response(response)
        return data.get("collections", [])

    def create_collection(self, name: str, metric: str = "cosine") -> dict:
        """Initializes a new isolated vector collection."""
        url = f"{self.base_url}/vdb/collections"
        payload = {"name": name, "metric": metric}
        response = requests.post(url, headers=self.headers, json=payload)
        return self._handle_response(response)

    def delete_collection(self, name: str) -> dict:
        """Permanently deletes a collection and all its embedded vectors."""
        url = f"{self.base_url}/vdb/collections/{name}"
        response = requests.delete(url, headers=self.headers)
        return self._handle_response(response)

    # ==========================================================================
    # Document Indexing Operations (CRUD Data)
    # ==========================================================================

    def add(self, collection: str, doc_id: str, text: str, metadata: dict = None) -> dict:
        """
        Indexes a single document.
        Embedding vectors are automatically generated behind the scenes using neural pipelines.
        """
        return self.add_batch(
            collection=collection,
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata] if metadata else None
        )

    def add_batch(self, collection: str, ids: list, documents: list, metadatas: list = None) -> dict:
        """Indexes a batch of multiple documents concurrently."""
        url = f"{self.base_url}/vdb/collections/{collection}/documents"
        payload = {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return self._handle_response(response)

    def update(self, collection: str, doc_id: str, text: str, metadata: dict = None) -> dict:
        """Updates an existing document text and metadata, re-calculating its neural embedding."""
        return self.update_batch(
            collection=collection,
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata] if metadata else None
        )

    def update_batch(self, collection: str, ids: list, documents: list, metadatas: list = None) -> dict:
        """Updates a batch of multiple existing documents and re-generates embeddings."""
        url = f"{self.base_url}/vdb/collections/{collection}/documents"
        payload = {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
        response = requests.put(url, headers=self.headers, json=payload)
        return self._handle_response(response)

    def delete(self, collection: str, doc_id: str) -> dict:
        """Deletes a single document by its ID."""
        return self.delete_batch(collection=collection, ids=[doc_id])

    def delete_batch(self, collection: str, ids: list) -> dict:
        """Deletes a batch of multiple documents by their IDs."""
        url = f"{self.base_url}/vdb/collections/{collection}/documents"
        payload = {"ids": ids}
        response = requests.delete(url, headers=self.headers, json=payload)
        return self._handle_response(response)

    def get(self, collection: str, limit: int = 100) -> dict:
        """Fetches all raw documents and metadatas currently stored in the collection."""
        url = f"{self.base_url}/vdb/collections/{collection}/documents?limit={limit}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)

    # ==========================================================================
    # Semantic Search Operations
    # ==========================================================================

    def query(self, collection: str, query_text: str, n_results: int = 5) -> list:
        """
        Performs a semantic similarity search.
        Vectorizes the query phrase and returns the top matching documents with distance scores.
        """
        url = f"{self.base_url}/vdb/collections/{collection}/query"
        payload = {
            "query_text": query_text,
            "n_results": n_results
        }
        response = requests.post(url, headers=self.headers, json=payload)
        data = self._handle_response(response)
        return data.get("results", [])
