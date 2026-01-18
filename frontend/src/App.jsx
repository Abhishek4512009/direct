import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Browse from './pages/Browse';
import Player from './pages/Player';

import { useEffect } from 'react';

function App() {
    useEffect(() => {
        const pingBackend = async () => {
            try {
                await fetch('https://moviesda-backend.onrender.com/');
            } catch (e) {
                console.log("Keep-alive ping failed", e);
            }
        };
        // Ping every 5 minutes
        const interval = setInterval(pingBackend, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <Router>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/browse" element={<Browse />} />
                <Route path="/player" element={<Player />} />
            </Routes>
        </Router>
    );
}

export default App;
