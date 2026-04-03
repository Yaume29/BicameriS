import type { MainTab } from '../types/app';

interface TabBarProps {
  activeTab: MainTab;
  onTabChange: (tab: MainTab) => void;
}

const tabs: { id: MainTab; label: string; icon: string }[] = [
  { id: 'models', label: 'Modèles', icon: '🧩' },
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'lab', label: 'Laboratoire', icon: '🔬' },
  { id: 'journal', label: 'Journal', icon: '📊' },
  { id: 'settings', label: 'Réglages', icon: '⚙️' },
];

export default function TabBar({ activeTab, onTabChange }: TabBarProps) {
  return (
    <div className="flex items-center bg-bg-secondary border-b border-border-subtle px-2">
      <div className="flex gap-0.5">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`relative px-4 py-3 text-xs font-medium transition-all duration-200 flex items-center gap-2 rounded-t-lg ${
              activeTab === tab.id
                ? 'text-text-primary bg-bg-tertiary'
                : 'text-text-muted hover:text-text-secondary hover:bg-bg-hover'
            }`}
          >
            <span className="text-sm">{tab.icon}</span>
            <span>{tab.label}</span>
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-accent-cyan via-accent-purple to-accent-magenta rounded-full" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
