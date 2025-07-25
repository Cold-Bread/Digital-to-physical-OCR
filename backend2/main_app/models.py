from pydantic import BaseModel
from typing import Optional

# Pydantic model (like a DTO or data template)
class Patient(BaseModel):
    name: str
    dob: str
    last_visit: str
    taken_from: str
    placed_in: str
    to_shred: bool
    date_shredded: Optional[str] = None  # None if not shredded yet

