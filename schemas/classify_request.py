from pydantic import BaseModel, field_validator

class ClassifyRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        if len(v) > 4000:
            raise ValueError("text must be 4000 characters or fewer")
        return v.strip()