import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

// Middlewares
app.use(cors());
app.use(express.json());

// Initialize Gemini Client
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const model = 'gemini-2.5-flash';

// API Endpoints
app.post('/api/suggest-topics', async (req, res) => {
    try {
        const { category } = req.body;
        const prompt = `Suggest 5 highly technical, trending blog post topics for the category: "${category}". 
The topics must be based on the latest 2025-2026 data. 
Return ONLY a valid JSON array of objects, where each object has a 'title' (string) and 'description' (string) field.`;

        // Enable Google Search Grounding
        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
            config: {
                tools: [{ googleSearch: {} }]
            }
        });
        const parsed = JSON.parse(response.text.replace(/```json/g, '').replace(/```/g, ''));
        res.json(parsed);
    } catch (error) {
        console.error('Error suggesting topics:', error);
        res.status(500).json({ error: 'Failed to suggest topics' });
    }
});

app.post('/api/suggest-themes', async (req, res) => {
    try {
        const { topic } = req.body;
        const prompt = `Based on the topic "${topic}", suggest 5 highly specific article themes/angles that are SEO/AEO optimized. 
Return ONLY a valid JSON array of objects. Each object should have a 'theme' (string) and 'rationale' (string for why it's a good angle).`;

        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
            config: {
                responseMimeType: 'application/json',
            }
        });
        const parsed = JSON.parse(response.text.replace(/```json/g, '').replace(/```/g, ''));
        res.json(parsed);
    } catch (error) {
        console.error('Error suggesting themes:', error);
        res.status(500).json({ error: 'Failed to suggest themes' });
    }
});

app.post('/api/deep-research', async (req, res) => {
    try {
        const { theme } = req.body;
        const prompt = `Conduct deep research on the theme "${theme}". 
Gather EXACTLY 8 high-authority sources (academic papers, official whitepapers, tier-1 tech news).
CONSTRAINT: Only use sources published between 2024 and 2026.
Return ONLY a valid JSON array of objects, where each object has:
- 'title' (string)
- 'url' (string)
- 'snippet' (string)
- 'date' (string, approx publication date)`;

        // Enable Google Search Grounding
        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
            config: {
                tools: [{ googleSearch: {} }]
            }
        });
        const parsed = JSON.parse(response.text.replace(/```json/g, '').replace(/```/g, ''));
        res.json(parsed);
    } catch (error) {
        console.error('Error during deep research:', error);
        res.status(500).json({ error: 'Failed to conduct deep research' });
    }
});

app.post('/api/generate-article', async (req, res) => {
    try {
        const { theme, sources } = req.body;
        const sourcesContext = sources.map((s, i) => `[${i + 1}] ${s.title} - ${s.url}`).join('\\n');
        const prompt = `As a top-tier technical writer, write a 2,000-word authoritative article based on the following theme and sources.
Simulate NotebookLM's deep contextual understanding.
Theme: "${theme}"

Sources:
${sourcesContext}


Formatting Requirements:
1. Use Markdown for structure (headings, bold, lists).
2. MUST use LaTeX for formulas (e.g. enclose inline math with single dollar signs $...$ and block math with double dollar signs $$...$$).
3. Ensure Fixstars-style extreme technical depth (include realistic code snippets, architecture details, or performance numbers where applicable).
4. Cite sources explicitly using [1], [2], etc., corresponding to the provided sources list.
5. Do NOT output a JSON wrapper, just the raw markdown article starting with a # Title.`;

        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
        });
        res.json({ article: response.text });
    } catch (error) {
        console.error('Error generating article:', error);
        res.status(500).json({ error: 'Failed to generate article' });
    }
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});
