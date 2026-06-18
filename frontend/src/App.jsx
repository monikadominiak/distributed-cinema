import { useState } from "react";
import SeatMap from "./components/SeatMap";
import ReservationsTable from "./components/ReservationsTable";

function App() {

    const [refreshKey, setRefreshKey] = useState(0);

    const refreshSystem = () => {
        setRefreshKey(prev => prev + 1);
    };

    return (
        <div style={{ padding: "20px" }}>

            <h1>Distributed Cinema Reservation System</h1>

            <SeatMap
                key={`seat-${refreshKey}`}
                onReservationChange={refreshSystem}
            />

            <ReservationsTable
                key={`table-${refreshKey}`}
                onRefresh={refreshSystem}
            />

        </div>
    );
}

export default App;