import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import TimetableUpload from '../../components/admin/TimetableUpload';
import { Calendar, Database, CheckCircle, RefreshCw } from 'lucide-react';

export default function TimetablePage() {
    const { user } = useAuth();
    const [uploadComplete, setUploadComplete] = useState(false);
    const [timetables, setTimetables] = useState([]);
    const [loading, setLoading] = useState(false);
    const [timetableCount, setTimetableCount] = useState(0);

    const fetchTimetables = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/admin/timetables', {
                headers: { 'X-User-ID': user?.id || '' },
            });
            if (response.ok) {
                const data = await response.json();
                if (Array.isArray(data)) {
                    setTimetables(data.slice(0, 20));
                    setTimetableCount(data.length);
                }
            }
        } catch (err) {
            console.log('Note: Could not fetch timetables list');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTimetables();
    }, [uploadComplete]);

    const onUploadComplete = () => {
        setUploadComplete(true);
        setTimeout(() => setUploadComplete(false), 3000);
        setTimeout(() => fetchTimetables(), 500);
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white flex items-center gap-3">
                    <Calendar className="h-7 w-7 text-indigo-400" />
                    Timetable Management
                </h2>
                <p className="text-sm text-slate-300/85 mt-2">Upload and manage class timetables (CSV/XLSX) to make them available for querying.</p>
            </div>

            {/* Success Notification */}
            {uploadComplete && (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3">
                    <div className="h-2 w-2 bg-emerald-400 rounded-full"></div>
                    <p className="text-emerald-300 font-medium text-sm">Timetable data uploaded successfully!</p>
                </div>
            )}

            {/* Stats Cards */}
            <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-indigo-500/10 p-3 rounded-lg border border-indigo-500/20">
                            <Database className="h-6 w-6 text-indigo-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Total Entries</p>
                            <p className="mt-1 text-2xl font-bold text-white">{timetableCount || '0'}</p>
                        </div>
                    </div>
                </div>

                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20">
                            <CheckCircle className="h-6 w-6 text-emerald-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Status</p>
                            <p className="mt-1 text-2xl font-bold text-emerald-400">Ready</p>
                        </div>
                    </div>
                </div>

                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-cyan-500/10 p-3 rounded-lg border border-cyan-500/20">
                            <RefreshCw className="h-6 w-6 text-cyan-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">System</p>
                            <p className="mt-1 text-sm font-bold text-cyan-400">Connected</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Upload Component */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <TimetableUpload userId={user?.id} onUploadComplete={onUploadComplete} />
            </section>

            {/* Uploaded Timetables Preview */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="flex items-center gap-2 text-lg font-semibold text-white">📅 Uploaded Timetable Entries</h3>
                    <button
                        onClick={fetchTimetables}
                        disabled={loading}
                        className="inline-flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-3 py-1.5 text-sm font-semibold text-slate-200 hover:bg-white/10 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Refresh
                    </button>
                </div>
                
                {loading ? (
                    <div className="text-center py-6">
                        <div className="inline-block">
                            <div className="h-8 w-8 border-4 border-indigo-500/20 border-t-indigo-400 rounded-full animate-spin"></div>
                        </div>
                        <p className="text-slate-300/80 mt-3">Loading overview...</p>
                    </div>
                ) : timetableCount > 0 ? (
                    <div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-left text-sm text-slate-100">
                                <thead>
                                    <tr className="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                                        <th className="px-4 py-3 font-semibold">Class</th>
                                        <th className="px-4 py-3 font-semibold">Day</th>
                                        <th className="px-4 py-3 font-semibold">Time</th>
                                        <th className="px-4 py-3 font-semibold">Subject</th>
                                        <th className="px-4 py-3 font-semibold">Room</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {timetables.map((entry, idx) => (
                                        <tr key={idx} className="border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-colors">
                                            <td className="px-4 py-3 font-medium text-white">
                                                {entry.class_name || '-'}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {entry.day || '-'}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {entry.start_time || ''} – {entry.end_time || ''}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {entry.subject || '-'}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="rounded-full border border-indigo-300/25 bg-indigo-300/10 px-3 py-1 text-xs font-semibold text-indigo-200">
                                                    {entry.room || '-'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {timetableCount > 20 && (
                            <p className="text-xs text-slate-400 mt-4">
                                Showing 20 of {timetableCount} total entries
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="bg-white/5 border border-white/10 rounded-lg p-6 text-center">
                        <Calendar className="h-12 w-12 text-slate-500 mx-auto mb-3 opacity-50" />
                        <p className="text-slate-300">No timetable entries found</p>
                        <p className="text-sm text-slate-400 mt-2">Upload a timetable CSV/XLSX file above to get started</p>
                    </div>
                )}
            </section>

            {/* Instructions */}
            <section className="astro-glass bg-indigo-500/5 rounded-2xl border border-indigo-500/20 p-5 md:p-6">
                <h3 className="font-semibold text-indigo-300 mb-3 text-lg">📋 Instructions</h3>
                <ol className="text-sm text-slate-300/80 space-y-2 list-decimal list-inside">
                    <li>Prepare your CSV or XLSX file with the required timetable columns.</li>
                    <li>Click <strong>"Choose File"</strong> to select your timetable document.</li>
                    <li>Click <strong>"Upload Timetable"</strong> to parse and store the schedule.</li>
                    <li>The system will automatically recognize the schedule and structure it.</li>
                    <li>Use the chat interface to query the timetable (e.g., "Where is Professor Smith's class on Monday?").</li>
                </ol>
            </section>

            {/* Sample Data Section */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <h3 className="text-lg font-semibold text-white mb-3">📚 Sample Data</h3>
                <p className="text-sm text-slate-300/80 mb-4">
                    Download the sample CSV file to understand the required timetable format:
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                    <a
                        href="/sample_data/timetable.csv"
                        download="timetable.csv"
                        className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-400 to-purple-500 px-4 py-2 text-sm font-semibold text-white transition-transform hover:scale-[1.02]"
                    >
                        📥 Download timetable.csv
                    </a>
                </div>
            </section>
        </div>
    );
}
