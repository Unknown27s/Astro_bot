import { useState, useEffect } from 'react';
import { getHealth, getProviderStatuses } from '../../services/api';
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
  const [providers, setProviders] = useState({});
  const [loadingProviders, setLoadingProviders] = useState(false);

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

  const refreshProviders = async () => {
    setLoadingProviders(true);
    try {
      const { data } = await getProviderStatuses();
      const { _mode, ...rest } = data || {};
      setProviders(rest);
    } catch {
      toast.error('Failed to fetch provider statuses');
    }
    setLoadingProviders(false);
  };

  useEffect(() => { refresh(); }, []);

  if (!health && loading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading health diagnostics">
        <section className="astro-glass rounded-2xl border border-white/10 p-5 animate-pulse">
          <div className="h-5 w-40 rounded bg-white/10" />
          <div className="mt-3 h-16 rounded-xl bg-white/5" />
        </section>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="astro-glass rounded-xl border border-white/10 p-4 animate-pulse">
              <div className="h-4 w-24 rounded bg-white/10" />
              <div className="mt-2 h-3 w-44 rounded bg-white/10" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const components = health?.components || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">System Health</h2>
          <p className="text-sm text-slate-300/85">Core platform diagnostics and provider availability.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-white/10"
            onClick={refresh}
            disabled={loading}
            type="button"
            aria-label="Refresh core health status"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Core
          </button>
          <button
            className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-white/10"
            onClick={refreshProviders}
            disabled={loadingProviders}
            type="button"
            aria-label="Check LLM provider status"
          >
            <RefreshCw size={14} className={loadingProviders ? 'spin' : ''} /> Check Providers
          </button>
        </div>
      </div>

      {health && (
        <section className="astro-glass rounded-2xl border border-white/10 p-5 text-center md:p-6">
          <div className="text-4xl">{health.status === 'healthy' ? '✅' : health.status === 'degraded' ? '⚠️' : '❌'}</div>
          <h3 className="mt-2 text-xl font-bold text-white">
            {health.status === 'healthy' ? 'All Systems Operational' : health.status === 'degraded' ? 'Degraded Performance' : 'System Issues Detected'}
          </h3>
          <div className="mt-2">{statusBadge(health.status)}</div>
        </section>
      )}

      <section>
        <h3 className="mb-3 text-lg font-semibold text-white">Core Components</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {Object.entries(components).map(([name, comp]) => (
            <div className="astro-glass rounded-xl border border-white/10 p-4" key={name}>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  {statusIcon(comp.status || comp)}
                  <span className="capitalize">{name.replace(/_/g, ' ')}</span>
                </div>
                {statusBadge(typeof comp === 'string' ? comp : comp.status)}
              </div>
              {comp.message && <p className="mt-2 text-sm text-slate-300/85">{comp.message}</p>}
              {comp.details && typeof comp.details === 'object' && (
                <div className="mt-2 space-y-1 text-xs text-slate-300/80">
                  {Object.entries(comp.details).map(([k, v]) => (
                    <div key={k}><code>{k}</code>: {String(v)}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-lg font-semibold text-white">LLM Providers</h3>
        {Object.keys(providers).length > 0 ? (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {Object.entries(providers).map(([name, prov]) => (
              <div className="astro-glass rounded-xl border border-white/10 p-4" key={name}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    {statusIcon(prov.status)}
                    <span className="capitalize">{name}</span>
                  </div>
                  {statusBadge(prov.status)}
                </div>
                {prov.model && <p className="mt-2 text-sm text-slate-300/85">Model: {prov.model}</p>}
                {prov.message && <p className="mt-1 text-sm text-slate-300/85">{prov.message}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-300/80">Providers not checked yet. Click "Check Providers" to run diagnostics.</p>
        )}
      </section>

      <details className="astro-glass rounded-xl border border-white/10 p-4">
        <summary className="cursor-pointer text-sm font-semibold text-cyan-100" aria-label="Expand raw health JSON">Raw Health Data</summary>
        <pre className="astro-scrollbar mt-3 overflow-auto rounded-lg border border-white/10 bg-black/20 p-3 text-xs text-slate-200/90">
          {JSON.stringify(health, null, 2)}
        </pre>
      </details>
    </div>
  );
}
