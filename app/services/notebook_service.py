from app.core.models import Notebook, NotebookCreate
from app.services.repository import InMemoryRepository


class NotebookService:
    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo

    def create_notebook(self, payload: NotebookCreate) -> Notebook:
        notebook = Notebook(name=payload.name)
        return self.repo.add_notebook(notebook)

    def list_notebooks(self) -> list[Notebook]:
        return self.repo.list_notebooks()
