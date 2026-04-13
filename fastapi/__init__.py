from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]


class APIRouter:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix
        self.routes: list[_Route] = []

    def post(self, path: str, response_model: Any | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("POST", path)

    def get(self, path: str, response_model: Any | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("GET", path)

    def _register(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method=method, path=f"{self.prefix}{path}", handler=func))
            return func

        return decorator


class FastAPI:
    def __init__(self, title: str = "", version: str = "") -> None:
        self.title = title
        self.version = version
        self.routes: list[_Route] = []

    def include_router(self, router: APIRouter) -> None:
        self.routes.extend(router.routes)

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method="GET", path=path, handler=func))
            return func

        return decorator
