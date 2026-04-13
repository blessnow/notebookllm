from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class NotebookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class Notebook(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentCreate(BaseModel):
    notebook_id: str
    title: str
    source_type: Literal["pdf", "doc", "url", "youtube", "text"] = "text"
    source_uri: str | None = None
    content: str | None = Field(default=None, min_length=20)

    @model_validator(mode="after")
    def validate_content_or_uri(self) -> "DocumentCreate":
        if not self.content and not self.source_uri:
            raise ValueError("Either content or source_uri must be provided.")
        return self


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    notebook_id: str
    title: str
    source_type: str
    source_uri: str | None = None
    status: Literal["processing", "done", "failed"] = "processing"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    notebook_id: str
    content: str
    start_offset: int
    end_offset: int


class ChatRequest(BaseModel):
    notebook_id: str
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    id: int
    doc_id: str
    chunk_id: str
    snippet: str
    start_offset: int
    end_offset: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
