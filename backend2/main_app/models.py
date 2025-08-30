from pydantic import BaseModel
from typing import Optional, List

class OCRResult(BaseModel):
    name: str
    dob: Optional[str] = None

class Patient(BaseModel):
    name: str
    dob: Optional[str] = None
    year_joined: int
    last_dos: int
    shred_year: int
    is_child_when_joined: bool
    box_number: str

class OCRResponse(BaseModel):
    ocr1: List[OCRResult]
    ocr2: List[OCRResult]
    ocr3: List[OCRResult]
    finalResult: OCRResult
