import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sendChat, getChatStatus, getSuggestions, sendAudioMessage, getAnnouncements, deleteAnnouncement } from '../services/api';
import { Send, LogOut, Trash2, Clock, TrendingUp, Sparkles, Mic, Bell, MessageSquare, Megaphone, Pin, ChevronRight, X, AtSign } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [llmOnline, setLlmOnline] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [unreadAnnouncements, setUnreadAnnouncements] = useState(0);
  const [activeView, setActiveView] = useState('chat'); // 'chat' or 'announcements'
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const bottomRef = useRef(null);

  // ── Audio Recording State ──
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // ── Autocomplete state ──
  const [suggestions, setSuggestions] = useState({ recent: [], popular: [], preset: [] });
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const debounceRef = useRef(null);
  const suggestionsRef = useRef(null);
  const inputRef = useRef(null);

  // ── @ Command state ──
  const [showAtCommands, setShowAtCommands] = useState(false);
  const [atCommandIndex, setAtCommandIndex] = useState(-1);
  const atCommandsRef = useRef(null);

  const AT_COMMANDS = [
    { cmd: '@Announcement', description: 'Post an institutional announcement', icon: '📢' },
  ];

  const isAdmin = user?.role === 'admin';
  const isFaculty = user?.role === 'faculty';
  const canPost = isAdmin || isFaculty;

  useEffect(() => {
    getChatStatus().then(r => setLlmOnline(r.data.available)).catch(() => setLlmOnline(false));
  }, []);

  useEffect(() => {
    const fetchAnnouncements = async () => {
      try {
        const { data } = await getAnnouncements();
        setAnnouncements(data);
        const lastSeen = localStorage.getItem(`lastSeenAnnouncement_${user?.id}`);
        if (data.length > 0) {
          const newIndex = data.findIndex(a => a.id === lastSeen);
          if (newIndex === -1 && lastSeen) {
            setUnreadAnnouncements(data.length);
          } else if (newIndex > 0) {
            setUnreadAnnouncements(newIndex);
          } else if (!lastSeen) {
            setUnreadAnnouncements(data.length);
          }
        }
      } catch (err) {}
    };
    fetchAnnouncements();
    const interval = setInterval(fetchAnnouncements, 30000);
    return () => clearInterval(interval);
  }, [user?.id]);

  const handleDeleteAnnouncement = async (id) => {
    if (!window.confirm("Are you sure you want to delete this announcement?")) return;
    
    try {
      await deleteAnnouncement(id, user.id, user.role);
      toast.success("Announcement deleted successfully");
      const { data } = await getAnnouncements();
      setAnnouncements(data);
    } catch (error) {
      toast.error("Failed to delete announcement");
      console.error(error);
    }
  };

  const handleSwitchToAnnouncements = () => {
    setActiveView('announcements');
    if (announcements.length > 0) {
      setUnreadAnnouncements(0);
      localStorage.setItem(`lastSeenAnnouncement_${user?.id}`, announcements[0].id);
    }
  };

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

  // Handle sending
  const handleSend = async (overrideQuery) => {
    const query = (overrideQuery || input).trim();
    if (!query || loading) return;
    setInput('');
    setShowSuggestions(false);
    // Switch to chat view when sending a message
    setActiveView('chat');
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
      // If it was an announcement, refresh the announcements list
      if (query.trim().toLowerCase().startsWith('@announcement')) {
        try {
          const annResult = await getAnnouncements();
          setAnnouncements(annResult.data);
        } catch {}
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Failed to get a response. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        handleSendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
      alert("Microphone access denied. Please allow microphone permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  const handleSendAudio = async (audioBlob) => {
    if (loading) return;
    setActiveView('chat');
    setMessages(prev => [...prev, { role: 'user', content: '🎤 [Processing Voice Message...]' }]);
    setLoading(true);
    try {
      const { data } = await sendAudioMessage(audioBlob, user.id, user.username);
      
      if (data.transcribed_text) {
        setMessages(prev => {
           const newMsgs = [...prev];
           newMsgs[newMsgs.length - 1].content = `🎤 ${data.transcribed_text}`;
           return newMsgs;
        });
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        citations: data.citations,
        time: data.response_time_ms,
      }]);
    } catch (err) {
      setMessages(prev => {
         const newMsgs = [...prev];
         newMsgs[newMsgs.length - 1].content = '🎤 [Voice message failed]';
         return [...newMsgs, { role: 'assistant', content: '⚠️ Failed to process audio. Please try again.' }];
      });
    } finally {
      setLoading(false);
    }
  };

  // Keyboard navigation for suggestions & @ commands
  const handleKeyDown = (e) => {
    // Handle @ command navigation
    if (showAtCommands) {
      const filteredCmds = canPost
        ? AT_COMMANDS.filter(c => c.cmd.toLowerCase().startsWith(input.trim().toLowerCase()))
        : [];

      if (e.key === 'Escape') {
        setShowAtCommands(false);
        setAtCommandIndex(-1);
        return;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setAtCommandIndex(prev => (prev < filteredCmds.length - 1 ? prev + 1 : 0));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setAtCommandIndex(prev => (prev > 0 ? prev - 1 : filteredCmds.length - 1));
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        if (atCommandIndex >= 0 && atCommandIndex < filteredCmds.length) {
          selectAtCommand(filteredCmds[atCommandIndex].cmd);
        }
        return;
      }
    }

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

    // @ command detection for admin/faculty
    if (canPost && val.trim() === '@') {
      setShowAtCommands(true);
      setAtCommandIndex(0);
      setShowSuggestions(false);
      return;
    }
    if (canPost && val.trim().startsWith('@') && val.trim().length > 1 && !val.trim().includes(' ')) {
      // Filter commands as they type
      const query = val.trim().toLowerCase();
      const matches = AT_COMMANDS.filter(c => c.cmd.toLowerCase().startsWith(query));
      if (matches.length > 0) {
        setShowAtCommands(true);
        setAtCommandIndex(0);
        setShowSuggestions(false);
        return;
      }
    }
    setShowAtCommands(false);
    setAtCommandIndex(-1);
    fetchSuggestions(val);
  };

  const selectAtCommand = (cmd) => {
    setInput(cmd + ' ');
    setShowAtCommands(false);
    setAtCommandIndex(-1);
    inputRef.current?.focus();
  };

  const handleInputFocus = () => {
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

  const latestAnnouncement = announcements.length > 0 ? announcements[0] : null;

  return (
    <div className="chatpage-layout">
      {/* ── Left Sidebar ── */}
      <div className={`chatpage-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="chatpage-sidebar-header">
          <div className="chatpage-sidebar-brand">
            <span style={{ fontSize: 22 }}>🤖</span>
            {!sidebarCollapsed && <span className="chatpage-sidebar-title">AstroBot</span>}
          </div>
          <button
            className="chatpage-sidebar-toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronRight size={16} style={{ transform: sidebarCollapsed ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.2s' }} />
          </button>
        </div>

        <nav className="chatpage-sidebar-nav">
          {/* Chat Button */}
          <button
            className={`chatpage-sidebar-link ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveView('chat')}
          >
            <MessageSquare size={18} />
            {!sidebarCollapsed && <span>Chat</span>}
          </button>

          {/* Announcements Button */}
          <button
            className={`chatpage-sidebar-link ${activeView === 'announcements' ? 'active' : ''}`}
            onClick={handleSwitchToAnnouncements}
            style={{ position: 'relative' }}
          >
            <Megaphone size={18} />
            {!sidebarCollapsed && <span>Announcements</span>}
            {unreadAnnouncements > 0 && (
              <span className="chatpage-unread-badge">
                {unreadAnnouncements}
              </span>
            )}
          </button>
        </nav>

        <div className="chatpage-sidebar-footer">
          <div className="chatpage-sidebar-user">
            <div className="chatpage-sidebar-avatar">
              {user?.username?.charAt(0)?.toUpperCase() || '?'}
            </div>
            {!sidebarCollapsed && (
              <div className="chatpage-sidebar-userinfo">
                <span className="chatpage-sidebar-username">{user?.username}</span>
                <span className="chatpage-sidebar-role">{user?.role}</span>
              </div>
            )}
          </div>
          {isStandalone && (
            <button
              className="chatpage-sidebar-link"
              onClick={handleLogout}
              style={{ marginTop: 8 }}
            >
              <LogOut size={18} />
              {!sidebarCollapsed && <span>Logout</span>}
            </button>
          )}
        </div>
      </div>

      {/* ── Main Content Area ── */}
      <div className="chatpage-main">
        {/* Header Bar */}
        <div className="chatpage-header">
          <div className="flex items-center gap-2">
            {activeView === 'chat' ? (
              <>
                <MessageSquare size={18} />
                <h3 style={{ margin: 0 }}>Chat with AstroBot</h3>
              </>
            ) : (
              <>
                <Megaphone size={18} />
                <h3 style={{ margin: 0 }}>Announcements</h3>
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={`badge ${llmOnline ? 'badge-ok' : 'badge-warning'}`}>
              {llmOnline ? '🟢 Online' : '🟡 Fallback'}
            </span>
            {activeView === 'chat' && (
              <button className="btn btn-ghost btn-sm" onClick={() => setMessages([])}><Trash2 size={14} /> Clear</button>
            )}
          </div>
        </div>

        {/* ── Chat View ── */}
        {activeView === 'chat' && (
          <>
            {/* Pinned Announcement Banner */}
            {latestAnnouncement && (
              <div className="chatpage-pinned-banner" onClick={handleSwitchToAnnouncements}>
                <div className="chatpage-pinned-icon"><Pin size={14} /></div>
                <div className="chatpage-pinned-content">
                  <span className="chatpage-pinned-label">📢 Latest Announcement</span>
                  <span className="chatpage-pinned-text">
                    {latestAnnouncement.content.length > 120
                      ? latestAnnouncement.content.substring(0, 120) + '...'
                      : latestAnnouncement.content}
                  </span>
                </div>
                <ChevronRight size={16} className="text-muted" />
              </div>
            )}

            {/* Messages */}
            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="text-center text-muted" style={{ marginTop: '20vh' }}>
                  <p style={{ fontSize: 48 }}>🤖</p>
                  <h3>Welcome to IMS AstroBot</h3>
                  <p className="text-sm" style={{ marginTop: 8 }}>Ask me anything about institutional documents</p>
                  <p className="text-sm text-muted" style={{ marginTop: 4 }}>💡 Start typing to see suggested questions</p>
                  {canPost && (
                    <p className="text-sm" style={{ marginTop: 12, color: 'var(--primary)' }}>
                      💡 Type <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>@Announcement your message</code> to post an announcement
                    </p>
                  )}
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
              {/* @ Command Suggestions (Admin/Faculty only) */}
              {showAtCommands && canPost && (
                <div className="autocomplete-dropdown at-commands-dropdown" ref={atCommandsRef}>
                  <div className="autocomplete-section">
                    <AtSign size={12} /> Commands
                  </div>
                  {AT_COMMANDS
                    .filter(c => c.cmd.toLowerCase().startsWith(input.trim().toLowerCase()))
                    .map((cmd, i) => (
                    <div
                      key={cmd.cmd}
                      className={`autocomplete-item at-command-item ${i === atCommandIndex ? 'active' : ''}`}
                      onMouseEnter={() => setAtCommandIndex(i)}
                      onMouseDown={(e) => { e.preventDefault(); selectAtCommand(cmd.cmd); }}
                    >
                      <span style={{ fontSize: 18, marginRight: 8 }}>{cmd.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: 'var(--primary)' }}>{cmd.cmd}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{cmd.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Regular Suggestions */}
              {!showAtCommands && showSuggestions && allSuggestions().length > 0 && (
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
                  placeholder={isRecording ? "Listening..." : (canPost ? "Ask a question or type @Announcement..." : "Ask a question about institutional documents...")}
                  disabled={loading || isRecording}
                  autoComplete="off"
                />
                <button 
                  className={`btn ${isRecording ? 'btn-danger' : 'btn-outline'}`} 
                  onClick={toggleRecording} 
                  disabled={loading} 
                  title={isRecording ? "Stop recording" : "Record voice message"}
                  style={{ padding: '0 12px' }}
                >
                  <Mic size={18} className={isRecording ? "animate-pulse" : ""} />
                </button>
                <button className="btn btn-primary" onClick={() => handleSend()} disabled={loading || !input.trim() || isRecording}>
                  <Send size={18} />
                </button>
              </div>
            </div>
          </>
        )}

        {/* ── Announcements View ── */}
        {activeView === 'announcements' && (
          <div className="chatpage-announcements-view">
            {announcements.length === 0 ? (
              <div className="text-center text-muted" style={{ marginTop: '20vh' }}>
                <Megaphone size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
                <h3>No Announcements Yet</h3>
                <p className="text-sm" style={{ marginTop: 8 }}>
                  {canPost
                    ? 'Type @Announcement in chat to create the first one!'
                    : 'Check back later for institutional updates.'}
                </p>
              </div>
            ) : (
              <div className="chatpage-announcements-list">
                {announcements.map((ann, idx) => (
                  <div key={ann.id} className={`chatpage-announcement-card ${idx === 0 ? 'latest' : ''}`}>
                    <div className="chatpage-announcement-header">
                      <div className="chatpage-announcement-avatar">
                        {ann.author_name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <div className="chatpage-announcement-meta">
                        <strong>{ann.author_name}</strong>
                        <span className="text-muted text-sm">
                          {new Date(ann.created_at).toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', year: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {idx === 0 && <span className="chatpage-announcement-latest-badge">Latest</span>}
                        {(isAdmin || user?.id === ann.user_id) && (
                          <button 
                            className="btn btn-ghost btn-sm" 
                            style={{ padding: '4px', color: 'var(--error)' }}
                            onClick={() => handleDeleteAnnouncement(ann.id)}
                            title="Delete Announcement"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="chatpage-announcement-body">
                      {ann.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
