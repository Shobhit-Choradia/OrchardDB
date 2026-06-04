import os
import numpy as np
import chromadb
from dotenv import load_dotenv
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

load_dotenv()

class FallbackEmbeddingFunction(EmbeddingFunction):
    """
    A embedding function that tries to load the default 
    Chroma ONNX all-MiniLM-L6-v2 model, with high-speed local 
    deterministic hash fallback to prevent API crashes.
    """
    def __init__(self, offline_mode: bool = False):
        self.onnx_ef = None
        self._is_fallback_mode = offline_mode
        if offline_mode:
            print("[ChromaManager] OFFLINE_MODE is active. Bypassing ONNX download.")
        else:
            self._get_onnx_ef()

    def _get_onnx_ef(self):
        if self._is_fallback_mode:
            return None
        if self.onnx_ef is None:
            try:
                self.onnx_ef = ONNXMiniLM_L6_V2()
            except Exception as e:
                print(f"[ChromaManager] WARNING: Failed to load default ONNX embedding function: {e}")
                self._is_fallback_mode = True
        return self.onnx_ef

    def __call__(self, input: Documents) -> Embeddings:
        onnx_ef = self._get_onnx_ef()
        if onnx_ef is not None:
            try:
                return onnx_ef(input)
            except Exception as e:
                print(f"[ChromaManager] WARNING: Embedding generation failed: {e}")
                self._is_fallback_mode = True
        
        embeddings = []
        for text in input:
            seed = sum(ord(c) for c in text) % (2**32)
            state = np.random.RandomState(seed)
            vector = state.normal(0.0, 1.0, 384).tolist()
            embeddings.append(vector)
        return embeddings

class ChromaManager:
    def __init__(self):
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = os.getenv("CHROMA_PORT", "8010")
        self.client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        offline_mode = os.getenv("OFFLINE_MODE", "False").lower() in ("true", "1", "yes")
        self.fallback_ef = FallbackEmbeddingFunction(offline_mode=offline_mode)
    
    def _scope_name(self, tenant_id: str, collection_name: str) -> str:
        return f"tenant_{tenant_id}_{collection_name}"

    def get_scoped_collection(self, tenant_id: str, name: str) -> chromadb.Collection:
        scoped_name = self._scope_name(tenant_id, name)
        collection = self.client.get_collection(name=scoped_name, embedding_function=self.fallback_ef)
        if not collection:
            raise ValueError("Collection not found")
        return collection
