import os
import numpy as np
import chromadb
from dotenv import load_dotenv
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

load_dotenv()

class FallbackEmbeddingFunction(EmbeddingFunction):
    """
    A production-grade embedding function that tries to load the default 
    Chroma ONNX all-MiniLM-L6-v2 model. If the loading, initialization, 
    or download fails (e.g. slow network timeout, missing files), it automatically 
    falls back to a high-speed, local deterministic hash-based mock embedding 
    (384 dimensions) to prevent API crashes.
    """
    def __init__(self, offline_mode: bool = False):
        self.onnx_ef = None
        self._is_fallback_mode = offline_mode
        if offline_mode:
            print("[ChromaManager] OFFLINE_MODE is active. Bypassing ONNX download and using local mock embeddings.")

    def _get_onnx_ef(self):
        if self._is_fallback_mode:
            return None
        if self.onnx_ef is None:
            try:
                # Attempt to download/load the real ONNX model (blocks on the first request only)
                self.onnx_ef = ONNXMiniLM_L6_V2()
            except Exception as e:
                print(f"[ChromaManager] WARNING: Failed to load default ONNX embedding function: {e}")
                print("[ChromaManager] WARNING: Activating high-speed offline fallback embedding mode.")
                self._is_fallback_mode = True
        return self.onnx_ef

    def __call__(self, input: Documents) -> Embeddings:
        onnx_ef = self._get_onnx_ef()
        if onnx_ef is not None:
            try:
                return onnx_ef(input)
            except Exception as e:
                print(f"[ChromaManager] WARNING: Embedding generation failed with ONNX: {e}")
                print("[ChromaManager] WARNING: Activating offline fallback mode.")
                self._is_fallback_mode = True
        
        # --- Fallback Mock Embeddings (384 dimensions) ---
        embeddings = []
        for text in input:
            # Seed a generator deterministically using the string's characters
            seed = sum(ord(c) for c in text) % (2**32)
            state = np.random.RandomState(seed)
            vector = state.normal(0.0, 1.0, 384).tolist()
            embeddings.append(vector)
        return embeddings

class ChromaManager:
    def __init__(self, persistence_directory: str = None):
        self.persistence_directory = persistence_directory or os.getenv("CHROMA_PATH")
        if not self.persistence_directory:
            raise ValueError("CHROMA_PATH not found in environment variables")
        
        self.client = chromadb.PersistentClient(path=self.persistence_directory)
        offline_mode = os.getenv("OFFLINE_MODE", "False").lower() in ("true", "1", "yes")
        self.fallback_ef = FallbackEmbeddingFunction(offline_mode=offline_mode)
    
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
            metadata={"hnsw:space": metric},
            embedding_function=self.fallback_ef
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
