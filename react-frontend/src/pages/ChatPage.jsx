import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sendChat, getChatStatus } from '../services/api';
import { Send, LogOut, Trash2 } from 'lucide-react';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [llmOnline, setLlmOnline] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    getChatStatus().then(r => setLlmOnline(r.data.available)).catch(() => setLlmOnline(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);
    try {
      const { data } = await sendChat(query, user.id, user.username);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        citations: data.citations,
        time: data.response_time_ms,
      }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Failed to get a response. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => { logout(); navigate('/login'); };
  const isStandalone = !window.location.pathname.startsWith('/admin');

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="flex items-center justify-between" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2">
          <h3>💬 Chat with AstroBot</h3>
          <span className="text-sm text-muted">({user?.username})</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${llmOnline ? 'badge-ok' : 'badge-warning'}`}>
            {llmOnline ? '🟢 LLM Online' : '🟡 Fallback'}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => setMessages([])}><Trash2 size={14} /> Clear</button>
          {isStandalone && (
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}><LogOut size={14} /> Logout</button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="text-center text-muted" style={{ marginTop: '20vh' }}>
            <p style={{ fontSize: 48 }}>🤖</p>
            <h3>Welcome to IMS AstroBot</h3>
            <p className="text-sm" style={{ marginTop: 8 }}>Ask me anything about institutional documents</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {msg.citations && (
              <details style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                <summary>📚 Sources</summary>
                <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{msg.citations}</div>
              </details>
            )}
            {msg.time && (
              <div className="text-sm text-muted" style={{ marginTop: 4 }}>{msg.time.toFixed(0)}ms</div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <span className="spinner" /> Searching documents and generating response...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question about institutional documents..."
          disabled={loading}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
