from sqlalchemy.orm import Session
from typing import List

from src.models.addresses import Address
from src.schemas.addresses import AddressCreate, AddressUpdate, AddressOut


def list_addresses(db: Session, user_id: int) -> List[AddressOut]:
    records = db.query(Address).filter(Address.user_id == user_id).order_by(Address.id.desc()).all()
    return [AddressOut.model_validate(r) for r in records]


def create_address(db: Session, user_id: int, data: AddressCreate) -> AddressOut:
    address = Address(
        user_id=user_id,
        full_name=data.full_name,
        phone_number=data.phone_number,
        address_line_1=data.address_line_1,
        address_line_2=data.address_line_2,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        country=data.country,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return AddressOut.model_validate(address)


def get_address(db: Session, user_id: int, address_id: int) -> AddressOut:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise LookupError("Address not found")
    return AddressOut.model_validate(address)


def update_address(db: Session, user_id: int, address_id: int, data: AddressUpdate) -> AddressOut:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise LookupError("Address not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return AddressOut.model_validate(address)


def delete_address(db: Session, user_id: int, address_id: int) -> None:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise LookupError("Address not found")
    db.delete(address)
    db.commit()


