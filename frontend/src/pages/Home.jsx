import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import MovieRow from '../components/MovieRow';
import { getYears, getMovies } from '../lib/api';
import { Play, Info } from 'lucide-react';
import { Link } from 'react-router-dom';

const Home = () => {
    const [years, setYears] = useState([]);
    const [error, setError] = useState(null);
    const [heroMovie, setHeroMovie] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Get Years
                const yearsData = await getYears();
                if (yearsData && yearsData.length > 0) {
                    setYears(yearsData);

                    // 2. Get Random 2026/Recent Movie for Hero
                    // Use the first year (usually 2026 or newest)
                    const newestYear = yearsData[0];
                    const movies = await getMovies(newestYear.link, 1);

                    if (movies && movies.length > 0) {
                        // Pick random movie
                        const randomMovie = movies[Math.floor(Math.random() * movies.length)];
                        setHeroMovie({
                            title: randomMovie.title,
                            desc: `Experience the latest release from ${newestYear.name}. Stream '${randomMovie.title}' in high quality now.`,
                            link: randomMovie.link
                        });
                    }
                } else {
                    setError("No movies found. Is the backend running?");
                }
            } catch (err) {
                console.error(err);
                setError("Failed to connect to backend. Please ensure the server is running on port 8000.");
            }
        };
        fetchData();
    }, []);

    return (
        <div className="bg-[#141414] min-h-screen pb-20 overflow-x-hidden">
            <Navbar />

            {error && (
                <div className="bg-red-600 text-white text-center py-2 px-4 font-bold relative z-50">
                    {error}
                </div>
            )}

            {/* Hero Section */}
            <div className="relative h-[85vh] w-full">
                {/* Background (Gradient Placeholder) */}
                <div className="absolute inset-0 bg-gradient-to-br from-red-900/40 via-black to-black">
                    <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?q=80&w=2670&auto=format&fit=crop')] bg-cover bg-center opacity-30 mix-blend-overlay"></div>
                </div>

                {/* Gradient Masks */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-black/60"></div>
                <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/40 to-transparent"></div>

                {/* Content */}
                <div className="absolute bottom-[30%] left-4 md:left-12 max-w-2xl space-y-4">
                    <h1 className="text-5xl md:text-7xl font-black text-white drop-shadow-2xl tracking-tight line-clamp-2">
                        {heroMovie?.title ? heroMovie.title.replace(/\(\d{4}\)/, '') : 'Loading...'}
                    </h1>
                    <p className="text-lg md:text-xl text-gray-200 drop-shadow-md font-medium max-w-lg line-clamp-3">
                        {heroMovie?.desc || "Loading latest blockbusters..."}
                    </p>

                    <div className="flex items-center gap-4 pt-4">
                        <Link
                            to={heroMovie ? `/player?title=${encodeURIComponent(heroMovie.title)}&link=${encodeURIComponent(heroMovie.link)}` : '#'}
                            className={`flex items-center gap-2 bg-white text-black px-8 py-3 rounded hover:bg-white/90 transition font-bold text-lg ${!heroMovie ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <Play fill="black" size={24} /> Play
                        </Link>
                        <button className="flex items-center gap-2 bg-gray-500/40 text-white px-8 py-3 rounded hover:bg-gray-500/50 transition font-bold text-lg backdrop-blur-sm">
                            <Info size={24} /> More Info
                        </button>
                    </div>
                </div>
            </div>

            {/* Rows */}
            <div className="-mt-16 relative z-10 space-y-8">
                {years.map((year) => (
                    <MovieRow key={year.link} title={year.name} yearUrl={year.link} />
                ))}
            </div>
        </div>
    );
};

export default Home;
