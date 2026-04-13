import { useEffect, useMemo, useState } from 'react';
import {
    getTraceMonitorEvents,
    getTraceMonitorOverview,
} from '../../services/api';
import {
    Activity,
    AlertTriangle,
    CheckCircle2,
    RefreshCw,
    XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';

const statusClassMap = {
    ok: 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100',
    healthy: 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100',
    warning: 'border-amber-300/30 bg-amber-500/10 text-amber-100',
    degraded: 'border-amber-300/30 bg-amber-500/10 text-amber-100',
    error: 'border-rose-300/30 bg-rose-500/10 text-rose-100',
    http_error: 'border-rose-300/30 bg-rose-500/10 text-rose-100',
    unhealthy: 'border-rose-300/30 bg-rose-500/10 text-rose-100',
};

function StatusBadge({ value }) {
    const key = String(value || 'unknown').toLowerCase();
    const cls = statusClassMap[key] || 'border-white/20 bg-white/10 text-slate-100';
    return (
        <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${cls}`}>
            {value || 'unknown'}
        </span>
    );
}

function statusIcon(status) {
    const key = String(status || '').toLowerCase();
    if (key === 'ok' || key === 'healthy') return <CheckCircle2 size={16} className="text-emerald-300" />;
    if (key === 'warning' || key === 'degraded') return <AlertTriangle size={16} className="text-amber-300" />;
    return <XCircle size={16} className="text-rose-300" />;
}

export default function TraceMonitorPage() {
    const [overview, setOverview] = useState(null);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [filters, setFilters] = useState({
        status: '',
        endpoint: '',
        provider: '',
        minutes: 60,
        includeProviders: true,
    });

    const loadData = async ({ silent = false } = {}) => {
        if (silent) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }

        try {
            const [overviewRes, eventsRes] = await Promise.all([
                getTraceMonitorOverview(filters.minutes, filters.includeProviders),
                getTraceMonitorEvents({
                    limit: 200,
                    status: filters.status || undefined,
                    endpoint: filters.endpoint || undefined,
                    provider: filters.provider || undefined,
                }),
            ]);
            setOverview(overviewRes.data || null);
            setEvents(Array.isArray(eventsRes.data?.items) ? eventsRes.data.items : []);
        } catch (error) {
            toast.error('Failed to load trace monitor data');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const alertCount = overview?.alerts?.length || 0;
    const summary = overview?.trace_summary || {};

    const endpointOptions = useMemo(() => {
        const setVals = new Set(events.map((item) => item.endpoint).filter(Boolean));
        return Array.from(setVals).sort();
    }, [events]);

    const providerOptions = useMemo(() => {
        const setVals = new Set(events.map((item) => item.provider).filter(Boolean));
        return Array.from(setVals).sort();
    }, [events]);

    if (loading) {
        return (
            <div className="space-y-4" aria-busy="true" aria-label="Loading trace monitor">
                <section className="astro-glass rounded-2xl border border-white/10 p-5 animate-pulse">
                    <div className="h-5 w-44 rounded bg-white/10" />
                    <div className="mt-3 h-20 rounded-xl bg-white/5" />
                </section>
                <section className="astro-glass rounded-2xl border border-white/10 p-5 animate-pulse">
                    <div className="h-5 w-64 rounded bg-white/10" />
                    <div className="mt-3 h-64 rounded-xl bg-white/5" />
                </section>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                    <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">Trace Monitor</h2>
                    <p className="text-sm text-slate-300/85">Trace timeline, retrieval quality, fallback flow, and failing subsystem alerts.</p>
                </div>
                <button
                    className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-white/10"
                    type="button"
                    onClick={() => loadData({ silent: true })}
                    disabled={refreshing}
                >
                    <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                    Refresh
                </button>
            </div>

            <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Monitor Status</p>
                    <div className="mt-2 flex items-center gap-2">
                        {statusIcon(overview?.status)}
                        <StatusBadge value={overview?.status || 'unknown'} />
                    </div>
                </div>
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Total Requests</p>
                    <p className="mt-1 text-2xl font-bold text-white">{summary.total_requests ?? 0}</p>
                </div>
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Failures</p>
                    <p className="mt-1 text-2xl font-bold text-rose-100">{summary.failed_requests ?? 0}</p>
                </div>
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Failure Rate</p>
                    <p className="mt-1 text-2xl font-bold text-white">{summary.failure_rate ?? 0}%</p>
                </div>
                <div className="astro-glass rounded-xl border border-white/10 p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Avg Latency</p>
                    <p className="mt-1 text-2xl font-bold text-white">{summary.avg_latency_ms ?? 0} ms</p>
                </div>
            </section>

            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-lg font-semibold text-white">Subsystem Alerts</h3>
                    <div className="inline-flex items-center gap-2 text-xs text-slate-300/90">
                        <Activity size={14} />
                        Last {overview?.window_minutes ?? filters.minutes} minutes
                    </div>
                </div>

                {alertCount === 0 ? (
                    <p className="mt-4 rounded-xl border border-emerald-300/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">
                        No active subsystem alerts detected.
                    </p>
                ) : (
                    <div className="mt-4 space-y-2">
                        {overview.alerts.map((alert, idx) => (
                            <div key={`${alert.type}-${alert.name}-${idx}`} className="rounded-xl border border-white/15 bg-white/5 px-3 py-2">
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-white">
                                        {statusIcon(alert.status)}
                                        <span>{alert.type}: {alert.name}</span>
                                    </div>
                                    <StatusBadge value={alert.status} />
                                </div>
                                <p className="mt-1 text-xs text-slate-300/85">{alert.message}</p>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-lg font-semibold text-white">Trace Timeline</h3>
                    <div className="flex flex-wrap gap-2">
                        <select
                            className="rounded-xl border border-white/15 bg-black/20 px-3 py-2 text-xs text-slate-100"
                            value={filters.status}
                            onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
                            aria-label="Filter traces by status"
                        >
                            <option value="">All statuses</option>
                            <option value="ok">ok</option>
                            <option value="http_error">http_error</option>
                            <option value="error">error</option>
                        </select>
                        <select
                            className="rounded-xl border border-white/15 bg-black/20 px-3 py-2 text-xs text-slate-100"
                            value={filters.endpoint}
                            onChange={(event) => setFilters((prev) => ({ ...prev, endpoint: event.target.value }))}
                            aria-label="Filter traces by endpoint"
                        >
                            <option value="">All endpoints</option>
                            {endpointOptions.map((endpoint) => (
                                <option value={endpoint} key={endpoint}>{endpoint}</option>
                            ))}
                        </select>
                        <select
                            className="rounded-xl border border-white/15 bg-black/20 px-3 py-2 text-xs text-slate-100"
                            value={filters.provider}
                            onChange={(event) => setFilters((prev) => ({ ...prev, provider: event.target.value }))}
                            aria-label="Filter traces by provider"
                        >
                            <option value="">All providers</option>
                            {providerOptions.map((provider) => (
                                <option value={provider} key={provider}>{provider}</option>
                            ))}
                        </select>
                        <button
                            type="button"
                            onClick={() => loadData({ silent: true })}
                            className="rounded-xl border border-cyan-300/40 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-100 hover:bg-cyan-400/20"
                        >
                            Apply
                        </button>
                    </div>
                </div>

                {events.length === 0 ? (
                    <p className="mt-4 text-sm text-slate-300/85">No trace events found for current filters.</p>
                ) : (
                    <div className="astro-scrollbar mt-4 overflow-x-auto">
                        <table className="min-w-full text-sm">
                            <thead className="bg-white/5 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                                <tr>
                                    <th className="px-3 py-2 text-left">Time</th>
                                    <th className="px-3 py-2 text-left">Trace</th>
                                    <th className="px-3 py-2 text-left">Endpoint</th>
                                    <th className="px-3 py-2 text-left">Status</th>
                                    <th className="px-3 py-2 text-left">Top Score</th>
                                    <th className="px-3 py-2 text-left">Provider</th>
                                    <th className="px-3 py-2 text-left">Latency</th>
                                    <th className="px-3 py-2 text-left">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.map((item) => (
                                    <tr className="border-t border-white/10 text-slate-100/90" key={item.id}>
                                        <td className="px-3 py-2 text-xs text-slate-300/85">
                                            {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-[11px] text-cyan-100">
                                            {String(item.trace_id || '').slice(0, 8)}
                                        </td>
                                        <td className="px-3 py-2">{item.endpoint || '-'}</td>
                                        <td className="px-3 py-2"><StatusBadge value={item.status} /></td>
                                        <td className="px-3 py-2">
                                            {typeof item.retrieval_top_score === 'number' ? `${(item.retrieval_top_score * 100).toFixed(0)}%` : '-'}
                                        </td>
                                        <td className="px-3 py-2">
                                            <div className="text-xs text-slate-100">{item.provider || '-'}</div>
                                            {item.model ? <div className="text-[11px] text-slate-300/75">{item.model}</div> : null}
                                        </td>
                                        <td className="px-3 py-2">{item.response_time_ms ? `${Math.round(item.response_time_ms)} ms` : '-'}</td>
                                        <td className="px-3 py-2">
                                            <details>
                                                <summary className="cursor-pointer text-xs text-cyan-100">view</summary>
                                                <div className="mt-2 space-y-1 text-xs text-slate-300/85">
                                                    <div>mode: {item.retrieval_mode || '-'}</div>
                                                    <div>hyde: {item.hyde_applied ? 'yes' : 'no'}</div>
                                                    <div>chunks: {item.chunks_count ?? 0}</div>
                                                    <div>memory: {item.from_memory ? 'hit' : 'miss'}</div>
                                                    <div>query: {(item.query_preview || '-').slice(0, 140)}</div>
                                                    {item.error_message ? <div className="text-rose-200">error: {item.error_message}</div> : null}
                                                </div>
                                            </details>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}
