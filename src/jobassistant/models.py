from datetime import datetime

import unicodedata
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, HttpUrl, field_validator


def _normalize(text: str) -> str:
    """Minúsculas y sin acentos: 'Málaga' -> 'malaga'."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


class JobSearch(BaseModel):
    """Criterios de búsqueda del usuario."""

    query: str = "python"
    locations: list[str] = Field(default_factory=lambda: ["Málaga", "Madrid"])
    max_days_old: int = Field(default=7, ge=1, le=90)
    results_per_page: int = Field(default=20, ge=1, le=50)


class JobPosting(BaseModel):
    """Oferta normalizada, independiente de la fuente."""

    source: str                       # "adzuna", "remoteok"...
    external_id: str                  # id de la oferta en su fuente
    title: str
    company: str | None = None
    location: str | None = None
    description: str
    url: HttpUrl
    posted_at: datetime | None = None
    salary_min: float | None = None
    salary_max: float | None = None

    @field_validator("external_id", mode="before")
    @classmethod
    def _id_to_str(cls, value):
        return str(value)

    def is_recent(self, max_days_old: int = 7) -> bool:
        """True si se publicó dentro de los últimos N días."""
        if self.posted_at is None:
            return False
        posted = self.posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        return posted >= datetime.now(timezone.utc) - timedelta(days=max_days_old)

    def matches_locations(self, locations: list[str]) -> bool:
        """True si la ubicación contiene alguna de las ciudades (sin acentos)."""
        if not self.location:
            return False
        loc = _normalize(self.location)
        return any(_normalize(city) in loc for city in locations)

    def matches(self, search: JobSearch) -> bool:
        return self.is_recent(search.max_days_old) and self.matches_locations(
            search.locations
        )