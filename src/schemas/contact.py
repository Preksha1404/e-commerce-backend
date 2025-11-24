from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional

class ContactRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[PhoneNumber] = None
    subject: str
    message: str
