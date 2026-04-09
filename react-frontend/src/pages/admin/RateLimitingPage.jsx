import { useState, useEffect } from 'react';
import { getRateLimits, updateRateLimit, toggleRateLimit, resetRateLimits } from '../../services/api';
import { Save, RotateCcw, AlertTriangle, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RateLimitingPage() {
  const [limits, setLimits] = useState(null);
  const [editing, setEditing] = useState({});
  const [saving, setSaving] = useState({});
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    loadRateLimits();
  }, []);

  const loadRateLimits = async () => {
    try {
      const { data } = await getRateLimits();
      setLimits(data.rate_limits || []);
    } catch {
      toast.error('Failed to load rate limits');
    }
  };

  const handleUpdateLimit = async (item) => {
    if (!editing[item.id]) return;

    const changes = editing[item.id];
    setSaving(prev => ({ ...prev, [item.id]: true }));

    try {
      const response = await updateRateLimit(
        item.endpoint,
        changes.limit_requests || item.limit_requests,
        changes.limit_window_seconds || item.limit_window_seconds,
        item.enabled
      );
      toast.success(`${item.endpoint} rate limit updated!`);

      // Update local state with actual values from server
      const updatedLimit = response.data.rate_limit;
      setLimits(prev => prev.map(l =>
        l.id === item.id ? { ...l, ...updatedLimit } : l
      ));
      setEditing(prev => ({ ...prev, [item.id]: null }));
    } catch (err) {
      toast.error(`Failed to update ${item.endpoint}`);
    } finally {
      setSaving(prev => ({ ...prev, [item.id]: false }));
    }
  };

  const handleToggle = async (item) => {
    setSaving(prev => ({ ...prev, [item.id]: true }));

    try {
      const response = await toggleRateLimit(item.endpoint, !item.enabled);
      toast.success(`${item.endpoint} ${!item.enabled ? 'enabled' : 'disabled'}`);

      // Update local state with actual values from server
      const updatedLimit = response.data.rate_limit;
      setLimits(prev => prev.map(l =>
        l.id === item.id ? { ...l, ...updatedLimit } : l
      ));
    } catch {
      toast.error(`Failed to toggle ${item.endpoint}`);
    } finally {
      setSaving(prev => ({ ...prev, [item.id]: false }));
    }
  };

  const handleReset = async () => {
    if (!window.confirm('⚠️ Reset ALL rate limits to defaults? This cannot be undone!')) return;

    setResetting(true);
    try {
      await resetRateLimits();
      toast.success('Rate limits reset to defaults!');
      await loadRateLimits();
    } catch {
      toast.error('Failed to reset rate limits');
    } finally {
      setResetting(false);
    }
  };

  if (!limits) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading rate limits">
        <section className="astro-glass rounded-2xl border border-white/10 p-5 animate-pulse">
          <div className="h-5 w-36 rounded bg-white/10" />
          <div className="mt-3 h-10 rounded-xl bg-white/5" />
        </section>
        {[1, 2, 3].map((idx) => (
          <section key={idx} className="astro-glass rounded-xl border border-white/10 p-4 animate-pulse">
            <div className="h-4 w-40 rounded bg-white/10" />
            <div className="mt-3 h-10 rounded-xl bg-white/5" />
            <div className="mt-2 h-10 rounded-xl bg-white/5" />
          </section>
        ))}
      </div>
    );
  }

  const getCategoryColor = (endpoint) => {
    if (endpoint.includes('auth')) return '#FF6B6B';
    if (endpoint.includes('chat')) return '#4ECDC4';
    if (endpoint.includes('upload')) return '#45B7D1';
    if (endpoint.includes('tag')) return '#96CEB4';
    if (endpoint.includes('read')) return '#FFEAA7';
    if (endpoint.includes('classify')) return '#DDA0DD';
    return '#95E1D3';
  };

  const getCategoryIcon = (endpoint) => {
    if (endpoint.includes('auth')) return '🔐';
    if (endpoint.includes('chat')) return '💬';
    if (endpoint.includes('upload')) return '📤';
    if (endpoint.includes('tag')) return '🏷️';
    if (endpoint.includes('read')) return '📖';
    if (endpoint.includes('classify')) return '📋';
    return '🌐';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">Rate Limiting</h2>
          <p className="text-sm text-slate-300/85">Fine-tune endpoint throttling and enforce abuse protection.</p>
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-xl border border-rose-300/35 bg-rose-500/15 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/25 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={handleReset}
          disabled={resetting}
          title="Reset all to defaults"
          type="button"
          aria-label="Reset all rate limits"
        >
          {resetting ? <><span className="spinner" /> Resetting...</> : <><RotateCcw size={14} /> Reset Defaults</>}
        </button>
      </div>

      <section className="astro-glass rounded-xl border border-amber-300/35 bg-amber-500/10 p-4 text-amber-100">
        <div className="flex gap-2">
          <AlertTriangle size={18} className="mt-0.5 flex-shrink-0 text-amber-200" />
          <div>
            <p className="text-sm">
              <strong>Rate Limiting</strong> controls requests per user or IP within a window. Changes apply immediately.
            </p>
            <p className="mt-1 text-xs text-amber-100/85">
              Disabled limits do not enforce throttling, but endpoint activity is still tracked.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-3">
        {limits.map(item => (
          <article
            key={item.id}
            className="astro-glass rounded-xl border p-4"
            style={{
              borderColor: `${getCategoryColor(item.endpoint)}66`,
              opacity: item.enabled ? 1 : 0.65
            }}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="flex items-start gap-2">
                <span className="text-lg leading-none">{getCategoryIcon(item.endpoint)}</span>
                <div>
                  <h3 className="text-base font-semibold text-white">{item.endpoint}</h3>
                  <p className="text-xs text-slate-300/80">{item.description || 'No description'}</p>
                </div>
              </div>
              <button
                className={[
                  'rounded-xl px-3 py-1.5 text-xs font-semibold',
                  item.enabled
                    ? 'border border-cyan-300/45 bg-cyan-500/20 text-cyan-100 hover:bg-cyan-500/30'
                    : 'border border-white/15 bg-white/5 text-slate-200 hover:bg-white/10'
                ].join(' ')}
                onClick={() => handleToggle(item)}
                disabled={saving[item.id]}
                type="button"
                aria-label={`${item.enabled ? 'Disable' : 'Enable'} rate limiting for ${item.endpoint}`}
              >
                {saving[item.id] ? 'Toggling...' : (item.enabled ? 'Enabled' : 'Disabled')}
              </button>
            </div>

            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.1em] text-slate-300/70">Requests per window</label>
                <input
                  type="number"
                  min="1"
                  value={editing[item.id]?.limit_requests || item.limit_requests}
                  onChange={e => setEditing(prev => ({
                    ...prev,
                    [item.id]: { ...prev[item.id], limit_requests: parseInt(e.target.value, 10) }
                  }))}
                  disabled={!item.enabled || saving[item.id]}
                  className="w-full rounded-xl border border-white/15 bg-black/20 px-3 py-2 text-sm text-white"
                  style={{ opacity: item.enabled ? 1 : 0.5 }}
                  aria-label={`Requests per window for ${item.endpoint}`}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.1em] text-slate-300/70">Window size (seconds)</label>
                <input
                  type="number"
                  min="1"
                  value={editing[item.id]?.limit_window_seconds || item.limit_window_seconds}
                  onChange={e => setEditing(prev => ({
                    ...prev,
                    [item.id]: { ...prev[item.id], limit_window_seconds: parseInt(e.target.value, 10) }
                  }))}
                  disabled={!item.enabled || saving[item.id]}
                  className="w-full rounded-xl border border-white/15 bg-black/20 px-3 py-2 text-sm text-white"
                  style={{ opacity: item.enabled ? 1 : 0.5 }}
                  aria-label={`Window size in seconds for ${item.endpoint}`}
                />
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-300/80">
              <span className="inline-flex items-center gap-1">
                <Activity size={12} />
                {item.limit_requests} reqs / {item.limit_window_seconds}s
                {item.updated_by && ` - Updated by ${item.updated_by}`}
              </span>
              <button
                className="inline-flex items-center gap-1 rounded-xl border border-cyan-300/45 bg-cyan-500/15 px-3 py-1.5 text-xs font-semibold text-cyan-100 hover:bg-cyan-500/25 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={() => handleUpdateLimit(item)}
                disabled={!item.enabled || !editing[item.id] || saving[item.id]}
                type="button"
                aria-label={`Save rate limit settings for ${item.endpoint}`}
              >
                {saving[item.id] ? 'Saving...' : <><Save size={12} /> Save</>}
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className="astro-glass overflow-hidden rounded-xl border border-white/10">
        <div className="border-b border-white/10 px-4 py-3">
          <h3 className="text-sm font-semibold text-white">Rate Limit Guidelines</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-white/5 text-xs uppercase tracking-[0.12em] text-slate-300/80">
              <tr>
                <th className="px-4 py-3 text-left">Endpoint</th>
                <th className="px-4 py-3 text-left">Recommended</th>
                <th className="px-4 py-3 text-left">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {[
                { endpoint: 'auth', recommended: '5/60s', purpose: 'Brute-force protection for login attempts' },
                { endpoint: 'chat', recommended: '5/60s', purpose: 'Expensive LLM queries, GPU-intensive' },
                { endpoint: 'upload', recommended: '10/60s', purpose: 'Document upload, I/O intensive' },
                { endpoint: 'tags', recommended: '30/60s', purpose: 'Tag CRUD operations, moderate load' },
                { endpoint: 'read', recommended: '60/60s', purpose: 'Read-only operations like listing' },
                { endpoint: 'classify', recommended: '30/60s', purpose: 'Classification operations' },
                { endpoint: 'global', recommended: '100/60s', purpose: 'All requests combined fallback' }
              ].map((guide, idx) => (
                <tr key={idx} className="border-t border-white/10 text-slate-100/90">
                  <td className="px-4 py-3 font-semibold">{guide.endpoint}</td>
                  <td className="px-4 py-3 text-slate-300/90">{guide.recommended}</td>
                  <td className="px-4 py-3 text-slate-300/90">{guide.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="astro-glass rounded-xl border border-white/10 p-4 text-sm text-slate-300/85">
        <h3 className="font-semibold text-white">Admin Notes</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Limits are applied per authenticated user ID or anonymous IP.</li>
          <li>Window-based counters reset every configured period.</li>
          <li>Disabling a limit removes throttling for that endpoint.</li>
          <li>Global limit acts as a fallback safety net.</li>
        </ul>
      </section>
    </div>
  );
}
