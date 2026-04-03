import { useState, useEffect, useCallback } from 'react';
import type { ModelConfig, ModelSubTab, ExternalProvider, MainTab } from '../types/app';

const externalProviders: ExternalProvider[] = [
  { id: 'openai', name: 'OpenAI', icon: '🟢', protocol: 'OpenAI API', defaultEndpoint: 'https://api.openai.com/v1', authType: 'bearer', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { id: 'anthropic', name: 'Anthropic', icon: '🟣', protocol: 'Anthropic API', defaultEndpoint: 'https://api.anthropic.com/v1', authType: 'api-key', models: ['claude-3-5-sonnet', 'claude-3-opus'] },
  { id: 'ollama', name: 'Ollama', icon: '🦙', protocol: 'Ollama API', defaultEndpoint: 'http://localhost:11434/api', authType: 'custom' },
  { id: 'lmstudio', name: 'LM Studio', icon: '💻', protocol: 'OpenAI Compatible', defaultEndpoint: 'http://localhost:1234/v1', authType: 'bearer' },
];

interface LocalModel {
  name: string;
  path: string;
  size: string;
  params: string;
  quantization?: string;
  loaded?: boolean;
}

interface ModelsPageProps {
  models: ModelConfig[];
  onModelsChange: (models: ModelConfig[]) => void;
}

export default function ModelsPage({ models, onModelsChange }: ModelsPageProps) {
  const [subTab, setSubTab] = useState<ModelSubTab>('local');
  const [llamaCppMode, setLlamaCppMode] = useState(true);
  const [scanPath, setScanPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [selectedLeftModel, setSelectedLeftModel] = useState<string | null>(null);
  const [selectedRightModel, setSelectedRightModel] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<'double' | 'single'>('double');
  const [lmStudioEndpoint, setLmStudioEndpoint] = useState('http://localhost:1234/v1');
  const [lmStudioConnected, setLmStudioConnected] = useState(false);
  const [showAddExternal, setShowAddExternal] = useState(false);
  const [newExternal, setNewExternal] = useState({ provider: 'openai', endpoint: '', apiKey: '', modelId: '', hemisphere: 'both' });

  const fetchDefaultPath = useCallback(async () => {
    try {
      const res = await fetch('/api/models/default-path');
      const data = await res.json();
      if (data.path) setScanPath(data.path);
    } catch (err) {
      console.error('Failed to fetch default path:', err);
    }
  }, []);

  useEffect(() => { fetchDefaultPath(); }, [fetchDefaultPath]);

  const handleScan = useCallback(async () => {
    if (!scanPath.trim()) return;
    setScanning(true);

    try {
      const res = await fetch('/api/models/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: scanPath }),
      });
      const data = await res.json();

      if (data.status === 'ok' && data.models) {
        setLocalModels(data.models.map((m: { name: string; path: string; size: number; size_formatted: string; parameters?: string; quantization?: string }) => ({
          name: m.name,
          path: m.path,
          size: m.size_formatted,
          params: m.parameters || 'N/A',
          quantization: m.quantization,
        })));
      }
    } catch (err) {
      console.error('Scan error:', err);
    } finally {
      setScanning(false);
    }
  }, [scanPath]);

  const handleConnectLmStudio = useCallback(async () => {
    setLmStudioConnected(false);
    try {
      const res = await fetch('/api/models/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: lmStudioEndpoint }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setLmStudioConnected(true);
        setLocalModels(data.models?.map((m: { name: string }) => ({ name: m.name, path: '', size: 'Remote', params: 'N/A', loaded: false })) || []);
      }
    } catch {
      setLmStudioConnected(true);
    }
  }, [lmStudioEndpoint]);

  const applyLocalModels = useCallback(() => {
    const newModels: ModelConfig[] = [];
    if (selectedLeftModel) {
      const leftModel = localModels.find(m => m.name === selectedLeftModel);
      if (leftModel) {
        newModels.push({
          id: `local-left-${Date.now()}`,
          name: leftModel.name,
          type: llamaCppMode ? 'llama-cpp' : 'lm-studio',
          hemisphere: 'left',
          weight: 1,
          path: leftModel.path,
          size: leftModel.size,
        });
      }
    }
    if (selectedRightModel && connectionMode !== 'single') {
      const rightModel = localModels.find(m => m.name === selectedRightModel);
      if (rightModel) {
        newModels.push({
          id: `local-right-${Date.now()}`,
          name: rightModel.name,
          type: llamaCppMode ? 'llama-cpp' : 'lm-studio',
          hemisphere: 'right',
          weight: 1,
          path: rightModel.path,
          size: rightModel.size,
        });
      }
    }
    onModelsChange([...models.filter(m => m.type !== 'llama-cpp' && m.type !== 'lm-studio'), ...newModels]);
  }, [selectedLeftModel, selectedRightModel, localModels, llamaCppMode, connectionMode, models, onModelsChange]);

  const loadModelsToBackend = useCallback(async () => {
    if (!selectedLeftModel) return;

    const leftM = localModels.find(m => m.name === selectedLeftModel);
    const rightM = connectionMode !== 'single' ? localModels.find(m => m.name === selectedRightModel) : null;

    try {
      await fetch('/api/models/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          left_path: leftM?.path || selectedLeftModel,
          right_path: rightM?.path || selectedRightModel || leftM?.path,
        }),
      });
      applyLocalModels();
    } catch (err) {
      console.error('Load error:', err);
    }
  }, [selectedLeftModel, selectedRightModel, localModels, connectionMode, applyLocalModels]);

  const selectedProvider = externalProviders.find(p => p.id === newExternal.provider);

  return (
    <div className="flex-1 overflow-y-auto p-6 animate-fade-in">
      <div className="flex gap-1 mb-6 bg-bg-glass rounded-xl p-1 w-fit">
        <button onClick={() => setSubTab('local')} className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${subTab === 'local' ? 'bg-bg-tertiary text-text-primary shadow-sm' : 'text-text-muted hover:text-text-secondary'}`}>
          🖥️ Modèles Locaux
        </button>
        <button onClick={() => setSubTab('external')} className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${subTab === 'external' ? 'bg-bg-tertiary text-text-primary shadow-sm' : 'text-text-muted hover:text-text-secondary'}`}>
          🌐 Clients Externes
        </button>
      </div>

      {subTab === 'local' && (
        <div className="space-y-6">
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">Moteur d'inférence</h3>
                <p className="text-[10px] text-text-muted mt-0.5">Sélectionnez le protocole de connexion</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-[10px] font-medium ${llamaCppMode ? 'text-accent-cyan' : 'text-text-muted'}`}>llama-cpp</span>
                <button
                  onClick={() => setLlamaCppMode(!llamaCppMode)}
                  className={`relative w-11 h-6 rounded-full transition-all duration-300 ${llamaCppMode ? 'bg-accent-cyan/30' : 'bg-accent-purple/30'}`}
                >
                  <div className={`absolute top-0.5 w-5 h-5 rounded-full transition-all duration-300 shadow-md ${llamaCppMode ? 'left-0.5 bg-accent-cyan' : 'left-5 bg-accent-purple'}`} />
                </button>
                <span className={`text-[10px] font-medium ${!llamaCppMode ? 'text-accent-purple' : 'text-text-muted'}`}>LM Studio</span>
              </div>
            </div>

            {llamaCppMode ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Chemin du dossier de modèles GGUF..."
                    value={scanPath}
                    onChange={e => setScanPath(e.target.value)}
                    className="flex-1 bg-bg-primary border border-border-subtle rounded-lg px-3 py-2.5 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/50"
                  />
                  <button
                    onClick={handleScan}
                    disabled={scanning || !scanPath.trim()}
                    className="px-4 py-2.5 bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/30 rounded-lg text-xs font-medium hover:bg-accent-cyan/30 transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {scanning ? '⟳ Scan...' : '📁 Scanner'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-bg-primary border border-border-subtle">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-accent-purple">LM Studio Server</span>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${lmStudioConnected ? 'bg-accent-green' : 'bg-text-muted'}`} />
                      <span className={`text-[9px] ${lmStudioConnected ? 'text-accent-green' : 'text-text-muted'}`}>
                        {lmStudioConnected ? 'Connecté' : 'Déconnecté'}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={lmStudioEndpoint}
                      onChange={e => setLmStudioEndpoint(e.target.value)}
                      className="flex-1 bg-bg-tertiary border border-border-subtle rounded-lg px-3 py-1.5 text-[10px] text-text-primary font-mono focus:outline-none focus:border-accent-purple/40"
                    />
                    <button onClick={handleConnectLmStudio} className="px-3 py-1.5 bg-accent-purple/20 text-accent-purple border border-accent-purple/30 rounded-lg text-[10px] font-medium hover:bg-accent-purple/30 transition-all">
                      Connecter
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {localModels.length > 0 && (
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text-primary">Modèles détectés ({localModels.length})</h3>
                <div className="flex gap-1.5">
                  {(['double', 'single'] as const).map(mode => (
                    <button
                      key={mode}
                      onClick={() => setConnectionMode(mode)}
                      className={`px-2.5 py-1 rounded-lg text-[9px] font-medium transition-all border ${
                        connectionMode === mode
                          ? 'border-accent-purple/40 bg-accent-purple/10 text-accent-purple'
                          : 'border-border-subtle text-text-muted hover:border-border-accent'
                      }`}
                    >
                      {mode === 'double' ? '🧠 Double' : '🔀 Unique'}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {localModels.map((model, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                      selectedLeftModel === model.name || selectedRightModel === model.name
                        ? 'border-accent-cyan/40 bg-accent-cyan/5'
                        : 'border-border-subtle bg-bg-glass hover:border-border-accent'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${selectedLeftModel === model.name || selectedRightModel === model.name ? 'bg-accent-cyan/20' : 'bg-bg-tertiary'}`}>
                          {model.loaded ? '✅' : '🤖'}
                        </div>
                        <div>
                          <div className="text-xs font-medium text-text-primary">{model.name}</div>
                          <div className="text-[10px] text-text-muted mt-0.5">{model.params} • {model.size}</div>
                        </div>
                      </div>
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => setSelectedLeftModel(selectedLeftModel === model.name ? null : model.name)}
                          className={`px-2 py-1 rounded text-[9px] font-medium transition-all ${
                            selectedLeftModel === model.name
                              ? 'bg-left-hemi/20 text-left-hemi border border-left-hemi/30'
                              : 'bg-bg-glass text-text-muted border border-border-subtle hover:border-left-hemi/30'
                          }`}
                        >
                          🧠L
                        </button>
                        {connectionMode !== 'single' && (
                          <button
                            onClick={() => setSelectedRightModel(selectedRightModel === model.name ? null : model.name)}
                            className={`px-2 py-1 rounded text-[9px] font-medium transition-all ${
                              selectedRightModel === model.name
                                ? 'bg-right-hemi/20 text-right-hemi border border-right-hemi/30'
                                : 'bg-bg-glass text-text-muted border border-border-subtle hover:border-right-hemi/30'
                            }`}
                          >
                            🧠R
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(selectedLeftModel || selectedRightModel) && (
            <button
              onClick={loadModelsToBackend}
              disabled={!selectedLeftModel}
              className="w-full py-2.5 bg-gradient-to-r from-left-hemi/20 to-right-hemi/20 text-text-primary border border-accent-purple/30 rounded-xl text-xs font-medium hover:from-left-hemi/30 hover:to-right-hemi/30 transition-all disabled:opacity-50"
            >
              ⚡ Charger les modèles et démarrer
            </button>
          )}
        </div>
      )}

      {subTab === 'external' && (
        <div className="space-y-6">
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text-primary">Clients configurés ({models.filter(m => m.type !== 'llama-cpp' && m.type !== 'lm-studio').length})</h3>
              <button onClick={() => setShowAddExternal(!showAddExternal)} className="px-3 py-1.5 bg-accent-purple/20 text-accent-purple border border-accent-purple/30 rounded-lg text-[10px] font-medium hover:bg-accent-purple/30 transition-all">
                + Ajouter
              </button>
            </div>

            {showAddExternal && (
              <div className="space-y-4 mt-4 pt-4 border-t border-border-subtle">
                <div>
                  <label className="text-[10px] text-text-secondary mb-1.5 block">Fournisseur</label>
                  <div className="grid grid-cols-4 gap-2">
                    {externalProviders.slice(0, 4).map(p => (
                      <button
                        key={p.id}
                        onClick={() => setNewExternal(prev => ({ ...prev, provider: p.id, endpoint: p.defaultEndpoint }))}
                        className={`p-2 rounded-lg border text-center transition-all ${newExternal.provider === p.id ? 'border-accent-purple/40 bg-accent-purple/10' : 'border-border-subtle bg-bg-glass hover:border-border-accent'}`}
                      >
                        <div className="text-lg mb-0.5">{p.icon}</div>
                        <div className="text-[9px] text-text-primary">{p.name}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-text-secondary mb-1.5 block">Endpoint</label>
                  <input
                    type="text"
                    value={newExternal.endpoint}
                    onChange={e => setNewExternal(prev => ({ ...prev, endpoint: e.target.value }))}
                    className="w-full bg-bg-primary border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary font-mono"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-text-secondary mb-1.5 block">Clé API</label>
                  <input
                    type="password"
                    value={newExternal.apiKey}
                    onChange={e => setNewExternal(prev => ({ ...prev, apiKey: e.target.value }))}
                    className="w-full bg-bg-primary border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary font-mono"
                  />
                </div>
                <button
                  onClick={() => {
                    const provider = externalProviders.find(p => p.id === newExternal.provider);
                    onModelsChange([...models, { id: `ext-${Date.now()}`, name: `${provider?.name} - ${newExternal.modelId || 'default'}`, type: newExternal.provider, hemisphere: newExternal.hemisphere, weight: 1, endpoint: newExternal.endpoint || provider?.defaultEndpoint, apiKey: newExternal.apiKey, modelId: newExternal.modelId }]);
                    setShowAddExternal(false);
                    setNewExternal({ provider: 'openai', endpoint: '', apiKey: '', modelId: '', hemisphere: 'both' });
                  }}
                  disabled={!newExternal.apiKey}
                  className="w-full py-2.5 bg-accent-purple/20 text-accent-purple border border-accent-purple/30 rounded-lg text-xs font-medium hover:bg-accent-purple/30 disabled:opacity-50"
                >
                  ⚡ Connecter
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
