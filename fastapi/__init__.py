from __future__ import annotations

import inspect
import json
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

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope.get("type") != "http":
            await send({"type": "http.response.start", "status": 500, "headers": []})
            await send({"type": "http.response.body", "body": b"Unsupported scope type"})
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        for route in self.routes:
            params = self._match_path(route.path, path)
            if route.method == method and params is not None:
                kwargs = dict(params)
                sig = inspect.signature(route.handler)
                for name in sig.parameters:
                    if name in kwargs:
                        continue
                    kwargs[name] = None
                result = route.handler(**kwargs)
                if hasattr(result, "model_dump"):
                    result = result.model_dump()
                payload = json.dumps(result, default=str).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send({"type": "http.response.body", "body": payload})
                return

        payload = json.dumps({"detail": "Not Found"}).encode("utf-8")
        await send({"type": "http.response.start", "status": 404, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": payload})

    @staticmethod
    def _match_path(template: str, actual: str) -> dict[str, str] | None:
        template_parts = template.strip("/").split("/")
        actual_parts = actual.strip("/").split("/")
        if len(template_parts) != len(actual_parts):
            return None

        params: dict[str, str] = {}
        for t, a in zip(template_parts, actual_parts):
            if t.startswith("{") and t.endswith("}"):
                params[t[1:-1]] = a
            elif t != a:
                return None
        return params
