import { useEffect, useState } from "react";
import api from "../api";

function SeatMap({ onReservationChange }) {

    const [seats, setSeats] = useState([]);
    const [selectedSeat, setSelectedSeat] = useState(null);

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");

    const [movie, setMovie] = useState("MOVIE1");

    const [loading, setLoading] = useState(false);

    const loadSeats = async () => {
        try {
            const response = await api.get("/seats");
            setSeats(response.data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {

        loadSeats();

        const interval = setInterval(loadSeats, 3000);

        return () => clearInterval(interval);

    }, []);

    const reserveSeat = async () => {

        if (!selectedSeat) {
            alert("Select a seat");
            return;
        }

        if (!name || !email) {
            alert("Enter name and email");
            return;
        }

        try {

            setLoading(true);

            await api.post("/reservations", {
                seat_number: selectedSeat,
                customer_name: name,
                customer_email: email,
                movie_id: movie
            });

            alert("Reservation successful");

            setSelectedSeat(null);
            setName("");
            setEmail("");

            loadSeats();

            if (onReservationChange) {
                onReservationChange();
            }

        } catch (error) {

            if (error.response?.status === 409) {
                alert("Seat already reserved");
            } else {
                alert("Reservation failed");
            }

        } finally {
            setLoading(false);
        }
    };

    const occupied = seats.filter(s => s.occupied).length;
    const available = seats.length - occupied;

    return (
        <div style={{ padding: "20px" }}>

            <h2>Cinema Room</h2>

            <div
                style={{
                    marginBottom: "20px",
                    padding: "15px",
                    border: "1px solid #ddd",
                    borderRadius: "8px"
                }}
            >
                <h3>Statistics</h3>

                <p>Total Seats: {seats.length}</p>
                <p>Occupied: {occupied}</p>
                <p>Available: {available}</p>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(10, 60px)",
                    gap: "10px",
                    marginBottom: "30px"
                }}
            >
                {seats.map((seat) => (

                    <button
                        key={seat.seat}
                        title={
                            seat.occupied
                                ? "Reserved"
                                : "Available"
                        }
                        onClick={() => {
                            if (!seat.occupied) {
                                setSelectedSeat(seat.seat);
                            }
                        }}
                        style={{
                            height: "50px",
                            borderRadius: "6px",
                            cursor: seat.occupied
                                ? "not-allowed"
                                : "pointer",
                            border:
                                selectedSeat === seat.seat
                                    ? "3px solid blue"
                                    : "none",
                            backgroundColor:
                                selectedSeat === seat.seat
                                    ? "#2563eb"
                                    : seat.occupied
                                    ? "#dc2626"
                                    : "#16a34a",
                            color: "white",
                            fontWeight: "bold"
                        }}
                    >
                        {seat.seat}
                    </button>

                ))}
            </div>

            {selectedSeat && (

                <div
                    style={{
                        border: "1px solid #ccc",
                        padding: "20px",
                        borderRadius: "8px",
                        maxWidth: "400px"
                    }}
                >
                    <h3>Selected Seat: {selectedSeat}</h3>

                    <select
                        value={movie}
                        onChange={(e) => setMovie(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px",
                            marginBottom: "10px"
                        }}
                    >
                        <option value="MOVIE1">Movie 1</option>
                    </select>

                    <input
                        type="text"
                        placeholder="Name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px",
                            marginBottom: "10px"
                        }}
                    />

                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px",
                            marginBottom: "10px"
                        }}
                    />

                    <button
                        onClick={reserveSeat}
                        disabled={loading}
                        style={{
                            width: "100%",
                            padding: "12px"
                        }}
                    >
                        {loading
                            ? "Reserving..."
                            : "Reserve Seat"}
                    </button>

                </div>

            )}

        </div>
    );
}

export default SeatMap;