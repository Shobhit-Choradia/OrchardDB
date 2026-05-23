import io
import pypdf
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFProcessor:

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", " "],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def extract_text_from_pdf(
        self,
        file_stream: io.BytesIO,
        filename: str,
        source_id: int | str = None
    ) -> List[Dict[str, Any]]:
        """
        Reads PDF bytes, extracts text per page, chunks the text,
        and returns:

        [
            {
                "id": "pdf_1_chunk_0",
                "text": "...",
                "metadata": {
                    "source_id": 1,
                    "source_name": "example.pdf",
                    "page": 1,
                    "chunk_index": 0,
                }
            }
        ]
        """

        reader = pypdf.PdfReader(file_stream)
        total_pages = len(reader.pages)

        raw_chunks = []

        # Extract text page-by-page
        for page_num, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if not text or not text.strip():
                continue

            page_chunks = self.splitter.split_text(text)

            for chunk in page_chunks:
                raw_chunks.append(
                    {
                        "text": chunk,
                        "page": page_num
                    }
                )

        processed_chunks = []

        for chunk_index, chunk_data in enumerate(raw_chunks):

            processed_chunks.append(
                {
                    "id": f"pdf_{source_id}_chunk_{chunk_index}",
                    "text": chunk_data["text"],
                    "metadata": {
                        "source_id": source_id,
                        "source_name": filename,
                        "page": chunk_data["page"],
                        "chunk_index": chunk_index,
                    }
                }
            )

        return processed_chunks