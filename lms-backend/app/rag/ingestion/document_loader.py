import io
import re
import os
import tempfile
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
import pypdf

class DocumentLoadResult:
    def __init__(self, documents: List[Document], metadata: Dict[str, Any]):
        self.documents = documents
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "documents": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in self.documents],
            "metadata": self.metadata
        }

class DocumentLoader:
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\f', '\n\n')
        text = text.replace('\t', '  ')
        
        text = re.sub(r'[\u2018\u2019]', "'", text)
        text = re.sub(r'[\u201C\u201D]', '"', text)
        text = re.sub(r'[\u2013\u2014]', '-', text)
        text = text.replace('\u2026', '...')
        
        text = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', text)
        text = re.sub(r'[^\S\n]+', ' ', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()

    def preserve_table_structure(self, text: str) -> str:
        lines = text.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            prev_line = lines[i - 1] if i > 0 else ""
            next_line = lines[i + 1] if i < len(lines) - 1 else ""
            
            segments = [s.strip() for s in re.split(r'\s{2,}', line) if s.strip()]
            prev_segments = [s.strip() for s in re.split(r'\s{2,}', prev_line) if s.strip()]
            next_segments = [s.strip() for s in re.split(r'\s{2,}', next_line) if s.strip()]
            
            if len(segments) >= 3:
                is_similar_to_prev = abs(len(segments) - len(prev_segments)) <= 1
                is_similar_to_next = abs(len(segments) - len(next_segments)) <= 1
                
                if is_similar_to_prev or is_similar_to_next:
                    processed_lines.append('\t'.join(segments))
                    continue
            
            processed_lines.append(line)
            
        return '\n'.join(processed_lines)

    async def load_pdf(
        self,
        file_buffer: bytes,
        file_name: str,
        metadata: Dict[str, Any] = None
    ) -> DocumentLoadResult:
        meta = metadata or {}
        documents = []
        extraction_method = "pypdf"

        try:
            pdf_file = io.BytesIO(file_buffer)
            reader = pypdf.PdfReader(pdf_file)
            
            for index, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                normalized = self.normalize_text(page_text)
                preserved = self.preserve_table_structure(normalized)
                
                if preserved.strip():
                    doc_meta = {
                        "source": file_name,
                        "page": index + 1,
                        "loc": {"pageNumber": index + 1},
                        "docType": "pdf",
                        "extractionMethod": extraction_method,
                        **meta
                    }
                    documents.append(
                        Document(page_content=preserved, metadata=doc_meta)
                    )

            total_chars = sum(len(d.page_content) for d in documents)
            if total_chars < 50:
                print(f"⚠️ PyPDF extraction yielded minimal content ({total_chars} chars) for {file_name}")

            return DocumentLoadResult(
                documents=documents,
                metadata={
                    "fileName": file_name,
                    "docType": "pdf",
                    "totalPages": len(documents),
                    "totalCharacters": total_chars,
                    "extractionMethod": extraction_method,
                    **meta
                }
            )
        except Exception as e:
            print(f"PDF loading failed: {str(e)}")
            raise Exception(f"Failed to load PDF: {str(e)}")

    async def load_text(
        self,
        content: str,
        file_name: str,
        metadata: Dict[str, Any] = None
    ) -> DocumentLoadResult:
        meta = metadata or {}
        normalized = self.normalize_text(content)
        document = Document(
            page_content=normalized,
            metadata={
                "source": file_name,
                "docType": "text",
                **meta
            }
        )
        return DocumentLoadResult(
            documents=[document],
            metadata={
                "fileName": file_name,
                "docType": "text",
                **meta
            }
        )

    async def load_from_path(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> DocumentLoadResult:
        meta = metadata or {}
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                return await self.load_pdf(f.read(), os.path.basename(file_path), meta)
        elif ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return await self.load_text(content, os.path.basename(file_path), meta)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
