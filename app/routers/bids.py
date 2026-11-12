from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status as http_status

from app.database import get_db
from app.models import Bid, Client
from app.schemas import BidCreate, BidResponse, BidStatus, BidUpdate

router = APIRouter(prefix="/bids", tags=["Bids"])


@router.post("/", response_model=BidResponse, status_code=http_status.HTTP_201_CREATED)
def create_bid(bid_in: BidCreate, db: Session = Depends(get_db)):
    client = db.get(Client, bid_in.client_id)
    if not client:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Client with id {bid_in.client_id} not found",
        )

    bid = Bid(**bid_in.model_dump())
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.get("/", response_model=list[BidResponse])
def list_bids(
    status: BidStatus | None = None,
    client_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Bid)
    if status:
        query = query.filter(Bid.status == status.value)
    if client_id:
        query = query.filter(Bid.client_id == client_id)
    return query.all()


@router.get("/{bid_id}", response_model=BidResponse)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )
    return bid


@router.put("/{bid_id}", response_model=BidResponse)
def update_bid(bid_id: int, bid_in: BidUpdate, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )

    for field, value in bid_in.model_dump(exclude_none=True).items():
        setattr(bid, field, value)

    db.commit()
    db.refresh(bid)
    return bid


@router.delete("/{bid_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )

    db.delete(bid)
    db.commit()
