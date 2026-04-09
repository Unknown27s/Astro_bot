import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, Badge } from '../ui/index';
import { MessageSquare, Users, FileText, Clock } from 'lucide-react';

// Mock data
const mockQueryTrends = [
  { date: 'Mon', queries: 120 },
  { date: 'Tue', queries: 150 },
  { date: 'Wed', queries: 130 },
  { date: 'Thu', queries: 180 },
  { date: 'Fri', queries: 200 },
  { date: 'Sat', queries: 90 },
  { date: 'Sun', queries: 110 },
];

const mockUserDistribution = [
  { name: 'Students', value: 75, color: '#7C3AED' },
  { name: 'Faculty', value: 20, color: '#14B8A6' },
  { name: 'Admin', value: 5, color: '#F59E0B' },
];

const mockLatencyData = [
  { endpoint: '/chat', latency: 350 },
  { endpoint: '/search', latency: 120 },
  { endpoint: '/upload', latency: 800 },
  { endpoint: '/analytics', latency: 100 },
];

const mockPopularQuestions = [
  { question: 'What are placement statistics?', count: 145 },
  { question: 'How to apply for events?', count: 98 },
  { question: 'Faculty contact details', count: 87 },
  { question: 'Canteen timings', count: 76 },
  { question: 'Library hours', count: 65 },
];

export default function AnalyticsPage() {
  const [stats, setStats] = useState({
    totalQueries: 2847,
    activeUsers: 342,
    documentsIndexed: 156,
    avgLatency: 265,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 mb-2">Analytics Dashboard</h1>
        <p className="text-slate-600">Monitor system performance and user activity</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Queries */}
        <Card padding="lg" shadow="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-sm font-medium">Total Queries</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-2">
                {stats.totalQueries.toLocaleString()}
              </h3>
              <p className="text-xs text-green-600 mt-2">+12% from last week</p>
            </div>
            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        {/* Active Users */}
        <Card padding="lg" shadow="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-sm font-medium">Active Users</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-2">
                {stats.activeUsers.toLocaleString()}
              </h3>
              <p className="text-xs text-green-600 mt-2">+8% from last week</p>
            </div>
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        {/* Documents Indexed */}
        <Card padding="lg" shadow="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-sm font-medium">Documents</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-2">
                {stats.documentsIndexed}
              </h3>
              <p className="text-xs text-slate-500 mt-2">Knowledge base</p>
            </div>
            <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        {/* Average Latency */}
        <Card padding="lg" shadow="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-sm font-medium">Avg Latency</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-2">
                {stats.avgLatency}ms
              </h3>
              <p className="text-xs text-green-600 mt-2">Excellent</p>
            </div>
            <div className="h-12 w-12 bg-amber-100 rounded-lg flex items-center justify-center">
              <Clock className="h-6 w-6 text-amber-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Trends */}
        <Card padding="lg" shadow="md">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Query Trends (This Week)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockQueryTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="date" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                }}
              />
              <Line
                type="monotone"
                dataKey="queries"
                stroke="#7C3AED"
                strokeWidth={2}
                dot={{ fill: '#7C3AED', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* User Distribution */}
        <Card padding="lg" shadow="md">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">User Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={mockUserDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {mockUserDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* API Latency */}
        <Card padding="lg" shadow="md">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">API Latency</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mockLatencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="endpoint" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="latency" fill="#14B8A6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Popular Questions */}
        <Card padding="lg" shadow="md">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Popular Questions</h3>
          <div className="space-y-3">
            {mockPopularQuestions.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between pb-3 border-b border-slate-200 last:border-b-0">
                <span className="text-sm text-slate-600 flex-1">{item.question}</span>
                <Badge variant="primary" size="sm">
                  {item.count}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
