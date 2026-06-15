import { useEffect, useState } from "react";
import api from "../api";

function ReservationsTable({ onReservationChange }) {
    const [reservations, setReservations] = useState([]);

    const loadReservations = async () => {
        try {
            const response = await api.get("/reservations");
            setReservations(response.data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        loadReservations();
    }, []);

    const cancelReservation = async (seatNumber) => {
        try {
            await api.delete(`/reservations/${seatNumber}`);

            alert(`Cancelled ${seatNumber}`);

            loadReservations();

            if (onRefresh) {
                onRefresh();
            }
        

        } catch (error) {
            alert("Failed to cancel");
        }
    };

    return (
        <div style={{ marginTop: "40px" }}>

            <h2>Reservations</h2>

            <button
                onClick={loadReservations}
                style={{
                    marginBottom: "15px",
                    padding: "8px"
                }}
            >
                Refresh Reservations
            </button>

            <table
                border="1"
                cellPadding="10"
                style={{
                    borderCollapse: "collapse",
                    width: "100%"
                }}
            >
                <thead>
                    <tr>
                        <th>Seat</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Movie</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>

                <tbody>

                    {reservations.map((reservation) => (

                        <tr key={reservation.reservation_id}>

                            <td>{reservation.seat_number}</td>

                            <td>{reservation.customer_name}</td>

                            <td>{reservation.customer_email}</td>

                            <td>{reservation.movie_id}</td>

                            <td>{reservation.status}</td>

                            <td>

                                {reservation.status === "ACTIVE" && (

                                    <button
                                        onClick={() =>
                                            cancelReservation(
                                                reservation.seat_number
                                            )
                                        }
                                    >
                                        Cancel
                                    </button>

                                )}

                            </td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>
    );
}

export default ReservationsTable;