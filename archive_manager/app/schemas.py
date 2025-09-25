from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .models import DeclarationStatus, DeclarationType


class CollaboratorBase(BaseModel):
    full_name: str = Field(..., example="Alice Martin")
    email: EmailStr = Field(..., example="alice.martin@example.com")
    role: Optional[str] = Field(None, example="Responsable fiscal")
    active: bool = True


class CollaboratorCreate(CollaboratorBase):
    pass


class CollaboratorUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class CollaboratorRead(CollaboratorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClientBase(BaseModel):
    name: str = Field(..., example="SARL Dupont")
    tax_identifier: str = Field(..., example="FR123456789")
    sector: Optional[str] = Field(None, example="BTP")
    contact_email: Optional[EmailStr] = Field(None, example="contact@client.fr")
    archived: bool = False


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    archived: Optional[bool] = None


class ClientRead(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DeclarationAttachmentBase(BaseModel):
    file_name: str
    description: Optional[str] = None
    storage_path: Optional[str] = None


class DeclarationAttachmentCreate(DeclarationAttachmentBase):
    pass


class DeclarationAttachmentRead(DeclarationAttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DeclarationBase(BaseModel):
    declaration_type: DeclarationType
    status: DeclarationStatus = DeclarationStatus.brouillon
    reference: Optional[str] = Field(None, example="TVA-2024-05-001")
    amount: Optional[float] = None
    period_start: date
    period_end: date
    due_date: date
    submitted_at: Optional[datetime] = None
    archived: bool = False
    notes: Optional[str] = None
    collaborator_id: int
    client_id: int


class DeclarationCreate(DeclarationBase):
    attachments: Optional[List[DeclarationAttachmentCreate]] = None


class DeclarationUpdate(BaseModel):
    status: Optional[DeclarationStatus] = None
    reference: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[date] = None
    submitted_at: Optional[datetime] = None
    archived: Optional[bool] = None
    notes: Optional[str] = None
    collaborator_id: Optional[int] = None
    client_id: Optional[int] = None


class DeclarationHistoryRead(BaseModel):
    id: int
    previous_status: DeclarationStatus
    new_status: DeclarationStatus
    changed_at: datetime
    comment: Optional[str]

    class Config:
        from_attributes = True


class DeclarationRead(DeclarationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    attachments: List[DeclarationAttachmentRead] = Field(default_factory=list)
    history: List[DeclarationHistoryRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
