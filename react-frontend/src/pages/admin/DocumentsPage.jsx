import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { listDocuments, uploadDocument, deleteDocument, getKnowledgeBaseStats } from '../../services/api';
import { Upload, Trash2, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

export default function DocumentsPage() {
  const { user } = useAuth();
  const [docs, setDocs] = useState([]);
  const [stats, setStats] = useState({ total_chunks: 0 });
  const [uploading, setUploading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  const load = async () => {
    setLoadingData(true);
    try {
      const [docsRes, statsRes] = await Promise.all([
        listDocuments(),
        getKnowledgeBaseStats(),
      ]);
      setDocs(docsRes.data);
      setStats(statsRes.data);
    } catch {
      toast.error('Failed to load knowledge base data');
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => { load(); }, []);

  const safeDocs = Array.isArray(docs) ? docs : [];
  const totalSizeMb = useMemo(
    () => safeDocs.reduce((sum, doc) => sum + (doc.file_size || 0), 0) / (1024 * 1024),
    [safeDocs]
  );

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return 'N/A';
    return d.toLocaleString();
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    setUploading(true);
    let success = 0;
    for (const file of files) {
      try {
        await uploadDocument(file, user?.id);
        success++;
      } catch (err) {
        // Extract error message with priority
        let errorMsg = 'Upload failed';

        if (err.response?.data?.detail) {
          // Handle both string and array detail formats from Pydantic
          const detail = err.response.data.detail;
          if (typeof detail === 'string') {
            errorMsg = detail;
          } else if (Array.isArray(detail) && detail[0]?.msg) {
            errorMsg = detail[0].msg;
          }
        } else if (err.response?.data?.error) {
          errorMsg = err.response.data.error;
        } else if (err.response?.status === 403) {
          errorMsg = '❌ Only administrators can upload documents';
        } else if (err.response?.status === 404) {
          errorMsg = '❌ User not found';
        } else if (err.response?.status === 413) {
          errorMsg = '❌ File too large (max 50MB)';
        } else if (err.response?.status === 422) {
          errorMsg = '❌ PDF is password-protected or invalid format';
        }

        toast.error(`${file.name}: ${errorMsg}`);
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
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">Document Management</h2>
          <p className="text-sm text-slate-300/85">Upload, index, and maintain the institutional knowledge base.</p>
        </div>
        <span className="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-100">
          {stats.total_chunks || 0} Chunks Indexed
        </span>
      </div>

      <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-semibold text-white"><Upload size={18} /> Upload Documents</h3>
            <p className="mt-1 text-sm text-slate-300/80">Supported formats: PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML.</p>
          </div>
        </div>
        <div className="mt-4">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2.5 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02]" aria-busy={uploading}>
            {uploading ? <><span className="spinner" /> Processing...</> : 'Choose Files'}
            <input
              type="file"
              multiple
              onChange={handleUpload}
              className="hidden"
              disabled={uploading}
              accept=".pdf,.docx,.txt,.xlsx,.csv,.pptx,.html,.htm"
              aria-label="Upload knowledge base documents"
            />
          </label>
        </div>
      </section>

      {loadingData ? (
        <>
          <section className="grid grid-cols-1 gap-3 sm:grid-cols-3" aria-busy="true" aria-label="Loading document statistics">
            {[1, 2, 3].map((idx) => (
              <div key={idx} className="astro-glass rounded-xl border border-white/10 p-4 animate-pulse">
                <div className="h-3 w-24 rounded bg-white/10" />
                <div className="mt-3 h-7 w-20 rounded bg-white/10" />
              </div>
            ))}
          </section>

          <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6" aria-busy="true" aria-label="Loading document table">
            <div className="h-5 w-48 rounded bg-white/10 animate-pulse" />
            <div className="mt-4 space-y-2">
              {[1, 2, 3, 4].map((idx) => (
                <div key={idx} className="h-12 rounded-xl bg-white/5 animate-pulse" />
              ))}
            </div>
          </section>
        </>
      ) : (
        <>
          <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Documents</p>
              <p className="mt-1 text-2xl font-bold text-white">{safeDocs.length}</p>
            </div>
            <div className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Indexed Chunks</p>
              <p className="mt-1 text-2xl font-bold text-white">{stats.total_chunks || 0}</p>
            </div>
            <div className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Storage Size</p>
              <p className="mt-1 text-2xl font-bold text-white">{totalSizeMb.toFixed(2)} MB</p>
            </div>
          </section>

          <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
            <h3 className="text-lg font-semibold text-white">Knowledge Base Files</h3>

            {safeDocs.length === 0 ? (
              <p className="py-10 text-center text-sm text-slate-300/80">No documents uploaded yet.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm text-slate-100">
                  <thead>
                    <tr className="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                      <th className="px-3 py-3">File</th>
                      <th className="px-3 py-3">Type</th>
                      <th className="px-3 py-3">Chunks</th>
                      <th className="px-3 py-3">Size</th>
                      <th className="px-3 py-3">Uploaded</th>
                      <th className="px-3 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {safeDocs.map((doc) => (
                      <tr key={doc.id} className="border-b border-white/10 last:border-b-0">
                        <td className="px-3 py-3">
                          <div className="flex items-center gap-2">
                            <FileText size={16} className="text-cyan-200" />
                            <span className="font-medium text-white">{doc.original_name}</span>
                          </div>
                        </td>
                        <td className="px-3 py-3 text-slate-200/90">{doc.file_type || '-'}</td>
                        <td className="px-3 py-3 text-slate-200/90">{doc.chunk_count || 0}</td>
                        <td className="px-3 py-3 text-slate-200/90">{((doc.file_size || 0) / 1024).toFixed(1)} KB</td>
                        <td className="px-3 py-3 text-slate-200/90">{formatDate(doc.uploaded_at)}</td>
                        <td className="px-3 py-3 text-right">
                          <button
                            className="inline-flex items-center gap-1 rounded-lg border border-rose-300/25 bg-rose-400/10 px-3 py-1.5 text-xs font-semibold text-rose-100 transition-colors hover:bg-rose-400/20"
                            onClick={() => handleDelete(doc)}
                            type="button"
                            aria-label={`Delete document ${doc.original_name}`}
                          >
                            <Trash2 size={13} /> Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
