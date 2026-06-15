import { useEffect, useState } from "react";
import api from "../api";

function SeatMap({ onReservationChange }) {

    const [seats, setSeats] = useState([]);
    const [selectedSeat, setSelectedSeat] = useState(null);

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");

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
    }, []);

    const reserveSeat = async () => {

        if (!selectedSeat) {
            alert("Please select a seat.");
            return;
        }

        if (!name || !email) {
            alert("Please enter name and email.");
            return;
        }

        try {

            await api.post("/reservations", {
                seat_number: selectedSeat,
                customer_name: name,
                customer_email: email,
                movie_id: "MOVIE1"
            });

            alert("Reservation successful!");

            setName("");
            setEmail("");
            setSelectedSeat(null);

            loadSeats();
            if (onReservationChange) {
                onReservationChange();
            }
        } catch (error) {

            console.error(error);

            if (error.response?.status === 409) {
                alert("Seat already reserved.");
            } else {
                alert("Reservation failed.");
            }
        }
    };

    return (
        <div style={{ padding: "20px" }}>

            <h2>Cinema Room</h2>

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
                        onClick={() => {
                            if (!seat.occupied) {
                                setSelectedSeat(seat.seat);
                            }
                        }}
                        style={{
                            height: "50px",
                            border: selectedSeat === seat.seat
                                ? "3px solid blue"
                                : "none",
                            borderRadius: "6px",
                            cursor: seat.occupied
                                ? "not-allowed"
                                : "pointer",
                            backgroundColor: seat.occupied
                                ? "red"
                                : "green",
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
                        style={{
                            width: "100%",
                            padding: "12px",
                            cursor: "pointer"
                        }}
                    >
                        Reserve Seat
                    </button>
                </div>
            )}
        </div>
    );
}

export default SeatMap;