import { useState } from 'react';
import { Upload, Check, AlertCircle } from 'lucide-react';

export default function TimetableUpload({ userId, onUploadComplete }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);

    const upload = async (e) => {
        e.preventDefault();
        if (!file) return;
        setLoading(true);
        setStatus(null);
        const formData = new FormData();
        formData.append('file', file);
        if (userId) formData.append('uploaded_by', userId);
        try {
            const res = await fetch('/api/admin/upload/timetable', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            if (res.ok) {
                setStatus({ type: 'success', message: `${data.entries_added || 'Timetable'} records uploaded` });
                setFile(null);
                if (onUploadComplete) onUploadComplete();
            } else {
                setStatus({ type: 'error', message: data.detail || 'Upload failed' });
            }
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="astro-glass rounded-xl border border-white/10 p-5 bg-black/10">
            <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
                <Upload className="h-4 w-4 text-indigo-400" />
                Upload Timetable (CSV / XLSX)
            </h4>
            <p className="text-xs text-slate-400 mb-4 h-8">
                Columns: <span className="font-mono text-[10px]">course_code, course_name, department, semester, section, day, start_time, end_time, room, instructor</span>
            </p>
            <form onSubmit={upload} className="space-y-4">
                <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    disabled={loading}
                    className="block w-full text-sm text-slate-300 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-white/10 file:text-indigo-100 hover:file:bg-white/20 disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={!file || loading}
                    className="w-full rounded-xl bg-gradient-to-r from-indigo-400 to-purple-500 px-4 py-2.5 text-sm font-semibold text-white transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                >
                    {loading ? 'Uploading...' : 'Upload Timetable'}
                </button>
            </form>
            {status && (
                <div className={`mt-4 p-3 rounded-xl flex items-center gap-2 text-sm border ${status.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' : 'bg-rose-500/10 border-rose-500/20 text-rose-300'}`}>
                    {status.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                    {status.message}
                </div>
            )}
        </div>
    );
}
