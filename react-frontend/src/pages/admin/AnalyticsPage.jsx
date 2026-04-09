import { useState, useEffect } from 'react';
import { getAnalytics, getQueryLogs } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [analyticsRes, logsRes] = await Promise.all([
          getAnalytics(),
          getQueryLogs(50),
        ]);
        setAnalytics(analyticsRes.data);
        setLogs(logsRes.data);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading analytics">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="astro-glass rounded-xl border border-white/10 p-4 animate-pulse">
              <div className="h-3 w-24 rounded bg-white/10" />
              <div className="mt-2 h-8 w-20 rounded bg-white/10" />
            </div>
          ))}
        </div>
        <div className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6 animate-pulse">
          <div className="h-5 w-56 rounded bg-white/10" />
          <div className="mt-4 h-64 rounded-xl bg-white/5" />
        </div>
      </div>
    );
  }

  if (!analytics) {
    return <div className="astro-glass rounded-xl border border-white/10 p-6 text-sm text-slate-300/85">Analytics data is currently unavailable.</div>;
  }

  const dailyData = Array.isArray(analytics.daily_queries)
    ? analytics.daily_queries.map((item) => {
      if (Array.isArray(item)) {
        const [day, cnt] = item;
        return { date: day, count: cnt };
      }
      return {
        date: item.day ?? item.date,
        count: item.cnt ?? item.count,
      };
    })
    : [];

  const topUsers = Array.isArray(analytics.top_users) ? analytics.top_users : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">Usage Analytics</h2>
        <p className="text-sm text-slate-300/85">Live platform metrics from analytics and query-log APIs.</p>
      </div>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="astro-glass rounded-xl border border-white/10 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Total Queries</p>
          <p className="mt-1 text-2xl font-bold text-white">{analytics.total_queries ?? 0}</p>
        </div>
        <div className="astro-glass rounded-xl border border-white/10 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Documents</p>
          <p className="mt-1 text-2xl font-bold text-white">{analytics.total_documents ?? 0}</p>
        </div>
        <div className="astro-glass rounded-xl border border-white/10 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Users</p>
          <p className="mt-1 text-2xl font-bold text-white">{analytics.total_users ?? 0}</p>
        </div>
        <div className="astro-glass rounded-xl border border-white/10 p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-300/80">Avg Response</p>
          <p className="mt-1 text-2xl font-bold text-white">{analytics.avg_response_ms ?? 0} ms</p>
        </div>
      </section>

      {dailyData.length > 0 ? (
        <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
          <h3 className="text-lg font-semibold text-white">Queries Per Day (Last 7 Days)</h3>
          <div className="mt-4 h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyData}>
                <XAxis dataKey="date" tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={{ stroke: '#334155' }} tickLine={{ stroke: '#334155' }} />
                <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={{ stroke: '#334155' }} tickLine={{ stroke: '#334155' }} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 10, color: '#f8fafc' }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Bar dataKey="count" fill="#22d3ee" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      ) : (
        <section className="astro-glass rounded-2xl border border-white/10 p-5 text-sm text-slate-300/85">
          Daily query trend data is not available yet.
        </section>
      )}

      {topUsers.length > 0 ? (
        <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
          <h3 className="text-lg font-semibold text-white">Top Querying Users</h3>
          <div className="mt-4 space-y-2">
            {topUsers.map((item, i) => (
              <div key={i} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <span className="text-sm text-slate-100">{item.username ?? item[0]}</span>
                <span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-2.5 py-1 text-xs font-semibold text-emerald-100">
                  {(item.cnt ?? item.count ?? item[1])} queries
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="astro-glass rounded-2xl border border-white/10 p-5 text-sm text-slate-300/85">
          No top-user usage records found yet.
        </section>
      )}

      <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
        <h3 className="text-lg font-semibold text-white">Recent Query Logs</h3>
        {logs.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-300/80">No queries yet.</p>
        ) : (
          <div className="mt-4 space-y-2">
            {logs.map((log, i) => (
              <details key={i} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <summary className="cursor-pointer text-sm font-medium text-slate-100" aria-label={`View query log ${i + 1}`}>
                  {log.query_text?.slice(0, 90)}{log.query_text?.length > 90 ? '...' : ''}
                  <span className="ml-2 text-xs text-slate-300/75">
                    - {log.username} ({log.created_at?.slice(0, 16)})
                  </span>
                </summary>
                <div className="mt-3 space-y-1 text-sm text-slate-200/90">
                  <p><strong>Response:</strong> {log.response_text}</p>
                  {log.sources && <p><strong>Sources:</strong> {log.sources}</p>}
                  <p><strong>Response time:</strong> {log.response_time_ms?.toFixed(0)} ms</p>
                </div>
              </details>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
