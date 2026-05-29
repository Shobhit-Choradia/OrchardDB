import os
import pypdf
import chromadb
from worker import celery_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

# Initialize the embedder and text splitter once at the worker process level
embedder = ONNXMiniLM_L6_V2()
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],
    chunk_size=1000,
    chunk_overlap=200
)

# Connect to ChromaDB
chroma_host = os.getenv("CHROMA_HOST", "localhost")
chroma_port = os.getenv("CHROMA_PORT", "8001")
chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

@celery_app.task(name="process_pdf_task", bind=True)
def process_pdf_task(self, filepath: str, document_id: str, filename: str, tenant_id: str, collection_name: str):
    try:
        # 1. Read and chunk the PDF
        raw_chunks = []
        with open(filepath, "rb") as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            for page_num, page in enumerate(reader.pages, start=1):
                # Report progress
                self.update_state(state="PROCESSING", meta={'current': page_num, 'total': total_pages})
                
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                page_chunks = text_splitter.split_text(text)
                for chunk in page_chunks:
                    raw_chunks.append({"text": chunk, "page": page_num})
        
        # 2. Format chunks and metadata
        ids = []
        documents = []
        metadatas = []
        
        for chunk_index, chunk_data in enumerate(raw_chunks):
            ids.append(f"pdf_{document_id}_chunk_{chunk_index}")
            documents.append(chunk_data["text"])
            metadatas.append({
                "source_id": document_id,
                "source_name": filename,
                "page": chunk_data["page"],
                "chunk_index": chunk_index,
            })
            
        # 3. Insert into ChromaDB
        scoped_collection_name = f"tenant_{tenant_id}_{collection_name}"
        
        # Get or create the collection
        try:
            collection = chroma_client.get_collection(name=scoped_collection_name, embedding_function=embedder)
        except Exception:
            # If it doesn't exist, create it (fallback behavior)
            collection = chroma_client.create_collection(name=scoped_collection_name, embedding_function=embedder)
            
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        
        # 4. Clean up the file from the shared volume
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return {"status": "SUCCESS", "chunks_processed": len(ids)}
        
    except Exception as e:
        # Log failure and potentially retry depending on Celery config
        print(f"Failed to process PDF {filepath}: {str(e)}")
        raise e
