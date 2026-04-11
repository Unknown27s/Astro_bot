import { useState, useRef, useEffect } from 'react';
import { Send, Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatInputArea({
  onSendMessage,
  onRecordVoice,
  onInputChange,
  loading = false,
  recording = false,
  inputValue,
  suggestions = [],
}) {
  const [internalMessage, setInternalMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const voiceEnabled = typeof onRecordVoice === 'function';
  const isControlled = typeof inputValue === 'string';
  const message = isControlled ? inputValue : internalMessage;

  const updateMessage = (nextValue) => {
    if (isControlled) {
      onInputChange?.(nextValue);
      return;
    }

    setInternalMessage(nextValue);
    onInputChange?.(nextValue);
  };

  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message);
      updateMessage('');
      setShowSuggestions(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (text) => {
    updateMessage(text);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="astro-glass-heavy rounded-2xl border border-white/20 p-3 md:p-4">
      {/* Suggestions Dropdown */}
      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            ref={suggestionsRef}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.2 }}
            className="astro-scrollbar mb-3 max-h-48 overflow-y-auto rounded-xl border border-white/20 bg-slate-950/78"
            role="listbox"
            aria-label="Suggested prompts"
          >
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion.text)}
                className="w-full border-b border-white/10 px-4 py-2 text-left text-sm transition-colors last:border-b-0 hover:bg-white/10"
                type="button"
                role="option"
              >
                <div className="font-medium text-slate-50">{suggestion.text}</div>
                {suggestion.category && (
                  <div className="mt-0.5 text-xs text-cyan-100">{suggestion.category}</div>
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="flex items-end gap-3">
        {/* Text Input */}
        <div className="flex-1">
          <textarea
            ref={inputRef}
            value={message}
            onChange={(e) => {
              updateMessage(e.target.value);
              setShowSuggestions(e.target.value.length > 0);
            }}
            onFocus={() => message.length > 0 && setShowSuggestions(true)}
            onKeyDown={handleKeyPress}
            placeholder="Ask me anything about the college..."
            disabled={loading || recording}
            className="w-full resize-none rounded-xl border border-white/25 bg-black/35 px-4 py-3 text-slate-50 placeholder-slate-200/90 transition-all duration-200 focus:border-cyan-300/80 focus:outline-none focus:ring-2 focus:ring-cyan-300/35 disabled:opacity-50"
            rows="3"
            maxLength={500}
            aria-label="Message input"
          />
          <div className="mt-1 text-right text-xs text-slate-200/95">
            {message.length}/500
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-2">
          {voiceEnabled && (
            <button
              onClick={() => onRecordVoice?.()}
              type="button"
              disabled={loading}
              className={`rounded-xl border p-3 text-slate-50 transition-all duration-200 ${recording
                ? 'border-red-300/70 bg-red-500/30 hover:bg-red-500/35'
                : 'border-white/25 bg-white/10 hover:bg-white/15'} disabled:cursor-not-allowed disabled:opacity-50`}
              title={recording ? 'Stop voice input' : 'Start voice input'}
              aria-label={recording ? 'Stop voice input' : 'Start voice input'}
            >
              <Mic className="h-5 w-5" />
            </button>
          )}

          <button
            onClick={handleSendMessage}
            disabled={!message.trim() || loading || recording}
            type="button"
            className="astro-glow-cyan flex items-center justify-center rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 p-3 text-slate-900 transition-all duration-200 hover:scale-[1.04] active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Send message"
          >
            {loading ? (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-900/25 border-t-slate-900" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
