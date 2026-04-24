import { useEffect, useState } from 'react';
import { MessageCircleQuestion, Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { addFaq, addFaqBulk, clearFaq, getFaqStats } from '../../services/api';

export default function FaqPage() {
    const [faqCount, setFaqCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [category, setCategory] = useState('');
    const [source, setSource] = useState('');
    const [bulkJson, setBulkJson] = useState('');

    const loadStats = async () => {
        try {
            const res = await getFaqStats();
            setFaqCount(Number(res.data?.total_faq_entries || 0));
        } catch {
            toast.error('Failed to load FAQ stats');
        }
    };

    useEffect(() => {
        loadStats();
    }, []);

    const handleAddFaq = async (event) => {
        event.preventDefault();
        if (!question.trim() || !answer.trim()) {
            toast.error('Question and answer are required');
            return;
        }

        setLoading(true);
        try {
            await addFaq(question.trim(), answer.trim(), {
                category: category.trim() || undefined,
                source: source.trim() || undefined,
            });
            toast.success('FAQ entry added');
            setQuestion('');
            setAnswer('');
            setCategory('');
            setSource('');
            await loadStats();
        } catch (err) {
            const detail = err.response?.data?.detail;
            toast.error(typeof detail === 'string' ? detail : 'Failed to add FAQ');
        } finally {
            setLoading(false);
        }
    };

    const handleBulkImport = async () => {
        if (!bulkJson.trim()) {
            toast.error('Paste FAQ JSON first');
            return;
        }

        setLoading(true);
        try {
            const parsed = JSON.parse(bulkJson);
            if (!Array.isArray(parsed)) {
                toast.error('JSON must be an array of entries');
                return;
            }
            await addFaqBulk(parsed);
            toast.success('FAQ bulk import completed');
            setBulkJson('');
            await loadStats();
        } catch (err) {
            if (err instanceof SyntaxError) {
                toast.error(`Invalid JSON: ${err.message}`);
            } else {
                const detail = err.response?.data?.detail;
                toast.error(typeof detail === 'string' ? detail : 'Bulk import failed');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleClearFaq = async () => {
        const confirmed = window.confirm('Clear all FAQ entries from index?');
        if (!confirmed) return;

        setLoading(true);
        try {
            const res = await clearFaq();
            toast.success(`FAQ index cleared (${res.data?.deleted || 0} removed)`);
            await loadStats();
        } catch {
            toast.error('Failed to clear FAQ index');
        } finally {
            setLoading(false);
        }
    };

    const cardClass = 'astro-glass rounded-2xl border border-white/10 p-5 md:p-6';
    const inputClass = 'w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none';
    const labelClass = 'mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80';

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                    <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">FAQ Management</h2>
                    <p className="text-sm text-slate-300/85">Manage structured FAQ entries for FAQ-aware retrieval.</p>
                </div>
                <span className="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-100">
                    {faqCount} FAQ Indexed
                </span>
            </div>

            <section className={cardClass}>
                <h3 className="flex items-center gap-2 text-lg font-semibold text-white"><MessageCircleQuestion size={18} /> Add FAQ Entry</h3>
                <form className="mt-4 space-y-3" onSubmit={handleAddFaq}>
                    <div>
                        <label className={labelClass}>Question</label>
                        <input className={inputClass} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What is the admission process?" />
                    </div>
                    <div>
                        <label className={labelClass}>Answer</label>
                        <textarea className={inputClass} value={answer} onChange={(e) => setAnswer(e.target.value)} rows={4} placeholder="Apply online, upload required documents..." />
                    </div>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <div>
                            <label className={labelClass}>Category (optional)</label>
                            <input className={inputClass} value={category} onChange={(e) => setCategory(e.target.value)} placeholder="admission" />
                        </div>
                        <div>
                            <label className={labelClass}>Source (optional)</label>
                            <input className={inputClass} value={source} onChange={(e) => setSource(e.target.value)} placeholder="Admission Handbook" />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2.5 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        <Plus size={16} /> Add FAQ
                    </button>
                </form>
            </section>

            <section className={cardClass}>
                <h3 className="text-lg font-semibold text-white">Bulk Import</h3>
                <p className="mt-1 text-sm text-slate-300/80">Paste a JSON array: [{"{\"question\":\"...\",\"answer\":\"...\",\"metadata\":{...}}"}]</p>
                <textarea
                    className="mt-4 w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none"
                    rows={8}
                    value={bulkJson}
                    onChange={(e) => setBulkJson(e.target.value)}
                    placeholder='[{"question":"What is the admission process?","answer":"Apply online...","metadata":{"category":"admission"}}]'
                />
                <button
                    type="button"
                    disabled={loading}
                    onClick={handleBulkImport}
                    className="mt-3 inline-flex items-center gap-2 rounded-xl border border-emerald-300/40 bg-emerald-400/15 px-4 py-2.5 text-sm font-semibold text-emerald-100 transition-colors hover:bg-emerald-400/25 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    Import FAQs
                </button>
            </section>

            <section className={cardClass}>
                <h3 className="text-lg font-semibold text-white">Danger Zone</h3>
                <p className="mt-1 text-sm text-slate-300/80">Clear all indexed FAQ entries.</p>
                <button
                    type="button"
                    disabled={loading}
                    onClick={handleClearFaq}
                    className="mt-3 inline-flex items-center gap-2 rounded-xl border border-rose-300/40 bg-rose-400/15 px-4 py-2.5 text-sm font-semibold text-rose-100 transition-colors hover:bg-rose-400/25 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    <Trash2 size={16} /> Clear FAQ Index
                </button>
            </section>
        </div>
    );
}
