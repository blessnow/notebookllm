import math
import re
from collections import Counter, defaultdict

from app.core.models import Chunk, Document, Notebook

TOKEN_PATTERN = re.compile(r"[\w\-\u4e00-\u9fff]+")


class InMemoryRepository:
    def __init__(self) -> None:
        self.notebooks: dict[str, Notebook] = {}
        self.documents: dict[str, Document] = {}
        self.chunks: dict[str, Chunk] = {}
        self.chunks_by_notebook: dict[str, list[str]] = defaultdict(list)
        self.chunk_term_freq: dict[str, Counter[str]] = {}
        self.df: Counter[str] = Counter()

    def add_notebook(self, notebook: Notebook) -> Notebook:
        self.notebooks[notebook.id] = notebook
        return notebook

    def list_notebooks(self) -> list[Notebook]:
        return list(self.notebooks.values())

    def add_document(self, doc: Document) -> Document:
        self.documents[doc.id] = doc
        return doc

    def list_documents(self, notebook_id: str) -> list[Document]:
        return [d for d in self.documents.values() if d.notebook_id == notebook_id]

    def get_document(self, doc_id: str) -> Document | None:
        return self.documents.get(doc_id)

    def add_chunk(self, chunk: Chunk) -> Chunk:
        self.chunks[chunk.id] = chunk
        self.chunks_by_notebook[chunk.notebook_id].append(chunk.id)

        terms = self._tokenize(chunk.content)
        term_freq = Counter(terms)
        self.chunk_term_freq[chunk.id] = term_freq

        for term in set(term_freq):
            self.df[term] += 1

        return chunk

    def list_chunks(self, notebook_id: str) -> list[Chunk]:
        return [self.chunks[cid] for cid in self.chunks_by_notebook.get(notebook_id, [])]

    def idf(self, term: str) -> float:
        total_chunks = len(self.chunks)
        doc_freq = self.df.get(term, 0)
        return math.log((1 + total_chunks) / (1 + doc_freq)) + 1.0

    def tfidf_vector(self, chunk_id: str) -> dict[str, float]:
        tf = self.chunk_term_freq.get(chunk_id, Counter())
        return {term: freq * self.idf(term) for term, freq in tf.items()}

    def reset(self) -> None:
        self.notebooks.clear()
        self.documents.clear()
        self.chunks.clear()
        self.chunks_by_notebook.clear()
        self.chunk_term_freq.clear()
        self.df.clear()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]
