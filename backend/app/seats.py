# app/seats.py

ROWS = ["A", "B", "C", "D", "E"]

SEATS_PER_ROW = 10

SEATS = []

for row in ROWS:
    for number in range(1, SEATS_PER_ROW + 1):
        SEATS.append(f"{row}{number}")