from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime


class NewsletterSubscribe(BaseModel):
    email: EmailStr


class NewsletterUnsubscribe(BaseModel):
    email: EmailStr


class NewsletterSubscriberOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

    @field_serializer('created_at', when_used='json')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat() if value else None
