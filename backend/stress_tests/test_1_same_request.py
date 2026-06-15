import concurrent.futures
from utils import post

SEAT = "A1"

def task(i):
    payload = {
        "seat_number": SEAT,
        "customer_name": f"User{i}",
        "customer_email": f"user{i}@test.com",
        "movie_id": "MOVIE1"
    }
    return post("/reservations", payload)

print("\n--- TEST 1: SAME REQUEST ---")

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
    results = list(ex.map(task, range(50)))

success = sum(1 for r in results if r[0] == 200)
conflict = sum(1 for r in results if r[0] == 409)

print("Success:", success)
print("Conflict:", conflict)