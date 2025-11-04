from pydantic import BaseModel, Field
from typing import Optional


class AddressBase(BaseModel):
    full_name: str = Field(...)
    phone_number: str = Field(...)
    address_line_1: str = Field(...)
    address_line_2: Optional[str] = Field(None)
    city: str = Field(...)
    state: str = Field(...)
    postal_code: str = Field(...)
    country: str = Field(...)

class AddressCreate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True