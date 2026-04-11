import { useMemo, useState } from 'react';
import {
  Bell,
  MessageCircle,
  Clock,
  LogOut,
  Menu,
  MessageSquarePlus,
  Newspaper,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import chatbotLogo from '../../assets/astrobot-logo.svg';

const CHATBOT_LOGO_URL = '/astrobot-logo.png';

export default function ChatSidebar({
  conversations = [],
  announcements = [],
  activeView = 'chat',
  currentConversationId,
  onSelectConversation,
  onOpenChat,
  onOpenAnnouncements,
  onSelectAnnouncement,
  onNewChat,
  onDeleteConversation,
  onClearHistory,
  onLogout,
  isOpen,
  onToggleSidebar,
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = useMemo(() => {
    if (searchQuery.trim() === '') {
      return conversations;
    }

    return conversations.filter((conv) =>
      conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.lastMessage?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery, conversations]);

  const handleDeleteConversation = (e, convId) => {
    e.stopPropagation();
    onDeleteConversation?.(convId);
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all conversations?')) {
      onClearHistory?.();
    }
  };

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={onToggleSidebar}
        className="fixed left-4 top-4 z-50 rounded-xl border border-white/25 bg-slate-950/70 p-2 text-slate-100 backdrop-blur md:hidden"
        type="button"
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-white/10 bg-slate-950/50 p-4 backdrop-blur-2xl transition-transform duration-300 md:static md:z-0 md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="astro-glass flex h-full flex-col rounded-2xl border border-white/10">
          {/* Header */}
          <div className="mt-12 border-b border-white/10 px-4 pb-4 pt-2 md:mt-0 md:pt-5">
            <div className="flex items-center gap-3">
              <img
                src={CHATBOT_LOGO_URL}
                alt="AstroBot logo"
                className="astro-glow-cyan h-10 w-10 rounded-xl border border-cyan-300/35 object-cover"
                onError={(event) => {
                  event.currentTarget.onerror = null;
                  event.currentTarget.src = chatbotLogo;
                }}
              />
              <div>
                <h2 className="font-astro-headline text-lg font-extrabold tracking-tight text-white">AstroBot</h2>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-200/80">Status Online</p>
              </div>
            </div>

            <button
              onClick={onNewChat}
              type="button"
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400/85 to-blue-500/90 px-4 py-2.5 text-sm font-bold text-slate-950 transition-transform hover:scale-[1.01]"
            >
              <MessageSquarePlus size={16} />
              New Chat
            </button>

            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={onOpenChat}
                className={`inline-flex items-center justify-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold transition ${activeView === 'chat'
                  ? 'border-cyan-300/70 bg-cyan-300/15 text-cyan-100'
                  : 'border-white/15 bg-white/5 text-slate-200 hover:bg-white/10'
                  }`}
              >
                <MessageCircle size={13} />
                Chat
              </button>
              <button
                type="button"
                onClick={onOpenAnnouncements}
                className={`inline-flex items-center justify-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold transition ${activeView === 'announcements'
                  ? 'border-cyan-300/70 bg-cyan-300/15 text-cyan-100'
                  : 'border-white/15 bg-white/5 text-slate-200 hover:bg-white/10'
                  }`}
              >
                <Newspaper size={13} />
                Announcements
              </button>
            </div>
          </div>

          <div className="border-b border-white/10 px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200/75">Conversation History</p>
          </div>

          {/* Search */}
          <div className="px-3 py-3">
            <label className="relative block">
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
              <input
                type="text"
                placeholder="Search conversations"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-white/20 bg-white/5 py-2 pl-9 pr-3 text-sm text-white placeholder:text-slate-300/80 focus:border-cyan-300/70 focus:outline-none"
              />
            </label>
          </div>

          {/* Conversations List */}
          <div className="astro-scrollbar flex-1 overflow-y-auto px-3 pb-2">
            {filteredConversations.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/20 bg-white/5 p-4 text-center text-sm text-slate-300/85">
                {searchQuery ? 'No conversations found.' : 'No chats yet. Start your first conversation.'}
              </div>
            ) : (
              <div className="space-y-2">
                {filteredConversations.map((conv, idx) => {
                  const active = conv.id === currentConversationId;
                  return (
                    <button
                      key={conv.id || idx}
                      onClick={() => onSelectConversation(conv)}
                      type="button"
                      className={`group w-full rounded-xl border p-3 text-left transition-all ${active
                        ? 'border-cyan-300/70 bg-cyan-300/15'
                        : 'border-white/10 bg-white/5 hover:border-white/30 hover:bg-white/10'
                        }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <h3 className="truncate text-sm font-semibold text-white">{conv.title || 'Untitled Chat'}</h3>
                          <p className="mt-1 truncate text-xs text-slate-200/75">{conv.lastMessage || 'No messages yet'}</p>
                          {conv.timestamp && (
                            <div className="mt-1 flex items-center gap-1 text-[11px] text-slate-300/70">
                              <Clock size={11} />
                              {new Date(conv.timestamp).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        <span
                          onClick={(e) => handleDeleteConversation(e, conv.id)}
                          className="rounded-md p-1 text-slate-300 opacity-0 transition-all hover:bg-red-500/20 hover:text-red-200 group-hover:opacity-100"
                          role="button"
                          aria-label="Delete conversation"
                        >
                          <Trash2 size={14} />
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="mt-4 border-t border-white/10 pt-4">
              <div className="mb-2 flex items-center justify-between px-1">
                <p className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-cyan-200/75">
                  <Bell size={12} />
                  Announcements
                </p>
                <span className="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-100">
                  {announcements.length}
                </span>
              </div>

              {announcements.length === 0 ? (
                <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-3 text-xs text-slate-300/80">
                  No announcements yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {announcements.slice(0, 4).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => onSelectAnnouncement?.(item.id)}
                      className="w-full rounded-xl border border-white/10 bg-white/5 p-3 text-left transition hover:bg-white/10"
                    >
                      <p className="line-clamp-2 text-xs font-semibold leading-relaxed text-slate-100">
                        {item.content}
                      </p>
                      <div className="mt-1 flex items-center justify-between gap-2">
                        <span className="truncate text-[10px] uppercase tracking-[0.12em] text-cyan-200/80">
                          {item.author_name || 'Faculty'}
                        </span>
                        <span className="text-[10px] text-slate-300/75">
                          {item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="space-y-3 border-t border-white/10 px-4 py-4">
            <button
              onClick={onLogout}
              type="button"
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-rose-300/25 bg-rose-400/10 px-3 py-2 text-sm font-semibold text-rose-100 transition-colors hover:bg-rose-400/20"
              aria-label="Logout"
            >
              <LogOut size={14} />
              Logout
            </button>
            <button
              onClick={handleClearHistory}
              type="button"
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-red-300/25 bg-red-400/10 px-3 py-2 text-sm font-semibold text-red-100 transition-colors hover:bg-red-400/20"
              aria-label="Clear conversation history"
            >
              <Trash2 size={14} />
              Clear History
            </button>
            <p className="text-center text-[11px] uppercase tracking-[0.16em] text-slate-300/70">
              {conversations.length} Conversation{conversations.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          onClick={onToggleSidebar}
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
        />
      )}
    </>
  );
}
