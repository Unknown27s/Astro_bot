import { useState, useEffect } from 'react';
import { getAnalytics, getQueryLogs } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    getAnalytics().then(r => setAnalytics(r.data)).catch(() => {});
    getQueryLogs(50).then(r => setLogs(r.data)).catch(() => {});
  }, []);

  if (!analytics) return <div className="text-center" style={{ padding: 48 }}><span className="spinner" /></div>;

  return (
    <div>
      <h2>📊 Usage Analytics</h2>
      <div className="divider" />

      {/* Metrics */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="card metric">
          <div className="metric-value">{analytics.total_queries}</div>
          <div className="metric-label">Total Queries</div>
        </div>
        <div className="card metric">
          <div className="metric-value">{analytics.total_documents}</div>
          <div className="metric-label">Documents</div>
        </div>
        <div className="card metric">
          <div className="metric-value">{analytics.total_users}</div>
          <div className="metric-label">Users</div>
        </div>
        <div className="card metric">
          <div className="metric-value">{analytics.avg_response_ms}ms</div>
          <div className="metric-label">Avg Response</div>
        </div>
      </div>

      {/* Chart */}
      {analytics.daily_queries?.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 16 }}>Queries Per Day (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={analytics.daily_queries.map(([date, count]) => ({ date, count }))}>
              <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Users */}
      {analytics.top_users?.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 12 }}>Top Querying Users</h3>
          {analytics.top_users.map(([name, count], i) => (
            <div key={i} className="table-row">
              <span style={{ flex: 1 }}>{name}</span>
              <span className="badge badge-ok">{count} queries</span>
            </div>
          ))}
        </div>
      )}

      {/* Query Logs */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>📋 Recent Query Logs</h3>
        {logs.length === 0 ? (
          <p className="text-muted text-center" style={{ padding: 24 }}>No queries yet.</p>
        ) : (
          logs.map((log, i) => (
            <details key={i} className="table-row" style={{ display: 'block', cursor: 'pointer' }}>
              <summary style={{ fontWeight: 500 }}>
                🔍 {log.query_text?.slice(0, 80)}{log.query_text?.length > 80 ? '...' : ''}
                <span className="text-sm text-muted"> — {log.username} ({log.created_at?.slice(0, 16)})</span>
              </summary>
              <div style={{ padding: '8px 0', fontSize: 13, color: 'var(--text-muted)' }}>
                <p><strong>Response:</strong> {log.response_text}</p>
                {log.sources && <p><strong>Sources:</strong> {log.sources}</p>}
                <p>Response time: {log.response_time_ms?.toFixed(0)}ms</p>
              </div>
            </details>
          ))
        )}
      </div>
    </div>
  );
}
