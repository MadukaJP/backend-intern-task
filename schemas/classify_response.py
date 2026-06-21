from pydantic import BaseModel

class ClassifyResponse(BaseModel):
    type: str
    confidence: float