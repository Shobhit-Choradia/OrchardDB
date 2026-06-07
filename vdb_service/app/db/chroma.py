import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from app.core.config import settings

class ChromaManager:
    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        self.embedding_function = ONNXMiniLM_L6_V2()
    
    def _scope_name(self, tenant_id: str, collection_name: str) -> str:
        """Prefixes collection names with the developer's unique tenant_id."""
        return f"tenant_{tenant_id}_{collection_name}"

    def create_scoped_collection(self, tenant_id: str, name: str, metric: str = "cosine") -> chromadb.Collection:
        """Returns a native Chroma Collection scoped to the tenant."""
        scoped_name = self._scope_name(tenant_id, name)
        exists = False

        try:
            self.client.get_collection(scoped_name)
            exists = True
        except Exception:
            pass
        
        if exists:
            raise ValueError("Collection already exists please delete old collection first.")

        return self.client.create_collection(
            name=scoped_name, 
            metadata={"hnsw:space": metric},
            embedding_function=self.embedding_function
        )

    def get_scoped_collection(self, tenant_id: str, name: str) -> chromadb.Collection:
        """Returns a native Chroma Collection scoped to the tenant."""
        scoped_name = self._scope_name(tenant_id, name)
        collection = self.client.get_collection(name=scoped_name, embedding_function=self.embedding_function)
        if not collection:
            raise ValueError("Collection not found")
        return collection

    def delete_scoped_collection(self, tenant_id: str, name: str):
        """Deletes a collection scoped to the tenant."""
        scoped_name = self._scope_name(tenant_id, name)
        self.client.delete_collection(name=scoped_name)

    def list_scoped_collections(self, tenant_id: str) -> list:
        """Lists all collection names belonging to a specific tenant, stripping the prefix."""
        prefix = f"tenant_{tenant_id}_"
        all_collections = self.client.list_collections()
        
        output = [
            {
                "name": collection.name.replace(prefix, ""), 
                "metric": (collection.metadata or {}).get("hnsw:space", "cosine")
            } 
            for collection in all_collections 
            if collection.name.startswith(prefix)
        ]
        return output
