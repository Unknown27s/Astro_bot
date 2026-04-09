import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('astrobot_user');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('astrobot_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('astrobot_user');
    }
  }, [user]);

  // Listen for external localStorage changes (e.g., from test buttons on same tab)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'astrobot_user') {
        const newUser = e.newValue ? JSON.parse(e.newValue) : null;
        setUser(newUser);
      }
    };

    // Handle external storage changes (other tabs)
    window.addEventListener('storage', handleStorageChange);

    // Handle same-tab changes (custom event from test buttons)
    const handleCustomEvent = (e) => {
      const newUser = localStorage.getItem('astrobot_user');
      setUser(newUser ? JSON.parse(newUser) : null);
    };
    window.addEventListener('astrobot:user-changed', handleCustomEvent);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('astrobot:user-changed', handleCustomEvent);
    };
  }, []);

  const loginUser = (userData) => setUser(userData);
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loginUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
