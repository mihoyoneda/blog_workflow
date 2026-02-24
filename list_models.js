import { GoogleGenAI } from '@google/genai';
import dotenv from 'dotenv';
dotenv.config();

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
async function run() {
  try {
    const models = await ai.models.list();
    for await (const model of models) {
        if (model.name.includes("image") || model.name.includes("imagen") || model.supportedGenerationMethods.includes("predict")) {
            console.log(model.name, model.supportedGenerationMethods);
        }
    }
  } catch (e) {
    console.log(e);
  }
}
run();
