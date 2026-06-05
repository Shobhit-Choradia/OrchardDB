import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from app.core.config import settings

class ChromaManager:
    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        self.embedding_function = ONNXMiniLM_L6_V2()
    
    def _scope_name(self, tenant_id: str, collection_name: str) -> str:
        return f"tenant_{tenant_id}_{collection_name}"

    def get_scoped_collection(self, tenant_id: str, name: str) -> chromadb.Collection:
        scoped_name = self._scope_name(tenant_id, name)
        collection = self.client.get_collection(name=scoped_name, embedding_function=self.embedding_function)
        if not collection:
            raise ValueError("Collection not found")
        return collection

    def get_or_create_scoped_collection(self, tenant_id: str, name: str) -> chromadb.Collection:
        scoped_name = self._scope_name(tenant_id, name)
        try:
            return self.client.get_collection(name=scoped_name, embedding_function=self.embedding_function)
        except Exception:
            return self.client.create_collection(name=scoped_name, embedding_function=self.embedding_function)
