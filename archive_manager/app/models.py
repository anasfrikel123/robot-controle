from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class DeclarationType(str, Enum):
    fiscale = "fiscale"
    sociale = "sociale"


class DeclarationStatus(str, Enum):
    brouillon = "brouillon"
    en_attente_validation = "en_attente_validation"
    validee = "validee"
    deposee = "deposee"
    rejetee = "rejetee"
    archivee = "archivee"


class Collaborator(Base):
    __tablename__ = "collaborators"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(120), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    declarations = relationship("Declaration", back_populates="collaborator")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_identifier = Column(String(100), unique=True, nullable=False)
    sector = Column(String(150), nullable=True)
    contact_email = Column(String(255), nullable=True)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    declarations = relationship("Declaration", back_populates="client")


class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    declaration_type = Column(SqlEnum(DeclarationType), nullable=False)
    status = Column(SqlEnum(DeclarationStatus), default=DeclarationStatus.brouillon, nullable=False)
    reference = Column(String(120), nullable=True, unique=True)
    amount = Column(Float, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    archived = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    collaborator_id = Column(Integer, ForeignKey("collaborators.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    collaborator = relationship("Collaborator", back_populates="declarations")
    client = relationship("Client", back_populates="declarations")
    attachments = relationship("DeclarationAttachment", back_populates="declaration", cascade="all, delete-orphan")
    history = relationship("DeclarationHistory", back_populates="declaration", cascade="all, delete-orphan")


class DeclarationAttachment(Base):
    __tablename__ = "declaration_attachments"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("declarations.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    storage_path = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    declaration = relationship("Declaration", back_populates="attachments")


class DeclarationHistory(Base):
    __tablename__ = "declaration_history"

    id = Column(Integer, primary_key=True, index=True)
    declaration_id = Column(Integer, ForeignKey("declarations.id"), nullable=False)
    previous_status = Column(SqlEnum(DeclarationStatus), nullable=False)
    new_status = Column(SqlEnum(DeclarationStatus), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    comment = Column(Text, nullable=True)

    declaration = relationship("Declaration", back_populates="history")
