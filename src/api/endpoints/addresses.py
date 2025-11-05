from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User, UserRole
from src.schemas.addresses import (
    AddressCreate,
    AddressUpdate,
    AddressOut,
    CreateAddressResponse,
    UpdateAddressResponse,
    DeleteAddressResponse,
)
from src.services.address_service import (
    list_addresses,
    create_address,
    get_address,
    update_address,
    delete_address,
)


router = APIRouter(prefix="/user/addresses", tags=["Addresses"])


@router.get("/", response_model=list[AddressOut])
def get_user_addresses(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return list_addresses(db, current_user.id)


@router.post("/", response_model=CreateAddressResponse)
def create_user_address(payload: AddressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create addresses"
        )
    address = create_address(db, current_user.id, payload)
    return CreateAddressResponse(message="Address created", address=address)


@router.get("/{address_id}", response_model=AddressOut)
def get_user_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return get_address(db, current_user.id, address_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{address_id}", response_model=UpdateAddressResponse)
def update_user_address(address_id: int, payload: AddressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can update addresses"
        )
    try:
        address = update_address(db, current_user.id, address_id, payload)
        return UpdateAddressResponse(message="Address updated", address=address)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{address_id}", response_model=DeleteAddressResponse)
def delete_user_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can delete addresses"
        )
    try:
        delete_address(db, current_user.id, address_id)
        return DeleteAddressResponse(message="Address deleted")
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


