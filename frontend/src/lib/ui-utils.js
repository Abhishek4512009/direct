export const generateGradient = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }

    const c1 = `hsl(${hash % 360}, 70%, 20%)`;
    const c2 = `hsl(${(hash + 40) % 360}, 70%, 15%)`;
    const c3 = `hsl(${(hash + 80) % 360}, 70%, 10%)`;

    return `linear-gradient(135deg, ${c1}, ${c2}, ${c3})`;
};
