import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TabBar from './components/TabBar';
import ModelsPage from './components/ModelsPage';
import ChatPage from './components/ChatPage';
import LabPage from './components/LabPage';
import type { MainTab, ModelConfig } from './types/app';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<MainTab>('models');
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [activePreset, setActivePreset] = useState('balanced');
  const [modelsLoaded, setModelsLoaded] = useState(false);

  useEffect(() => {
    fetch('/api/models/status')
      .then(r => r.json())
      .then(data => {
        if (data.left || data.right) {
          setModelsLoaded(true);
          setActiveTab('chat');
        }
      })
      .catch(() => {});
  }, []);

  const handleModelsChange = (newModels: ModelConfig[]) => {
    setModels(newModels);
    if (newModels.length >= 1) {
      setModelsLoaded(true);
      setActiveTab('chat');
    }
  };

  const renderPage = () => {
    switch (activeTab) {
      case 'models':
        return <ModelsPage models={models} onModelsChange={handleModelsChange} />;
      case 'chat':
        return <ChatPage />;
      case 'lab':
        return <LabPage />;
      default:
        return <ModelsPage models={models} onModelsChange={handleModelsChange} />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-bg-primary overflow-hidden">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        activePreset={activePreset}
        onPresetChange={setActivePreset}
        modelsLoaded={modelsLoaded}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
        <div className="flex-1 overflow-hidden">
          {renderPage()}
        </div>
      </div>
    </div>
  );
}
