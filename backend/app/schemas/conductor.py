from datetime import datetime

from pydantic import BaseModel, Field


class ConductorCapabilityResponse(BaseModel):
    id: str
    label: str
    description: str
    prompt: str
    source_title: str
    source_url: str


class ChatCapabilitySource(BaseModel):
    capability_id: str
    source_title: str
    source_url: str = Field(
        pattern=(
            r"^(?:/(?:chat\.html|focus\.html(?:#next-actions)?|librarian\.html|"
            r"archive\.html)|https://www\.linkt\.com\.au/using-toll-roads/"
            r"about-brisbane-toll-roads/toll-pricing/brisbane)$"
        )
    )
    generated_at: datetime
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
