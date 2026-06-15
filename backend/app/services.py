# from uuid import uuid4
# from app.database import session
# from app.seats import SEATS


# # In services.py — replace create_reservation
# def create_reservation(data):
#     if data.seat_number not in SEATS:
#         return "INVALID_SEAT"

#     reservation_id = str(uuid4())

#     # IF NOT EXISTS is an atomic compare-and-set in Cassandra
#     result = session.execute("""
#         INSERT INTO reservations (
#             seat_number, reservation_id,
#             customer_name, customer_email,
#             movie_id, status
#         ) VALUES (%s,%s,%s,%s,%s,'ACTIVE')
#         IF NOT EXISTS
#     """, (
#         data.seat_number, reservation_id,
#         data.customer_name, data.customer_email,
#         data.movie_id
#     ))

#     applied = result.one().applied

#     if not applied:
#         # Seat taken — check if it's cancelled (then update)
#         existing = get_reservation(data.seat_number)
#         if existing and existing["status"] == "CANCELLED":
#             update_result = session.execute("""
#                 UPDATE reservations SET
#                     customer_name=%s, customer_email=%s,
#                     movie_id=%s, status='ACTIVE'
#                 WHERE seat_number=%s
#                 IF status = 'CANCELLED'
#             """, (
#                 data.customer_name, data.customer_email,
#                 data.movie_id, data.seat_number
#             ))
#             if update_result.one().applied:
#                 return get_reservation(data.seat_number)
#         return None  # genuinely taken

#     return get_reservation(data.seat_number)


# def get_reservation(seat_number):

#     result = session.execute(
#         """
#         SELECT *
#         FROM reservations
#         WHERE seat_number = %s
#         """,
#         [seat_number]
#     )

#     row = result.one()

#     if not row:
#         return None

#     return dict(row._asdict())


# def get_all_reservations():

#     rows = session.execute(
#         """
#         SELECT *
#         FROM reservations
#         ALLOW FILTERING
#         """
#     )

#     return [dict(row._asdict()) for row in rows]


# def update_reservation(seat_number, data):

#     reservation = get_reservation(seat_number)

#     if not reservation:
#         return None

#     session.execute(
#         """
#         UPDATE reservations
#         SET customer_name = %s,
#             customer_email = %s
#         WHERE seat_number = %s
#         """,
#         (
#             data.customer_name,
#             data.customer_email,
#             seat_number
#         )
#     )

#     return get_reservation(seat_number)


# def cancel_reservation(seat_number):

#     reservation = get_reservation(seat_number)

#     if not reservation:
#         return None

#     session.execute(
#         """
#         UPDATE reservations
#         SET status = %s
#         WHERE seat_number = %s
#         """,
#         (
#             "CANCELLED",
#             seat_number
#         )
#     )

#     return get_reservation(seat_number)


# def bulk_cancel(seat_numbers):

#     cancelled = []

#     for seat in seat_numbers:

#         reservation = get_reservation(seat)

#         if reservation and reservation["status"] == "ACTIVE":

#             session.execute(
#                 """
#                 UPDATE reservations
#                 SET status = %s
#                 WHERE seat_number = %s
#                 """,
#                 (
#                     "CANCELLED",
#                     seat
#                 )
#             )

#             cancelled.append(seat)

#     return cancelled


# def is_seat_occupied(seat_number):

#     reservation = get_reservation(seat_number)

#     if not reservation:
#         return False

#     return reservation["status"] == "ACTIVE"


from uuid import uuid4
from cassandra import OperationTimedOut, WriteTimeout, ReadTimeout
from app.database import session
from app.seats import SEATS


def _safe_execute(query, params):
    """Execute a CQL statement, raising a RuntimeError on Cassandra timeouts."""
    try:
        return session.execute(query, params)
    except (OperationTimedOut, WriteTimeout, ReadTimeout) as e:
        raise RuntimeError(f"Database timeout: {e}")


def create_reservation(data):
    if data.seat_number not in SEATS:
        return "INVALID_SEAT"

    reservation_id = str(uuid4())

    result = _safe_execute("""
        INSERT INTO reservations (
            seat_number, reservation_id,
            customer_name, customer_email,
            movie_id, status
        ) VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
        IF NOT EXISTS
    """, (
        data.seat_number, reservation_id,
        data.customer_name, data.customer_email,
        data.movie_id
    ))

    if result.one().applied:
        return get_reservation(data.seat_number)

    # Seat row exists — reactivate only if it's CANCELLED
    existing = get_reservation(data.seat_number)
    if existing and existing["status"] == "CANCELLED":
        update_result = _safe_execute("""
            UPDATE reservations
            SET customer_name = %s,
                customer_email = %s,
                movie_id       = %s,
                status         = 'ACTIVE'
            WHERE seat_number = %s
            IF status = 'CANCELLED'
        """, (
            data.customer_name, data.customer_email,
            data.movie_id, data.seat_number
        ))
        if update_result.one().applied:
            return get_reservation(data.seat_number)

    return None  # genuinely taken


def get_reservation(seat_number):
    result = _safe_execute(
        "SELECT * FROM reservations WHERE seat_number = %s",
        [seat_number]
    )
    row = result.one()
    return dict(row._asdict()) if row else None


def get_all_reservations():
    result = _safe_execute(
        "SELECT * FROM reservations ALLOW FILTERING",
        []
    )
    return [dict(row._asdict()) for row in result]


def update_reservation(seat_number, data):
    """
    Update name/email only if the reservation is ACTIVE.
    Uses LWT (IF status = 'ACTIVE') to prevent blind overwrites.
    Returns None if the seat doesn't exist or isn't ACTIVE.
    """
    reservation = get_reservation(seat_number)
    if not reservation:
        return None

    result = _safe_execute("""
        UPDATE reservations
        SET customer_name  = %s,
            customer_email = %s
        WHERE seat_number = %s
        IF status = 'ACTIVE'
    """, (
        data.customer_name,
        data.customer_email,
        seat_number
    ))

    if not result.one().applied:
        return None  # was cancelled or taken by someone else concurrently

    return get_reservation(seat_number)


def cancel_reservation(seat_number):
    """
    Cancel only if ACTIVE.
    Uses LWT (IF status = 'ACTIVE') so double-cancels are detected.
    Returns None if the seat doesn't exist or was already cancelled.
    """
    reservation = get_reservation(seat_number)
    if not reservation:
        return None

    result = _safe_execute("""
        UPDATE reservations
        SET status = 'CANCELLED'
        WHERE seat_number = %s
        IF status = 'ACTIVE'
    """, (seat_number,))

    if not result.one().applied:
        return None  # already cancelled

    return get_reservation(seat_number)


def bulk_cancel(seat_numbers):
    """
    Cancel a list of seats. Each cancellation is independent (no batch LWT —
    Cassandra batch LWTs are expensive and limited to one partition anyway).
    Only seats that were ACTIVE are included in the returned list.
    """
    cancelled = []
    for seat in seat_numbers:
        result = _safe_execute("""
            UPDATE reservations
            SET status = 'CANCELLED'
            WHERE seat_number = %s
            IF status = 'ACTIVE'
        """, (seat,))
        # result is None if the row didn't exist; check before .one()
        if result and result.one().applied:
            cancelled.append(seat)
    return cancelled


def is_seat_occupied(seat_number):
    reservation = get_reservation(seat_number)
    return bool(reservation and reservation["status"] == "ACTIVE")