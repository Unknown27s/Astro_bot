import { useState, useEffect } from 'react';
import { getHealth } from '../../services/api';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';

const statusIcon = (status) => {
  if (status === 'ok' || status === 'healthy') return <CheckCircle size={16} style={{ color: 'var(--success)' }} />;
  if (status === 'warning' || status === 'degraded') return <AlertTriangle size={16} style={{ color: 'var(--warning)' }} />;
  return <XCircle size={16} style={{ color: 'var(--error)' }} />;
};

const statusBadge = (status) => {
  const cls = (status === 'ok' || status === 'healthy') ? 'badge-ok'
    : (status === 'warning' || status === 'degraded') ? 'badge-warn' : 'badge-err';
  return <span className={`badge ${cls}`}>{status}</span>;
};

export default function HealthPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try {
      const { data } = await getHealth();
      setHealth(data);
    } catch {
      toast.error('Failed to fetch health');
    }
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  if (!health && loading) return <div className="text-center" style={{ padding: 48 }}><span className="spinner" /></div>;

  const components = health?.components || {};
  const providers = health?.providers || {};

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2>💚 System Health</h2>
        <button className="btn btn-ghost" onClick={refresh} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>
      <div className="divider" />

      {/* Overall Status */}
      {health && (
        <div className="card" style={{ marginBottom: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 48 }}>{health.status === 'healthy' ? '✅' : health.status === 'degraded' ? '⚠️' : '❌'}</div>
          <h2>{health.status === 'healthy' ? 'All Systems Operational' : health.status === 'degraded' ? 'Degraded Performance' : 'System Issues Detected'}</h2>
          {statusBadge(health.status)}
        </div>
      )}

      {/* Components */}
      <h3 style={{ marginBottom: 8 }}>🧩 Core Components</h3>
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {Object.entries(components).map(([name, comp]) => (
          <div className="card" key={name}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {statusIcon(comp.status || comp)}
                <strong style={{ textTransform: 'capitalize' }}>{name.replace(/_/g, ' ')}</strong>
              </div>
              {statusBadge(typeof comp === 'string' ? comp : comp.status)}
            </div>
            {comp.message && <p className="text-sm text-muted" style={{ marginTop: 6 }}>{comp.message}</p>}
            {comp.details && typeof comp.details === 'object' && (
              <div className="text-sm text-muted" style={{ marginTop: 6 }}>
                {Object.entries(comp.details).map(([k, v]) => (
                  <div key={k}><code>{k}</code>: {String(v)}</div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* LLM Providers */}
      {Object.keys(providers).length > 0 && (
        <>
          <h3 style={{ marginBottom: 8 }}>🤖 LLM Providers</h3>
          <div className="grid-2" style={{ marginBottom: 16 }}>
            {Object.entries(providers).map(([name, prov]) => (
              <div className="card" key={name}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {statusIcon(prov.status)}
                    <strong style={{ textTransform: 'capitalize' }}>{name}</strong>
                  </div>
                  {statusBadge(prov.status)}
                </div>
                {prov.model && <p className="text-sm text-muted" style={{ marginTop: 6 }}>Model: {prov.model}</p>}
                {prov.message && <p className="text-sm text-muted" style={{ marginTop: 4 }}>{prov.message}</p>}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Raw JSON Toggle */}
      <details style={{ marginTop: 16 }}>
        <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>🔍 Raw Health Data</summary>
        <pre style={{ marginTop: 8, padding: 12, background: 'var(--bg-secondary)', borderRadius: 8, overflow: 'auto', fontSize: 12 }}>
          {JSON.stringify(health, null, 2)}
        </pre>
      </details>
    </div>
  );
}
