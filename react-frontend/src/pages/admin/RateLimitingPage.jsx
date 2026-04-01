import { useState, useEffect } from 'react';
import { getRateLimits, updateRateLimit, toggleRateLimit, resetRateLimits } from '../../services/api';
import { Save, RotateCcw, AlertTriangle, Shield, Activity } from 'lucide-react';
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

  if (!limits) return <div className="text-center" style={{ padding: 48 }}><span className="spinner" /></div>;

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
    <div>
      <div className="flex items-center justify-between">
        <h2>⚡ Rate Limiting Configuration</h2>
        <button
          className="btn btn-danger"
          onClick={handleReset}
          disabled={resetting}
          title="Reset all to defaults"
        >
          {resetting ? <><span className="spinner" /> Resetting...</> : <><RotateCcw size={16} /> Reset Defaults</>}
        </button>
      </div>
      <div className="divider" />

      {/* Info Box */}
      <div className="card" style={{ marginBottom: 16, backgroundColor: 'rgba(255, 193, 7, 0.1)', borderLeft: '4px solid #FFC107' }}>
        <div className="flex gap-2">
          <AlertTriangle size={20} style={{ color: '#FFC107', flexShrink: 0 }} />
          <div>
            <p style={{ fontSize: 14, margin: 0 }}>
              <strong>Rate Limiting:</strong> Controls requests per user/IP per time window. Limits apply globally and per endpoint.
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '4px 0 0' }}>
              Disabled limits will not enforce throttling. Changes apply immediately.
            </p>
          </div>
        </div>
      </div>

      {/* Rate Limits Grid */}
      <div style={{ display: 'grid', gap: 12 }}>
        {limits.map(item => (
          <div key={item.id} className="card" style={{
            borderLeft: `4px solid ${getCategoryColor(item.endpoint)}`,
            opacity: item.enabled ? 1 : 0.6
          }}>
            <div className="flex items-start justify-between" style={{ marginBottom: 12 }}>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 20 }}>{getCategoryIcon(item.endpoint)}</span>
                <div>
                  <h3 style={{ margin: '0 0 2px', fontSize: 16 }}>{item.endpoint}</h3>
                  <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>
                    {item.description || 'No description'}
                  </p>
                </div>
              </div>
              <button
                className={`btn btn-sm ${item.enabled ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => handleToggle(item)}
                disabled={saving[item.id]}
                style={{ minWidth: 100 }}
              >
                {saving[item.id] ? <><span className="spinner" /> Toggling...</> : (item.enabled ? '✓ Enabled' : '○ Disabled')}
              </button>
            </div>

            <div className="grid-2" style={{ gap: 12, marginBottom: 12 }}>
              <div>
                <label>Requests per Window</label>
                <input
                  type="number"
                  min="1"
                  value={editing[item.id]?.limit_requests || item.limit_requests}
                  onChange={e => setEditing(prev => ({
                    ...prev,
                    [item.id]: { ...prev[item.id], limit_requests: parseInt(e.target.value) }
                  }))}
                  disabled={!item.enabled || saving[item.id]}
                  style={{ opacity: item.enabled ? 1 : 0.5 }}
                />
              </div>
              <div>
                <label>Window Size (seconds)</label>
                <input
                  type="number"
                  min="1"
                  value={editing[item.id]?.limit_window_seconds || item.limit_window_seconds}
                  onChange={e => setEditing(prev => ({
                    ...prev,
                    [item.id]: { ...prev[item.id], limit_window_seconds: parseInt(e.target.value) }
                  }))}
                  disabled={!item.enabled || saving[item.id]}
                  style={{ opacity: item.enabled ? 1 : 0.5 }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <div style={{ flex: 1, fontSize: 12, color: 'var(--text-muted)' }}>
                <Activity size={12} style={{ marginRight: 4, display: 'inline' }} />
                {item.limit_requests} reqs / {item.limit_window_seconds}s
                {item.updated_by && ` • Updated by ${item.updated_by}`}
              </div>
              <button
                className={`btn btn-sm ${editing[item.id] ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => handleUpdateLimit(item)}
                disabled={!item.enabled || !editing[item.id] || saving[item.id]}
              >
                {saving[item.id] ? <><span className="spinner" /> Saving...</> : <><Save size={14} /> Save</>}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Rate Limit Guidelines */}
      <div className="card" style={{ marginTop: 24, backgroundColor: 'rgba(76, 175, 80, 0.05)' }}>
        <h3 style={{ marginBottom: 12 }}>📊 Rate Limit Guidelines</h3>
        <table style={{
          width: '100%',
          fontSize: 13,
          borderCollapse: 'collapse'
        }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ textAlign: 'left', padding: '8px 0', fontWeight: 600 }}>Endpoint</th>
              <th style={{ textAlign: 'left', padding: '8px 0', fontWeight: 600 }}>Recommended</th>
              <th style={{ textAlign: 'left', padding: '8px 0', fontWeight: 600 }}>Purpose</th>
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
              { endpoint: 'global', recommended: '100/60s', purpose: 'All requests combined fallback' },
            ].map((guide, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '8px 0', fontWeight: 500 }}>{guide.endpoint}</td>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>{guide.recommended}</td>
                <td style={{ padding: '8px 0', color: 'var(--text-muted)' }}>{guide.purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Admin Notes */}
      <div className="card" style={{ marginTop: 16, backgroundColor: 'rgba(33, 150, 243, 0.05)' }}>
        <h3>ℹ️ Admin Notes</h3>
        <ul style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0, paddingLeft: 20 }}>
          <li>Rate limits are applied per user (authenticated) or per IP (anonymous)</li>
          <li>Authenticated users have their X-User-ID prioritized in rate limit key</li>
          <li>Limits reset every window period (e.g., 60s means new count every minute)</li>
          <li>Disabling a limit removes throttling but endpoint is still logged</li>
          <li>Reset defaults is irreversible - backup current settings if needed</li>
          <li>Global limit acts as fallback when endpoint-specific limit is exceeded</li>
        </ul>
      </div>
    </div>
  );
}
