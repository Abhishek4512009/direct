import React, { useEffect, useState } from 'react';
import { getMovies } from '../lib/api';
import { Link } from 'react-router-dom';
import { Play, ChevronLeft, ChevronRight } from 'lucide-react';
import { generateGradient } from '../lib/ui-utils';

const MovieRow = ({ title, yearUrl }) => {
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(true);
    const scrollRef = React.useRef(null);

    useEffect(() => {
        // For Home rows, we fetch fewer pages to keep it fast
        const fetchMovies = async () => {
            try {
                const data = await getMovies(yearUrl, 1); // Only 1 page for home rows
                setMovies(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchMovies();
    }, [yearUrl]);

    const scroll = (direction) => {
        if (scrollRef.current) {
            const scrollAmount = direction === 'left' ? -500 : 500;
            scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        }
    };

    if (loading) return (
        <div className="mb-8 px-4 md:px-12 animate-pulse">
            <div className="h-6 w-32 bg-gray-800 rounded mb-4"></div>
            <div className="flex gap-4 overflow-hidden">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex-none w-[200px] h-[112px] bg-gray-800 rounded"></div>
                ))}
            </div>
        </div>
    );

    if (!movies.length) return null;

    return (
        <div className="mb-12 group/row relative px-4 md:px-12">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl md:text-2xl font-bold text-white group-hover/row:text-red-500 transition-colors cursor-pointer">
                    <Link to={`/browse?name=${encodeURIComponent(title)}&url=${encodeURIComponent(yearUrl)}`}>
                        {title}
                    </Link>
                </h2>
                <Link
                    to={`/browse?name=${encodeURIComponent(title)}&url=${encodeURIComponent(yearUrl)}`}
                    className="text-xs font-semibold text-gray-400 hover:text-white uppercase tracking-wider"
                >
                    See All
                </Link>
            </div>

            {/* Navigation - Visible on Hover */}
            <button
                onClick={() => scroll('left')}
                className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-12 h-full bg-gradient-to-r from-black to-transparent flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity disabled:opacity-0"
            >
                <ChevronLeft className="w-8 h-8 text-white" />
            </button>
            <button
                onClick={() => scroll('right')}
                className="absolute right-0 top-1/2 -translate-y-1/2 z-20 w-12 h-full bg-gradient-to-l from-black to-transparent flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity"
            >
                <ChevronRight className="w-8 h-8 text-white" />
            </button>

            <div
                ref={scrollRef}
                className="flex overflow-x-auto scrollbar-hide gap-4 pb-4 -mx-4 px-4 md:-mx-12 md:px-12"
            >
                {movies.map((movie, idx) => (
                    <Link
                        to={`/player?title=${encodeURIComponent(movie.title)}&link=${encodeURIComponent(movie.link)}`}
                        key={idx}
                        className="flex-none w-[200px] md:w-[240px] group/card relative transition-transform duration-300 hover:scale-105 hover:z-10"
                    >
                        {/* Poster Card */}
                        <div
                            className="aspect-video rounded-md overflow-hidden relative shadow-lg bg-gray-900"
                        >
                            {movie.poster ? (
                                <img
                                    src={movie.poster}
                                    alt={movie.title}
                                    className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
                                    onError={(e) => { e.target.style.display = 'none'; }} // Fallback if image fails
                                />
                            ) : (
                                <div
                                    className="w-full h-full"
                                    style={{ background: generateGradient(movie.title) }}
                                ></div>
                            )}

                            {/* Title Overlay (Only visible if no poster OR on error/load) */}
                            {(!movie.poster) && (
                                <div className="absolute inset-0 flex items-center justify-center p-4">
                                    <span className="text-base font-bold text-white text-center drop-shadow-md line-clamp-3">
                                        {movie.title.replace(/\(\d{4}\)/, '')}
                                    </span>
                                </div>
                            )}

                            {/* Year Badge */}
                            <div className="absolute top-2 right-2 bg-black/60 backdrop-blur text-[10px] font-bold text-gray-200 px-2 py-0.5 rounded z-10">
                                {(movie.title.match(/\((\d{4})\)/) || [])[1] || 'HD'}
                            </div>

                            {/* Hover Overlay */}
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/card:opacity-100 transition-opacity flex items-center justify-center border-2 border-transparent group-hover/card:border-red-600/50 rounded-md">
                                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center shadow-red-glow">
                                    <Play className="w-5 h-5 text-white fill-current ml-1" />
                                </div>
                            </div>
                        </div>


                        {/* Title Below Poster */}
                        < div className="mt-2" >
                            <h3 className="text-sm font-medium text-gray-200 truncate group-hover/card:text-white transition-colors">
                                {movie.title}
                            </h3>
                            <p className="text-[10px] text-gray-500 truncate">
                                {(movie.title.match(/\((\d{4})\)/) || [])[1] || 'Movie'}
                            </p>
                        </div>
                    </Link>
                ))
                }
            </div >
        </div >
    );
};

export default MovieRow;
