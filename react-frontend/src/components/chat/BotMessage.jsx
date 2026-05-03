import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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

export default function BotMessage({ content, sources = [], citations = '', timestamp, traceId = null, routeMode = '', onFeedback = null, isStreaming = false }) {
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
      className="flex gap-3"
    >
      <img
        src={CHATBOT_LOGO_URL}
        alt="AstroBot logo"
        className="astro-glow-cyan mt-1 h-20 w-20 shrink-0 rounded-full border border-cyan-300/30 object-cover"
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
        <div className="astro-glass-heavy max-w-3xl rounded-2xl rounded-tl-sm border border-white/20 p-4 text-slate-50 md:p-5 shadow-lg">
          <div className="prose prose-sm md:prose-base prose-invert max-w-none prose-headings:text-cyan-100 prose-headings:font-bold prose-p:text-slate-200 prose-p:leading-relaxed prose-a:text-cyan-300 hover:prose-a:text-cyan-100 prose-a:transition-colors prose-a:decoration-cyan-500/30 hover:prose-a:decoration-cyan-400 prose-strong:text-white prose-strong:font-semibold prose-code:text-cyan-200 prose-code:bg-cyan-950/40 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none prose-pre:bg-[#0f172a] prose-pre:border prose-pre:border-white/10 prose-pre:shadow-inner prose-blockquote:border-l-cyan-500 prose-blockquote:bg-cyan-950/20 prose-blockquote:px-4 prose-blockquote:py-1 prose-blockquote:rounded-r-lg prose-blockquote:text-slate-300 prose-blockquote:not-italic prose-li:marker:text-cyan-500 prose-ul:my-2 prose-ol:my-2 prose-table:border-collapse prose-table:w-full prose-table:overflow-hidden prose-table:rounded-lg prose-th:bg-cyan-900/40 prose-th:text-cyan-100 prose-th:font-semibold prose-th:p-3 prose-th:border prose-th:border-white/10 prose-td:p-3 prose-td:border prose-td:border-white/5 prose-td:text-slate-300 prose-tr:border-b prose-tr:border-white/5 even:prose-tr:bg-white/[0.02] hover:prose-tr:bg-white/[0.04] prose-tr:transition-colors">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            {isStreaming && (
              <motion.span
                aria-label="Streaming"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="ml-1 inline-block h-3.5 w-3.5 align-middle rounded-full border-2 border-cyan-300/35 border-t-cyan-300"
              />
            )}
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
                    <div className="mt-1 text-[11px] uppercase tracking-[0.12em] text-white">
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
