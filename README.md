# Gestion des Déclarations Fiscales et Sociales

Ce dépôt contient un exemple d'API pour préparer un logiciel de suivi et d'archivage des déclarations fiscales et sociales réalisées par les collaborateurs d'un cabinet comptable. L'application est construite avec [FastAPI](https://fastapi.tiangolo.com/) et persiste les données dans une base SQLite via SQLAlchemy.

## Fonctionnalités

- Gestion des collaborateurs (création, activation/désactivation, mise à jour des rôles).
- Gestion des clients du cabinet avec archivage.
- Création, suivi et mise à jour des déclarations fiscales et sociales, incluant :
  - Type de déclaration (fiscale ou sociale) et période concernée.
  - Statut workflow (brouillon, en attente de validation, validée, déposée, rejetée, archivée).
  - Historique automatique des changements de statut.
  - Gestion de pièces jointes (métadonnées).
- Tableau de bord synthétique (volumétrie par statut, échéances imminentes, archivage).

## Installation

1. Créez un environnement virtuel (optionnel mais recommandé) :

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Sous Windows : .venv\\Scripts\\activate
   ```

2. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

## Lancement de l'API

Initialisez la base de données et démarrez le serveur de développement :

```bash
uvicorn archive_manager.main:app --reload
```

L'interface de documentation interactive est disponible à l'adresse [http://localhost:8000/docs](http://localhost:8000/docs).

## Structure des données

Les principaux modèles sont :

- **Collaborateur** : nom complet, email (unique), rôle, statut actif.
- **Client** : raison sociale, identifiant fiscal, secteur d'activité, email de contact, statut archivé.
- **Déclaration** : type (fiscale/sociale), période, échéance, montant, statut, notes, liens vers le collaborateur et le client, pièces jointes, historique des changements.

Chaque changement de statut alimente une table d'historique avec horodatage et commentaire éventuel.

## Exemple d'utilisation (extraits JSON)

### Création d'un collaborateur

```json
POST /collaborateurs
{
  "full_name": "Alice Martin",
  "email": "alice.martin@example.com",
  "role": "Responsable fiscal"
}
```

### Création d'une déclaration

```json
POST /declarations
{
  "declaration_type": "fiscale",
  "status": "brouillon",
  "reference": "TVA-2024-05-001",
  "amount": 15230.5,
  "period_start": "2024-05-01",
  "period_end": "2024-05-31",
  "due_date": "2024-06-19",
  "collaborator_id": 1,
  "client_id": 1,
  "attachments": [
    {
      "file_name": "bordereau_tva_mai2024.pdf",
      "description": "Bordereau généré depuis le portail fiscal"
    }
  ]
}
```

### Mise à jour du statut d'une déclaration

```json
PUT /declarations/1?comment=Transmission%20au%20client
{
  "status": "en_attente_validation"
}
```

## Tests

Aucun test automatisé n'est fourni, mais il est recommandé d'ajouter des cas de tests (Pytest) avant une mise en production.

## Licence

Projet fourni à titre d'exemple pédagogique.
