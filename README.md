# Distributed Cinema Reservation System

A distributed cinema seat reservation system built with FastAPI and Apache Cassandra. The application supports seat reservations, updates, cancellations, bulk cancellations, and concurrent reservation handling using Cassandra lightweight transactions (LWT).


## Tech Stack

### Backend

* Python 3.11+
* FastAPI
* Cassandra Driver
* Uvicorn

### Database

* Apache Cassandra

### Frontend

* React
* Vite

---

## Prerequisites

Install:

* Python 3.11+
* Apache Cassandra
* Node.js 18+
* npm

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/monikadominiak/distributed-cinema.git
cd distributed-cinema
```

### 2. Start Cassandra

Make sure Cassandra is running locally on:

```text
127.0.0.1:9042
```

Verify:

```bash
cqlsh
```

### 3. Create the keyspace

```sql
CREATE KEYSPACE cinema
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 3
};
```

### 4. Create the reservations table

```sql
CREATE TABLE reservations (
    seat_number text PRIMARY KEY,
    reservation_id text,
    customer_name text,
    customer_email text,
    movie_id text,
    status text
);
```

### 5. Install backend dependencies

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 6. Start backend

```bash
uvicorn app.main:app --reload
```

Backend runs on:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## Running Stress Tests

Open a new terminal:

```bash
cd backend
```

Run:

```bash
python stress_tests/tests.py
```

---

## API Endpoints

### Get all seats

```http
GET /seats
```

### Create reservation

```http
POST /reservations
```

Example body:

```json
{
  "seat_number": "A1",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "movie_id": "MOVIE1"
}
```

### Get reservation

```http
GET /reservations/{seat_number}
```

### Update reservation

```http
PUT /reservations/{seat_number}
```

### Cancel reservation

```http
DELETE /reservations/{seat_number}
```

### Bulk cancel

```http
POST /bulk-cancel
```

---

## Project Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── services.py
│   ├── models.py
│   ├── database.py
│   └── seats.py
│
├── stress_tests/
│
└── requirements.txt

frontend/
│
├──src/
|   ├──components/
│       ├── ReservationsTable.jsx
│       ├── SeatMap.jsx
│
|    ├── App.jsx
|    ├── index.jss
|    ├── App.css
|    └── main.jsx


```
## Authors

Monika Dominiak 160307
Antonina Gardzielewska 160286






<img width="1897" height="875" alt="image" src="https://github.com/user-attachments/assets/a284e58c-0f1c-4edc-892c-0bb61cd6eef9" />
<img width="1883" height="890" alt="image" src="https://github.com/user-attachments/assets/4b44fa9e-5839-443e-bdfe-4fbf66d4a167" />
<img width="1877" height="908" alt="image" src="https://github.com/user-attachments/assets/a79c16a6-7288-4640-8a90-304ad2006d20" />
<img width="1877" height="903" alt="image" src="https://github.com/user-attachments/assets/e59d9f91-e40a-416c-b6c1-0bb0b6f9c2fe" />
<img width="1521" height="900" alt="image" src="https://github.com/user-attachments/assets/16c54ff7-c19a-4596-a7ec-90638ed70948" />
<img width="1636" height="907" alt="image" src="https://github.com/user-attachments/assets/7e4ed4ae-807a-4fdf-b72e-09037e9121ff" />
<img width="1523" height="907" alt="image" src="https://github.com/user-attachments/assets/515b7f37-2c75-44f6-9a61-2ec95d9d2139" />
<img width="1521" height="900" alt="image" src="https://github.com/user-attachments/assets/1288912a-fd3e-43a9-9110-b6aabad25d40" />

<img width="1597" height="892" alt="image" src="https://github.com/user-attachments/assets/420bc4b4-3da3-4cf6-bcd4-684758673a62" />
<img width="1550" height="911" alt="image" src="https://github.com/user-attachments/assets/aa2c5143-7252-4e37-a52f-7ef3a72cba77" />
<img width="1472" height="900" alt="image" src="https://github.com/user-attachments/assets/da121974-2ad5-439e-9efa-08f265251106" />





