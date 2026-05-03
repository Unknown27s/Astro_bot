import { useState } from 'react';
import { Upload, Check, AlertCircle } from 'lucide-react';

export default function StudentMarksUpload({ userId, onUploadComplete }) {
    const [studentFile, setStudentFile] = useState(null);
    const [marksFile, setMarksFile] = useState(null);
    const [studentLoading, setStudentLoading] = useState(false);
    const [marksLoading, setMarksLoading] = useState(false);
    const [studentStatus, setStudentStatus] = useState(null);
    const [marksStatus, setMarksStatus] = useState(null);

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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Student Upload */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Student Data
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                    CSV or XLSX with columns: roll_no, name, email, phone, department, semester, gpa
                </p>
                <form onSubmit={uploadStudents}>
                    <input
                        type="file"
                        accept=".csv,.xlsx"
                        onChange={(e) => setStudentFile(e.target.files?.[0] || null)}
                        disabled={studentLoading}
                        className="block w-full text-sm text-gray-500 mb-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <button
                        type="submit"
                        disabled={!studentFile || studentLoading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {studentLoading ? 'Uploading...' : 'Upload Students'}
                    </button>
                </form>
                {studentStatus && (
                    <div className={`mt-4 p-3 rounded flex items-center gap-2 ${studentStatus.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                        {studentStatus.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                        {studentStatus.message}
                    </div>
                )}
            </div>

            {/* Marks Upload */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Marks Data
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                    CSV or XLSX with columns: roll_no, subject_code, subject_name, semester, internal_marks, external_marks, grade
                </p>
                <form onSubmit={uploadMarks}>
                    <input
                        type="file"
                        accept=".csv,.xlsx"
                        onChange={(e) => setMarksFile(e.target.files?.[0] || null)}
                        disabled={marksLoading}
                        className="block w-full text-sm text-gray-500 mb-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <button
                        type="submit"
                        disabled={!marksFile || marksLoading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {marksLoading ? 'Uploading...' : 'Upload Marks'}
                    </button>
                </form>
                {marksStatus && (
                    <div className={`mt-4 p-3 rounded flex items-center gap-2 ${marksStatus.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                        {marksStatus.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                        {marksStatus.message}
                    </div>
                )}
            </div>
        </div>
    );
}
