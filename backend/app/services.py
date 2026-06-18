from uuid import uuid4

from cassandra import (
    OperationTimedOut,
    RequestExecutionException
)
from cassandra.cluster import NoHostAvailable

from app.database import session
from app.seats import SEATS


def safe_execute(query, params=None):
    try:
        return session.execute(query, params)
    except (
        OperationTimedOut,
        NoHostAvailable,
        RequestExecutionException
    ):
        return None


def create_reservation(data):

    if data.seat_number not in SEATS:
        return "INVALID_SEAT"

    reservation_id = str(uuid4())

    result = safe_execute("""
        INSERT INTO reservations (
            seat_number,
            reservation_id,
            customer_name,
            customer_email,
            movie_id,
            status
        )
        VALUES (%s,%s,%s,%s,%s,'ACTIVE')
        IF NOT EXISTS
    """, (
        data.seat_number,
        reservation_id,
        data.customer_name,
        data.customer_email,
        data.movie_id
    ))

    if result is None:
        return None

    row = result.one()

    if row and getattr(row, "applied", False):
        return get_reservation(data.seat_number)

    existing = get_reservation(data.seat_number)

    if existing and existing["status"] == "CANCELLED":

        update_result = safe_execute("""
            UPDATE reservations
            SET customer_name=%s,
                customer_email=%s,
                movie_id=%s,
                status='ACTIVE'
            WHERE seat_number=%s
            IF status='CANCELLED'
        """, (
            data.customer_name,
            data.customer_email,
            data.movie_id,
            data.seat_number
        ))

        if update_result is None:
            return None

        update_row = update_result.one()

        if update_row and getattr(update_row, "applied", False):
            return get_reservation(data.seat_number)

    return None


def get_reservation(seat_number):

    result = safe_execute("""
        SELECT *
        FROM reservations
        WHERE seat_number=%s
    """, [seat_number])

    if result is None:
        return None

    row = result.one()

    if row is None:
        return None

    return dict(row._asdict())


def get_all_reservations():

    rows = safe_execute("""
        SELECT *
        FROM reservations
        ALLOW FILTERING
    """)

    if rows is None:
        return []

    return [dict(row._asdict()) for row in rows]


def update_reservation(seat_number, data):

    reservation = get_reservation(seat_number)

    if reservation is None:
        return None

    result = safe_execute("""
        UPDATE reservations
        SET customer_name=%s,
            customer_email=%s
        WHERE seat_number=%s
        IF status='ACTIVE'
    """, (
        data.customer_name,
        data.customer_email,
        seat_number
    ))

    if result is None:
        return None

    row = result.one()

    if row and not getattr(row, "applied", False):
        return None

    return get_reservation(seat_number)


def cancel_reservation(seat_number):

    reservation = get_reservation(seat_number)

    if reservation is None:
        return None

    result = safe_execute("""
        UPDATE reservations
        SET status='CANCELLED'
        WHERE seat_number=%s
        IF status='ACTIVE'
    """, (seat_number,))

    if result is None:
        return None

    row = result.one()

    if row and not getattr(row, "applied", False):
        return None

    return get_reservation(seat_number)


def bulk_cancel(seat_numbers):

    cancelled = []

    for seat in seat_numbers:

        result = safe_execute("""
            UPDATE reservations
            SET status='CANCELLED'
            WHERE seat_number=%s
            IF status='ACTIVE'
        """, (seat,))

        if result is None:
            continue

        row = result.one()

        if row and getattr(row, "applied", False):
            cancelled.append(seat)

    return cancelled


def is_seat_occupied(seat_number):

    reservation = get_reservation(seat_number)

    if reservation is None:
        return False

    return reservation["status"] == "ACTIVE"