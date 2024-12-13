import uuid
from typing import Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import CreditRequest, ChargeSale, PhoneNumber
from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate

async def get_user(session: AsyncSession, user_id: Any) -> User | None:
    return await session.get(User, user_id)

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.scalar_one_or_none()

async def authenticate(
    session: AsyncSession, email: str, password: str
) -> User | None:
    user = await get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    db_user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        is_superuser=user_create.is_superuser,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def update_user(
    session: AsyncSession, user: User, user_in: UserUpdate
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    for field, value in update_data.items():
        setattr(user, field, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def create_item(session: AsyncSession, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

async def get_active_phone_numbers(session: AsyncSession):
    statement = select(PhoneNumber).where(PhoneNumber.is_active == True)
    result = await session.exec(statement)
    return result.scalars().all()

async def get_phone_number(session: AsyncSession, phone_id: int) -> PhoneNumber | None:
    return await session.get(PhoneNumber, phone_id)

async def get_user_credit_requests(session: AsyncSession, user_id: uuid.UUID):
    statement = select(CreditRequest).where(CreditRequest.user_id == user_id)
    result = await session.exec(statement)
    return result.scalars().all()

async def create_credit_request(
    session: AsyncSession, user_id: uuid.UUID, amount: int
) -> CreditRequest:
    credit_request = CreditRequest(user_id=user_id, amount=amount)
    session.add(credit_request)
    await session.commit()
    await session.refresh(credit_request)
    return credit_request

async def approve_credit_request(
    session: AsyncSession, request_id: int, user_id: uuid.UUID
) -> CreditRequest:
    async with session.begin():
        # Lock the credit request and user rows
        statement = select(CreditRequest).where(
            CreditRequest.id == request_id
        ).with_for_update()
        result = await session.exec(statement)
        credit_request = result.scalar_one()

        if credit_request.processed:
            raise ValueError("Request already processed")

        user_statement = select(User).where(User.id == user_id).with_for_update()
        result = await session.exec(user_statement)
        user = result.scalar_one()

        # Update credit request
        credit_request.status = "APPROVED"
        credit_request.processed = True

        # Update user credit
        user.credit += credit_request.amount

        await session.commit()
        await session.refresh(credit_request)
        return credit_request

async def create_charge_sale(
    session: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    phone_number_id: int,
) -> ChargeSale:
    async with session.begin():
        # Lock the user and phone number rows
        user_stmt = select(User).where(User.id == user_id).with_for_update()
        result = await session.exec(user_stmt)
        user = result.scalar_one()

        if user.credit < amount:
            raise ValueError("Insufficient credit")

        phone_stmt = select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id
        ).with_for_update()
        result = await session.exec(phone_stmt)
        phone = result.scalar_one()

        # Create charge sale
        charge_sale = ChargeSale(
            user_id=user_id,
            amount=amount,
            phone_number_id=phone_number_id,
            status="APPROVED",
            processed=True,
        )
        
        # Update balances
        user.credit -= amount
        phone.current_charge += amount
        
        session.add(charge_sale)
        await session.commit()
        await session.refresh(charge_sale)
        return charge_sale
