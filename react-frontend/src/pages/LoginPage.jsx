import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login, register } from '../services/api';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [mode, setMode] = useState('login'); // login | register
  const [loginType, setLoginType] = useState('student'); // student | admin
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('student');
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username || !password) return toast.error('Fill in all fields');
    setLoading(true);
    try {
      const { data } = await login(username, password);
      if (loginType === 'admin' && data.role !== 'admin') {
        toast.error('This account is not an administrator');
        setLoading(false);
        return;
      }
      if (loginType === 'student' && data.role === 'admin') {
        toast.error('Admin accounts should use Admin Login');
        setLoading(false);
        return;
      }
      loginUser(data);
      toast.success(`Welcome, ${data.username}!`);
      navigate(data.role === 'admin' ? '/admin/documents' : '/chat');
    } catch {
      toast.error('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!username || !password || !fullName) return toast.error('Fill in all fields');
    setLoading(true);
    try {
      await register(username, password, role, fullName);
      toast.success('Account created! You can now log in.');
      setMode('login');
    } catch {
      toast.error('Username already taken');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div className="text-center" style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 36 }}>🤖 IMS AstroBot</h1>
          <p className="text-muted">Institutional AI Assistant — Powered by RAG</p>
        </div>

        {mode === 'login' ? (
          <div className="card">
            <div className="flex gap-2" style={{ marginBottom: 16 }}>
              <button
                className={`btn btn-block ${loginType === 'student' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setLoginType('student')}
              >🎓 Student / Faculty</button>
              <button
                className={`btn btn-block ${loginType === 'admin' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setLoginType('admin')}
              >🔑 Admin</button>
            </div>
            <form onSubmit={handleLogin} className="flex flex-col gap-3">
              <div>
                <label>Username</label>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter username" />
              </div>
              <div>
                <label>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" />
              </div>
              <button className="btn btn-primary btn-block" disabled={loading}>
                {loading ? <span className="spinner" /> : 'Login'}
              </button>
            </form>
            {loginType === 'student' && (
              <p className="text-center text-sm text-muted" style={{ marginTop: 12 }}>
                Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); setMode('register'); }}>Register</a>
              </p>
            )}
          </div>
        ) : (
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>📝 Create Account</h3>
            <form onSubmit={handleRegister} className="flex flex-col gap-3">
              <div>
                <label>Full Name</label>
                <input value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Enter your full name" />
              </div>
              <div>
                <label>Username</label>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Choose a username" />
              </div>
              <div>
                <label>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Choose a password" />
              </div>
              <div>
                <label>Role</label>
                <select value={role} onChange={e => setRole(e.target.value)}>
                  <option value="student">Student</option>
                  <option value="faculty">Faculty</option>
                </select>
              </div>
              <button className="btn btn-primary btn-block" disabled={loading}>
                {loading ? <span className="spinner" /> : 'Register'}
              </button>
            </form>
            <p className="text-center text-sm text-muted" style={{ marginTop: 12 }}>
              Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); setMode('login'); }}>Login</a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
