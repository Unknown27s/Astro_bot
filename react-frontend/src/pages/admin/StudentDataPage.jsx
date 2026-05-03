
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import StudentMarksUpload from '../../components/admin/StudentMarksUpload';
import { BookOpen, Database, Users, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';

export default function StudentDataPage() {
    const { user } = useAuth();
    const [uploadComplete, setUploadComplete] = useState(false);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [studentCount, setStudentCount] = useState(0);

    // Fetch uploaded students
    const fetchStudents = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/documents');
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
    {/* Stats Cards */ }
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-4">
                <div className="bg-blue-50 p-3 rounded-lg">
                    <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                    <p className="text-sm text-slate-600">Total Students</p>
                    <p className="text-2xl font-bold text-slate-900">{studentCount || '0'}</p>
                </div>
            </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-4">
                <div className="bg-green-50 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
                <div>
                    <p className="text-sm text-slate-600">Status</p>
                    <p className="text-2xl font-bold text-green-600">Ready</p>
                </div>
            </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-4">
                <div className="bg-purple-50 p-3 rounded-lg">
                    <Database className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                    <p className="text-sm text-slate-600">System</p>
                    <p className="text-sm font-bold text-purple-600">Connected</p>
                </div>
            </div>
        </div>
    </div>
    {/* Students List Section */ }
    <div className="bg-white rounded-lg border border-slate-200 p-8 mb-8">
        <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-900">👥 Uploaded Students</h2>
            <button
                onClick={fetchStudents}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
                <RefreshCw className="h-4 w-4" />
                Refresh
            </button>
        </div>

        {loading ? (
            <div className="text-center py-8">
                <div className="inline-block">
                    <div className="h-8 w-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
                <p className="text-slate-600 mt-3">Loading students...</p>
            </div>
        ) : studentCount > 0 ? (
            <div>
                <p className="text-sm text-slate-600 mb-4">Showing student records uploaded to the system</p>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th className="px-4 py-3 text-left font-semibold text-slate-700">Roll No</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-700">Name</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-700">Email</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-700">Department</th>
                                <th className="px-4 py-3 text-left font-semibold text-slate-700">GPA</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                            {students.map((student, idx) => (
                                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                                    <td className="px-4 py-3 text-slate-900 font-medium">
                                        {student.roll_no || student.id?.slice(0, 6) || `STU-${idx + 1}`}
                                    </td>
                                    <td className="px-4 py-3 text-slate-600">
                                        {student.name || student.filename || 'N/A'}
                                    </td>
                                    <td className="px-4 py-3 text-slate-600">
                                        {student.email || '-'}
                                    </td>
                                    <td className="px-4 py-3 text-slate-600">
                                        {student.department || '-'}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                                            {student.gpa || student.chunk_count || '-'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {studentCount > 10 && (
                    <p className="text-xs text-slate-500 mt-4">
                        Showing 10 of {studentCount} total students
                    </p>
                )}
            </div>
        ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
                <Users className="h-12 w-12 text-blue-400 mx-auto mb-3 opacity-50" />
                <p className="text-slate-600">No students uploaded yet</p>
                <p className="text-sm text-slate-500 mt-2">Upload a student CSV file above to get started</p>
            </div>
        )}
    </div>
    return (
        <div className="max-w-6xl mx-auto">
            {/* Page Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <BookOpen className="h-8 w-8 text-purple-600" />
                    <h1 className="text-3xl font-bold text-slate-900">Student Data Management</h1>
                </div>
                <p className="text-slate-600">Upload and manage student information and academic marks</p>
            </div>

            {/* Success Notification */}
            {uploadComplete && (
                <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-3">
                    <div className="h-2 w-2 bg-emerald-600 rounded-full"></div>
                    <p className="text-emerald-700 font-medium">Data uploaded successfully!</p>
                </div>
            )}

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Students Card */}
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="h-5 w-5 text-blue-600" />
                        <h3 className="font-semibold text-slate-900">Student Records</h3>
                    </div>
                    <p className="text-sm text-slate-600 mb-4">
                        Upload CSV or XLSX files containing student information including roll number, name, contact details, department, and GPA.
                    </p>
                    <div className="text-xs text-slate-500 space-y-1">
                        <p><strong>Required columns:</strong></p>
                        <p className="font-mono">roll_no, name, email, phone, department, semester, gpa</p>
                    </div>
                </div>

                {/* Marks Card */}
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="h-5 w-5 text-green-600" />
                        <h3 className="font-semibold text-slate-900">Student Marks</h3>
                    </div>
                    <p className="text-sm text-slate-600 mb-4">
                        Upload CSV or XLSX files containing academic marks including subject codes, internal and external marks, and grades.
                    </p>
                    <div className="text-xs text-slate-500 space-y-1">
                        <p><strong>Required columns:</strong></p>
                        <p className="font-mono">roll_no, subject_code, subject_name, semester, internal_marks, external_marks, grade</p>
                    </div>
                </div>
            </div>

            {/* Upload Component */}
            <div className="bg-white rounded-lg border border-slate-200 p-8">
                <h2 className="text-xl font-semibold text-slate-900 mb-6">Upload Data</h2>
                <StudentMarksUpload
                    userId={user?.id}
                    onUploadComplete={handleUploadComplete}
                />
            </div>

            {/* Instructions */}
            <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
                <h3 className="font-semibold text-blue-900 mb-3">📋 Instructions</h3>
                <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
                    <li>Prepare your CSV or XLSX file with the required columns</li>
                    <li>Click <strong>"Choose File"</strong> to select your student data file</li>
                    <li>Click <strong>"Upload Students"</strong> to import the student records</li>
                    <li>Upload the marks data file in the same way</li>
                    <li>Students will be linked to marks records by roll_no automatically</li>
                    <li>Use the chat interface to query marks (e.g., "Show my marks")</li>
                </ol>
            </div>

            {/* Sample Data Section */}
            <div className="mt-8 bg-slate-50 rounded-lg border border-slate-200 p-6">
                <h3 className="font-semibold text-slate-900 mb-3">📚 Sample Data</h3>
                <p className="text-sm text-slate-600 mb-4">
                    Download sample CSV files to understand the required format:
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                    <a
                        href="/sample_data/students.csv"
                        download="students.csv"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                        📥 Download students.csv
                    </a>
                    <a
                        href="/sample_data/marks.csv"
                        download="marks.csv"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                    >
                        📥 Download marks.csv
                    </a>
                </div>
            </div>
        </div>
    );
}
