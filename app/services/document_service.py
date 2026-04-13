from app.core.models import Chunk, Document, DocumentCreate
from app.services.parser_service import ParserService
from app.services.repository import InMemoryRepository


class DocumentService:
    def __init__(self, repo: InMemoryRepository, chunk_size: int = 800, overlap: int = 120) -> None:
        self.repo = repo
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parser = ParserService()

    def create_document(self, payload: DocumentCreate) -> Document:
        doc = Document(
            notebook_id=payload.notebook_id,
            title=payload.title,
            source_type=payload.source_type,
            source_uri=payload.source_uri,
            status="processing",
        )
        self.repo.add_document(doc)

        extracted_text = self.parser.extract_text(payload.source_type, payload.source_uri, payload.content)

        for chunk in self._split_into_chunks(extracted_text):
            self.repo.add_chunk(
                Chunk(
                    document_id=doc.id,
                    notebook_id=doc.notebook_id,
                    content=chunk["content"],
                    start_offset=chunk["start_offset"],
                    end_offset=chunk["end_offset"],
                )
            )

        doc.status = "done"
        self.repo.add_document(doc)
        return doc

    def list_documents(self, notebook_id: str) -> list[Document]:
        return self.repo.list_documents(notebook_id)

    def _split_into_chunks(self, content: str) -> list[dict[str, int | str]]:
        text = " ".join(content.split())
        if not text:
            return []

        chunks: list[dict[str, int | str]] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            window = text[start:end]

            if end < len(text):
                split = max(window.rfind("。"), window.rfind("."), window.rfind("\n"), window.rfind(" "))
                if split > int(self.chunk_size * 0.6):
                    end = start + split + 1
                    window = text[start:end]

            chunks.append({"content": window.strip(), "start_offset": start, "end_offset": end})
            if end == len(text):
                break
            start = max(0, end - self.overlap)

        return chunks
