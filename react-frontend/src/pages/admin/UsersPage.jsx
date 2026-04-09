import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { listUsers, createUser, toggleUser, deleteUser } from '../../services/api';
import { UserPlus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ username: '', password: '', fullName: '', role: 'student' });

  const load = async () => {
    setLoading(true);
    try {
      const result = await listUsers();
      setUsers(result.data);
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.username || !form.password) return toast.error('Username and password required');
    try {
      await createUser(form.username, form.password, form.role, form.fullName);
      toast.success(`User '${form.username}' created`);
      setForm({ username: '', password: '', fullName: '', role: 'student' });
      load();
    } catch {
      toast.error('Username already exists');
    }
  };

  const handleToggle = async (u) => {
    const newActive = u.is_active === 1 ? false : true;
    try {
      await toggleUser(u.id, newActive);
      toast.success(`User ${newActive ? 'enabled' : 'disabled'}`);
      load();
    } catch (err) {
      toast.error(
        err.response?.data?.detail || 'Failed to update user status'
      );
    }
  };

  const handleDelete = async (u) => {
    if (!confirm(`Delete user "${u.username}"?`)) return;
    try {
      await deleteUser(u.id);
      toast.success('User deleted');
      load();
    } catch (err) {
      toast.error(
        err.response?.data?.detail || 'Failed to delete user'
      );
    }
  };

  const roleBadge = { admin: '🔑 Admin', faculty: '🎓 Faculty', student: '📚 Student' };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">User Management</h2>
        <p className="text-sm text-slate-300/85">Create and manage platform users with role-based access.</p>
      </div>

      <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-white"><UserPlus size={18} /> Create New User</h3>
        <form onSubmit={handleCreate} className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80">Username</label>
            <input
              value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })}
              className="w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none"
              placeholder="username"
              aria-label="Username"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              className="w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none"
              placeholder="password"
              aria-label="Password"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80">Full Name</label>
            <input
              value={form.fullName}
              onChange={e => setForm({ ...form, fullName: e.target.value })}
              className="w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none"
              placeholder="full name"
              aria-label="Full name"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80">Role</label>
            <select
              value={form.role}
              onChange={e => setForm({ ...form, role: e.target.value })}
              className="w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white focus:border-cyan-300/70 focus:outline-none"
              aria-label="Role"
            >
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <button type="submit" aria-label="Create user" className="rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2.5 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02]">
              Create User
            </button>
          </div>
        </form>
      </section>

      <section className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6">
        <h3 className="text-lg font-semibold text-white">Existing Users</h3>
        {loading ? (
          <div className="mt-4 space-y-2" aria-busy="true" aria-label="Loading users">
            {[1, 2, 3, 4].map((idx) => (
              <div key={idx} className="h-12 rounded-xl bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : users.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-300/80">No users found.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-100">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-slate-300/80">
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3">Username</th>
                  <th className="px-3 py-3">Full Name</th>
                  <th className="px-3 py-3">Role</th>
                  <th className="px-3 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-white/10 last:border-b-0">
                    <td className="px-3 py-3">{u.is_active === 1 ? '🟢' : '🔴'}</td>
                    <td className="px-3 py-3 font-medium text-white">{u.username}</td>
                    <td className="px-3 py-3 text-slate-200/90">{u.full_name || '-'}</td>
                    <td className="px-3 py-3 text-slate-200/90">{roleBadge[u.role] || u.role}</td>
                    <td className="px-3 py-3 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          className="rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 transition-colors hover:bg-white/10"
                          onClick={() => handleToggle(u)}
                          type="button"
                          aria-label={`${u.is_active === 1 ? 'Disable' : 'Enable'} user ${u.username}`}
                        >
                          {u.is_active === 1 ? 'Disable' : 'Enable'}
                        </button>
                        {u.username !== currentUser?.username && (
                          <button
                            className="inline-flex items-center gap-1 rounded-lg border border-rose-300/25 bg-rose-400/10 px-3 py-1.5 text-xs font-semibold text-rose-100 transition-colors hover:bg-rose-400/20"
                            onClick={() => handleDelete(u)}
                            type="button"
                            aria-label={`Delete user ${u.username}`}
                          >
                            <Trash2 size={13} /> Delete
                          </button>
                        )}
                      </div>
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
