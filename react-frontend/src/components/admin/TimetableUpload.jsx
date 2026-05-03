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
                setStatus({ type: 'success', message: `${data.entries_added} timetable entries uploaded` });
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
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Timetable (CSV / XLSX)
            </h3>
            <p className="text-sm text-gray-600 mb-4">CSV/XLSX with columns: course_code, course_name, department, semester, section, day, start_time, end_time, room, instructor</p>
            <form onSubmit={upload}>
                <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    disabled={loading}
                    className="block w-full text-sm text-gray-500 mb-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <button
                    type="submit"
                    disabled={!file || loading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Uploading...' : 'Upload Timetable'}
                </button>
            </form>
            {status && (
                <div className={`mt-4 p-3 rounded flex items-center gap-2 ${status.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {status.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                    {status.message}
                </div>
            )}
        </div>
    );
}
