from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.seats import SEATS
from app.services import is_seat_occupied, get_all_reservations
from app.database import session
from app.models import ReservationCreate, ReservationUpdate
from app.services import (
    create_reservation,
    get_reservation,
    update_reservation,
    cancel_reservation,
    get_all_reservations,
    bulk_cancel
)
from app.room import ROOM
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Distributed Cinema Reservation System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BulkCancelRequest(BaseModel):
    seat_numbers: list[str]


@app.get("/")
def root():
    return {"message": "Cinema Reservation API"}

@app.get("/seats")
def get_seats():

    result = []

    for seat in SEATS:

        result.append({
            "seat": seat,
            "occupied": is_seat_occupied(seat)
        })

    return result


@app.get("/room")
def get_room():
    return ROOM

@app.post("/reservations")
def reserve(data: ReservationCreate):

    reservation = create_reservation(data)

    if reservation is None:
        raise HTTPException(
            status_code=409,
            detail="Seat already reserved"
        )

    return reservation


@app.get("/reservations")
def all_reservations():
    return get_all_reservations()


@app.get("/reservations/{seat_number}")
def reservation_by_seat(seat_number: str):

    reservation = get_reservation(seat_number)

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return reservation


@app.put("/reservations/{seat_number}")
def update(seat_number: str, data: ReservationUpdate):

    reservation = update_reservation(
        seat_number,
        data
    )

    if reservation == "INVALID_SEAT":
        raise HTTPException(
            status_code=400,
            detail="Seat does not exist"
    )

    if not reservation:
        raise HTTPException(
            status_code=409,
            detail="Seat already reserved"
    )

    return reservation


@app.delete("/reservations/{seat_number}")
def cancel(seat_number: str):

    reservation = cancel_reservation(seat_number)

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return reservation


@app.post("/bulk-cancel")
def bulk_cancel_endpoint(data: BulkCancelRequest):

    cancelled = bulk_cancel(data.seat_numbers)

    return {
        "cancelled_count": len(cancelled),
        "cancelled_seats": cancelled
    }
