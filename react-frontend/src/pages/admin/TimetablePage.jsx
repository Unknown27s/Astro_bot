import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import TimetableUpload from '../../components/admin/TimetableUpload';
import { Calendar } from 'lucide-react';

export default function TimetablePage() {
    const { user } = useAuth();
    const [uploaded, setUploaded] = useState(false);

    const onUploadComplete = () => {
        setUploaded(true);
        setTimeout(() => setUploaded(false), 3000);
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                    <Calendar className="h-8 w-8 text-indigo-600" />
                    <h1 className="text-3xl font-bold text-slate-900">Timetable Management</h1>
                </div>
                <p className="text-slate-600">Upload and manage class timetables (CSV/XLSX)</p>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-8 mb-8">
                <h2 className="text-xl font-semibold text-slate-900 mb-6">Upload Timetable</h2>
                <TimetableUpload userId={user?.id} onUploadComplete={onUploadComplete} />
            </div>

            {uploaded && (
                <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <p className="text-emerald-700 font-medium">Timetable uploaded successfully!</p>
                </div>
            )}
        </div>
    );
}
