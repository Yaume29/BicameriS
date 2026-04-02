import { useState, useEffect, useCallback } from 'react';

interface LocalModel {
  name: string;
  path: string;
  size: string;
  params: string;
  quantization?: string;
  loaded?: boolean;
}

interface BootScreenProps {
  onBootSuccess: () => void;
}

export default function BootScreen({ onBootSuccess }: BootScreenProps) {
  const [subTab, setSubTab] = useState<'local' | 'lmstudio'>('local');
  const [scanPath, setScanPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [selectedLeftModel, setSelectedLeftModel] = useState<string | null>(null);
  const [selectedRightModel, setSelectedRightModel] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<'double' | 'single' | 'schizo'>('double');
  const [lmStudioEndpoint, setLmStudioEndpoint] = useState('http://localhost:1234/v1');
  const [lmStudioConnected, setLmStudioConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadStatus, setLoadStatus] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchDefaultPath = useCallback(async () => {
    try {
      const res = await fetch('/api/models/default-path');
      const data = await res.json();
      if (data.path) setScanPath(data.path);
    } catch (err) {
      console.error('Failed to fetch default path:', err);
    }
  }, []);

  const handleScan = useCallback(async () => {
    if (!scanPath.trim()) return;
    setScanning(true);
    setError(null);

    try {
      const res = await fetch('/api/models/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: scanPath }),
      });
      const data = await res.json();

      if (data.status === 'ok' && data.models) {
        const formatted: LocalModel[] = data.models.map((m: { name: string; path: string; size: number; size_formatted: string }) => ({
          name: m.name,
          path: m.path,
          size: m.size_formatted,
          params: m.parameters || 'N/A',
          quantization: m.quantization,
        }));
        setLocalModels(formatted);
      } else {
        setError(data.message || 'Aucun modèle trouvé');
      }
    } catch (err) {
      setError(`Erreur: ${err}`);
    } finally {
      setScanning(false);
    }
  }, [scanPath]);

  const handleConnectLmStudio = useCallback(async () => {
    setLmStudioConnected(false);
    setError(null);

    try {
      const res = await fetch('/api/models/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: lmStudioEndpoint }),
      });
      const data = await res.json();

      if (data.status === 'ok' && data.models) {
        setLmStudioConnected(true);
        setLocalModels(data.models.map((m: { name: string }) => ({
          name: m.name,
          path: '',
          size: 'Remote',
          params: 'N/A',
          loaded: false,
        })));
      } else {
        setLmStudioConnected(true);
        setLocalModels([
          { name: 'Aucun modèle chargé', path: '', size: 'Remote', params: '-', loaded: false },
        ]);
      }
    } catch {
      setLmStudioConnected(true);
      setLocalModels([{ name: 'Connecté (utilisez LM Studio)', path: '', size: 'Remote', params: '-', loaded: false }]);
    }
  }, [lmStudioEndpoint]);

  const loadModels = useCallback(async () => {
    if (!selectedLeftModel) {
      setError('Sélectionnez un modèle pour le moins');
      return;
    }

    setIsLoading(true);
    setError(null);
    setLoadStatus('Initialisation du Cortex Bicaméral...');

    try {
      const leftM = localModels.find(m => m.name === selectedLeftModel);
      const rightM = connectionMode !== 'single' ? localModels.find(m => m.name === selectedRightModel) : null;

      const res = await fetch('/api/models/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          left_path: leftM?.path || selectedLeftModel,
          right_path: rightM?.path || selectedRightModel || leftM?.path,
        }),
      });

      const data = await res.json();
      if (data.status === 'ok' || data.status === 'loaded') {
        setLoadStatus('Allocation VRAM terminée');
        onBootSuccess();
      } else {
        setError(data.message || data.error || 'Échec du chargement');
      }
    } catch (err) {
      setError(`Erreur: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [selectedLeftModel, selectedRightModel, localModels, connectionMode, onBootSuccess]);

  useEffect(() => {
    fetchDefaultPath();
  }, [fetchDefaultPath]);

  return (
    <div className="flex items-center justify-center h-screen w-screen bg-gray-950 overflow-y-auto">
      <div className="w-full max-w-4xl p-6">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-5xl mb-3">🧠</div>
          <h1 className="text-3xl font-bold text-white tracking-widest">BICAMERIS</h1>
          <div className="text-xs text-gray-500 mt-1">CORTEX COGNITIF BICAMÉRAL v4.0</div>
        </div>

        {/* Sub Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-800/50 rounded-xl p-1 w-fit mx-auto">
          <button
            onClick={() => setSubTab('local')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              subTab === 'local'
                ? 'bg-gray-700 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            🖥️ Modèles Locaux
          </button>
          <button
            onClick={() => setSubTab('lmstudio')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              subTab === 'lmstudio'
                ? 'bg-gray-700 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            ⚡ LM Studio
          </button>
        </div>

        {/* Content Card */}
        <div className="bg-gray-900/80 border border-gray-700 rounded-2xl p-5">
          {subTab === 'local' ? (
            <div className="space-y-4">
              {/* Scan Path */}
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Chemin du dossier de modèles GGUF</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={scanPath}
                    onChange={(e) => setScanPath(e.target.value)}
                    placeholder="C:\Users\...\models"
                    className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={handleScan}
                    disabled={scanning || !scanPath.trim()}
                    className="px-4 py-2.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg text-sm font-medium hover:bg-cyan-500/30 transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {scanning ? (
                      <>
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Scan...
                      </>
                    ) : (
                      '📁 Scanner'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* LM Studio Connection */}
              <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-purple-400">LM Studio Server</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${lmStudioConnected ? 'bg-green-500' : 'bg-gray-500'}`} />
                    <span className={`text-xs ${lmStudioConnected ? 'text-green-400' : 'text-gray-500'}`}>
                      {lmStudioConnected ? 'Connecté' : 'Déconnecté'}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={lmStudioEndpoint}
                    onChange={(e) => setLmStudioEndpoint(e.target.value)}
                    className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-purple-500"
                  />
                  <button
                    onClick={handleConnectLmStudio}
                    className="px-4 py-2 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-lg text-xs font-medium hover:bg-purple-500/30 transition-all"
                  >
                    Connecter
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Model List */}
          {localModels.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">
                  Modèles détectés ({localModels.length})
                </h3>
                <div className="flex gap-1.5">
                  {(['double', 'single', 'schizo'] as const).map(mode => (
                    <button
                      key={mode}
                      onClick={() => setConnectionMode(mode)}
                      className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all border ${
                        connectionMode === mode
                          ? 'border-purple-500/40 bg-purple-500/10 text-purple-400'
                          : 'border-gray-600 text-gray-500 hover:border-gray-500'
                      }`}
                    >
                      {mode === 'double' ? '🧠 Double' : mode === 'single' ? '🔀 Unique' : '🌀 Schizo'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {localModels.map((model, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedLeftModel === model.name || selectedRightModel === model.name
                        ? 'border-cyan-500/40 bg-cyan-500/5'
                        : 'border-gray-700 bg-gray-800/30 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${
                          selectedLeftModel === model.name || selectedRightModel === model.name
                            ? 'bg-cyan-500/20'
                            : 'bg-gray-700'
                        }`}>
                          {model.loaded ? '✅' : '🤖'}
                        </div>
                        <div>
                          <div className="text-xs font-medium text-white">{model.name}</div>
                          <div className="text-[10px] text-gray-500 mt-0.5">
                            {model.params} • {model.size} {model.quantization && `• ${model.quantization}`}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => setSelectedLeftModel(selectedLeftModel === model.name ? null : model.name)}
                          className={`px-2 py-1 rounded text-[10px] font-medium transition-all ${
                            selectedLeftModel === model.name
                              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                              : 'bg-gray-700 text-gray-400 border border-gray-600 hover:border-cyan-500/30'
                          }`}
                        >
                          🧠L
                        </button>
                        {connectionMode !== 'single' && (
                          <button
                            onClick={() => setSelectedRightModel(selectedRightModel === model.name ? null : model.name)}
                            className={`px-2 py-1 rounded text-[10px] font-medium transition-all ${
                              selectedRightModel === model.name
                                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                                : 'bg-gray-700 text-gray-400 border border-gray-600 hover:border-purple-500/30'
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

          {/* Hemisphere Config */}
          {(selectedLeftModel || selectedRightModel) && (
            <div className="mt-6 p-4 rounded-xl bg-gray-800/30 border border-gray-700 animate-fade-in">
              <h3 className="text-sm font-semibold text-white mb-3">Configuration des hémisphères</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className={`p-4 rounded-xl border ${selectedLeftModel ? 'border-cyan-500/30 bg-cyan-500/5' : 'border-gray-700 bg-gray-800/30'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                    <span className="text-xs font-medium text-white">Hémisphère Gauche</span>
                  </div>
                  {selectedLeftModel && (
                    <div className="text-[10px] text-cyan-400 truncate">
                      {selectedLeftModel}
                    </div>
                  )}
                </div>

                <div className={`p-4 rounded-xl border ${selectedRightModel ? 'border-purple-500/30 bg-purple-500/5' : 'border-gray-700 bg-gray-800/30'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                    <span className="text-xs font-medium text-white">Hémisphère Droit</span>
                  </div>
                  {connectionMode === 'single' ? (
                    <div className="text-[10px] text-gray-500 italic">Mode unique</div>
                  ) : selectedRightModel ? (
                    <div className="text-[10px] text-purple-400 truncate">
                      {selectedRightModel}
                    </div>
                  ) : (
                    <div className="text-[10px] text-gray-500">Non sélectionné</div>
                  )}
                </div>
              </div>

              {connectionMode === 'schizo' && (
                <div className="mt-3 p-3 rounded-lg bg-pink-500/10 border border-pink-500/20">
                  <p className="text-[10px] text-pink-400">
                    🌀 Mode Schizophrénique : Contexte forcé pour dualité de personnalité
                  </p>
                </div>
              )}

              <button
                onClick={loadModels}
                disabled={isLoading || !selectedLeftModel}
                className="mt-4 w-full py-3 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 border border-cyan-500/30 rounded-xl text-sm font-semibold text-white uppercase tracking-widest hover:from-cyan-500/30 hover:to-purple-500/30 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {loadStatus || 'Chargement...'}
                  </span>
                ) : (
                  '⚡ Initialiser le Core Bicaméral'
                )}
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 text-center text-xs text-red-400 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-[10px] text-gray-600 mt-6">
          <span className="text-gray-500">VRAM Requis:</span> ~4GB par hémisphère
        </div>
      </div>
    </div>
  );
}
