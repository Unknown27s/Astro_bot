import { useState, useEffect } from 'react';
import { getMemoryStats, deleteMemoryEntry, runMemoryCleanup, clearAllMemory } from '../../services/api';
import { RefreshCw, Trash2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function MemoryPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('statistics');
  const [clearing, setClearing] = useState(false);
  const [cleaningUp, setCleaningUp] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const { data } = await getMemoryStats();
      setStats(data);
    } catch (error) {
      toast.error('Failed to fetch memory stats');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleCleanup = async () => {
    if (!confirm('Run cleanup on expired entries and low-usage responses?')) return;
    setCleaningUp(true);
    try {
      await runMemoryCleanup();
      toast.success('Cleanup completed');
      fetchStats();
    } catch {
      toast.error('Cleanup failed');
    }
    setCleaningUp(false);
  };

  const handleClearAll = async () => {
    if (!confirm('⚠️ This will DELETE ALL conversation memory. Are you sure?')) return;
    setClearing(true);
    try {
      await clearAllMemory();
      toast.success('All memory cleared');
      fetchStats();
    } catch {
      toast.error('Failed to clear memory');
    }
    setClearing(false);
  };

  const handleDelete = async (memoryId) => {
    if (!confirm('Delete this memory entry?')) return;
    setDeleting(memoryId);
    try {
      await deleteMemoryEntry(memoryId);
      toast.success('Entry deleted');
      fetchStats();
    } catch {
      toast.error('Failed to delete entry');
    }
    setDeleting(null);
  };

  if (!stats || loading) {
    return (
      <div className="text-center" style={{ padding: 48 }}>
        <span className="spinner" />
      </div>
    );
  }

  const { enabled, stats: statsData } = stats;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2>💾 Conversation Memory</h2>
        <button className="btn btn-ghost" onClick={fetchStats} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>
      <div className="divider" />

      {!enabled && (
        <div className="card" style={{ background: 'var(--warning-light)', borderLeft: '4px solid var(--warning)' }}>
          <div className="flex items-start gap-2">
            <AlertCircle size={20} style={{ color: 'var(--warning)', marginTop: 2 }} />
            <div>
              <strong>Memory is currently disabled</strong>
              <p style={{ marginTop: 4, fontSize: 14, color: 'var(--text-secondary)' }}>
                Enable memory in <code>.env</code>: <code>CONV_ENABLED=true</code> and restart FastAPI
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2" style={{ marginBottom: 16, borderBottom: '1px solid var(--border)' }}>
        <button
          onClick={() => setActiveTab('statistics')}
          className={`tab ${activeTab === 'statistics' ? 'active' : ''}`}
        >
          📊 Statistics
        </button>
        <button
          onClick={() => setActiveTab('manage')}
          className={`tab ${activeTab === 'manage' ? 'active' : ''}`}
        >
          🧹 Cleanup
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
        >
          ⚙️ Settings
        </button>
      </div>

      {/* Tab 1: Statistics */}
      {activeTab === 'statistics' && (
        <div>
          <h3>📊 Memory Statistics</h3>
          <div className="grid-4" style={{ marginBottom: 24 }}>
            <div className="card stat-card">
              <div className="text-sm text-muted">Total Entries</div>
              <div style={{ fontSize: 32, fontWeight: 'bold', marginTop: 8 }}>
                {statsData.total_entries}
              </div>
            </div>
            <div className="card stat-card">
              <div className="text-sm text-muted">Avg Usage Per Entry</div>
              <div style={{ fontSize: 32, fontWeight: 'bold', marginTop: 8 }}>
                {statsData.avg_usage_per_entry.toFixed(2)}
              </div>
            </div>
            <div className="card stat-card">
              <div className="text-sm text-muted">Cache Hit Rate</div>
              <div style={{ fontSize: 32, fontWeight: 'bold', marginTop: 8 }}>
                {statsData.total_entries > 0 ? (statsData.avg_usage_per_entry * 100).toFixed(0) : '0'}%
              </div>
            </div>
            <div className="card stat-card">
              <div className="text-sm text-muted">Status</div>
              <div style={{ fontSize: 14, marginTop: 8 }}>
                <span className="badge badge-ok">{enabled ? 'Enabled' : 'Disabled'}</span>
              </div>
            </div>
          </div>

          {/* By-User Breakdown */}
          {statsData.by_user && statsData.by_user.length > 0 && (
            <div>
              <h3>By User</h3>
              <div className="table-responsive" style={{ marginBottom: 24 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border)' }}>
                      <th style={{ padding: 12, textAlign: 'left' }}>User</th>
                      <th style={{ padding: 12, textAlign: 'center' }}>Entries</th>
                      <th style={{ padding: 12, textAlign: 'center' }}>Avg Usage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statsData.by_user.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: 12 }}>{row.username || 'Global'}</td>
                        <td style={{ padding: 12, textAlign: 'center' }}>{row.entries}</td>
                        <td style={{ padding: 12, textAlign: 'center' }}>{row.avg_usage.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {statsData.total_entries === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: 32, background: 'var(--bg-secondary)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>
                No memory entries yet. Start asking questions to populate the cache!
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Cleanup */}
      {activeTab === 'manage' && (
        <div>
          <h3>🧹 Memory Maintenance</h3>
          <div className="card" style={{ marginBottom: 16, padding: 20 }}>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ marginBottom: 8 }}>Manual Cleanup</h4>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Remove entries older than 90 days and responses with low usage (&lt;1 use).
              </p>
              <button
                className="btn btn-primary"
                onClick={handleCleanup}
                disabled={cleaningUp || !enabled}
              >
                {cleaningUp ? '⏳ Running cleanup...' : '🧹 Run Cleanup'}
              </button>
            </div>
          </div>

          <div className="card" style={{ padding: 20, borderLeft: '4px solid var(--error)' }}>
            <div>
              <h4 style={{ marginBottom: 8, color: 'var(--error)' }}>⚠️ Clear All Memory</h4>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Permanently delete ALL conversation memory. This action cannot be undone.
              </p>
              <button
                className="btn"
                style={{ background: 'var(--error)', color: 'white' }}
                onClick={handleClearAll}
                disabled={clearing || !enabled}
              >
                {clearing ? '⏳ Clearing...' : '🗑️ Clear All Memory'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Settings */}
      {activeTab === 'settings' && (
        <div>
          <h3>⚙️ Memory Configuration</h3>
          <div className="card" style={{ marginBottom: 16 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: 12, fontWeight: 'bold', width: '40%' }}>Status</td>
                  <td style={{ padding: 12 }}>
                    <span className={`badge ${enabled ? 'badge-ok' : 'badge-err'}`}>
                      {enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>Match Threshold</td>
                  <td style={{ padding: 12 }}>0.88 (strict semantic matching)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>Storage Type</td>
                  <td style={{ padding: 12 }}>ChromaDB (vector) + SQLite (metadata)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>Scope</td>
                  <td style={{ padding: 12 }}>Global (shared institutional knowledge)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>TTL</td>
                  <td style={{ padding: 12 }}>90 days (automatically expired)</td>
                </tr>
                <tr>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>Persistence</td>
                  <td style={{ padding: 12 }}>Enabled (ChromaDB collection)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="card" style={{ background: 'var(--bg-secondary)' }}>
            <h4 style={{ marginBottom: 8 }}>📝 To modify settings:</h4>
            <ol style={{ marginLeft: 16, color: 'var(--text-secondary)', fontSize: 14 }}>
              <li style={{ marginBottom: 6 }}>Edit <code>.env</code> file in project root</li>
              <li style={{ marginBottom: 6 }}>Update variables: <code>CONV_ENABLED</code>, <code>CONV_MATCH_THRESHOLD</code>, etc.</li>
              <li style={{ marginBottom: 6 }}>Restart FastAPI server</li>
              <li>Settings will take effect immediately</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
