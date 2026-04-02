import { useState, useEffect, useCallback } from 'react';

interface ModelInfo {
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  parameters?: string;
  quantization?: string;
}

interface BootScreenProps {
  onBootSuccess: () => void;
}

export default function BootScreen({ onBootSuccess }: BootScreenProps) {
  const [scanPath, setScanPath] = useState<string>('');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [leftModel, setLeftModel] = useState<ModelInfo | null>(null);
  const [rightModel, setRightModel] = useState<ModelInfo | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadStatus, setLoadStatus] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchDefaultPath = useCallback(async () => {
    try {
      const res = await fetch('/api/models/default-path');
      const data = await res.json();
      if (data.path) {
        setScanPath(data.path);
      }
    } catch (err) {
      console.error('Failed to fetch default path:', err);
    }
  }, []);

  const scanModels = useCallback(async () => {
    if (!scanPath) return;
    setIsScanning(true);
    setError(null);
    setModels([]);

    try {
      const res = await fetch('/api/models/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: scanPath }),
      });
      const data = await res.json();

      if (data.status === 'ok' && data.models) {
        setModels(data.models);
      } else {
        setError(data.message || 'Scan failed');
      }
    } catch (err) {
      setError(`Scan error: ${err}`);
    } finally {
      setIsScanning(false);
    }
  }, [scanPath]);

  const loadModels = useCallback(async () => {
    if (!leftModel || !rightModel) {
      setError('Sélectionnez un modèle pour chaque hémisphère');
      return;
    }

    setIsLoading(true);
    setError(null);
    setLoadStatus('Initialisation du Cortex Bicaméral...');

    try {
      const res = await fetch('/api/models/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          left_path: leftModel.path,
          right_path: rightModel.path,
        }),
      });

      const data = await res.json();

      if (data.status === 'ok' || data.status === 'loaded') {
        setLoadStatus('Allocation VRAM terminée');
        onBootSuccess();
      } else {
        setError(data.message || 'Failed to load models');
      }
    } catch (err) {
      setError(`Loading error: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [leftModel, rightModel, onBootSuccess]);

  useEffect(() => {
    fetchDefaultPath();
  }, [fetchDefaultPath]);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <div className="flex items-center justify-center h-screen w-screen bg-gray-950">
      <div className="w-full max-w-2xl p-8 bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🧠</div>
          <h1 className="text-2xl font-bold text-white tracking-wider">BICAMERIS</h1>
          <div className="text-xs text-gray-500 mt-1">CORTEX COGNITIF BICAMÉRAL v4.0</div>
        </div>

        {/* Path Input */}
        <div className="mb-6">
          <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wide">
            Chemin des Modèles .GGUF
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={scanPath}
              onChange={(e) => setScanPath(e.target.value)}
              placeholder="C:\Users\...\models"
              className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={scanModels}
              disabled={isScanning || !scanPath}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isScanning ? '⟳' : 'Scanner'}
            </button>
          </div>
        </div>

        {/* Models Selection */}
        {models.length > 0 && (
          <div className="grid grid-cols-2 gap-4 mb-6">
            {/* Left Hemisphere */}
            <div>
              <label className="block text-xs text-cyan-400 mb-2 uppercase tracking-wide">
                Hémisphère Gauche (Analytique)
              </label>
              <select
                value={leftModel?.path || ''}
                onChange={(e) => {
                  const m = models.find((m) => m.path === e.target.value);
                  setLeftModel(m || null);
                }}
                className="w-full bg-gray-800 border border-cyan-500/30 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="">Sélectionner un modèle...</option>
                {models.map((m) => (
                  <option key={`left-${m.path}`} value={m.path}>
                    {m.name} ({m.size_formatted})
                  </option>
                ))}
              </select>
              {leftModel && (
                <div className="mt-2 text-[10px] text-cyan-400/70">
                  {leftModel.quantization || 'GGUF'} • {leftModel.parameters || 'N/A'}
                </div>
              )}
            </div>

            {/* Right Hemisphere */}
            <div>
              <label className="block text-xs text-purple-400 mb-2 uppercase tracking-wide">
                Hémisphère Droit (Intuitif)
              </label>
              <select
                value={rightModel?.path || ''}
                onChange={(e) => {
                  const m = models.find((m) => m.path === e.target.value);
                  setRightModel(m || null);
                }}
                className="w-full bg-gray-800 border border-purple-500/30 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
              >
                <option value="">Sélectionner un modèle...</option>
                {models.map((m) => (
                  <option key={`right-${m.path}`} value={m.path}>
                    {m.name} ({m.size_formatted})
                  </option>
                ))}
              </select>
              {rightModel && (
                <div className="mt-2 text-[10px] text-purple-400/70">
                  {rightModel.quantization || 'GGUF'} • {rightModel.parameters || 'N/A'}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Load Button */}
        <div className="mb-6">
          <button
            onClick={loadModels}
            disabled={isLoading || !leftModel || !rightModel}
            className="w-full py-4 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 border border-cyan-500/30 rounded-xl text-sm font-semibold text-white uppercase tracking-widest hover:from-cyan-500/30 hover:to-purple-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⟳</span>
                {loadStatus}
              </span>
            ) : (
              '⚡ Initialiser le Core Bicaméral'
            )}
          </button>
        </div>

        {/* Status / Error */}
        {error && (
          <div className="text-center text-xs text-red-400 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
            {error}
          </div>
        )}

        {!error && loadStatus && isLoading && (
          <div className="text-center text-xs text-cyan-400 p-3 bg-cyan-900/10 border border-cyan-500/20 rounded-lg animate-pulse">
            {loadStatus}
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-[10px] text-gray-600 mt-6">
          <span className="text-gray-500">VRAM Requis:</span> ~8GB par hemisphere
        </div>
      </div>
    </div>
  );
}
