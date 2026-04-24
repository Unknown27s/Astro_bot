import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useState } from 'react';
import chatbotLogo from '../../assets/astrobot-logo.svg';

const CHATBOT_LOGO_URL = '/astrobot-logo.png';

const ROUTE_LABELS = {
  general_chat: 'General Chat',
  faq: 'FAQ',
  document: 'Document',
  official_site: 'Official Site',
  hybrid: 'Hybrid',
  unclear: 'Auto',
};

export default function BotMessage({ content, sources = [], citations = '', timestamp, traceId = null, routeMode = '', onFeedback = null }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedbackClick = async (value) => {
    setFeedback(value > 0);
    if (onFeedback && traceId) {
      await onFeedback(traceId, value);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-6 flex gap-3"
    >
      <img
        src={CHATBOT_LOGO_URL}
        alt="AstroBot logo"
        className="astro-glow-cyan mt-1 h-10 w-10 shrink-0 rounded-full border border-cyan-300/30 object-cover"
        onError={(event) => {
          event.currentTarget.onerror = null;
          event.currentTarget.src = chatbotLogo;
        }}
      />
      <div className="flex-1 space-y-3">
        <div className="flex items-center gap-2">
          <span className="font-astro-headline text-sm font-bold tracking-wide text-cyan-100">ASTROBOT</span>
          {routeMode && (
            <span className="rounded-full border border-cyan-200/35 bg-cyan-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-cyan-100">
              {ROUTE_LABELS[routeMode] || routeMode}
            </span>
          )}
          {timestamp && (
            <span className="text-xs text-slate-200/90">
              {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>

        {/* Main Message */}
        <div className="astro-glass-heavy max-w-3xl rounded-2xl rounded-tl-sm border border-cyan-100/20 p-4 text-slate-50 md:p-5">
          <div className="prose prose-sm max-w-none prose-headings:text-cyan-100 prose-strong:text-white prose-p:text-slate-50 prose-a:text-cyan-200 prose-code:text-cyan-100">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>

        {/* Sources */}
        {sources && sources.length > 0 && (
          <details className="group max-w-3xl cursor-pointer text-sm">
            <summary className="inline-flex items-center gap-2 rounded-full border border-cyan-200/25 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-100 transition-colors hover:bg-cyan-300/20">
              Sources {sources.length}
            </summary>
            <div className="mt-3 space-y-2">
              {sources.slice(0, 3).map((source, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs text-slate-50"
                >
                  <div className="font-semibold text-cyan-100">
                    {source.source || 'Source ' + (idx + 1)}
                  </div>
                  {source.heading && <div className="mt-1 text-slate-100">{source.heading}</div>}
                  {typeof source.score === 'number' && (
                    <div className="mt-1 text-[11px] uppercase tracking-[0.12em] text-cyan-200/85">
                      Relevance {(source.score * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}

        {citations && (
          <div className="max-w-3xl rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-100">
            <span className="font-semibold text-cyan-100">Citations:</span> {citations}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={copyToClipboard}
            className="rounded-lg p-1.5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
            title="Copy"
          >
            <Copy className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleFeedbackClick(1)}
            className={`rounded-lg p-1.5 transition-colors ${feedback === true ? 'bg-emerald-400/20 text-emerald-200' : 'text-slate-300 hover:bg-emerald-400/10 hover:text-emerald-100'
              }`}
            title="Helpful"
          >
            <ThumbsUp className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleFeedbackClick(-1)}
            className={`rounded-lg p-1.5 transition-colors ${feedback === false ? 'bg-red-400/20 text-red-200' : 'text-slate-300 hover:bg-red-400/10 hover:text-red-100'
              }`}
            title="Not helpful"
          >
            <ThumbsDown className="h-4 w-4" />
          </button>
          {copied && <span className="text-xs font-medium text-emerald-200">Copied</span>}
        </div>
      </div>
    </motion.div>
  );
}
