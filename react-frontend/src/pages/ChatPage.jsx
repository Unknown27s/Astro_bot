import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sendChat, getChatStatus, getSuggestions } from '../services/api';
import { Send, LogOut, Trash2, Clock, TrendingUp, Sparkles } from 'lucide-react';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [llmOnline, setLlmOnline] = useState(null);
  const bottomRef = useRef(null);

  // ── Autocomplete state ──
  const [suggestions, setSuggestions] = useState({ recent: [], popular: [], preset: [] });
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const debounceRef = useRef(null);
  const suggestionsRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    getChatStatus().then(r => setLlmOnline(r.data.available)).catch(() => setLlmOnline(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Build flat list of all suggestions for keyboard nav
  const allSuggestions = useCallback(() => {
    const items = [];
    if (suggestions.recent.length > 0) {
      suggestions.recent.forEach(q => items.push({ text: q, type: 'recent' }));
    }
    if (suggestions.popular.length > 0) {
      suggestions.popular.forEach(q => items.push({ text: q, type: 'popular' }));
    }
    if (suggestions.preset.length > 0) {
      suggestions.preset.forEach(q => items.push({ text: q, type: 'preset' }));
    }
    return items;
  }, [suggestions]);

  // Fetch suggestions with debounce
  const fetchSuggestions = useCallback((query) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query || query.trim().length < 2) {
      // Show presets even when input is short/empty (on focus)
      if (query.trim().length === 0) {
        getSuggestions('', user?.id)
          .then(({ data }) => {
            setSuggestions(data);
            const hasAny = (data.recent?.length || 0) + (data.popular?.length || 0) + (data.preset?.length || 0) > 0;
            setShowSuggestions(hasAny);
          })
          .catch(() => {});
      } else {
        setShowSuggestions(false);
        setSuggestions({ recent: [], popular: [], preset: [] });
      }
      return;
    }

    debounceRef.current = setTimeout(() => {
      getSuggestions(query.trim(), user?.id)
        .then(({ data }) => {
          setSuggestions(data);
          const hasAny = (data.recent?.length || 0) + (data.popular?.length || 0) + (data.preset?.length || 0) > 0;
          setShowSuggestions(hasAny);
          setActiveIndex(-1);
        })
        .catch(() => {
          setShowSuggestions(false);
        });
    }, 300);
  }, [user?.id]);

  // Handle selecting a suggestion
  const selectSuggestion = useCallback((text) => {
    setInput(text);
    setShowSuggestions(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  }, []);

  // Handle sending (also usable from suggestion click)
  const handleSend = async (overrideQuery) => {
    const query = (overrideQuery || input).trim();
    if (!query || loading) return;
    setInput('');
    setShowSuggestions(false);
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

  // Keyboard navigation for suggestions
  const handleKeyDown = (e) => {
    const items = allSuggestions();

    if (e.key === 'Escape') {
      setShowSuggestions(false);
      setActiveIndex(-1);
      return;
    }

    if (!showSuggestions || items.length === 0) {
      if (e.key === 'Enter') handleSend();
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < items.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : items.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < items.length) {
        selectSuggestion(items[activeIndex].text);
      } else {
        handleSend();
      }
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);
    fetchSuggestions(val);
  };

  const handleInputFocus = () => {
    // Show suggestions on focus (presets when empty, search when has text)
    fetchSuggestions(input);
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowSuggestions(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex >= 0 && suggestionsRef.current) {
      const activeEl = suggestionsRef.current.querySelector('.autocomplete-item.active');
      activeEl?.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex]);

  const handleLogout = () => { logout(); navigate('/login'); };
  const isStandalone = !window.location.pathname.startsWith('/admin');

  // Render suggestion section
  const renderSection = (label, icon, items, type, startIndex) => {
    if (!items || items.length === 0) return null;
    return (
      <>
        <div className="autocomplete-section">
          {icon} {label}
        </div>
        {items.map((text, i) => {
          const globalIdx = startIndex + i;
          return (
            <div
              key={`${type}-${i}`}
              className={`autocomplete-item ${globalIdx === activeIndex ? 'active' : ''}`}
              onMouseEnter={() => setActiveIndex(globalIdx)}
              onMouseDown={(e) => { e.preventDefault(); selectSuggestion(text); }}
            >
              <span className="autocomplete-item-text">{highlightMatch(text, input)}</span>
            </div>
          );
        })}
      </>
    );
  };

  // Highlight matching part of suggestion
  const highlightMatch = (text, query) => {
    if (!query || query.trim().length < 2) return text;
    const idx = text.toLowerCase().indexOf(query.trim().toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <strong className="autocomplete-highlight">{text.slice(idx, idx + query.trim().length)}</strong>
        {text.slice(idx + query.trim().length)}
      </>
    );
  };

  const recentStartIdx = 0;
  const popularStartIdx = suggestions.recent.length;
  const presetStartIdx = suggestions.recent.length + suggestions.popular.length;

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
            <p className="text-sm text-muted" style={{ marginTop: 4 }}>💡 Start typing to see suggested questions</p>
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

      {/* Input with Autocomplete */}
      <div className="autocomplete-wrapper">
        {/* Suggestions dropdown (renders ABOVE the input) */}
        {showSuggestions && allSuggestions().length > 0 && (
          <div className="autocomplete-dropdown" ref={suggestionsRef}>
            {renderSection('Recent', <Clock size={12} />, suggestions.recent, 'recent', recentStartIdx)}
            {renderSection('Popular', <TrendingUp size={12} />, suggestions.popular, 'popular', popularStartIdx)}
            {renderSection('Suggested', <Sparkles size={12} />, suggestions.preset, 'preset', presetStartIdx)}
          </div>
        )}

        <div className="chat-input-bar">
          <input
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleInputFocus}
            placeholder="Ask a question about institutional documents..."
            disabled={loading}
            autoComplete="off"
          />
          <button className="btn btn-primary" onClick={() => handleSend()} disabled={loading || !input.trim()}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
