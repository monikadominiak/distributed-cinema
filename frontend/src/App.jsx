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

            <h1>Cinema System</h1>

            <SeatMap
                key={refreshKey}
            />

            <ReservationsTable
                key={refreshKey}
                onRefresh={refreshSystem}
            />

        </div>
    );
}

export default App;