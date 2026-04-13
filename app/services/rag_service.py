import math
import re
from collections import Counter

from app.core.models import ChatRequest, ChatResponse, Citation
from app.services.repository import InMemoryRepository

TOKEN_PATTERN = re.compile(r"[\w\-\u4e00-\u9fff]+")


class RagService:
    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo

    def answer(self, payload: ChatRequest) -> ChatResponse:
        ranked_chunk_ids = self._retrieve_and_rerank(payload.question, payload.notebook_id, payload.top_k)
        if not ranked_chunk_ids:
            return ChatResponse(answer="不知道（当前资料库暂无可用内容）。", citations=[])

        citations: list[Citation] = []
        answer_parts: list[str] = []

        for idx, chunk_id in enumerate(ranked_chunk_ids, start=1):
            chunk = self.repo.chunks[chunk_id]
            doc = self.repo.get_document(chunk.document_id)
            if doc is None:
                continue

            snippet = chunk.content[:180]
            citations.append(
                Citation(
                    id=idx,
                    doc_id=doc.id,
                    chunk_id=chunk.id,
                    snippet=snippet,
                    start_offset=chunk.start_offset,
                    end_offset=chunk.end_offset,
                )
            )
            answer_parts.append(f"{snippet} [{idx}]")

        answer = "\n".join(answer_parts)
        return ChatResponse(answer=answer, citations=citations)

    def _retrieve_and_rerank(self, question: str, notebook_id: str, top_k: int) -> list[str]:
        candidate_chunks = self.repo.list_chunks(notebook_id)
        if not candidate_chunks:
            return []

        q_tokens = self._tokenize(question)
        if not q_tokens:
            return []

        query_tf = Counter(q_tokens)
        query_vector = {term: freq * self.repo.idf(term) for term, freq in query_tf.items()}

        scored: list[tuple[str, float]] = []
        for chunk in candidate_chunks:
            vector_score = self._cosine_similarity(query_vector, self.repo.tfidf_vector(chunk.id))
            bm25_score = self._bm25_score(q_tokens, chunk.id)
            hybrid_score = 0.7 * vector_score + 0.3 * bm25_score
            scored.append((chunk.id, hybrid_score))

        top_candidates = [chunk_id for chunk_id, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:20]]

        reranked: list[tuple[str, float]] = []
        q_set = set(q_tokens)
        for chunk_id in top_candidates:
            chunk = self.repo.chunks[chunk_id]
            c_tokens = set(self._tokenize(chunk.content))
            overlap = len(q_set & c_tokens) / max(len(q_set), 1)
            proximity_bonus = 0.2 if any(term in chunk.content.lower() for term in q_set) else 0.0
            reranked.append((chunk_id, overlap + proximity_bonus))

        return [chunk_id for chunk_id, _ in sorted(reranked, key=lambda x: x[1], reverse=True)[:top_k]]

    def _bm25_score(self, query_terms: list[str], chunk_id: str, k1: float = 1.5, b: float = 0.75) -> float:
        tf = self.repo.chunk_term_freq.get(chunk_id, Counter())
        dl = sum(tf.values())
        avgdl = sum(sum(freq.values()) for freq in self.repo.chunk_term_freq.values()) / max(len(self.repo.chunk_term_freq), 1)

        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            idf = self.repo.idf(term)
            numerator = freq * (k1 + 1)
            denominator = freq + k1 * (1 - b + b * (dl / max(avgdl, 1e-9)))
            score += idf * (numerator / denominator)
        return score

    @staticmethod
    def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
        if not v1 or not v2:
            return 0.0
        common = set(v1) & set(v2)
        numerator = sum(v1[t] * v2[t] for t in common)
        den1 = math.sqrt(sum(value * value for value in v1.values()))
        den2 = math.sqrt(sum(value * value for value in v2.values()))
        if den1 == 0 or den2 == 0:
            return 0.0
        return numerator / (den1 * den2)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]
