import concurrent.futures
import time
from utils import post, delete

SEAT = "B1"

def reserve(i):
    return post("/reservations", {
        "seat_number": SEAT,
        "customer_name": f"User{i}",
        "customer_email": f"u{i}@test.com",
        "movie_id": "MOVIE1"
    })

def cancel(_):
    return delete(f"/reservations/{SEAT}")

print("\n--- TEST 4: RESERVE + CANCEL LOOP ---")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
    tasks = []

    for i in range(20):
        tasks.append(ex.submit(reserve, i))
        tasks.append(ex.submit(cancel, i))

    results = [t.result() for t in tasks]

success = sum(1 for r in results if r[0] == 200)
conflict = sum(1 for r in results if r[0] == 409)

print("Success:", success)
print("Conflict:", conflict)