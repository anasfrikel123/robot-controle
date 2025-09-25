from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


# Collaborators

def create_collaborator(session: Session, collaborator_in: schemas.CollaboratorCreate) -> models.Collaborator:
    collaborator = models.Collaborator(**collaborator_in.model_dump())
    session.add(collaborator)
    session.flush()
    return collaborator


def get_collaborator(session: Session, collaborator_id: int) -> Optional[models.Collaborator]:
    return session.get(models.Collaborator, collaborator_id)


def get_collaborator_by_email(session: Session, email: str) -> Optional[models.Collaborator]:
    stmt = select(models.Collaborator).where(models.Collaborator.email == email)
    return session.execute(stmt).scalar_one_or_none()


def list_collaborators(session: Session) -> Iterable[models.Collaborator]:
    stmt = select(models.Collaborator).order_by(models.Collaborator.full_name)
    return session.execute(stmt).scalars().all()


def update_collaborator(
    session: Session, collaborator: models.Collaborator, collaborator_in: schemas.CollaboratorUpdate
) -> models.Collaborator:
    for field, value in collaborator_in.model_dump(exclude_unset=True).items():
        setattr(collaborator, field, value)
    session.add(collaborator)
    session.flush()
    return collaborator


# Clients

def create_client(session: Session, client_in: schemas.ClientCreate) -> models.Client:
    client = models.Client(**client_in.model_dump())
    session.add(client)
    session.flush()
    return client


def get_client(session: Session, client_id: int) -> Optional[models.Client]:
    return session.get(models.Client, client_id)


def list_clients(session: Session) -> Iterable[models.Client]:
    stmt = select(models.Client).order_by(models.Client.name)
    return session.execute(stmt).scalars().all()


def update_client(session: Session, client: models.Client, client_in: schemas.ClientUpdate) -> models.Client:
    for field, value in client_in.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    session.add(client)
    session.flush()
    return client


# Declarations

def create_declaration(
    session: Session, declaration_in: schemas.DeclarationCreate
) -> models.Declaration:
    data = declaration_in.model_dump(exclude={"attachments"})
    attachments = declaration_in.attachments or []

    declaration = models.Declaration(**data)
    session.add(declaration)
    session.flush()

    for attachment in attachments:
        session.add(
            models.DeclarationAttachment(
                declaration_id=declaration.id,
                **attachment.model_dump(),
            )
        )

    session.add(
        models.DeclarationHistory(
            declaration_id=declaration.id,
            previous_status=declaration.status,
            new_status=declaration.status,
            comment="Création de la déclaration",
        )
    )

    session.flush()
    session.refresh(declaration)
    return declaration


def list_declarations(
    session: Session,
    *,
    collaborator_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status: Optional[models.DeclarationStatus] = None,
    declaration_type: Optional[models.DeclarationType] = None,
) -> Iterable[models.Declaration]:
    stmt = select(models.Declaration).order_by(models.Declaration.due_date.desc())

    if collaborator_id is not None:
        stmt = stmt.where(models.Declaration.collaborator_id == collaborator_id)
    if client_id is not None:
        stmt = stmt.where(models.Declaration.client_id == client_id)
    if status is not None:
        stmt = stmt.where(models.Declaration.status == status)
    if declaration_type is not None:
        stmt = stmt.where(models.Declaration.declaration_type == declaration_type)

    return session.execute(stmt).scalars().all()


def get_declaration(session: Session, declaration_id: int) -> Optional[models.Declaration]:
    return session.get(models.Declaration, declaration_id)


def update_declaration(
    session: Session,
    declaration: models.Declaration,
    declaration_in: schemas.DeclarationUpdate,
    comment: str | None = None,
) -> models.Declaration:
    payload = declaration_in.model_dump(exclude_unset=True)

    old_status = declaration.status
    new_status = payload.get("status", declaration.status)

    for field, value in payload.items():
        setattr(declaration, field, value)

    session.add(declaration)
    session.flush()

    if new_status != old_status:
        session.add(
            models.DeclarationHistory(
                declaration_id=declaration.id,
                previous_status=old_status,
                new_status=new_status,
                comment=comment,
            )
        )

    session.refresh(declaration)
    return declaration


def add_attachment(
    session: Session, declaration: models.Declaration, attachment_in: schemas.DeclarationAttachmentCreate
) -> models.DeclarationAttachment:
    attachment = models.DeclarationAttachment(
        declaration_id=declaration.id, **attachment_in.model_dump()
    )
    session.add(attachment)
    session.flush()
    session.refresh(attachment)
    return attachment
