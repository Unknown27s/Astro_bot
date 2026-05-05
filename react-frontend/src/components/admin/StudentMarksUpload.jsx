import { useState } from 'react';
import { Upload, Check, AlertCircle, FileSpreadsheet, Users, FileText } from 'lucide-react';

export default function StudentMarksUpload({ userId, onUploadComplete }) {
    const [activeTab, setActiveTab] = useState('unified');
    
    // File states
    const [unifiedFile, setUnifiedFile] = useState(null);
    const [studentFile, setStudentFile] = useState(null);
    const [marksFile, setMarksFile] = useState(null);
    
    // Loading states
    const [unifiedLoading, setUnifiedLoading] = useState(false);
    const [studentLoading, setStudentLoading] = useState(false);
    const [marksLoading, setMarksLoading] = useState(false);
    
    // Status states
    const [unifiedStatus, setUnifiedStatus] = useState(null);
    const [studentStatus, setStudentStatus] = useState(null);
    const [marksStatus, setMarksStatus] = useState(null);

    const uploadUnified = async (e) => {
        e.preventDefault();
        if (!unifiedFile) return;

        setUnifiedLoading(true);
        setUnifiedStatus(null);

        const formData = new FormData();
        formData.append('file', unifiedFile);
        if (userId) formData.append('uploaded_by', userId);

        try {
            const response = await fetch('/api/admin/upload/unified', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (response.ok) {
                setUnifiedStatus({ type: 'success', message: `Processed ${data.total_records_processed} records (${data.students_added_or_updated} students, ${data.marks_added} marks)` });
                setUnifiedFile(null);
                if (onUploadComplete) onUploadComplete();
            } else {
                setUnifiedStatus({ type: 'error', message: data.detail || 'Upload failed' });
            }
        } catch (error) {
            setUnifiedStatus({ type: 'error', message: error.message });
        } finally {
            setUnifiedLoading(false);
        }
    };

    const uploadStudents = async (e) => {
        e.preventDefault();
        if (!studentFile) return;

        setStudentLoading(true);
        setStudentStatus(null);

        const formData = new FormData();
        formData.append('file', studentFile);
        if (userId) formData.append('uploaded_by', userId);

        try {
            const response = await fetch('/api/admin/upload/students', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (response.ok) {
                setStudentStatus({ type: 'success', message: `${data.students_added} students uploaded` });
                setStudentFile(null);
                if (onUploadComplete) onUploadComplete();
            } else {
                setStudentStatus({ type: 'error', message: data.detail || 'Upload failed' });
            }
        } catch (error) {
            setStudentStatus({ type: 'error', message: error.message });
        } finally {
            setStudentLoading(false);
        }
    };

    const uploadMarks = async (e) => {
        e.preventDefault();
        if (!marksFile) return;

        setMarksLoading(true);
        setMarksStatus(null);

        const formData = new FormData();
        formData.append('file', marksFile);
        if (userId) formData.append('uploaded_by', userId);

        try {
            const response = await fetch('/api/admin/upload/marks', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (response.ok) {
                setMarksStatus({ type: 'success', message: `${data.marks_added} marks records uploaded` });
                setMarksFile(null);
                if (onUploadComplete) onUploadComplete();
            } else {
                setMarksStatus({ type: 'error', message: data.detail || 'Upload failed' });
            }
        } catch (error) {
            setMarksStatus({ type: 'error', message: error.message });
        } finally {
            setMarksLoading(false);
        }
    };

    return (
        <div className="w-full">
            {/* Tabs */}
            <div className="flex flex-wrap border-b border-white/10 mb-6">
                <button
                    onClick={() => setActiveTab('unified')}
                    className={`flex items-center gap-2 px-6 py-3 font-semibold text-sm transition-colors border-b-2 ${
                        activeTab === 'unified'
                            ? 'border-indigo-400 text-indigo-300 bg-indigo-500/10 rounded-t-lg'
                            : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'
                    }`}
                >
                    <FileSpreadsheet className="h-4 w-4" />
                    Unified Upload
                </button>
                <button
                    onClick={() => setActiveTab('students')}
                    className={`flex items-center gap-2 px-6 py-3 font-semibold text-sm transition-colors border-b-2 ${
                        activeTab === 'students'
                            ? 'border-cyan-400 text-cyan-300 bg-cyan-500/10 rounded-t-lg'
                            : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'
                    }`}
                >
                    <Users className="h-4 w-4" />
                    Students Only
                </button>
                <button
                    onClick={() => setActiveTab('marks')}
                    className={`flex items-center gap-2 px-6 py-3 font-semibold text-sm transition-colors border-b-2 ${
                        activeTab === 'marks'
                            ? 'border-emerald-400 text-emerald-300 bg-emerald-500/10 rounded-t-lg'
                            : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'
                    }`}
                >
                    <FileText className="h-4 w-4" />
                    Marks Only
                </button>
            </div>

            {/* Tab Contents */}
            <div className="max-w-2xl">
                {activeTab === 'unified' && (
                    <div className="astro-glass rounded-xl border border-indigo-500/20 p-5 md:p-8 bg-indigo-500/5">
                        <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                            <Upload className="h-5 w-5 text-indigo-400" />
                            Upload Unified Data
                        </h4>
                        <p className="text-sm text-slate-300 mb-4">
                            Upload a single CSV/XLSX file containing both student details and marks. The system will automatically link them.
                        </p>
                        <div className="bg-black/20 rounded-lg p-3 mb-6 border border-white/5">
                            <p className="text-xs text-slate-400 mb-1">Required columns:</p>
                            <p className="font-mono text-xs text-indigo-200/80 break-all leading-relaxed">
                                roll_no, name, email, phone, department, semester, subject_code, subject_name, subject_semester, internal_marks, external_marks, grade
                            </p>
                        </div>
                        <form onSubmit={uploadUnified} className="space-y-4">
                            <input
                                type="file"
                                accept=".csv,.xlsx"
                                onChange={(e) => setUnifiedFile(e.target.files?.[0] || null)}
                                disabled={unifiedLoading}
                                className="block w-full text-sm text-slate-300 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/20 file:text-indigo-200 hover:file:bg-indigo-500/30 disabled:opacity-50 cursor-pointer border border-dashed border-white/20 rounded-xl p-4 bg-black/10"
                            />
                            <button
                                type="submit"
                                disabled={!unifiedFile || unifiedLoading}
                                className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/25 transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                            >
                                {unifiedLoading ? 'Processing...' : 'Upload Unified Data'}
                            </button>
                        </form>
                        {unifiedStatus && (
                            <div className={`mt-4 p-4 rounded-xl flex items-center gap-3 text-sm font-medium border ${unifiedStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'}`}>
                                {unifiedStatus.type === 'success' ? <Check className="h-5 w-5 flex-shrink-0" /> : <AlertCircle className="h-5 w-5 flex-shrink-0" />}
                                {unifiedStatus.message}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'students' && (
                    <div className="astro-glass rounded-xl border border-cyan-500/20 p-5 md:p-8 bg-cyan-500/5">
                        <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                            <Upload className="h-5 w-5 text-cyan-400" />
                            Upload Student Roster
                        </h4>
                        <p className="text-sm text-slate-300 mb-4">
                            Upload a CSV/XLSX file containing only student master data (no marks).
                        </p>
                        <div className="bg-black/20 rounded-lg p-3 mb-6 border border-white/5">
                            <p className="text-xs text-slate-400 mb-1">Required columns:</p>
                            <p className="font-mono text-xs text-cyan-200/80 break-all leading-relaxed">
                                roll_no, name, email, phone, department, semester, gpa
                            </p>
                        </div>
                        <form onSubmit={uploadStudents} className="space-y-4">
                            <input
                                type="file"
                                accept=".csv,.xlsx"
                                onChange={(e) => setStudentFile(e.target.files?.[0] || null)}
                                disabled={studentLoading}
                                className="block w-full text-sm text-slate-300 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-cyan-500/20 file:text-cyan-200 hover:file:bg-cyan-500/30 disabled:opacity-50 cursor-pointer border border-dashed border-white/20 rounded-xl p-4 bg-black/10"
                            />
                            <button
                                type="submit"
                                disabled={!studentFile || studentLoading}
                                className="w-full rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-3 text-sm font-bold text-slate-900 shadow-lg shadow-cyan-500/25 transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                            >
                                {studentLoading ? 'Processing...' : 'Upload Students'}
                            </button>
                        </form>
                        {studentStatus && (
                            <div className={`mt-4 p-4 rounded-xl flex items-center gap-3 text-sm font-medium border ${studentStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'}`}>
                                {studentStatus.type === 'success' ? <Check className="h-5 w-5 flex-shrink-0" /> : <AlertCircle className="h-5 w-5 flex-shrink-0" />}
                                {studentStatus.message}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'marks' && (
                    <div className="astro-glass rounded-xl border border-emerald-500/20 p-5 md:p-8 bg-emerald-500/5">
                        <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                            <Upload className="h-5 w-5 text-emerald-400" />
                            Upload Subject Marks
                        </h4>
                        <p className="text-sm text-slate-300 mb-4">
                            Upload a CSV/XLSX file containing academic marks. Students must already exist in the database.
                        </p>
                        <div className="bg-black/20 rounded-lg p-3 mb-6 border border-white/5">
                            <p className="text-xs text-slate-400 mb-1">Required columns:</p>
                            <p className="font-mono text-xs text-emerald-200/80 break-all leading-relaxed">
                                roll_no, subject_code, subject_name, semester, internal_marks, external_marks, grade
                            </p>
                        </div>
                        <form onSubmit={uploadMarks} className="space-y-4">
                            <input
                                type="file"
                                accept=".csv,.xlsx"
                                onChange={(e) => setMarksFile(e.target.files?.[0] || null)}
                                disabled={marksLoading}
                                className="block w-full text-sm text-slate-300 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-500/20 file:text-emerald-200 hover:file:bg-emerald-500/30 disabled:opacity-50 cursor-pointer border border-dashed border-white/20 rounded-xl p-4 bg-black/10"
                            />
                            <button
                                type="submit"
                                disabled={!marksFile || marksLoading}
                                className="w-full rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 px-4 py-3 text-sm font-bold text-slate-900 shadow-lg shadow-emerald-500/25 transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                            >
                                {marksLoading ? 'Processing...' : 'Upload Marks'}
                            </button>
                        </form>
                        {marksStatus && (
                            <div className={`mt-4 p-4 rounded-xl flex items-center gap-3 text-sm font-medium border ${marksStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'}`}>
                                {marksStatus.type === 'success' ? <Check className="h-5 w-5 flex-shrink-0" /> : <AlertCircle className="h-5 w-5 flex-shrink-0" />}
                                {marksStatus.message}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
