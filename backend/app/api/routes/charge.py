from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud
from app.api.deps import get_current_user, get_db
from app.models import (
    User, PhoneNumberResponse, CreditRequestCreate, 
    ChargeSaleCreate, CreditRequest, ChargeSale
)

router = APIRouter()

@router.get("/phone-numbers", response_model=List[PhoneNumberResponse])
async def list_phone_numbers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.get_active_phone_numbers(db)

@router.get("/phone-numbers/{phone_id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    phone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    phone = await crud.get_phone_number(db, phone_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return phone

@router.post("/credit-requests", response_model=CreditRequest)
async def create_credit_request(
    request: CreditRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.create_credit_request(db, current_user.id, request.amount)

@router.post("/credit-requests/{request_id}/approve", response_model=CreditRequest)
async def approve_credit_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await crud.approve_credit_request(db, request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/charge-sales", response_model=ChargeSale)
async def create_charge_sale(
    request: ChargeSaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await crud.create_charge_sale(
            db,
            current_user.id,
            request.amount,
            request.phone_number_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
