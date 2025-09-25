from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .app import crud, models, schemas
from .app.export import build_application_bundle
from .app.database import Base, engine, get_session

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gestion des Déclarations Fiscales et Sociales",
    description=(
        "API permettant de gérer l'archivage et le suivi des déclarations "
        "fiscales et sociales réalisées par les collaborateurs d'un cabinet comptable."
    ),
    version="1.0.0",
)


# Collaborateurs
@app.post("/collaborateurs", response_model=schemas.CollaboratorRead, status_code=status.HTTP_201_CREATED)
def create_collaborator(
    collaborator_in: schemas.CollaboratorCreate,
    session: Session = Depends(get_session),
) -> schemas.CollaboratorRead:
    if crud.get_collaborator_by_email(session, collaborator_in.email):
        raise HTTPException(status_code=400, detail="Un collaborateur avec cet email existe déjà.")
    collaborator = crud.create_collaborator(session, collaborator_in)
    return schemas.CollaboratorRead.model_validate(collaborator)


@app.get("/collaborateurs", response_model=List[schemas.CollaboratorRead])
def list_collaborators(session: Session = Depends(get_session)) -> List[schemas.CollaboratorRead]:
    collaborators = crud.list_collaborators(session)
    return [schemas.CollaboratorRead.model_validate(item) for item in collaborators]


@app.put("/collaborateurs/{collaborator_id}", response_model=schemas.CollaboratorRead)
def update_collaborator(
    collaborator_id: int,
    collaborator_in: schemas.CollaboratorUpdate,
    session: Session = Depends(get_session),
) -> schemas.CollaboratorRead:
    collaborator = crud.get_collaborator(session, collaborator_id)
    if not collaborator:
        raise HTTPException(status_code=404, detail="Collaborateur introuvable")
    collaborator = crud.update_collaborator(session, collaborator, collaborator_in)
    return schemas.CollaboratorRead.model_validate(collaborator)


# Clients
@app.post("/clients", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(client_in: schemas.ClientCreate, session: Session = Depends(get_session)) -> schemas.ClientRead:
    client = crud.create_client(session, client_in)
    return schemas.ClientRead.model_validate(client)


@app.get("/clients", response_model=List[schemas.ClientRead])
def list_clients(session: Session = Depends(get_session)) -> List[schemas.ClientRead]:
    clients = crud.list_clients(session)
    return [schemas.ClientRead.model_validate(client) for client in clients]


@app.put("/clients/{client_id}", response_model=schemas.ClientRead)
def update_client(
    client_id: int,
    client_in: schemas.ClientUpdate,
    session: Session = Depends(get_session),
) -> schemas.ClientRead:
    client = crud.get_client(session, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    client = crud.update_client(session, client, client_in)
    return schemas.ClientRead.model_validate(client)


# Déclarations
@app.post("/declarations", response_model=schemas.DeclarationRead, status_code=status.HTTP_201_CREATED)
def create_declaration(
    declaration_in: schemas.DeclarationCreate,
    session: Session = Depends(get_session),
) -> schemas.DeclarationRead:
    if not crud.get_collaborator(session, declaration_in.collaborator_id):
        raise HTTPException(status_code=400, detail="Collaborateur inexistant")
    if not crud.get_client(session, declaration_in.client_id):
        raise HTTPException(status_code=400, detail="Client inexistant")

    declaration = crud.create_declaration(session, declaration_in)
    return schemas.DeclarationRead.model_validate(declaration)


@app.get("/declarations", response_model=List[schemas.DeclarationRead])
def list_declarations(
    session: Session = Depends(get_session),
    collaborator_id: Optional[int] = Query(None),
    client_id: Optional[int] = Query(None),
    status_filter: Optional[models.DeclarationStatus] = Query(None, alias="status"),
    declaration_type: Optional[models.DeclarationType] = Query(None),
) -> List[schemas.DeclarationRead]:
    declarations = crud.list_declarations(
        session,
        collaborator_id=collaborator_id,
        client_id=client_id,
        status=status_filter,
        declaration_type=declaration_type,
    )
    return [schemas.DeclarationRead.model_validate(item) for item in declarations]


@app.get("/declarations/{declaration_id}", response_model=schemas.DeclarationRead)
def get_declaration(declaration_id: int, session: Session = Depends(get_session)) -> schemas.DeclarationRead:
    declaration = crud.get_declaration(session, declaration_id)
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration introuvable")
    return schemas.DeclarationRead.model_validate(declaration)


@app.put("/declarations/{declaration_id}", response_model=schemas.DeclarationRead)
def update_declaration(
    declaration_id: int,
    declaration_in: schemas.DeclarationUpdate,
    comment: Optional[str] = Query(None, description="Commentaire lié à la mise à jour"),
    session: Session = Depends(get_session),
) -> schemas.DeclarationRead:
    declaration = crud.get_declaration(session, declaration_id)
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration introuvable")
    declaration = crud.update_declaration(session, declaration, declaration_in, comment=comment)
    return schemas.DeclarationRead.model_validate(declaration)


@app.post(
    "/declarations/{declaration_id}/pieces",
    response_model=schemas.DeclarationAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_attachment(
    declaration_id: int,
    attachment_in: schemas.DeclarationAttachmentCreate,
    session: Session = Depends(get_session),
) -> schemas.DeclarationAttachmentRead:
    declaration = crud.get_declaration(session, declaration_id)
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration introuvable")
    attachment = crud.add_attachment(session, declaration, attachment_in)
    return schemas.DeclarationAttachmentRead.model_validate(attachment)


@app.get("/tableau-de-bord")
def dashboard(session: Session = Depends(get_session)) -> Dict[str, Any]:
    total_declarations = session.execute(
        select(func.count(models.Declaration.id))
    ).scalar_one()

    status_counts = {status.value: 0 for status in models.DeclarationStatus}
    status_counts_query = session.execute(
        select(models.Declaration.status, func.count(models.Declaration.id))
        .group_by(models.Declaration.status)
    )
    for status_value, count in status_counts_query.all():
        status_counts[status_value.value] = count

    upcoming_due_date = date.today() + timedelta(days=15)
    upcoming_declarations = session.execute(
        select(func.count(models.Declaration.id)).where(
            models.Declaration.due_date >= date.today(),
            models.Declaration.due_date <= upcoming_due_date,
            models.Declaration.status.in_(
                [
                    models.DeclarationStatus.brouillon,
                    models.DeclarationStatus.en_attente_validation,
                    models.DeclarationStatus.validee,
                ]
            ),
        )
    ).scalar_one()

    archived_count = session.execute(
        select(func.count(models.Declaration.id)).where(models.Declaration.archived.is_(True))
    ).scalar_one()

    active_collaborators = session.execute(
        select(func.count(models.Collaborator.id)).where(models.Collaborator.active.is_(True))
    ).scalar_one()

    active_clients = session.execute(
        select(func.count(models.Client.id)).where(models.Client.archived.is_(False))
    ).scalar_one()

    return {
        "total_declarations": total_declarations,
        "status_counts": status_counts,
        "a_traiter_avant": upcoming_due_date.isoformat(),
        "nombre_echeances_imminentes": upcoming_declarations,
        "archivees": archived_count,
        "collaborateurs_actifs": active_collaborators,
        "clients_actifs": active_clients,
    }


@app.get(
    "/telechargements/application",
    response_description="Archive ZIP de l'application prête à l'emploi",
)
def download_application(include_db: bool = Query(False)) -> StreamingResponse:
    """Expose un téléchargement de l'application et de sa configuration."""

    bundle = build_application_bundle(include_db=include_db)
    filename = "archive_manager_bundle.zip"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(bundle, media_type="application/zip", headers=headers)
