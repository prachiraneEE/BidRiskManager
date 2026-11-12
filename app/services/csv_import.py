import csv
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.logger import logger
from app.models import Bid, Client

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def import_clients(db: Session) -> dict:
    filepath = DATA_DIR / "clients.csv"
    imported = 0
    skipped = 0
    errors: list[str] = []

    with open(filepath, newline="") as f:
        for row_num, row in enumerate(csv.DictReader(f), start=2):
            try:
                name = row.get("name", "").strip()
                if not name:
                    raise ValueError("name is empty")

                existing = db.query(Client).filter(Client.name == name).first()
                if existing:
                    skipped += 1
                    continue

                client = Client(
                    name=name,
                    industry=row.get("industry", "").strip(),
                    past_bids_won=int(row.get("past_bids_won", 0)),
                    past_bids_lost=int(row.get("past_bids_lost", 0)),
                )
                db.add(client)
                imported += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {e}")
                logger.warning("Skipping clients row %d: %s", row_num, e)

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}


def import_bids(db: Session) -> dict:
    filepath = DATA_DIR / "bids.csv"
    imported = 0
    skipped = 0
    errors: list[str] = []

    clients_by_name = {c.name: c for c in db.query(Client).all()}

    with open(filepath, newline="") as f:
        for row_num, row in enumerate(csv.DictReader(f), start=2):
            try:
                client_name = row.get("client_name", "").strip()
                title = row.get("title", "").strip()

                if not client_name or not title:
                    raise ValueError("client_name or title is empty")

                client = clients_by_name.get(client_name)
                if not client:
                    raise ValueError(f"unknown client '{client_name}'")

                value = float(row["value"])
                estimated_cost = float(row["estimated_cost"])
                if value <= 0 or estimated_cost <= 0:
                    raise ValueError(f"value ({value}) and cost ({estimated_cost}) must be positive")

                existing = (
                    db.query(Bid)
                    .filter(Bid.client_id == client.id, Bid.title == title)
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

                bid = Bid(
                    client_id=client.id,
                    title=title,
                    value=value,
                    estimated_cost=estimated_cost,
                    deadline=date.fromisoformat(row["deadline"]),
                    status=row.get("status", "draft").strip(),
                    notes=row.get("notes", "").strip() or None,
                )
                db.add(bid)
                imported += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {e}")
                logger.warning("Skipping bids row %d: %s", row_num, e)

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}


def import_all(db: Session) -> dict:
    logger.info("Starting CSV import...")
    clients_result = import_clients(db)
    logger.info("Clients: %s", clients_result)
    bids_result = import_bids(db)
    logger.info("Bids: %s", bids_result)
    return {"clients": clients_result, "bids": bids_result}
