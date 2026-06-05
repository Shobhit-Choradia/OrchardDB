import os
import pypdf
from app.worker.celery_app import celery_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.db.chroma import ChromaManager

# Initialize the ChromaManager and text splitter once at the worker process level
chroma_manager = ChromaManager()
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],
    chunk_size=1000,
    chunk_overlap=200
)

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
        collection = chroma_manager.get_or_create_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        
        # 4. Clean up the file from the shared volume
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return {"status": "SUCCESS", "chunks_processed": len(ids)}
        
    except Exception as e:
        # Log failure
        print(f"Failed to process PDF {filepath}: {str(e)}")
        raise e
