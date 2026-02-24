import { GoogleGenAI } from '@google/genai';
import dotenv from 'dotenv';
import fs from 'fs';
dotenv.config();

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

async function run() {
  try {
    const response = await ai.models.generateImages({
      model: 'imagen-3.0-generate-001',
      prompt: 'A futuristic floating banana',
      config: {
        numberOfImages: 1,
        outputMimeType: 'image/jpeg',
      }
    });
    console.log("SUCCESS");
  } catch (e) {
    console.error("FAILED", e.message);
  }
}
run();
