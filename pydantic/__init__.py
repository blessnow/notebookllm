from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, get_args, get_origin


@dataclass
class FieldInfo:
    default: Any = None
    default_factory: Callable[[], Any] | None = None
    min_length: int | None = None
    max_length: int | None = None
    ge: int | float | None = None
    le: int | float | None = None


def Field(*, default: Any = None, default_factory: Callable[[], Any] | None = None, **kwargs: Any) -> FieldInfo:
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        min_length=kwargs.get("min_length"),
        max_length=kwargs.get("max_length"),
        ge=kwargs.get("ge"),
        le=kwargs.get("le"),
    )


class ValidationError(ValueError):
    pass


def model_validator(*, mode: str = "after") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, "__pydantic_model_validator__", True)
        setattr(func, "__pydantic_validator_mode__", mode)
        return func

    return decorator


class BaseModel:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        validators: list[Callable[..., Any]] = []
        for value in cls.__dict__.values():
            if callable(value) and getattr(value, "__pydantic_model_validator__", False):
                validators.append(value)
        cls.__pydantic_validators__ = validators

    def __init__(self, **kwargs: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name, annotation in annotations.items():
            has_class_value = hasattr(self.__class__, name)
            class_value = getattr(self.__class__, name, None)
            if name in kwargs:
                value = kwargs[name]
            elif isinstance(class_value, FieldInfo):
                value = class_value.default_factory() if class_value.default_factory else class_value.default
            elif has_class_value:
                value = class_value
            else:
                raise ValidationError(f"Field '{name}' is required")

            field_info = class_value if isinstance(class_value, FieldInfo) else None
            setattr(self, name, self._coerce_and_validate_field(name, value, annotation, field_info))

        for validator in getattr(self.__class__, "__pydantic_validators__", []):
            if getattr(validator, "__pydantic_validator_mode__", "after") == "after":
                validator(self)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "BaseModel":
        if isinstance(data, cls):
            return data
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

    @staticmethod
    def _is_optional(annotation: Any) -> bool:
        origin = get_origin(annotation)
        args = get_args(annotation)
        return origin is not None and type(None) in args

    def _coerce_and_validate_field(
        self,
        name: str,
        value: Any,
        annotation: Any,
        field_info: FieldInfo | None,
    ) -> Any:
        if value is None:
            if self._is_optional(annotation):
                return value
            raise ValidationError(f"Field '{name}' cannot be null")

        origin = get_origin(annotation)
        if origin is Literal:
            allowed = get_args(annotation)
            if value not in allowed:
                raise ValidationError(f"Field '{name}' must be one of {allowed}")

        if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
            value = annotation.model_validate(value)

        if field_info:
            if isinstance(value, str):
                if field_info.min_length is not None and len(value) < field_info.min_length:
                    raise ValidationError(f"Field '{name}' is shorter than {field_info.min_length}")
                if field_info.max_length is not None and len(value) > field_info.max_length:
                    raise ValidationError(f"Field '{name}' is longer than {field_info.max_length}")
            if isinstance(value, (int, float)):
                if field_info.ge is not None and value < field_info.ge:
                    raise ValidationError(f"Field '{name}' must be >= {field_info.ge}")
                if field_info.le is not None and value > field_info.le:
                    raise ValidationError(f"Field '{name}' must be <= {field_info.le}")
        return value
