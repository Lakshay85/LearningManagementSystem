import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from app.rag.structure.document_structure_parser import DocumentStructureParser
from app.rag.structure.smart_chunker import SmartChunker
from app.rag.structure.metadata_enricher import MetadataEnricher
from app.rag.ingestion.document_loader import DocumentLoader

class IngestionStats:
    def __init__(
        self,
        total_elements: int,
        total_chunks: int,
        element_breakdown: Dict[str, int],
        avg_chunk_size: int,
        processing_time_ms: int
    ):
        self.totalElements = total_elements
        self.totalChunks = total_chunks
        self.elementBreakdown = element_breakdown
        self.avgChunkSize = avg_chunk_size
        self.processingTimeMs = processing_time_ms

    def to_dict(self) -> dict:
        return self.__dict__

class StructuredIngestionResult:
    def __init__(
        self,
        structured_document: Any,
        chunks: List[Any],
        langchain_documents: List[Document],
        stats: IngestionStats
    ):
        self.structuredDocument = structured_document
        self.chunks = chunks
        self.langchainDocuments = langchain_documents
        self.stats = stats

    def to_dict(self) -> dict:
        return {
            "structuredDocument": self.structuredDocument.to_dict() if hasattr(self.structuredDocument, "to_dict") else self.structuredDocument,
            "chunks": [c.to_dict() if hasattr(c, "to_dict") else c for c in self.chunks],
            "langchainDocuments": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in self.langchainDocuments],
            "stats": self.stats.to_dict()
        }

class StructuredIngestionPipeline:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.enable_enrichment = self.config.get("enableEnrichment", True)
        
        self.document_loader = DocumentLoader()
        self.parser = DocumentStructureParser(self.config.get("parserConfig"))
        self.chunker = SmartChunker(self.config.get("chunkerConfig"))
        self.enricher = MetadataEnricher()

    async def process_text(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> StructuredIngestionResult:
        start_time = time.time()

        # Step 1: Parse document structure
        print("📐 Parsing document structure...")
        structured_doc = await self.parser.parse(content, {
            "docId": metadata["docId"],
            "fileName": metadata["fileName"],
            "docType": metadata["docType"],
            "page": metadata.get("page")
        })
        print(f"   Found {len(structured_doc.elements)} structural elements")

        # Step 2: Smart chunking
        print("✂️ Creating smart chunks...")
        chunks = await self.chunker.chunk_document(structured_doc)
        print(f"   Created {len(chunks)} chunks")

        # Filter empty chunks
        valid_chunks = []
        for chunk in chunks:
            if chunk.content and chunk.content.strip():
                valid_chunks.append(chunk)
            else:
                print(f"⚠️ Skipping empty chunk: {chunk.id}")

        if len(valid_chunks) < len(chunks):
            print(f"   Filtered {len(chunks) - len(valid_chunks)} empty chunks")
        chunks = valid_chunks

        # Step 3: Enrich metadata
        if self.enable_enrichment:
            print("🔍 Enriching chunk metadata...")
            chunks = await self.enricher.enrich_chunks(chunks)

        # Step 4: Convert to Langchain docs
        langchain_documents = self.chunker.to_langchain_documents(chunks)

        # Merge input metadata
        for doc in langchain_documents:
            doc.metadata.update({
                **metadata,
                "structureAware": True
            })

        # Calculate stats
        processing_time = int((time.time() - start_time) * 1000)
        total_len = sum(len(c.content) for c in chunks)
        avg_chunk = round(total_len / len(chunks)) if chunks else 0
        
        stats = IngestionStats(
            total_elements=len(structured_doc.elements),
            total_chunks=len(chunks),
            element_breakdown=structured_doc.metadata.get("elementCounts", {}),
            avg_chunk_size=avg_chunk,
            processing_time_ms=processing_time
        )

        return StructuredIngestionResult(
            structured_document=structured_doc,
            chunks=chunks,
            langchain_documents=langchain_documents,
            stats=stats
        )

    async def process_pdf(
        self,
        file_buffer: bytes,
        metadata: Dict[str, Any]
    ) -> StructuredIngestionResult:
        # Load PDF using loader
        load_result = await self.document_loader.load_pdf(
            file_buffer,
            metadata["fileName"],
            metadata
        )

        # Combine text of all pages
        combined_parts = []
        for idx, doc in enumerate(load_result.documents):
            combined_parts.append(f"[Page {idx + 1}]\n{doc.page_content}")
        combined_content = "\n\n".join(combined_parts)

        # Pass combined text to process_text
        text_metadata = {
            **metadata,
            "docId": metadata["docId"],
            "fileName": metadata["fileName"],
            "docType": "pdf",
            "totalPages": len(load_result.documents)
        }
        
        return await self.process_text(combined_content, text_metadata)

    async def process_multi_page_document(
        self,
        pages: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> StructuredIngestionResult:
        start_time = time.time()
        all_chunks = []
        combined_doc = None

        for page in pages:
            page_meta = {
                **metadata,
                "page": page["page"]
            }
            page_result = await self.process_text(page["content"], page_meta)

            for chunk in page_result.chunks:
                chunk.metadata["page"] = page["page"]
                all_chunks.append(chunk)

            if not combined_doc:
                combined_doc = page_result.structuredDocument
            else:
                combined_doc.elements.extend(page_result.structuredDocument.elements)

        # Re-index
        for idx, chunk in enumerate(all_chunks):
            chunk.metadata["chunkIndex"] = idx

        langchain_documents = self.chunker.to_langchain_documents(all_chunks)

        processing_time = int((time.time() - start_time) * 1000)
        total_len = sum(len(c.content) for c in all_chunks)
        avg_chunk = round(total_len / len(all_chunks)) if all_chunks else 0

        element_breakdown = combined_doc.metadata.get("elementCounts", {}) if combined_doc else {}
        total_elements = len(combined_doc.elements) if combined_doc else 0

        stats = IngestionStats(
            total_elements=total_elements,
            total_chunks=len(all_chunks),
            element_breakdown=element_breakdown,
            avg_chunk_size=avg_chunk,
            processing_time_ms=processing_time
        )

        return StructuredIngestionResult(
            structured_document=combined_doc,
            chunks=all_chunks,
            langchain_documents=langchain_documents,
            stats=stats
        )

    def get_config(self) -> dict:
        return self.config

    def update_config(self, config: dict):
        self.config.update(config)
        self.enable_enrichment = self.config.get("enableEnrichment", True)
        
        if "parserConfig" in config:
            self.parser = DocumentStructureParser(config["parserConfig"])
        if "chunkerConfig" in config:
            self.chunker = SmartChunker(config["chunkerConfig"])
