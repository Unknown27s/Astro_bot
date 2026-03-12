import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { listUsers, createUser, toggleUser, deleteUser } from '../../services/api';
import { UserPlus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ username: '', password: '', fullName: '', role: 'student' });

  const load = () => {
    listUsers()
      .then(r => setUsers(r.data))
      .catch(() => {});
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
    <div>
      <h2>👥 User Management</h2>
      <div className="divider" />

      {/* Create User */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 className="flex items-center gap-2"><UserPlus size={18} /> Create New User</h3>
        <form onSubmit={handleCreate} style={{ marginTop: 12 }}>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <div>
              <label>Username</label>
              <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
            </div>
            <div>
              <label>Password</label>
              <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
            </div>
            <div>
              <label>Full Name</label>
              <input value={form.fullName} onChange={e => setForm({ ...form, fullName: e.target.value })} />
            </div>
            <div>
              <label>Role</label>
              <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                <option value="student">Student</option>
                <option value="faculty">Faculty</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <button className="btn btn-primary">➕ Create User</button>
        </form>
      </div>

      {/* User List */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>Existing Users</h3>
        {users.length === 0 ? (
          <p className="text-muted text-center" style={{ padding: 24 }}>No users found.</p>
        ) : (
          users.map(u => (
            <div key={u.id} className="table-row">
              <span style={{ fontSize: 16 }}>{u.is_active === 1 ? '🟢' : '🔴'}</span>
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: 500 }}>{u.username}</span>
                <span className="text-sm text-muted"> ({u.full_name})</span>
              </div>
              <span className="text-sm">{roleBadge[u.role] || u.role}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => handleToggle(u)}>
                {u.is_active === 1 ? 'Disable' : 'Enable'}
              </button>
              {u.username !== currentUser?.username && (
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(u)}>
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
