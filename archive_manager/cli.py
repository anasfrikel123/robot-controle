from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

import typer
import uvicorn
from sqlalchemy import func, select

from .app import crud, models, schemas
from .app.database import Base, engine, session_scope
from .app.export import build_application_bundle


cli = typer.Typer(help="Utilitaires pour l'application de gestion des déclarations.")


@cli.command(help="Initialise la base de données SQLite.")
def init_db(
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Supprime et recrée les tables (attention, toutes les données seront perdues).",
    )
) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    typer.echo("Base de données initialisée dans archive_manager.db")


@cli.command(help="Insère des données d'exemple pour démarrer rapidement.")
def seed(force: bool = typer.Option(False, "--force", help="Force le remplissage même si des données existent.")) -> None:
    Base.metadata.create_all(bind=engine)
    with session_scope() as session:
        existing_count = session.execute(select(func.count(models.Declaration.id))).scalar_one()
        if existing_count and not force:
            typer.echo(
                "La base contient déjà des déclarations. Utilisez --force pour regénérer les données d'exemple."
            )
            raise typer.Exit(code=0)

        if force:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

        collaborator = crud.create_collaborator(
            session,
            schemas.CollaboratorCreate(
                full_name="Alice Martin",
                email="alice.martin@example.com",
                role="Responsable fiscal",
            ),
        )

        reviewer = crud.create_collaborator(
            session,
            schemas.CollaboratorCreate(
                full_name="Marc Dupuis",
                email="marc.dupuis@example.com",
                role="Contrôleur social",
            ),
        )

        client = crud.create_client(
            session,
            schemas.ClientCreate(
                name="Société ABC",
                tax_identifier="FR123456789",
                sector="Commerce de détail",
                contact_email="contact@societe-abc.fr",
            ),
        )

        holding = crud.create_client(
            session,
            schemas.ClientCreate(
                name="Holding XYZ",
                tax_identifier="FR987654321",
                sector="Services",
                contact_email="finance@holding-xyz.fr",
            ),
        )

        declarations = [
            schemas.DeclarationCreate(
                declaration_type=models.DeclarationType.fiscale,
                status=models.DeclarationStatus.brouillon,
                reference="TVA-2024-05-001",
                amount=15230.50,
                period_start=date(2024, 5, 1),
                period_end=date(2024, 5, 31),
                due_date=date.today() + timedelta(days=7),
                notes="TVA mensuelle mai 2024.",
                submitted_at=None,
                collaborator_id=collaborator.id,
                client_id=client.id,
                attachments=[
                    schemas.DeclarationAttachmentCreate(
                        file_name="bordereau_tva_mai2024.pdf",
                        description="Bordereau généré depuis le portail fiscal",
                        storage_path=None,
                    )
                ],
            ),
            schemas.DeclarationCreate(
                declaration_type=models.DeclarationType.sociale,
                status=models.DeclarationStatus.validee,
                reference="DSN-2024-05-001",
                amount=24200.00,
                period_start=date(2024, 5, 1),
                period_end=date(2024, 5, 31),
                due_date=date.today() + timedelta(days=12),
                notes="Déclaration sociale nominative de mai.",
                submitted_at=None,
                collaborator_id=reviewer.id,
                client_id=client.id,
                attachments=[],
            ),
            schemas.DeclarationCreate(
                declaration_type=models.DeclarationType.fiscale,
                status=models.DeclarationStatus.deposee,
                reference="IS-2023-ANNUEL",
                amount=53200.00,
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
                due_date=date(2024, 4, 15),
                submitted_at=datetime(2024, 4, 10, 10, 0),
                notes="Impôt sur les sociétés exercice 2023.",
                collaborator_id=collaborator.id,
                client_id=holding.id,
                attachments=[
                    schemas.DeclarationAttachmentCreate(
                        file_name="is2023.pdf",
                        description="Déclaration signée",
                        storage_path=None,
                    )
                ],
            ),
        ]

        created = [crud.create_declaration(session, payload) for payload in declarations]

        crud.update_declaration(
            session,
            created[1],
            schemas.DeclarationUpdate(status=models.DeclarationStatus.deposee),
            comment="Déclaration transmise sur Net-entreprises",
        )

        crud.update_declaration(
            session,
            created[2],
            schemas.DeclarationUpdate(archived=True),
            comment="Archivage automatique après dépôt.",
        )

    typer.echo("Données d'exemple insérées : collaborateurs, clients et déclarations.")


@cli.command(help="Démarre le serveur FastAPI via Uvicorn.")
def run(
    host: str = typer.Option("127.0.0.1", help="Adresse d'écoute du serveur"),
    port: int = typer.Option(8000, help="Port d'écoute du serveur"),
    reload: bool = typer.Option(False, help="Active le rechargement automatique (mode développement)."),
) -> None:
    uvicorn.run("archive_manager.main:app", host=host, port=port, reload=reload)


@cli.command(help="Génère une archive ZIP de l'application prête à l'emploi.")
def package(
    output: Path = typer.Option(
        Path("archive_manager_bundle.zip"),
        "--output",
        "-o",
        help="Chemin du fichier ZIP à produire.",
    ),
    include_db: bool = typer.Option(
        False,
        "--include-db",
        help="Inclut la base SQLite existante si elle est disponible.",
    ),
) -> None:
    """Crée une archive compressée contenant le code et la configuration nécessaires."""

    buffer = build_application_bundle(include_db=include_db)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(buffer.getvalue())
    typer.echo(f"Archive de l'application créée : {output}")


def main(args: Optional[Sequence[str]] = None) -> None:
    cli(args=args)


if __name__ == "__main__":
    main()
