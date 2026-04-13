from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

@dataclass
class Response:
    status_code: int
    _payload: Any

    def json(self) -> Any:
        return self._payload


class TestClient:
    def __init__(self, app: Any) -> None:
        self.app = app

    def post(self, path: str, json: dict[str, Any]) -> Response:
        return self._call("POST", path, json)

    def get(self, path: str) -> Response:
        return self._call("GET", path, None)

    def _call(self, method: str, path: str, payload: dict[str, Any] | None) -> Response:
        for route in self.app.routes:
            params = self._match_path(route.path, path)
            if route.method == method and params is not None:
                kwargs = dict(params)
                sig = inspect.signature(route.handler)
                for name, param in sig.parameters.items():
                    if name in kwargs:
                        continue
                    if payload is None:
                        continue
                    annotation = param.annotation
                    try:
                        if hasattr(annotation, "model_validate"):
                            kwargs[name] = annotation.model_validate(payload)
                        else:
                            kwargs[name] = payload
                    except (ValidationError, ValueError) as exc:
                        return Response(status_code=422, _payload={"detail": str(exc)})
                result = route.handler(**kwargs)
                if hasattr(result, "model_dump"):
                    result = result.model_dump()
                elif isinstance(result, list):
                    result = [item.model_dump() if hasattr(item, "model_dump") else item for item in result]
                return Response(status_code=200, _payload=result)
        return Response(status_code=404, _payload={"detail": "Not Found"})

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
