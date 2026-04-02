import { useState } from 'react';
import ChatPage from './components/ChatPage';
import ResearchPage from './components/ResearchPage';
import CodePage from './components/CodePage';

type AppMode = 'chat' | 'research' | 'code';

export default function App() {
  const [mode, setMode] = useState<AppMode>('chat');

  const renderPage = () => {
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
  };

  return (
    <div className="flex h-screen w-screen bg-gray-900 text-white overflow-hidden">
      {/* Mode Selector */}
      <div className="flex flex-col w-16 bg-gray-800 border-r border-gray-700">
        <button
          onClick={() => setMode('chat')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'chat'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Chat Simple"
        >
          🧠
        </button>
        <button
          onClick={() => setMode('research')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'research'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Research"
        >
          🔬
        </button>
        <button
          onClick={() => setMode('code')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'code'
              ? 'bg-green-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="Code"
        >
          💻
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderPage()}
      </div>
    </div>
  );
}
