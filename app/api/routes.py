from fastapi import APIRouter

from app.core.models import ChatRequest, ChatResponse, Document, DocumentCreate, Notebook, NotebookCreate
from app.services.document_service import DocumentService
from app.services.notebook_service import NotebookService
from app.services.rag_service import RagService
from app.services.repository import InMemoryRepository

router = APIRouter(prefix="/api")
repo = InMemoryRepository()
notebook_service = NotebookService(repo)
document_service = DocumentService(repo)
rag_service = RagService(repo)


@router.post("/notebooks", response_model=Notebook)
def create_notebook(payload: NotebookCreate) -> Notebook:
    return notebook_service.create_notebook(payload)


@router.get("/notebooks", response_model=list[Notebook])
def list_notebooks() -> list[Notebook]:
    return notebook_service.list_notebooks()


@router.post("/documents", response_model=Document)
def create_document(payload: DocumentCreate) -> Document:
    return document_service.create_document(payload)


@router.get("/notebooks/{notebook_id}/documents", response_model=list[Document])
def list_documents(notebook_id: str) -> list[Document]:
    return document_service.list_documents(notebook_id)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return rag_service.answer(payload)
