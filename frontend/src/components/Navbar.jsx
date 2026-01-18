import React, { useState, useEffect } from 'react';
import { Play, Search, User, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { getMovies } from '../lib/api'; // We might need a new API func searchMovies

const Navbar = () => {
    const [scrolled, setScrolled] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Debounced Search
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (query.trim().length > 2) {
                setLoading(true);
                try {
                    // Fetch from API
                    let apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                    if (!apiHost.startsWith('http')) apiHost = `https://${apiHost}`;
                    const apiBase = apiHost + '/api';
                    const res = await fetch(`${apiBase}/search?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    setResults(data);
                } catch (e) {
                    console.error("Search failed", e);
                }
                setLoading(false);
            } else {
                setResults([]);
            }
        }, 300); // 300ms debounce

        return () => clearTimeout(timer);
    }, [query]);

    return (
        <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-black/95 backdrop-blur-sm' : 'bg-transparent'}`}>
            <div className="flex items-center justify-between px-8 py-4">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-2 text-red-600 font-bold text-2xl hover:text-red-500 transition-colors z-50">
                    <Play fill="currentColor" size={28} />
                    <span className="tracking-tight">MOVIESDA</span>
                </Link>

                {/* Navigation Links (Hidden when search is actively expanded on mobile, or just hide on search open) */}
                <div className={`hidden md:flex items-center gap-8 text-sm font-medium transition-opacity ${isSearchOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                    <Link to="/" className="text-white hover:text-gray-300 transition-colors">Home</Link>
                    <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors">Movies</a>
                    <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors">New Releases</a>
                    <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors">My List</a>
                </div>

                {/* Right Side / Search Bar */}
                <div className="flex items-center gap-4 relative">
                    <div className={`flex items-center transition-all duration-300 ${isSearchOpen ? 'w-[300px] bg-black/50 border border-gray-700' : 'w-8 bg-transparent border-transparent'} rounded overflow-visible`}>
                        {isSearchOpen && (
                            <input
                                autoFocus
                                type="text"
                                placeholder="Titles, people, genres..."
                                className="bg-transparent text-white text-sm px-3 py-1 outline-none w-full"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                            />
                        )}
                        <button
                            onClick={() => {
                                setIsSearchOpen(!isSearchOpen);
                                if (isSearchOpen) { setQuery(''); setResults([]); }
                            }}
                            className="text-gray-300 hover:text-white transition-colors p-1"
                        >
                            {isSearchOpen ? <X size={20} /> : <Search size={22} />}
                        </button>

                        {/* Search Results Dropdown */}
                        {isSearchOpen && (query.length > 2) && (
                            <div className="absolute top-12 right-0 w-[400px] max-h-[60vh] overflow-y-auto bg-[#141414] border border-gray-800 rounded shadow-2xl overflow-hidden">
                                {loading ? (
                                    <div className="p-4 text-center text-gray-400">Searching...</div>
                                ) : results.length > 0 ? (
                                    <div className="flex flex-col">
                                        {results.slice(0, 10).map((movie, idx) => (
                                            <Link
                                                key={`${movie.link}-${idx}`}
                                                to={`/player?title=${encodeURIComponent(movie.title)}&link=${encodeURIComponent(movie.link)}`}
                                                className="flex items-center gap-3 p-3 hover:bg-gray-800 transition border-b border-gray-800/50 last:border-0"
                                                onClick={() => setIsSearchOpen(false)}
                                            >
                                                {/* Poster Thumbnail */}
                                                <div className="w-10 h-14 bg-gray-800 rounded flex-shrink-0 overflow-hidden">
                                                    {movie.poster ? (
                                                        <img src={movie.poster} alt="" className="w-full h-full object-cover" />
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center">
                                                            <Play size={16} className="text-gray-500" />
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex flex-col overflow-hidden">
                                                    <span className="text-white font-medium truncate">{movie.title}</span>
                                                    <span className="text-xs text-gray-400">{movie.year_category || 'Movie'}</span>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 text-center text-gray-500">No results found for "{query}"</div>
                                )}
                            </div>
                        )}
                    </div>

                    <button className="w-8 h-8 rounded bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center">
                        <User size={18} />
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
