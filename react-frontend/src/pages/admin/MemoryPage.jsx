import { useState, useEffect } from 'react';
import { getMemoryStats, deleteMemoryEntry, runMemoryCleanup, clearAllMemory } from '../../services/api';
import { RefreshCw, AlertCircle } from 'lucide-react';
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
      <div className="space-y-4" aria-busy="true" aria-label="Loading memory dashboard">
        <section className="astro-glass rounded-2xl border border-white/10 p-5 animate-pulse">
          <div className="h-5 w-48 rounded bg-white/10" />
          <div className="mt-3 h-10 rounded-xl bg-white/5" />
        </section>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="astro-glass rounded-xl border border-white/10 p-4 animate-pulse">
              <div className="h-3 w-24 rounded bg-white/10" />
              <div className="mt-2 h-7 w-20 rounded bg-white/10" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const { enabled, stats: statsData } = stats;

  const tabs = [
    { id: 'statistics', label: 'Statistics' },
    { id: 'manage', label: 'Cleanup' },
    { id: 'settings', label: 'Settings' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">Conversation Memory</h2>
          <p className="text-sm text-slate-300/85">Inspect semantic cache usage and run maintenance actions.</p>
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-white/10"
          onClick={fetchStats}
          disabled={loading}
          type="button"
          aria-label="Refresh memory statistics"
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {!enabled && (
        <section className="astro-glass rounded-xl border border-amber-300/35 bg-amber-400/10 p-4 text-amber-100">
          <div className="flex items-start gap-2">
            <AlertCircle size={18} className="mt-0.5 text-amber-200" />
            <div>
              <p className="font-semibold">Memory is currently disabled</p>
              <p className="mt-1 text-sm text-amber-100/90">
                Enable in <code>.env</code> with <code>CONV_ENABLED=true</code> and restart the FastAPI service.
              </p>
            </div>
          </div>
        </section>
      )}

      <div className="flex flex-wrap gap-2 border-b border-white/10 pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            aria-label={`Switch to ${tab.label} tab`}
            className={[
              'rounded-xl px-3 py-2 text-sm font-semibold transition',
              activeTab === tab.id
                ? 'border border-cyan-300/40 bg-cyan-300/15 text-cyan-100'
                : 'border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'statistics' && (
        <section className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <article className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300/80">Total Entries</p>
              <p className="mt-2 text-3xl font-bold text-white">{statsData.total_entries}</p>
            </article>
            <article className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300/80">Avg Usage</p>
              <p className="mt-2 text-3xl font-bold text-white">{statsData.avg_usage_per_entry.toFixed(2)}</p>
            </article>
            <article className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300/80">Cache Hit Rate</p>
              <p className="mt-2 text-3xl font-bold text-white">
                {statsData.total_entries > 0 ? (statsData.avg_usage_per_entry * 100).toFixed(0) : '0'}%
              </p>
            </article>
            <article className="astro-glass rounded-xl border border-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300/80">Status</p>
              <p className="mt-2 text-sm font-semibold text-white">{enabled ? 'Enabled' : 'Disabled'}</p>
            </article>
          </div>

          {statsData.by_user && statsData.by_user.length > 0 && (
            <div className="astro-glass overflow-hidden rounded-xl border border-white/10">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-white/5 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                    <tr>
                      <th className="px-4 py-3 text-left">User</th>
                      <th className="px-4 py-3 text-center">Entries</th>
                      <th className="px-4 py-3 text-center">Avg Usage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statsData.by_user.map((row, idx) => (
                      <tr key={idx} className="border-t border-white/10 text-slate-100/90">
                        <td className="px-4 py-3">{row.username || 'Global'}</td>
                        <td className="px-4 py-3 text-center">{row.entries}</td>
                        <td className="px-4 py-3 text-center">{row.avg_usage.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {statsData.total_entries === 0 && (
            <div className="astro-glass rounded-xl border border-white/10 p-6 text-center text-sm text-slate-300/80">
              No memory entries yet. Start asking questions to populate the cache.
            </div>
          )}
        </section>
      )}

      {activeTab === 'manage' && (
        <section className="space-y-4">
          <article className="astro-glass rounded-xl border border-white/10 p-5">
            <h3 className="text-base font-semibold text-white">Manual Cleanup</h3>
            <p className="mt-2 text-sm text-slate-300/85">
              Removes entries older than 90 days and low-use responses.
            </p>
            <div className="mt-4">
              <button
                className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handleCleanup}
                disabled={cleaningUp || !enabled}
                type="button"
                aria-label="Run memory cleanup"
              >
                {cleaningUp ? 'Running Cleanup...' : 'Run Cleanup'}
              </button>
            </div>
          </article>

          <article className="astro-glass rounded-xl border border-rose-300/35 bg-rose-500/10 p-5">
            <h3 className="text-base font-semibold text-rose-100">Danger Zone: Clear All Memory</h3>
            <p className="mt-2 text-sm text-rose-100/85">
              Permanently deletes all conversation memory and cannot be undone.
            </p>
            <div className="mt-4">
              <button
                className="rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-400 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handleClearAll}
                disabled={clearing || !enabled}
                type="button"
                aria-label="Clear all conversation memory"
              >
                {clearing ? 'Clearing...' : 'Clear All Memory'}
              </button>
            </div>
          </article>
        </section>
      )}

      {activeTab === 'settings' && (
        <section className="space-y-4">
          <div className="astro-glass overflow-hidden rounded-xl border border-white/10">
            <table className="min-w-full text-sm">
              <tbody>
                <tr className="border-b border-white/10">
                  <td className="px-4 py-3 font-semibold text-slate-200">Status</td>
                  <td className="px-4 py-3 text-slate-100">{enabled ? 'Enabled' : 'Disabled'}</td>
                </tr>
                <tr className="border-b border-white/10">
                  <td className="px-4 py-3 font-semibold text-slate-200">Match Threshold</td>
                  <td className="px-4 py-3 text-slate-100">0.88 (strict semantic matching)</td>
                </tr>
                <tr className="border-b border-white/10">
                  <td className="px-4 py-3 font-semibold text-slate-200">Storage Type</td>
                  <td className="px-4 py-3 text-slate-100">ChromaDB (vector) + SQLite (metadata)</td>
                </tr>
                <tr className="border-b border-white/10">
                  <td className="px-4 py-3 font-semibold text-slate-200">Scope</td>
                  <td className="px-4 py-3 text-slate-100">Global (shared institutional knowledge)</td>
                </tr>
                <tr className="border-b border-white/10">
                  <td className="px-4 py-3 font-semibold text-slate-200">TTL</td>
                  <td className="px-4 py-3 text-slate-100">90 days (automatically expired)</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-semibold text-slate-200">Persistence</td>
                  <td className="px-4 py-3 text-slate-100">Enabled (ChromaDB collection)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <article className="astro-glass rounded-xl border border-white/10 p-5 text-sm text-slate-300/90">
            <h3 className="text-base font-semibold text-white">How to modify memory settings</h3>
            <ol className="mt-3 list-decimal space-y-2 pl-5">
              <li>Edit the <code>.env</code> file in project root.</li>
              <li>Update values like <code>CONV_ENABLED</code> and <code>CONV_MATCH_THRESHOLD</code>.</li>
              <li>Restart FastAPI server.</li>
              <li>Refresh this page to verify values.</li>
            </ol>
          </article>
        </section>
      )}
    </div>
  );
}
