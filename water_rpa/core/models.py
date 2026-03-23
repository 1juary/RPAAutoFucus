from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RPATask:
    type: float
    value: str
    retry: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "RPATask":
        if not isinstance(data, dict):
            raise TypeError("RPATask.from_dict expects a dict")

        cmd_type = float(data.get("type", 1.0))
        value = "" if data.get("value") is None else str(data.get("value"))
        retry_raw = data.get("retry", 1)
        try:
            retry = int(retry_raw)
        except Exception:
            retry = 1

        return cls(type=cmd_type, value=value, retry=retry)

    def to_dict(self) -> dict:
        return {"type": float(self.type), "value": str(self.value), "retry": int(self.retry)}
