# OrchardDB Python SDK Client

A lightweight, professional, and dead-simple Python client for interacting with **OrchardDB** Vector Database trial spaces.

---

## 🔧 Installation

To install this package locally in your Python environment:

```bash
pip install -e ./client
```

---

## 🚀 Quick Start Example

```python
from orcharddb import OrchardClient

# 1. Connect to OrchardDB with your secret API Key
db = OrchardClient(api_key="orchard_YOUR_API_KEY_HERE")

# 2. Set up a collection space
db.create_collection("my-space", metric="cosine")

# 3. Add a document
db.add(
    collection="my-space",
    doc_id="doc_101",
    text="ChromaDB uses neural networks to automatically index raw document texts.",
    metadata={"category": "AI"}
)

# 4. Fetch collection contents
docs = db.get("my-space")
print("Indexed Records:", docs)

# 5. Perform semantic similarity search queries
results = db.query(
    collection="my-space",
    query_text="How does ChromaDB index text?",
    n_results=1
)
print("Search Results:", results)

# 6. Clean up/Delete a document record
db.delete("my-space", doc_id="doc_101")
```
