import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { Bot } from 'lucide-react';
import BrandingSection from '../components/auth/BrandingSection';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../context/AuthContext';
import { login, register } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const { loginUser } = useAuth();
  const [mode, setMode] = useState('login');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (data) => {
    setLoading(true);
    try {
      const response = await login(data.username, data.password);
      const userData = response.data;

      // Store user in AuthContext
      loginUser({
        id: userData.id,
        username: userData.username,
        role: userData.role,
        fullName: userData.fullName || userData.full_name,
      });

      toast.success('Login successful!');
      navigate(userData.role === 'admin' ? '/admin/documents' : '/chat');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Invalid credentials';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (data) => {
    setLoading(true);
    try {
      await register(data.username, data.password, data.role, data.fullName);

      toast.success('Registration successful! Please login.');
      setMode('login');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Registration failed';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#f7f9fb] text-[#191c1e]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/2 h-[40rem] w-[40rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#07376a]/10" />
        <div className="absolute left-1/2 top-1/2 h-[60rem] w-[60rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#07376a]/7" />
        <div className="absolute left-1/2 top-1/2 h-[80rem] w-[80rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#07376a]/5" />
        <div className="absolute inset-0 bg-gradient-to-tr from-[#f2f4f6] via-[#f7f9fb] to-white/90" />
      </div>

      <main className="relative z-10 w-full max-w-md px-6 py-10">
        <BrandingSection />

        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mt-8 rounded-xl border border-white/60 bg-white/30 p-6 shadow-[0_32px_64px_-16px_rgba(7,55,106,0.08)] backdrop-blur-2xl"
        >
          <div className="mb-6 flex justify-between gap-2">
            <button
              onClick={() => setMode('login')}
              type="button"
              className={`w-full rounded-full px-4 py-2.5 text-sm font-bold transition ${mode === 'login'
                ? 'bg-[#d5e3ff] text-[#07376a] ring-1 ring-[#07376a]/20'
                : 'text-[#737783] hover:bg-white/60'
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode('register')}
              type="button"
              className={`w-full rounded-full px-4 py-2.5 text-sm font-bold transition ${mode === 'register'
                ? 'bg-[#d5e3ff] text-[#07376a] ring-1 ring-[#07376a]/20'
                : 'text-[#737783] hover:bg-white/60'
                }`}
            >
              Create Account
            </button>
          </div>

          {mode === 'login' ? (
            <LoginForm onSubmit={handleLogin} loading={loading} onSwitchMode={() => setMode('register')} />
          ) : (
            <RegisterForm onSubmit={handleRegister} loading={loading} onSwitchMode={() => setMode('login')} />
          )}
        </motion.section>

        <p className="mt-8 text-center text-sm font-medium text-[#505f76]">
          Secure Gateway for Rajalakshmi Institute of Technology
        </p>
      </main>

      <footer className="relative z-10 mt-auto w-full max-w-7xl px-8 py-7">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-center text-xs font-medium uppercase tracking-wide text-slate-500 md:text-left">
            © 2026 Rajalakshmi Institute of Technology. All rights reserved.
          </p>
          <div className="flex gap-5">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Privacy Policy</span>
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Terms of Service</span>
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Help Center</span>
          </div>
        </div>
      </footer>

      <div className="pointer-events-none fixed bottom-10 right-10 hidden opacity-10 lg:block">
        <Bot size={170} className="text-[#07376a]" />
      </div>
    </div>
  );
}
