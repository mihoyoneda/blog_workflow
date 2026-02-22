import { useState } from 'react';
import { suggestTopics, suggestThemes, runDeepResearch, generateArticle } from './lib/api';
import type { Topic, Theme, Source } from './lib/api';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Loader2, ArrowRight, BookOpen, CheckCircle2, ChevronRight, FileText, Search, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const CATEGORIES = [
  'AI Performance Engineering',
  'GPU Computing & Hardware',
  'High-Performance Networking',
  'Robotics & Edge Computing'
];

type Step = 'category' | 'topic' | 'theme' | 'research' | 'article';

export default function App() {
  const [step, setStep] = useState<Step>('category');

  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

  const [themes, setThemes] = useState<Theme[]>([]);
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);

  const [sources, setSources] = useState<Source[]>([]);
  const [article, setArticle] = useState<string>('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCategorySelect = async (category: string) => {
    setSelectedCategory(category);
    setLoading(true);
    setError('');
    try {
      const data = await suggestTopics(category);
      setTopics(data);
      setStep('topic');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTopicSelect = async (topic: Topic) => {
    setSelectedTopic(topic);
    setLoading(true);
    setError('');
    try {
      const data = await suggestThemes(topic.title);
      setThemes(data);
      setStep('theme');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleThemeSelect = async (theme: Theme) => {
    setSelectedTheme(theme);
    setLoading(true);
    setError('');
    try {
      const data = await runDeepResearch(theme.theme);
      setSources(data);
      setStep('research');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateArticle = async () => {
    if (!selectedTheme) return;
    setLoading(true);
    setError('');
    try {
      const data = await generateArticle(selectedTheme.theme, sources);
      setArticle(data);
      setStep('article');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 pb-20">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-lg">
            <Sparkles className="w-5 h-5" />
            Antigravity Blog Automator
          </div>

          <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
            <span className={step === 'category' ? 'text-indigo-400' : ''}>Category</span>
            <ChevronRight className="w-4 h-4" />
            <span className={step === 'topic' ? 'text-indigo-400' : ''}>Topic</span>
            <ChevronRight className="w-4 h-4" />
            <span className={step === 'theme' ? 'text-indigo-400' : ''}>Theme</span>
            <ChevronRight className="w-4 h-4" />
            <span className={step === 'research' ? 'text-indigo-400' : ''}>Research</span>
            <ChevronRight className="w-4 h-4" />
            <span className={step === 'article' ? 'text-indigo-400' : ''}>Article</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 mt-12">
        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400">
            {error}
          </div>
        )}

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              className="flex flex-col items-center justify-center py-32 space-y-4"
            >
              <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
              <p className="text-xl text-slate-400 font-medium animate-pulse">Running Gemini 2.0 Pro Exp...</p>
            </motion.div>
          ) : (
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Step 1: Category */}
              {step === 'category' && (
                <div className="space-y-8">
                  <div className="text-center space-y-4">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
                      What are we <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">writing about today?</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                      Select a broad domain. Our AI will analyze 2025-2026 data to suggest high-impact structural topics.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                    {CATEGORIES.map(cat => (
                      <button
                        key={cat}
                        onClick={() => handleCategorySelect(cat)}
                        className="group p-6 text-left rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/50 transition-all duration-300 relative overflow-hidden"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <h3 className="text-xl font-semibold mb-2 relative z-10 flex items-center justify-between">
                          {cat}
                          <ArrowRight className="w-5 h-5 text-indigo-400 opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                        </h3>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 2: Topics */}
              {step === 'topic' && (
                <div className="space-y-8">
                  <div>
                    <h2 className="text-3xl font-bold mb-2">Trending Topics</h2>
                    <p className="text-slate-400">Based on 2025-2026 search trends in <strong className="text-white">{selectedCategory}</strong>.</p>
                  </div>

                  <div className="space-y-4">
                    {topics.map((topic, i) => (
                      <button
                        key={i}
                        onClick={() => handleTopicSelect(topic)}
                        className="w-full text-left p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 transition-all flex flex-col sm:flex-row gap-6 group hover:-translate-y-1"
                      >
                        <div className="flex-1 space-y-2">
                          <h3 className="text-xl font-bold group-hover:text-indigo-400 transition-colors">{topic.title}</h3>
                          <p className="text-slate-400 leading-relaxed">{topic.description}</p>
                        </div>
                        <div className="hidden sm:flex items-center">
                          <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center group-hover:bg-indigo-500 transition-colors">
                            <ArrowRight className="w-5 h-5" />
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 3: Themes */}
              {step === 'theme' && (
                <div className="space-y-8">
                  <div>
                    <h2 className="text-3xl font-bold mb-2">SEO/AEO Optimized Themes</h2>
                    <p className="text-slate-400">Refined angles for <strong className="text-white">{selectedTopic?.title}</strong>.</p>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    {themes.map((theme, i) => (
                      <button
                        key={i}
                        onClick={() => handleThemeSelect(theme)}
                        className="w-full text-left p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 transition-all group hover:-translate-y-1"
                      >
                        <h3 className="text-xl font-bold mb-3 group-hover:text-purple-400 transition-colors">{theme.theme}</h3>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <p className="text-sm font-semibold text-slate-300 mb-1 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            Why it works (SEO/AEO)
                          </p>
                          <p className="text-slate-400 text-sm leading-relaxed">{theme.rationale}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 4: Research */}
              {step === 'research' && (
                <div className="space-y-8">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                      <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                        <Search className="w-8 h-8 text-indigo-500" /> Deep Research
                      </h2>
                      <p className="text-slate-400">Gathered 8 top-tier 2024-2026 sources for: <strong className="text-white">{selectedTheme?.theme}</strong></p>
                    </div>
                    <button
                      onClick={handleGenerateArticle}
                      className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20"
                    >
                      <BookOpen className="w-5 h-5" />
                      Confirm & Send to NotebookLM
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {sources.map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
                      >
                        <div className="text-xs font-semibold text-indigo-400 mb-2">Source [{i + 1}] • {src.date}</div>
                        <h3 className="text-lg font-bold mb-2 line-clamp-2">{src.title}</h3>
                        <p className="text-sm text-slate-400 line-clamp-3 leading-relaxed">{src.snippet}</p>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 5: Article */}
              {step === 'article' && (
                <div className="space-y-8">
                  <div className="flex items-center gap-4 border-b border-slate-800 pb-6">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold">Generated Article</h2>
                      <p className="text-slate-400 text-sm">Authored by simulated NotebookLM</p>
                    </div>
                  </div>

                  <div className="w-full h-48 mb-8 relative rounded-3xl overflow-hidden border border-slate-800 shadow-2xl bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-pink-500/20 flex flex-col items-center justify-center p-6 text-center">
                    <Sparkles className="w-10 h-10 text-indigo-400 mb-2 opacity-50" />
                    <h3 className="text-xl font-bold text-white/90">{selectedTheme?.theme}</h3>
                    <div className="absolute bottom-4 left-4 right-4 text-center">
                      <p className="text-xs text-indigo-400 bg-indigo-950/80 backdrop-blur-md py-1 px-3 rounded-full inline-block">Abstract Theme Visualization (No API Configuration)</p>
                    </div>
                  </div>

                  <div className="prose prose-invert prose-slate max-w-none prose-headings:font-bold prose-a:text-indigo-400 prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-800">
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {article}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
