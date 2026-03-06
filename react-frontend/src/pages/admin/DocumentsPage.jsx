import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { listDocuments, uploadDocument, deleteDocument, getKnowledgeBaseStats } from '../../services/api';
import { Upload, Trash2, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

export default function DocumentsPage() {
  const { user } = useAuth();
  const [docs, setDocs] = useState([]);
  const [stats, setStats] = useState({ total_chunks: 0 });
  const [uploading, setUploading] = useState(false);

  const load = () => {
    listDocuments().then(r => setDocs(r.data)).catch(() => {});
    getKnowledgeBaseStats().then(r => setStats(r.data)).catch(() => {});
  };

  useEffect(load, []);

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    setUploading(true);
    let success = 0;
    for (const file of files) {
      try {
        await uploadDocument(file, user.id);
        success++;
      } catch {
        toast.error(`Failed: ${file.name}`);
      }
    }
    if (success) toast.success(`${success} file(s) uploaded & indexed`);
    e.target.value = '';
    setUploading(false);
    load();
  };

  const handleDelete = async (doc) => {
    if (!confirm(`Delete "${doc.original_name}"?`)) return;
    try {
      await deleteDocument(doc.id);
      toast.success('Deleted');
      load();
    } catch {
      toast.error('Delete failed');
    }
  };

  return (
    <div>
      <h2>📄 Document Management</h2>
      <div className="divider" />

      {/* Upload */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 className="flex items-center gap-2"><Upload size={18} /> Upload Documents</h3>
        <p className="text-sm text-muted" style={{ margin: '8px 0' }}>
          Supported: PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML
        </p>
        <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
          {uploading ? <><span className="spinner" /> Processing...</> : 'Choose Files'}
          <input type="file" multiple onChange={handleUpload} style={{ display: 'none' }} disabled={uploading}
            accept=".pdf,.docx,.txt,.xlsx,.csv,.pptx,.html,.htm" />
        </label>
      </div>

      {/* Stats + List */}
      <div className="card">
        <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
          <h3>Knowledge Base</h3>
          <span className="badge badge-ok">{stats.total_chunks} chunks indexed</span>
        </div>
        {docs.length === 0 ? (
          <p className="text-muted text-center" style={{ padding: 32 }}>No documents uploaded yet.</p>
        ) : (
          docs.map(doc => (
            <div key={doc.id} className="table-row">
              <FileText size={18} style={{ color: 'var(--primary)', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500 }}>{doc.original_name}</div>
                <div className="text-sm text-muted">
                  {doc.file_type} · {doc.chunk_count} chunks · {(doc.file_size / 1024).toFixed(1)} KB
                </div>
              </div>
              <span className="text-sm text-muted">{doc.uploaded_at?.slice(0, 16)}</span>
              <button className="btn btn-danger btn-sm" onClick={() => handleDelete(doc)}>
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
