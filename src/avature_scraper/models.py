from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Job:
    title: str
    description: str
    apply_url: str
    location: str | None = None
    posted_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source_site: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
