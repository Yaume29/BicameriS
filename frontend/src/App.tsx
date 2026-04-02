import { useState, useEffect, useCallback } from 'react';
import ChatPage from './components/ChatPage';
import ResearchPage from './components/ResearchPage';
import CodePage from './components/CodePage';
import type { AppMode } from './types/api';

const API_BASE = '/api/specialist';

export default function App() {
  const [mode, setModeState] = useState<AppMode>('chat');
  const [isSyncing, setIsSyncing] = useState(false);
  const [backendMode, setBackendMode] = useState<string | null>(null);

  const syncModeToBackend = useCallback(async (newMode: AppMode) => {
    setIsSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode }),
      });
      const data = await response.json();
      if (data.status === 'ok') {
        setBackendMode(data.mode);
      }
    } catch (err) {
      console.error('Failed to sync mode:', err);
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    syncModeToBackend(mode);
  }, [mode, syncModeToBackend]);

  const handleModeChange = (newMode: AppMode) => {
    setModeState(newMode);
  };

  return (
    <div className="flex h-screen w-screen bg-gray-900 text-white overflow-hidden">
      {/* Mode Selector */}
      <div className="flex flex-col w-16 bg-gray-800 border-r border-gray-700">
        <button
          onClick={() => handleModeChange('chat')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'chat'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Chat Simple"
          disabled={isSyncing}
        >
          🧠
        </button>
        <button
          onClick={() => handleModeChange('research')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'research'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Research"
          disabled={isSyncing}
        >
          🔬
        </button>
        <button
          onClick={() => handleModeChange('code')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'code'
              ? 'bg-green-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Code"
          disabled={isSyncing}
        >
          💻
        </button>
        {backendMode && (
          <div className="flex items-center justify-center text-[8px] text-gray-500 py-1">
            {backendMode === mode ? '✓' : '⟳'}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderPage(mode)}
      </div>
    </div>
  );
}

function renderPage(mode: AppMode) {
  switch (mode) {
    case 'chat':
      return <ChatPage />;
    case 'research':
      return <ResearchPage />;
    case 'code':
      return <CodePage />;
    default:
      return <ChatPage />;
  }
}
