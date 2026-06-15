from utils import post, delete, get

print("\n--- TEST 5: BULK CANCEL ---")

SEATS = [f"A{i}" for i in range(1, 11)]

# Step 1: reserve many seats
for i, seat in enumerate(SEATS):
    post("/reservations", {
        "seat_number": seat,
        "customer_name": f"User{i}",
        "customer_email": f"u{i}@test.com",
        "movie_id": "MOVIE1"
    })

# Step 2: bulk cancel
payload = {"seat_numbers": SEATS}
status, resp = post("/bulk-cancel", payload)

print("Bulk cancel response:", status, resp)

# Step 3: verify
status, seats = get("/seats")

occupied = sum(1 for s in seats if s["occupied"])

print("Occupied after cancel:", occupied)