import numpy as np
from typing import Literal, Any, Dict
from chromadb.api.models.Collection import Collection
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


class VectorVisualizer:

    min_docs = 3

    def reduce(self, collection: Collection, method: Literal["pca", "tsne"] = "pca") -> Dict[str, Any]:
        """
        Reduces vectors to 3 dimensions using PCA or t-SNE.
        Args: 
            collection: ChromaCollection
            method: "pca" or "tsne"
        Returns:
            np.ndarray: Reduced vectors
        """

        raw = collection.get(include=["embeddings", "documents"])
        ids = raw.get("ids", [])
        embeddings = raw.get("embeddings", [])
        documents = raw.get("documents", [])

        if len(ids) < self.min_docs:
            raise ValueError(f"Not enough documents to visualize. Minimum required: {self.min_docs}")
        
        matrix = np.array(embeddings, dtype=np.float32)

        if method == "pca":
            reducer = PCA(n_components=3, random_state=42)
            coordinates = reducer.fit_transform(matrix)
            variance_explained = [round(float(v), 4) for v in reducer.explained_variance_ratio_]

        elif method == "tsne":
            reducer = TSNE(n_components=3, random_state=42, perplexity=min(30.0, len(ids)-1), learning_rate='auto')
            coordinates = reducer.fit_transform(matrix)
            variance_explained = None
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        points = []
        for i, doc_id in enumerate(ids):
            points.append({
                "id":       doc_id,
                "x":        float(coordinates[i, 0]),
                "y":        float(coordinates[i, 1]),
                "z":        float(coordinates[i, 2]),
                "document": (documents[i] or "")[:200],
            })
        return {
            "method":             method,
            "n_docs":             len(ids),
            "points":             points,
            "variance_explained": variance_explained,
        }