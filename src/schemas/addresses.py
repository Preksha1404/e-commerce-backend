from pydantic import BaseModel, Field
from typing import Optional, List
from pydantic_extra_types.phone_numbers import PhoneNumber

class AddressBase(BaseModel):
    full_name: str = Field(max_length=100)
    phone_number: PhoneNumber
    address_line_1: str = Field(max_length=255)
    address_line_2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(max_length=100)


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address_line_1: Optional[str] = Field(default=None, max_length=255)
    address_line_2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)


class AddressOut(AddressBase):
    id: int

    class Config:
        from_attributes = True


class CreateAddressResponse(BaseModel):
    message: str
    address: AddressOut


class UpdateAddressResponse(BaseModel):
    message: str
    address: AddressOut


class DeleteAddressResponse(BaseModel):
    message: str