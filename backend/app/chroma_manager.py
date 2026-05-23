import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

class ChromaManager:
    def __init__(self, persistence_directory: str = None):
        self.persistence_directory = persistence_directory or os.getenv("CHROMA_PATH")
        if not self.persistence_directory:
            raise ValueError("CHROMA_PATH not found in environment variables")
        
        self.client = chromadb.PersistentClient(path=self.persistence_directory)
    
    def _scope_name(self, tenant_id: str, collection_name: str) -> str:
        """Prefixes collection names with the developer's unique tenant_id."""
        return f"tenant_{tenant_id}_{collection_name}"

    def get_scoped_collection(self, tenant_id: str, name: str, metric: str = "cosine") -> chromadb.Collection:
        """Returns a native Chroma Collection scoped to the tenant.
        Once retrieved, the caller can use all native Chroma Collection methods 
        (e.g., .add(), .query(), .get(), .delete()) directly on this object.
        """
        scoped_name = self._scope_name(tenant_id, name)
        return self.client.get_or_create_collection(
            name=scoped_name, 
            metadata={"hnsw:space": metric}
        )

    def delete_scoped_collection(self, tenant_id: str, name: str):
        """Deletes a collection scoped to the tenant."""
        scoped_name = self._scope_name(tenant_id, name)
        self.client.delete_collection(name=scoped_name)

    def list_scoped_collections(self, tenant_id: str) -> list[str]:
        """Lists all collection names belonging to a specific tenant, stripping the prefix."""
        prefix = f"tenant_{tenant_id}_"
        all_cols = self.client.list_collections()
        return [col.name[len(prefix):] for col in all_cols if col.name.startswith(prefix)]
