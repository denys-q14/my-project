from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class NoteCreate(BaseModel):
    user_id: int
    title: str
    content: Optional[str] = None
    is_archived: Optional[bool] = False
    remind_at: datetime

    @validator('remind_at')
    def remind_at_not_in_past(cls, v):
        if v < datetime.now(v.tzinfo):
            raise ValueError('remind_at не може бути в минулому')
        return v

class NoteRead(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str] = None
    is_archived: bool
    created_at: datetime
    remind_at: Optional[datetime] = None

    class Config:
        orm_mode = True
