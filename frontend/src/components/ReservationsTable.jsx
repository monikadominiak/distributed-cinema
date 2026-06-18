import { useEffect, useState } from "react";
import api from "../api";

function ReservationsTable({ onRefresh }) {

    const [reservations, setReservations] = useState([]);

    const [editingSeat, setEditingSeat] = useState(null);
    const [editName, setEditName] = useState("");
    const [editEmail, setEditEmail] = useState("");

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
            console.error(error);
            alert("Failed to cancel reservation");
        }
    };

    const startEdit = (reservation) => {
        setEditingSeat(reservation.seat_number);
        setEditName(reservation.customer_name);
        setEditEmail(reservation.customer_email);
    };

    const saveEdit = async () => {
        try {

            await api.put(`/reservations/${editingSeat}`, {
                customer_name: editName,
                customer_email: editEmail
            });

            alert("Reservation updated");

            setEditingSeat(null);

            loadReservations();

            if (onRefresh) {
                onRefresh();
            }

        } catch (error) {
            console.error(error);
            alert("Failed to update reservation");
        }
    };

    const cancelEdit = () => {
        setEditingSeat(null);
        setEditName("");
        setEditEmail("");
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
                        <th>Actions</th>
                    </tr>
                </thead>

                <tbody>

                    {reservations.map((reservation) => (

                        <tr key={reservation.reservation_id}>

                            <td>{reservation.seat_number}</td>

                            <td>
                                {editingSeat === reservation.seat_number ? (
                                    <input
                                        value={editName}
                                        onChange={(e) =>
                                            setEditName(e.target.value)
                                        }
                                    />
                                ) : (
                                    reservation.customer_name
                                )}
                            </td>

                            <td>
                                {editingSeat === reservation.seat_number ? (
                                    <input
                                        value={editEmail}
                                        onChange={(e) =>
                                            setEditEmail(e.target.value)
                                        }
                                    />
                                ) : (
                                    reservation.customer_email
                                )}
                            </td>

                            <td>{reservation.movie_id}</td>

                            <td>{reservation.status}</td>

                            <td>

                                {editingSeat === reservation.seat_number ? (

                                    <>
                                        <button
                                            onClick={saveEdit}
                                            style={{
                                                marginRight: "5px"
                                            }}
                                        >
                                            Save
                                        </button>

                                        <button
                                            onClick={cancelEdit}
                                        >
                                            Cancel
                                        </button>
                                    </>

                                ) : (

                                    <>
                                        {reservation.status === "ACTIVE" && (

                                            <>
                                                <button
                                                    onClick={() =>
                                                        startEdit(
                                                            reservation
                                                        )
                                                    }
                                                    style={{
                                                        marginRight: "5px"
                                                    }}
                                                >
                                                    Edit
                                                </button>

                                                <button
                                                    onClick={() =>
                                                        cancelReservation(
                                                            reservation.seat_number
                                                        )
                                                    }
                                                >
                                                    Cancel
                                                </button>
                                            </>

                                        )}
                                    </>

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