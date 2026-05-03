import { useState, useEffect, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import BotMessage from './BotMessage';
import UserMessage from './UserMessage';
import ChatInputArea from './ChatInputArea';
import ChatSidebar from './ChatSidebar';
import { useAuth } from '../../context/AuthContext';
import { sendChat, streamChat, sendAudioMessage, getAnnouncements, getSuggestions, submitFeedback } from '../../services/api';
import chatbotLogo from '../../assets/astrobot-logo.svg';

const CHATBOT_LOGO_URL = '/astrobot-logo.png';

const getWelcomeMessage = () => ({
  id: `welcome-${Date.now()}`,
  type: 'bot',
  content: "Welcome to AstroBot. I can help you with schedules, policies, departments, and campus guidance with cited institutional sources.",
  sources: [],
  timestamp: new Date().toISOString(),
});

const buildId = () => `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
const STREAM_WAITING_TEXTS = [
  'Thinking through your request...',
  'Gathering the best answer...',
  'Checking relevant sources...',
  'Preparing a clear response...',
];
const isStreamWaitingText = (value) => STREAM_WAITING_TEXTS.includes(value);

const mergeSuggestionGroups = (result, includeAnnouncementCommand, query) => {
  const items = [];
  const seen = new Set();

  const appendGroup = (values, category) => {
    (Array.isArray(values) ? values : []).forEach((value) => {
      if (typeof value !== 'string') return;
      const text = value.trim();
      if (!text) return;
      const dedupeKey = text.toLowerCase();
      if (seen.has(dedupeKey)) return;
      seen.add(dedupeKey);
      items.push({ text, category });
    });
  };

  appendGroup(result?.recent, 'Recent');
  appendGroup(result?.popular, 'Popular');
  appendGroup(result?.document_based, 'From Uploaded Docs');
  appendGroup(result?.preset, 'Suggested');

  const normalizedQuery = query.trim().toLowerCase();
  const showAnnouncementCommand =
    includeAnnouncementCommand &&
    normalizedQuery.length > 0 &&
    (normalizedQuery.startsWith('@') || '@announcement'.startsWith(normalizedQuery) || normalizedQuery.includes('announce'));

  if (showAnnouncementCommand && !seen.has('@announcement')) {
    items.unshift({
      text: '@Announcement ',
      category: 'Faculty/Admin Command',
    });
  }

  return items.slice(0, 8);
};

export default function ChatLayout() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [messages, setMessages] = useState([getWelcomeMessage()]);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [inputText, setInputText] = useState('');
  const [liveSuggestions, setLiveSuggestions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [conversations, setConversations] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [activeView, setActiveView] = useState('chat');
  const [activeAnnouncementId, setActiveAnnouncementId] = useState(null);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [waitingTextIndex, setWaitingTextIndex] = useState(0);
  const messagesEndRef = useRef(null);
  const hydratedRef = useRef(false);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const suggestionsRequestIdRef = useRef(0);
  const streamControllerRef = useRef(null);

  const currentUser = useMemo(() => {
    try {
      const user = JSON.parse(localStorage.getItem('astrobot_user') || '{}');
      return {
        id: user?.id || 'guest',
        username: user?.username || 'Guest',
        role: user?.role || 'student',
      };
    } catch {
      return {
        id: user?.id || 'guest',
        username: user?.username || 'Guest',
        role: user?.role || 'student',
      };
    }
  }, [user]);

  const canUseAnnouncementCommand = currentUser.role === 'admin' || currentUser.role === 'faculty';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!loading) {
      setWaitingTextIndex(0);
      return;
    }

    const timer = setInterval(() => {
      setWaitingTextIndex((prev) => (prev + 1) % STREAM_WAITING_TEXTS.length);
    }, 1400);

    return () => clearInterval(timer);
  }, [loading]);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('conversations');
    if (savedConversations) {
      try {
        setConversations(JSON.parse(savedConversations));
      } catch (e) {
        console.error('Error loading conversations:', e);
      }
    }
    hydratedRef.current = true;
  }, []);

  useEffect(() => {
    if (hydratedRef.current) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (streamControllerRef.current) {
        streamControllerRef.current.abort();
      }
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    const loadAnnouncements = async () => {
      try {
        const result = await getAnnouncements(20);
        if (mounted) {
          const items = Array.isArray(result.data) ? result.data : [];
          setAnnouncements(items);
          if (items.length > 0 && !activeAnnouncementId) {
            setActiveAnnouncementId(items[0].id);
          }
        }
      } catch (error) {
        if (mounted) {
          setAnnouncements([]);
        }
      }
    };

    loadAnnouncements();
    const timer = setInterval(loadAnnouncements, 30000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [activeAnnouncementId]);

  useEffect(() => {
    if (activeView !== 'chat') {
      setLiveSuggestions([]);
      return;
    }

    const query = inputText.trim();
    if (!query) {
      setLiveSuggestions([]);
      return;
    }

    const requestId = suggestionsRequestIdRef.current + 1;
    suggestionsRequestIdRef.current = requestId;

    const timer = setTimeout(async () => {
      try {
        const result = await getSuggestions(query, currentUser.id);
        if (requestId !== suggestionsRequestIdRef.current) return;
        setLiveSuggestions(
          mergeSuggestionGroups(result.data, canUseAnnouncementCommand, query)
        );
      } catch (error) {
        if (requestId !== suggestionsRequestIdRef.current) return;
        setLiveSuggestions(mergeSuggestionGroups({}, canUseAnnouncementCommand, query));
      }
    }, 220);

    return () => clearTimeout(timer);
  }, [inputText, activeView, currentUser.id, canUseAnnouncementCommand]);

  const saveConversationTurn = (userMsg, botMsg, conversationTitleSeed) => {
    if (!currentConversationId) {
      const newConvId = buildId();
      const newConv = {
        id: newConvId,
        title: conversationTitleSeed.substring(0, 50) + (conversationTitleSeed.length > 50 ? '...' : ''),
        lastMessage: botMsg.content.substring(0, 100) + (botMsg.content.length > 100 ? '...' : ''),
        timestamp: new Date().toISOString(),
        messages: [userMsg, botMsg],
      };
      const updatedConvs = [newConv, ...conversations];
      setConversations(updatedConvs);
      localStorage.setItem('conversations', JSON.stringify(updatedConvs));
      setCurrentConversationId(newConvId);
      return;
    }

    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === currentConversationId
          ? {
            ...conv,
            lastMessage: botMsg.content.substring(0, 100) + (botMsg.content.length > 100 ? '...' : ''),
            timestamp: new Date().toISOString(),
            messages: [...(conv.messages || []), userMsg, botMsg],
          }
          : conv
      )
    );
  };

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;
    setInputText('');
    setLiveSuggestions([]);

    // Abort any previous stream
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
    }

    // Add user message
    const userMsg = {
      id: buildId(),
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    // Create a placeholder bot message for streaming
    const botMsgId = buildId();
    const botMsgPlaceholder = {
      id: botMsgId,
      type: 'bot',
      content: STREAM_WAITING_TEXTS[0],
      sources: [],
      citations: '',
      routeMode: '',
      traceId: null,
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, botMsgPlaceholder]);
    setLoading(true);

    const controller = streamChat(
      messageText,
      currentUser.id,
      currentUser.username,
      {
        onChunk: (chunk) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? {
                  ...msg,
                  content: isStreamWaitingText(msg.content) ? chunk : msg.content + chunk,
                }
                : msg
            )
          );
        },
        onDone: async (finalData) => {
          // Update the bot message with final metadata
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? {
                  ...msg,
                  sources: finalData.sources || [],
                  citations: finalData.citations || '',
                  routeMode: finalData.route_mode || '',
                  isStreaming: false,
                }
                : msg
            )
          );
          setLoading(false);
          streamControllerRef.current = null;

          // Get the final bot message for conversation saving
          setMessages((prev) => {
            const finalBotMsg = prev.find((m) => m.id === botMsgId);
            if (finalBotMsg) {
              saveConversationTurn(userMsg, finalBotMsg, messageText);
            }
            return prev;
          });

          // Refresh announcement feed when a new announcement is posted via chat command.
          if (messageText.trim().toLowerCase().startsWith('@announcement')) {
            try {
              const result = await getAnnouncements(20);
              setAnnouncements(Array.isArray(result.data) ? result.data : []);
            } catch {
              // Ignore announcement refresh errors.
            }
          }
        },
        onError: (err) => {
          console.error('Stream error:', err);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? {
                  ...msg,
                  content: msg.content || 'Sorry, I encountered an error processing your request. Please try again.',
                  isStreaming: false,
                }
                : msg
            )
          );
          setLoading(false);
          streamControllerRef.current = null;
        },
      }
    );

    streamControllerRef.current = controller;
  };

  const handleRecordVoice = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    if (!navigator.mediaDevices || !window.MediaRecorder) {
      setMessages((prev) => [...prev, {
        id: buildId(),
        type: 'bot',
        content: 'Voice input is not supported in this browser. Please use a Chromium-based browser and allow microphone access.',
        sources: [],
        timestamp: new Date().toISOString(),
      }]);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        const streamRef = mediaStreamRef.current;
        mediaStreamRef.current = null;

        if (streamRef) {
          streamRef.getTracks().forEach((track) => track.stop());
        }

        const mimeType = recorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        audioChunksRef.current = [];

        if (audioBlob.size === 0) {
          setMessages((prev) => [...prev, {
            id: buildId(),
            type: 'bot',
            content: 'No audio was captured. Please try recording again.',
            sources: [],
            timestamp: new Date().toISOString(),
          }]);
          return;
        }

        setLoading(true);
        setInputText('');
        setLiveSuggestions([]);

        try {
          const response = await sendAudioMessage(audioBlob, currentUser.id, currentUser.username);
          const transcribedText = response.data.transcribed_text || '[Voice message]';

          const userMsg = {
            id: buildId(),
            type: 'user',
            content: transcribedText,
            timestamp: new Date().toISOString(),
          };

          const botMsg = {
            id: buildId(),
            type: 'bot',
            content: response.data.response,
            sources: response.data.sources || [],
            citations: response.data.citations || '',
            routeMode: response.data.route_mode || '',
            traceId: response.data.trace_id || null,
            timestamp: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, userMsg, botMsg]);
          saveConversationTurn(userMsg, botMsg, transcribedText);
        } catch (error) {
          console.error('Error sending audio message:', error);
          setMessages((prev) => [...prev, {
            id: buildId(),
            type: 'bot',
            content: 'Unable to process voice input right now. Please try again or type your question.',
            sources: [],
            timestamp: new Date().toISOString(),
          }]);
        } finally {
          setLoading(false);
        }
      };

      recorder.onerror = () => {
        setIsRecording(false);
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
        }
        audioChunksRef.current = [];
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      setIsRecording(false);
      setMessages((prev) => [...prev, {
        id: buildId(),
        type: 'bot',
        content: 'Microphone permission was denied or unavailable. Please allow microphone access and try again.',
        sources: [],
        timestamp: new Date().toISOString(),
      }]);
    }
  };

  const handleNewChat = () => {
    setMessages([getWelcomeMessage()]);
    setCurrentConversationId(null);
    setActiveView('chat');
    setSidebarOpen(false);
  };

  const handleSelectConversation = (conversation) => {
    setCurrentConversationId(conversation.id);
    setActiveView('chat');
    // Load messages from conversation if available
    if (conversation.messages && conversation.messages.length > 0) {
      setMessages(conversation.messages);
    }
    setSidebarOpen(false);
  };

  const handleDeleteConversation = (conversationId) => {
    setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
    if (currentConversationId === conversationId) {
      handleNewChat();
    }
  };

  const handleClearHistory = () => {
    setConversations([]);
    setCurrentConversationId(null);
    setMessages([getWelcomeMessage()]);
    localStorage.removeItem('conversations');
  };

  const handleLogout = () => {
    localStorage.removeItem('conversations');
    logout();
    navigate('/login');
  };

  const handleOpenAnnouncements = () => {
    setActiveView('announcements');
    if (!activeAnnouncementId && announcements.length > 0) {
      setActiveAnnouncementId(announcements[0].id);
    }
    setSidebarOpen(false);
  };

  const handleSelectAnnouncement = (announcementId) => {
    setActiveAnnouncementId(announcementId);
    setActiveView('announcements');
    setSidebarOpen(false);
  };

  const handleOpenChat = () => {
    setActiveView('chat');
    setSidebarOpen(false);
  };

  const handleBotFeedback = async (traceId, rating) => {
    if (!traceId || !rating) return;
    try {
      await submitFeedback(traceId, rating, currentUser.id);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const selectedAnnouncement = announcements.find((item) => item.id === activeAnnouncementId) || announcements[0] || null;

  return (
    <div className="astro-chat-shell relative h-screen w-full overflow-hidden font-astro-body text-white">
      <div className="pointer-events-none absolute inset-0 astro-nebula-bg" />
      <div className="pointer-events-none absolute inset-0 astro-noise-overlay" />

      <div className="relative flex h-full">
        {/* Sidebar */}
        <ChatSidebar
          conversations={conversations}
          announcements={announcements}
          activeView={activeView}
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onOpenChat={handleOpenChat}
          onOpenAnnouncements={handleOpenAnnouncements}
          onSelectAnnouncement={handleSelectAnnouncement}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
          onClearHistory={handleClearHistory}
          onLogout={handleLogout}
          isOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Main Chat Area */}
        <main className="flex min-w-0 flex-1 flex-col overflow-hidden" aria-label="Chat workspace">
          {/* Header */}
          <header className="astro-glass border-b border-white/10 px-4 py-4 shadow-[0_12px_40px_rgba(0,0,0,0.25)] md:px-8">
            <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <img
                  src={CHATBOT_LOGO_URL}
                  alt="AstroBot logo"
                  className="h-11 w-11 rounded-xl border border-cyan-300/30 object-cover"
                  onError={(event) => {
                    event.currentTarget.onerror = null;
                    event.currentTarget.src = chatbotLogo;
                  }}
                />
                <div>
                  <h1 className="font-astro-headline text-xl font-extrabold tracking-tight text-white md:text-2xl">
                    {activeView === 'announcements' ? 'Announcements' : 'Academic Concierge'}
                  </h1>
                  <p className="text-xs uppercase tracking-[0.24em] text-cyan-200/90">
                    {activeView === 'announcements' ? 'Institution Broadcasts' : 'Rajalakshmi Institute of Technology'}
                  </p>
                </div>
              </div>
              <div className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-right">
                {activeView === 'announcements' ? (
                  <div className="inline-flex items-center gap-2 text-xs font-semibold text-cyan-100">
                    <Bell size={14} />
                    {announcements.length} Updates
                  </div>
                ) : (
                  <>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-200/75">Signed In</p>
                    <p className="text-sm font-semibold text-slate-100">{currentUser.username}</p>
                  </>
                )}
              </div>
            </div>
          </header>

          {activeView === 'chat' ? (
            <>
              {/* Messages Container */}
              <div className="astro-scrollbar flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8">
                <div className="mx-auto w-full max-w-5xl space-y-8">
                  {messages.length === 1 && messages[0].type === 'bot' && !currentConversationId && (
                    <section className="grid grid-cols-1 gap-4">
                      <div className="astro-glass-heavy relative overflow-hidden rounded-3xl border border-cyan-200/20 p-6">
                        <div className="pointer-events-none absolute -right-10 -top-10 h-44 w-44 rounded-full bg-cyan-300/20 blur-3xl" />
                        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-cyan-300/10 px-2 py-1 text-[11px] text-cyan-100">
                          <img
                            src={CHATBOT_LOGO_URL}
                            alt="AstroBot logo"
                            className="h-5 w-5 rounded-full object-cover"
                            onError={(event) => {
                              event.currentTarget.onerror = null;
                              event.currentTarget.src = chatbotLogo;
                            }}
                          />
                          System Ready
                        </div>
                        <h2 className="mt-2 font-astro-headline text-2xl font-extrabold tracking-tight text-white md:text-3xl">Welcome to AstroBot</h2>
                        <p className="mt-3 max-w-2xl text-sm text-slate-100 md:text-base">
                          Ask about institutional policies, exam schedules, departments, library resources, and campus services.
                          I respond with grounded answers and source references.
                        </p>
                        <div className="mt-5 flex flex-wrap gap-2">
                          {[
                            'Show exam alerts',
                            'Find placement statistics',
                            'Locate Innovation Lab',
                          ].map((prompt) => (
                            <button
                              key={prompt}
                              onClick={() => handleSendMessage(prompt)}
                              disabled={loading}
                              className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-100 transition-all hover:border-cyan-300/70 hover:bg-cyan-300/10 disabled:cursor-not-allowed disabled:opacity-60"
                              type="button"
                            >
                              {prompt}
                            </button>
                          ))}
                        </div>
                      </div>
                    </section>
                  )}

                  <div className="space-y-6">
                    {messages.map((msg) => (
                      <div key={msg.id}>
                        {msg.type === 'bot' ? (
                          <BotMessage
                            content={msg.isStreaming && isStreamWaitingText(msg.content)
                              ? STREAM_WAITING_TEXTS[waitingTextIndex]
                              : msg.content}
                            sources={msg.sources}
                            citations={msg.citations}
                            routeMode={msg.routeMode}
                            traceId={msg.traceId}
                            timestamp={msg.timestamp}
                            userId={currentUser.id}
                            onFeedback={handleBotFeedback}
                            isStreaming={msg.isStreaming}
                          />
                        ) : (
                          <UserMessage
                            content={msg.content}
                            username={currentUser.username}
                            timestamp={msg.timestamp}
                          />
                        )}
                      </div>
                    ))}

                    <div ref={messagesEndRef} />
                  </div>
                </div>
              </div>

              {/* Input Area */}
              <div className="px-3 pb-3 md:px-6 md:pb-5">
                <ChatInputArea
                  onSendMessage={handleSendMessage}
                  onRecordVoice={handleRecordVoice}
                  onInputChange={setInputText}
                  inputValue={inputText}
                  loading={loading}
                  recording={isRecording}
                  suggestions={liveSuggestions}
                />
              </div>
            </>
          ) : (
            <div className="astro-scrollbar flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8">
              <div className="mx-auto grid w-full max-w-5xl gap-4 lg:grid-cols-[1.1fr_1.4fr]">
                <section className="astro-glass-heavy rounded-2xl border border-white/10 p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-cyan-200/80">Feed</h3>
                  <div className="mt-3 space-y-2">
                    {announcements.length === 0 ? (
                      <p className="rounded-xl border border-dashed border-white/15 bg-white/5 p-4 text-sm text-slate-200/85">
                        No announcements available.
                      </p>
                    ) : (
                      announcements.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleSelectAnnouncement(item.id)}
                          type="button"
                          className={`w-full rounded-xl border p-3 text-left transition ${selectedAnnouncement?.id === item.id
                            ? 'border-cyan-300/70 bg-cyan-300/10'
                            : 'border-white/10 bg-white/5 hover:bg-white/10'
                            }`}
                        >
                          <p className="line-clamp-2 text-sm font-semibold text-slate-100">{item.content}</p>
                          <div className="mt-2 flex items-center justify-between gap-2 text-xs text-slate-300/85">
                            <span>{item.author_name || 'Faculty'}</span>
                            <span>{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </section>

                <section className="astro-glass-heavy rounded-2xl border border-white/10 p-5">
                  {selectedAnnouncement ? (
                    <>
                      <div className="mb-3 flex items-center gap-2">
                        <img
                          src={CHATBOT_LOGO_URL}
                          alt="AstroBot logo"
                          className="h-7 w-7 rounded-full object-cover"
                          onError={(event) => {
                            event.currentTarget.onerror = null;
                            event.currentTarget.src = chatbotLogo;
                          }}
                        />
                        <p className="text-xs uppercase tracking-[0.16em] text-cyan-200/85">Announcement Detail</p>
                      </div>
                      <h4 className="text-lg font-bold leading-relaxed text-white">{selectedAnnouncement.content}</h4>
                      <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200/95">
                        <p><span className="font-semibold text-cyan-100">Author:</span> {selectedAnnouncement.author_name || 'Faculty'}</p>
                        <p className="mt-1"><span className="font-semibold text-cyan-100">Posted:</span> {selectedAnnouncement.created_at ? new Date(selectedAnnouncement.created_at).toLocaleString() : ''}</p>
                      </div>
                    </>
                  ) : (
                    <p className="rounded-xl border border-dashed border-white/15 bg-white/5 p-4 text-sm text-slate-200/85">
                      Select an announcement to view details.
                    </p>
                  )}
                </section>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
