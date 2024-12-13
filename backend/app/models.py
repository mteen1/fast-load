import uuid
from typing import Annotated, Optional
from pydantic import EmailStr, StringConstraints, field_validator
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from sqlalchemy import JSON


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    credit: int = Field(default=0)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: Annotated[str, StringConstraints(min_length=8, max_length=40)]


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class PhoneNumber(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    number: str = Field(unique=True, index=True)
    title: str = Field(default="")
    is_active: bool = Field(default=True, index=True)
    current_charge: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionBase(SQLModel):
    amount: int = Field(ge=0)
    status: str = Field(default="PENDING")
    processed: bool = Field(default=False)
    admin_notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: uuid.UUID = Field(foreign_key="user.id")


class CreditRequest(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    @field_validator('status')
    @classmethod
    def validate_status(cls, value):
        if value not in ['PENDING', 'APPROVED', 'REJECTED']:
            raise ValueError('Invalid status')
        return value


class ChargeSale(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number_id: int = Field(foreign_key="phonenumber.id")
    api_response: Optional[dict] = Field(default=None, sa_type=JSON)


# Request/Response models
class PhoneNumberResponse(SQLModel):
    id: int
    number: str
    is_active: bool


class CreditRequestCreate(SQLModel):
    amount: int = Field(gt=0)


class ChargeSaleCreate(SQLModel):
    amount: int = Field(gt=0)
    phone_number_id: int
