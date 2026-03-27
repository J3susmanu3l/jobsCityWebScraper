from pydantic import BaseModel, Field


class BusinessRecord(BaseModel):
    company_name: str
    category_query: str
    city: str
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    google_place_id: str = Field(default="")

