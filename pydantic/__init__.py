from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class FieldInfo:
    default: Any = None
    default_factory: Callable[[], Any] | None = None


def Field(*, default: Any = None, default_factory: Callable[[], Any] | None = None, **kwargs: Any) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory)


def model_validator(*, mode: str = "after") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


class BaseModel:
    def __init__(self, **kwargs: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            class_value = getattr(self.__class__, name, None)
            if name in kwargs:
                value = kwargs[name]
            elif isinstance(class_value, FieldInfo):
                value = class_value.default_factory() if class_value.default_factory else class_value.default
            else:
                value = class_value
            setattr(self, name, value)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "BaseModel":
        return cls(**data)

    def model_dump(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            value = getattr(self, name)
            if isinstance(value, BaseModel):
                out[name] = value.model_dump()
            elif isinstance(value, list):
                out[name] = [item.model_dump() if isinstance(item, BaseModel) else item for item in value]
            else:
                out[name] = value
        return out
