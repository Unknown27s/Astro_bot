import { useState, useEffect } from 'react';
import { getSettings, updateSettings, testProvider } from '../../services/api';
import { Save, Zap, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState({});
  const [testing, setTesting] = useState({});
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    getSettings().then(r => {
      setSettings(r.data);
      setForm(r.data);
    }).catch(() => toast.error('Failed to load settings'));
  }, []);

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSave = async () => {
    // Build payload with only changed fields using snake_case for Python API
    const payload = {};
    if (form.llm_mode !== settings.llm_mode) payload.llm_mode = form.llm_mode;
    if (form.primary_provider !== settings.primary_provider) payload.primary_provider = form.primary_provider;
    if (form.fallback_provider !== settings.fallback_provider) payload.fallback_provider = form.fallback_provider;
    if (form.ollama_base_url !== settings.ollama_base_url) payload.ollama_base_url = form.ollama_base_url;
    if (form.ollama_model !== settings.ollama_model) payload.ollama_model = form.ollama_model;
    if (form.groq_api_key) payload.groq_api_key = form.groq_api_key;
    if (form.groq_model !== settings.groq_model) payload.groq_model = form.groq_model;
    if (form.gemini_api_key) payload.gemini_api_key = form.gemini_api_key;
    if (form.gemini_model !== settings.gemini_model) payload.gemini_model = form.gemini_model;
    if (form.temperature !== settings.temperature) payload.temperature = form.temperature;
    if (form.max_tokens !== settings.max_tokens) payload.max_tokens = form.max_tokens;
    if (form.system_prompt !== settings.system_prompt) payload.system_prompt = form.system_prompt;

    if (!Object.keys(payload).length) return toast('No changes to save');
    try {
      await updateSettings(payload);
      toast.success('Settings saved!');
      // Refresh
      const r = await getSettings();
      setSettings(r.data);
      setForm(r.data);
    } catch {
      toast.error('Failed to save settings');
    }
  };

  const handleTest = async (provider) => {
    setTesting(prev => ({ ...prev, [provider]: true }));
    setTestResults(prev => ({ ...prev, [provider]: null }));
    try {
      const { data } = await testProvider(provider);
      setTestResults(prev => ({ ...prev, [provider]: data }));
      if (data.status === 'ok') toast.success(`${provider} connected!`);
      else toast.error(`${provider}: ${data.message}`);
    } catch {
      setTestResults(prev => ({ ...prev, [provider]: { status: 'error', message: 'Connection failed' } }));
      toast.error(`${provider} test failed`);
    }
    setTesting(prev => ({ ...prev, [provider]: false }));
  };

  if (!settings) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading AI settings">
        {[1, 2, 3].map((idx) => (
          <section key={idx} className="astro-glass rounded-2xl border border-white/10 p-5 md:p-6 animate-pulse">
            <div className="h-5 w-40 rounded bg-white/10" />
            <div className="mt-4 space-y-2">
              <div className="h-10 rounded-xl bg-white/5" />
              <div className="h-10 rounded-xl bg-white/5" />
            </div>
          </section>
        ))}
      </div>
    );
  }

  const StatusIcon = ({ result }) => {
    if (!result) return null;
    return result.status === 'ok'
      ? <CheckCircle size={16} style={{ color: 'var(--success)' }} />
      : <XCircle size={16} style={{ color: 'var(--error)' }} />;
  };

  const cardClass = 'astro-glass rounded-2xl border border-white/10 p-5 md:p-6';
  const inputClass = 'w-full rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none';
  const labelClass = 'mb-1 block text-xs uppercase tracking-[0.12em] text-slate-300/80';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-astro-headline text-2xl font-extrabold tracking-tight text-white">AI Settings</h2>
          <p className="text-sm text-slate-300/85">Configure providers, generation settings, and system prompt.</p>
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2.5 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02]"
          onClick={handleSave}
          type="button"
          aria-label="Save AI settings"
        >
          <Save size={16} /> Save Settings
        </button>
      </div>

      <section className={cardClass}>
        <h3 className="text-lg font-semibold text-white">LLM Mode</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {['local_only', 'cloud_only', 'hybrid'].map(mode => (
            <button
              key={mode}
              className={`rounded-xl border px-3 py-2 text-sm font-semibold transition-colors ${form.llm_mode === mode
                ? 'border-cyan-300/70 bg-cyan-300/15 text-white'
                : 'border-white/20 bg-white/5 text-slate-200 hover:bg-white/10'
                }`}
              onClick={() => update('llm_mode', mode)}
              type="button"
              aria-label={`Set LLM mode to ${mode}`}
            >
              {mode === 'local_only' ? 'Local Only' : mode === 'cloud_only' ? 'Cloud Only' : 'Hybrid'}
            </button>
          ))}
        </div>
        <p className="mt-2 text-sm text-slate-300/85">
          {form.llm_mode === 'local_only' && 'Uses Ollama local provider only.'}
          {form.llm_mode === 'cloud_only' && 'Uses cloud providers with primary-to-fallback routing.'}
          {form.llm_mode === 'hybrid' && 'Uses primary provider, then fallback, then Ollama as final fallback.'}
        </p>
        {form.llm_mode === 'local_only' && (
          <p className="mt-1 text-xs text-amber-200/90">
            Primary and fallback provider selections are ignored in Local Only mode.
          </p>
        )}
      </section>

      {form.llm_mode !== 'local_only' && (
        <section className={cardClass}>
          <h3 className="text-lg font-semibold text-white">Provider Priority</h3>
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className={labelClass}>Primary Provider</label>
              <select className={inputClass} value={form.primary_provider || 'ollama'} onChange={e => update('primary_provider', e.target.value)}>
                <option value="ollama">Ollama (Local)</option>
                <option value="groq">Groq</option>
                <option value="gemini">Gemini (Google)</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Fallback Provider</label>
              <select className={inputClass} value={form.fallback_provider || 'none'} onChange={e => update('fallback_provider', e.target.value)}>
                <option value="none">None</option>
                <option value="ollama">Ollama (Local)</option>
                <option value="groq">Groq</option>
                <option value="gemini">Gemini (Google)</option>
              </select>
            </div>
          </div>
        </section>
      )}

      <section className={cardClass}>
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">Ollama (Local)</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.ollama} />
            <button
              className="inline-flex items-center gap-1 rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 hover:bg-white/10"
              onClick={() => handleTest('ollama')}
              disabled={testing.ollama}
              type="button"
              aria-label="Test Ollama connection"
            >
              {testing.ollama ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label className={labelClass}>Base URL</label>
            <input className={inputClass} value={form.ollama_base_url || ''} onChange={e => update('ollama_base_url', e.target.value)} placeholder="http://localhost:11434" />
          </div>
          <div>
            <label className={labelClass}>Model Name</label>
            <input className={inputClass} value={form.ollama_model || ''} onChange={e => update('ollama_model', e.target.value)} placeholder="qwen3:0.6b" />
          </div>
        </div>
        {testResults.ollama?.models && (
          <p className="mt-3 text-sm text-slate-300/85">Available models: {testResults.ollama.models.join(', ')}</p>
        )}
      </section>

      <section className={cardClass}>
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">Groq</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.groq} />
            <button
              className="inline-flex items-center gap-1 rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 hover:bg-white/10"
              onClick={() => handleTest('groq')}
              disabled={testing.groq}
              type="button"
              aria-label="Test Groq connection"
            >
              {testing.groq ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label className={labelClass}>API Key {settings?.groq_api_key_set && <span className="ml-1 text-emerald-200">(set)</span>}</label>
            <input
              className={inputClass}
              type="password"
              value={form.groq_api_key || ''}
              onChange={e => update('groq_api_key', e.target.value)}
              placeholder={settings?.groq_api_key_set ? '••••••••' : 'Enter Groq API key'}
            />
          </div>
          <div>
            <label className={labelClass}>Model</label>
            <input className={inputClass} value={form.groq_model || ''} onChange={e => update('groq_model', e.target.value)} placeholder="llama-3.3-70b-versatile" />
          </div>
        </div>
      </section>

      <section className={cardClass}>
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">Gemini (Google)</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.gemini} />
            <button
              className="inline-flex items-center gap-1 rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 hover:bg-white/10"
              onClick={() => handleTest('gemini')}
              disabled={testing.gemini}
              type="button"
              aria-label="Test Gemini connection"
            >
              {testing.gemini ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label className={labelClass}>API Key {settings?.gemini_api_key_set && <span className="ml-1 text-emerald-200">(set)</span>}</label>
            <input
              className={inputClass}
              type="password"
              value={form.gemini_api_key || ''}
              onChange={e => update('gemini_api_key', e.target.value)}
              placeholder={settings?.gemini_api_key_set ? '••••••••' : 'Enter Gemini API key'}
            />
          </div>
          <div>
            <label className={labelClass}>Model</label>
            <input className={inputClass} value={form.gemini_model || ''} onChange={e => update('gemini_model', e.target.value)} placeholder="gemini-2.0-flash" />
          </div>
        </div>
      </section>

      <section className={cardClass}>
        <h3 className="text-lg font-semibold text-white">Generation Parameters</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className={labelClass}>Temperature: {form.temperature ?? 0.3}</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.05"
              value={form.temperature ?? 0.3}
              onChange={e => update('temperature', parseFloat(e.target.value))}
              className="w-full"
              aria-label="Temperature"
            />
          </div>
          <div>
            <label className={labelClass}>Max Tokens: {form.max_tokens ?? 512}</label>
            <input
              type="range"
              min="64"
              max="4096"
              step="64"
              value={form.max_tokens ?? 512}
              onChange={e => update('max_tokens', parseInt(e.target.value, 10))}
              className="w-full"
              aria-label="Max tokens"
            />
          </div>
        </div>
      </section>

      <section className={cardClass}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">System Prompt</h3>
          <button
            className="rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-100 transition-colors hover:bg-white/10"
            onClick={() => update('system_prompt',
              `You are IMS AstroBot, a helpful and accurate academic assistant for an institutional management system. \nYou answer questions based ONLY on the provided institutional documents and context.\nIf the context does not contain enough information to answer the question, say so clearly.\nDo not make up information. Always be concise, professional, and helpful.\nIf citing specific regulations or policies, mention the source document when possible.`
            )}
            type="button"
            aria-label="Reset system prompt to default"
          >
            Reset Default Prompt
          </button>
        </div>
        <p className="mt-2 text-sm text-slate-300/85">Prompt sent with each query to guide assistant behavior.</p>
        <textarea
          value={form.system_prompt || ''}
          onChange={e => update('system_prompt', e.target.value)}
          rows={7}
          className="mt-3 w-full resize-y rounded-xl border border-white/20 bg-black/20 px-3 py-2.5 font-mono text-sm text-white placeholder:text-slate-400 focus:border-cyan-300/70 focus:outline-none"
          placeholder="Enter system prompt for the AI assistant..."
        />
        <p className="mt-1 text-right text-xs text-slate-300/80">{(form.system_prompt || '').length} characters</p>
      </section>

      <button
        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-300 to-blue-500 px-4 py-2.5 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02]"
        onClick={handleSave}
        type="button"
        aria-label="Save all AI settings"
      >
        <Save size={16} /> Save All Settings
      </button>
    </div>
  );
}
