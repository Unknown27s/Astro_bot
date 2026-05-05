
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import StudentMarksUpload from '../../components/admin/StudentMarksUpload';
import { BookOpen, Database, Users, TrendingUp, RefreshCw } from 'lucide-react';

export default function StudentDataPage() {
    const { user } = useAuth();
    const [uploadComplete, setUploadComplete] = useState(false);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [studentCount, setStudentCount] = useState(0);

    const fetchStudents = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/admin/students', {
                headers: { 'X-User-ID': user?.id || '' },
            });
            if (response.ok) {
                const data = await response.json();
                if (Array.isArray(data)) {
                    setStudents(data.slice(0, 10));
                    setStudentCount(data.length);
                }
            }
        } catch (err) {
            console.log('Note: Could not fetch students list');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStudents();
    }, [uploadComplete]);

    const handleUploadComplete = () => {
        setUploadComplete(true);
        setTimeout(() => setUploadComplete(false), 3000);
        setTimeout(() => fetchStudents(), 500);
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white flex items-center gap-3">
                    <BookOpen className="h-7 w-7 text-cyan-400" />
                    Student Data Management
                </h2>
                <p className="text-sm text-slate-300/85 mt-2">Upload and manage student information and academic marks.</p>
            </div>

            {/* Success Notification */}
            {uploadComplete && (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3">
                    <div className="h-2 w-2 bg-emerald-400 rounded-full"></div>
                    <p className="text-emerald-300 font-medium text-sm">Data uploaded successfully!</p>
                </div>
            )}

            {/* Stats Cards */}
            <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-blue-500/10 p-3 rounded-lg border border-blue-500/20">
                            <Users className="h-6 w-6 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Total Students</p>
                            <p className="mt-1 text-2xl font-bold text-white">{studentCount || '0'}</p>
                        </div>
                    </div>
                </div>

                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20">
                            <TrendingUp className="h-6 w-6 text-emerald-400" />
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
                            <Database className="h-6 w-6 text-cyan-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">System</p>
                            <p className="mt-1 text-sm font-bold text-cyan-400">Connected</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="astro-glass rounded-xl border border-indigo-500/20 p-5 bg-indigo-500/5">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="h-5 w-5 text-indigo-400" />
                        <h3 className="font-semibold text-white">Unified Upload (Recommended)</h3>
                    </div>
                    <p className="text-sm text-slate-300/80 mb-4">
                        Upload a single CSV/XLSX file containing both student details and marks. The system automatically links them.
                    </p>
                    <div className="text-xs text-slate-400 space-y-1">
                        <p><strong>Required columns:</strong></p>
                        <p className="font-mono text-indigo-200/80">roll_no, name, email, phone, department, semester, subject_code, subject_name, subject_semester, internal_marks, external_marks, grade</p>
                    </div>
                    <a
                        href="/sample_data/unified_student_data.csv"
                        download="unified_student_data.csv"
                        className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-300 hover:text-indigo-200 transition-colors"
                    >
                        📥 Download Sample CSV
                    </a>
                </div>

                <div className="astro-glass rounded-xl border border-white/10 p-5">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="h-5 w-5 text-cyan-400" />
                        <h3 className="font-semibold text-white">Student Records Only</h3>
                    </div>
                    <p className="text-sm text-slate-300/80 mb-4">
                        Upload CSV/XLSX files containing student info (roll number, name, contact details, department, GPA).
                    </p>
                    <div className="text-xs text-slate-400 space-y-1">
                        <p><strong>Required columns:</strong></p>
                        <p className="font-mono text-cyan-200/80">roll_no, name, email, phone, department, semester, gpa</p>
                    </div>
                </div>

                <div className="astro-glass rounded-xl border border-white/10 p-5">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="h-5 w-5 text-emerald-400" />
                        <h3 className="font-semibold text-white">Student Marks Only</h3>
                    </div>
                    <p className="text-sm text-slate-300/80 mb-4">
                        Upload CSV/XLSX files containing academic marks (subject codes, internal/external marks, grades).
                    </p>
                    <div className="text-xs text-slate-400 space-y-1">
                        <p><strong>Required columns:</strong></p>
                        <p className="font-mono text-emerald-200/80">roll_no, subject_code, subject_name, semester, internal_marks, external_marks, grade</p>
                    </div>
                </div>
            </div>

            {/* Upload Component */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <StudentMarksUpload userId={user?.id} onUploadComplete={handleUploadComplete} />
            </section>

            {/* Students List Section */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <h3 className="flex items-center gap-2 text-lg font-semibold text-white">👥 Uploaded Students</h3>
                    <button
                        onClick={fetchStudents}
                        disabled={loading}
                        className="inline-flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-3 py-1.5 text-sm font-semibold text-slate-200 hover:bg-white/10 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Refresh
                    </button>
                </div>

                {loading ? (
                    <div className="text-center py-8">
                        <div className="inline-block">
                            <div className="h-8 w-8 border-4 border-cyan-500/20 border-t-cyan-400 rounded-full animate-spin"></div>
                        </div>
                        <p className="text-slate-300/80 mt-3">Loading students...</p>
                    </div>
                ) : studentCount > 0 ? (
                    <div>
                        <p className="text-sm text-slate-300/80 mb-4">Showing student records uploaded to the system</p>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-left text-sm text-slate-100">
                                <thead>
                                    <tr className="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                                        <th className="px-4 py-3 font-semibold">Roll No</th>
                                        <th className="px-4 py-3 font-semibold">Name</th>
                                        <th className="px-4 py-3 font-semibold">Email</th>
                                        <th className="px-4 py-3 font-semibold">Department</th>
                                        <th className="px-4 py-3 font-semibold">GPA</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {students.map((student, idx) => (
                                        <tr key={idx} className="border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-colors">
                                            <td className="px-4 py-3 font-medium text-white">
                                                {student.roll_no || '-'}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {student.name || 'N/A'}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {student.email || '-'}
                                            </td>
                                            <td className="px-4 py-3 text-slate-200/90">
                                                {student.department || '-'}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-100">
                                                    {student.gpa || '-'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {studentCount > 10 && (
                            <p className="text-xs text-slate-400 mt-4">
                                Showing 10 of {studentCount} total students
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="bg-white/5 border border-white/10 rounded-lg p-6 text-center">
                        <Users className="h-12 w-12 text-slate-500 mx-auto mb-3 opacity-50" />
                        <p className="text-slate-300">No students uploaded yet</p>
                        <p className="text-sm text-slate-400 mt-2">Upload a student CSV file above to get started</p>
                    </div>
                )}
            </section>

            {/* Instructions */}
            <section className="astro-glass bg-blue-500/5 rounded-2xl border border-blue-500/20 p-5 md:p-6">
                <h3 className="font-semibold text-blue-300 mb-3 text-lg">📋 Instructions</h3>
                <ol className="text-sm text-slate-300/80 space-y-2 list-decimal list-inside">
                    <li>Prepare your CSV or XLSX file with the required columns</li>
                    <li>Click <strong>"Choose File"</strong> to select your student data file</li>
                    <li>Click <strong>"Upload Students"</strong> to import the student records</li>
                    <li>Upload the marks data file in the same way</li>
                    <li>Students will be linked to marks records by roll_no automatically</li>
                    <li>Use the chat interface to query marks (e.g., "Show my marks")</li>
                </ol>
            </section>

            {/* Sample Data Section */}
            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <h3 className="text-lg font-semibold text-white mb-3">📚 Sample Data</h3>
                <p className="text-sm text-slate-300/80 mb-4">
                    Download sample CSV files to understand the required format:
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                    <a
                        href="/sample_data/students.csv"
                        download="students.csv"
                        className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02]"
                    >
                        📥 Download students.csv
                    </a>
                    <a
                        href="/sample_data/marks.csv"
                        download="marks.csv"
                        className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-300 to-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition-transform hover:scale-[1.02]"
                    >
                        📥 Download marks.csv
                    </a>
                </div>
            </section>
        </div>
    );
}
