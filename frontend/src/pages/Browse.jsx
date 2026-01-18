import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { Play, ArrowLeft, Loader } from 'lucide-react';
import { generateGradient } from '../lib/ui-utils';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api';

const Browse = () => {
    const [searchParams] = useSearchParams();
    const yearName = searchParams.get('name') || 'Movies';
    const yearUrl = searchParams.get('url');

    const [movies, setMovies] = useState([]);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [initialLoad, setInitialLoad] = useState(true);

    const fetchPage = useCallback(async (pageNum) => {
        if (!yearUrl || loading) return;

        setLoading(true);
        try {
            const baseUrl = yearUrl.replace(/\/$/, '');
            const url = pageNum === 1
                ? `${API_BASE}/movies?year_url=${encodeURIComponent(baseUrl)}&pages=1`
                : `${API_BASE}/movies?year_url=${encodeURIComponent(baseUrl + '/?page=' + pageNum)}&pages=1`;

            const response = await fetch(url);
            const data = await response.json();

            // Filter navigation links
            const filtered = data.filter(m =>
                !m.title.startsWith('Tamil') && !m.title.includes('Movies')
            );

            if (filtered.length === 0) {
                setHasMore(false);
            } else {
                setMovies(prev => [...prev, ...filtered]);
                setPage(pageNum + 1);
            }
        } catch (err) {
            console.error(err);
            setHasMore(false);
        } finally {
            setLoading(false);
            setInitialLoad(false);
        }
    }, [yearUrl, loading]);

    // Initial load - fetch first 3 pages immediately
    useEffect(() => {
        if (!yearUrl) return;

        const loadInitial = async () => {
            setLoading(true);
            try {
                const baseUrl = yearUrl.replace(/\/$/, '');
                const url = `${API_BASE}/movies?year_url=${encodeURIComponent(baseUrl)}&pages=3`;
                const response = await fetch(url);
                const data = await response.json();

                const filtered = data.filter(m =>
                    !m.title.startsWith('Tamil') && !m.title.includes('Movies')
                );

                setMovies(filtered);
                setPage(4); // Start from page 4 for load more
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
                setInitialLoad(false);
            }
        };

        loadInitial();
    }, [yearUrl]);

    // Load more button handler
    const loadMore = () => {
        fetchPage(page);
    };

    return (
        <div className="bg-[#0a0a0a] min-h-screen">
            <Navbar />

            {/* Header */}
            <div className="pt-28 px-4 md:px-12 pb-8">
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors bg-white/5 px-4 py-2 rounded-full">
                    <ArrowLeft size={18} /> Back to Home
                </Link>
                <h1 className="text-4xl md:text-5xl font-bold text-white">
                    {yearName.replace('Moviesda ', '')}
                </h1>
                <p className="text-gray-400 mt-2 text-lg">{movies.length} titles available</p>
            </div>

            {/* Movies Grid */}
            <div className="px-4 md:px-12 pb-20">
                {initialLoad ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader className="w-10 h-10 animate-spin text-red-500" />
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
                            {movies.map((movie, idx) => (
                                <Link
                                    to={`/player?title=${encodeURIComponent(movie.title)}&link=${encodeURIComponent(movie.link)}`}
                                    key={idx}
                                    className="group/card relative transition-transform duration-300 hover:scale-105 hover:z-10"
                                >
                                    <div
                                        className="aspect-[2/3] rounded-lg overflow-hidden relative shadow-lg bg-gray-900"
                                    >
                                        {movie.poster ? (
                                            <img
                                                src={movie.poster}
                                                alt={movie.title}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
                                                onError={(e) => { e.target.style.display = 'none'; }}
                                            />
                                        ) : (
                                            <div
                                                className="w-full h-full"
                                                style={{ background: generateGradient(movie.title) }}
                                            ></div>
                                        )}

                                        {/* Title Overlay (Only if no poster) */}
                                        {(!movie.poster) && (
                                            <div className="absolute inset-0 flex items-center justify-center p-4">
                                                <span className="text-lg font-bold text-white text-center drop-shadow-md line-clamp-4">
                                                    {movie.title.replace(/\(\d{4}\)/, '')}
                                                </span>
                                            </div>
                                        )}

                                        {/* Year Badge */}
                                        <div className="absolute top-2 right-2 bg-black/60 backdrop-blur text-xs font-bold text-gray-200 px-2 py-1 rounded z-10">
                                            {(movie.title.match(/\((\d{4})\)/) || [])[1] || 'HD'}
                                        </div>

                                        {/* Hover Play Button */}
                                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/card:opacity-100 transition-opacity flex items-center justify-center border-2 border-transparent group-hover/card:border-red-600/50 rounded-lg">
                                            <div className="w-14 h-14 bg-red-600 rounded-full flex items-center justify-center shadow-red-glow">
                                                <Play className="w-6 h-6 text-white fill-current ml-1" />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="pt-3">
                                        <h3 className="text-sm font-medium text-gray-200 truncate group-hover/card:text-red-500 transition-colors">
                                            {movie.title}
                                        </h3>
                                    </div>
                                </Link>
                            ))}
                        </div>

                        {/* Load More Button */}
                        {hasMore && (
                            <div className="flex justify-center mt-12">
                                <button
                                    onClick={loadMore}
                                    disabled={loading}
                                    className="btn-primary px-8 py-3 disabled:opacity-50 min-w-[200px] justify-center"
                                >
                                    {loading ? (
                                        <><Loader className="w-5 h-5 animate-spin" /> Loading...</>
                                    ) : (
                                        'Load More Movies'
                                    )}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default Browse;
