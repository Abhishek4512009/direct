import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAutoStream } from '../lib/api';
import { ArrowLeft, WifiOff, AlertCircle, Loader, Film } from 'lucide-react';

const Player = () => {
    const [searchParams] = useSearchParams();
    const movieTitle = searchParams.get('title');
    const movieLink = searchParams.get('link');
    const navigate = useNavigate();

    const [streamUrl, setStreamUrl] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [status, setStatus] = useState('Initializing...');
    const [quality, setQuality] = useState('');

    const [metadata, setMetadata] = useState({});

    // Use ref to prevent double-fetching in Strict Mode
    const hasFetched = useRef(false);

    useEffect(() => {
        if (!movieLink || hasFetched.current) return;
        hasFetched.current = true;

        const resolveStream = async () => {
            setLoading(true);
            setError(null);
            setStatus('Searching for best quality (1080p)...');

            try {
                // Determine base URL if needed, but getAutoStream expects the full path from the year page
                // The scraper logic inside getAutoStream handles the domain resolution
                const result = await getAutoStream(movieLink);

                if (result && result.stream_url) {
                    setStreamUrl(result.stream_url);
                    setQuality(result.quality);
                    setMetadata({
                        poster: result.poster,
                        desc: result.desc
                    });
                    setStatus('Ready to play');
                } else {
                    throw new Error("Could not resolve a valid stream link.");
                }
            } catch (err) {
                console.error(err);
                setError(err.message || 'Failed to load video');
            } finally {
                setLoading(false);
            }
        };

        resolveStream();
    }, [movieLink]);

    return (
        <div className="bg-black min-h-screen text-white flex flex-col items-center justify-center relative overflow-hidden">

            {/* Back Button */}
            <button
                onClick={() => navigate(-1)}
                className="absolute top-6 left-6 z-50 bg-black/50 p-2 rounded-full hover:bg-white/20 transition backdrop-blur-md group"
            >
                <ArrowLeft size={24} className="text-gray-300 group-hover:text-white" />
            </button>

            {loading ? (
                <div className="text-center space-y-6 max-w-md w-full px-4 animate-in fade-in zoom-in duration-500">
                    <div className="relative w-20 h-20 mx-auto">
                        <div className="absolute inset-0 border-4 border-red-900/30 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-red-600 rounded-full border-t-transparent animate-spin"></div>
                        <Film className="absolute inset-0 m-auto text-red-600 animate-pulse" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold mb-2">Loading Movie</h2>
                        <p className="text-red-500 font-medium animate-pulse">{status}</p>
                        <p className="text-gray-500 text-sm mt-2 max-w-xs mx-auto">
                            Resolving download servers and fetching highest quality link...
                        </p>
                    </div>
                </div>
            ) : error ? (
                <div className="text-center max-w-md p-8 bg-[#1a1a1a] rounded-xl border border-red-900/30 shadow-2xl">
                    <div className="w-16 h-16 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <AlertCircle className="text-red-500" size={32} />
                    </div>
                    <h2 className="text-xl font-bold text-red-500 mb-2">Playback Error</h2>
                    <p className="text-gray-400 mb-6">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-full font-medium transition"
                    >
                        Try Again
                    </button>
                    <div className="mt-4 text-xs text-gray-600">
                        Sometimes mirrors are busy. Retrying usually works.
                    </div>
                </div>
            ) : (
                <div className="w-full h-screen bg-black relative">
                    <video
                        controls
                        autoPlay
                        className="w-full h-full object-contain"
                        controlsList="nodownload"
                    >
                        <source src={streamUrl} type="video/mp4" />
                        <source src={streamUrl} type="video/x-matroska" />
                        Your browser does not support the video tag.
                    </video>

                    {/* Quality Overlay */}
                    <div className="absolute top-6 right-6 bg-black/60 backdrop-blur-md px-3 py-1 rounded border border-white/10 text-xs font-mono text-green-400 pointer-events-none">
                        ● Quality: {quality}
                    </div>
                </div>
            )}
            {/* Metadata Overlay (Visible when controls are likely visible, or always for now) */}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-8 pb-20 pointer-events-none transition-opacity duration-300 group-hover:opacity-100">
                <div className="max-w-4xl">
                    <h1 className="text-3xl font-bold text-white mb-2 drop-shadow-md">{movieTitle}</h1>
                    {/* Description / Cast */}
                    {metadata.desc && (
                        <p className="text-gray-200 text-sm md:text-base max-w-2xl leading-relaxed whitespace-pre-wrap drop-shadow">
                            {metadata.desc}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Player;
