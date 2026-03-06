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
    if (form.grok_api_key) payload.grok_api_key = form.grok_api_key;
    if (form.grok_model !== settings.grok_model) payload.grok_model = form.grok_model;
    if (form.gemini_api_key) payload.gemini_api_key = form.gemini_api_key;
    if (form.gemini_model !== settings.gemini_model) payload.gemini_model = form.gemini_model;
    if (form.temperature !== settings.temperature) payload.temperature = form.temperature;
    if (form.max_tokens !== settings.max_tokens) payload.max_tokens = form.max_tokens;

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

  if (!settings) return <div className="text-center" style={{ padding: 48 }}><span className="spinner" /></div>;

  const StatusIcon = ({ result }) => {
    if (!result) return null;
    return result.status === 'ok'
      ? <CheckCircle size={16} style={{ color: 'var(--success)' }} />
      : <XCircle size={16} style={{ color: 'var(--error)' }} />;
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2>🤖 AI Settings</h2>
        <button className="btn btn-primary" onClick={handleSave}><Save size={16} /> Save All Settings</button>
      </div>
      <div className="divider" />

      {/* LLM Mode */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 12 }}>⚡ LLM Mode</h3>
        <div className="flex gap-2">
          {['local_only', 'cloud_only', 'hybrid'].map(mode => (
            <button key={mode} className={`btn ${form.llm_mode === mode ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => update('llm_mode', mode)}>
              {mode === 'local_only' ? '🖥️ Local Only' : mode === 'cloud_only' ? '☁️ Cloud Only' : '🔄 Hybrid'}
            </button>
          ))}
        </div>
        <p className="text-sm text-muted" style={{ marginTop: 8 }}>
          {form.llm_mode === 'local_only' && 'Uses Ollama (local) only.'}
          {form.llm_mode === 'cloud_only' && 'Uses cloud providers (Grok/Gemini). Primary → Fallback.'}
          {form.llm_mode === 'hybrid' && 'Uses primary provider → fallback → Ollama as last resort.'}
        </p>
      </div>

      {/* Provider Priority */}
      {form.llm_mode !== 'local_only' && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>🔗 Provider Priority</h3>
          <div className="grid-2">
            <div>
              <label>Primary Provider</label>
              <select value={form.primary_provider} onChange={e => update('primary_provider', e.target.value)}>
                <option value="ollama">Ollama (Local)</option>
                <option value="grok">Grok (xAI)</option>
                <option value="gemini">Gemini (Google)</option>
              </select>
            </div>
            <div>
              <label>Fallback Provider</label>
              <select value={form.fallback_provider} onChange={e => update('fallback_provider', e.target.value)}>
                <option value="none">None</option>
                <option value="ollama">Ollama (Local)</option>
                <option value="grok">Grok (xAI)</option>
                <option value="gemini">Gemini (Google)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Ollama Settings */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="flex items-center justify-between">
          <h3>🖥️ Ollama (Local)</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.ollama} />
            <button className="btn btn-ghost btn-sm" onClick={() => handleTest('ollama')} disabled={testing.ollama}>
              {testing.ollama ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="grid-2" style={{ marginTop: 12 }}>
          <div>
            <label>Base URL</label>
            <input value={form.ollama_base_url || ''} onChange={e => update('ollama_base_url', e.target.value)} placeholder="http://localhost:11434" />
          </div>
          <div>
            <label>Model Name</label>
            <input value={form.ollama_model || ''} onChange={e => update('ollama_model', e.target.value)} placeholder="qwen3:0.6b" />
          </div>
        </div>
        {testResults.ollama?.models && (
          <div className="text-sm text-muted" style={{ marginTop: 8 }}>
            Available models: {testResults.ollama.models.join(', ')}
          </div>
        )}
      </div>

      {/* Grok Settings */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="flex items-center justify-between">
          <h3>⚡ Grok (xAI)</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.grok} />
            <button className="btn btn-ghost btn-sm" onClick={() => handleTest('grok')} disabled={testing.grok}>
              {testing.grok ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="grid-2" style={{ marginTop: 12 }}>
          <div>
            <label>API Key {settings.grok_api_key_set && <span className="badge badge-ok" style={{ marginLeft: 4 }}>Set</span>}</label>
            <input type="password" value={form.grok_api_key || ''} onChange={e => update('grok_api_key', e.target.value)}
              placeholder={settings.grok_api_key_set ? '••••••••' : 'Enter Grok API key'} />
          </div>
          <div>
            <label>Model</label>
            <input value={form.grok_model || ''} onChange={e => update('grok_model', e.target.value)} placeholder="grok-3" />
          </div>
        </div>
      </div>

      {/* Gemini Settings */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="flex items-center justify-between">
          <h3>✨ Gemini (Google)</h3>
          <div className="flex items-center gap-2">
            <StatusIcon result={testResults.gemini} />
            <button className="btn btn-ghost btn-sm" onClick={() => handleTest('gemini')} disabled={testing.gemini}>
              {testing.gemini ? <><span className="spinner" /> Testing...</> : <><Zap size={14} /> Test</>}
            </button>
          </div>
        </div>
        <div className="grid-2" style={{ marginTop: 12 }}>
          <div>
            <label>API Key {settings.gemini_api_key_set && <span className="badge badge-ok" style={{ marginLeft: 4 }}>Set</span>}</label>
            <input type="password" value={form.gemini_api_key || ''} onChange={e => update('gemini_api_key', e.target.value)}
              placeholder={settings.gemini_api_key_set ? '••••••••' : 'Enter Gemini API key'} />
          </div>
          <div>
            <label>Model</label>
            <input value={form.gemini_model || ''} onChange={e => update('gemini_model', e.target.value)} placeholder="gemini-2.0-flash" />
          </div>
        </div>
      </div>

      {/* Generation Parameters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 12 }}>⚙️ Generation Parameters</h3>
        <div className="grid-2">
          <div>
            <label>Temperature: {form.temperature}</label>
            <input type="range" min="0" max="2" step="0.05" value={form.temperature || 0.3}
              onChange={e => update('temperature', parseFloat(e.target.value))} style={{ padding: 0 }} />
          </div>
          <div>
            <label>Max Tokens: {form.max_tokens}</label>
            <input type="range" min="64" max="4096" step="64" value={form.max_tokens || 512}
              onChange={e => update('max_tokens', parseInt(e.target.value))} style={{ padding: 0 }} />
          </div>
        </div>
      </div>

      {/* Save Button (bottom) */}
      <button className="btn btn-primary btn-block" onClick={handleSave} style={{ marginTop: 8 }}>
        <Save size={16} /> Save All Settings
      </button>
    </div>
  );
}
