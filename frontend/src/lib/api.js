import axios from 'axios';

const api = axios.create({
    baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api',
});

export const getYears = async () => {
    const response = await api.get('/years');
    return response.data;
};

export const getMovies = async (yearUrl) => {
    const response = await api.get('/movies', { params: { year_url: yearUrl } });
    return response.data;
};

export const getStreamLink = async (fileUrl) => {
    const response = await api.get('/stream', { params: { file_url: fileUrl } });
    return response.data;
};

export const getDetails = async (movieUrl) => {
    const response = await api.get('/details', { params: { movie_url: movieUrl } });
    return response.data;
};

export const getFiles = async (qualityUrl) => {
    const response = await api.get('/files', { params: { quality_url: qualityUrl } });
    return response.data;
};

export const getAutoStream = async (movieUrl) => {
    const response = await api.get('/auto-stream', { params: { movie_url: movieUrl } });
    return response.data;
};
