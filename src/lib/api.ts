export const API_URL = 'http://localhost:3001/api';

export interface Topic {
    title: string;
    description: string;
}

export interface Theme {
    theme: string;
    rationale: string;
}

export interface Source {
    title: string;
    url: string;
    snippet: string;
    date: string;
}

export const suggestTopics = async (category: string): Promise<Topic[]> => {
    const res = await fetch(`${API_URL}/suggest-topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category })
    });
    if (!res.ok) throw new Error('Failed to fetch topics');
    return res.json();
};

export const suggestThemes = async (topic: string): Promise<Theme[]> => {
    const res = await fetch(`${API_URL}/suggest-themes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
    });
    if (!res.ok) throw new Error('Failed to fetch themes');
    return res.json();
};

export const runDeepResearch = async (theme: string): Promise<Source[]> => {
    const res = await fetch(`${API_URL}/deep-research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme })
    });
    if (!res.ok) throw new Error('Failed to perform deep research');
    return res.json();
};

export const generateArticle = async (theme: string, sources: Source[]): Promise<string> => {
    const res = await fetch(`${API_URL}/generate-article`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, sources })
    });
    if (!res.ok) throw new Error('Failed to generate article');
    const data = await res.json();
    return data.article;
};
