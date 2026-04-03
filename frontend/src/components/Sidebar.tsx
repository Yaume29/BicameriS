import { useState } from 'react';
import BrainSVG from './BrainSVG';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  activePreset: string;
  onPresetChange: (id: string) => void;
  modelsLoaded: boolean;
}

const personalityPresets = [
  { id: 'balanced', name: 'Équilibré', icon: '⚖️', description: 'Harmonie logique et créative', color: '#8b5cf6' },
  { id: 'analytical', name: 'Analytique', icon: '🔬', description: 'Précision logique maximale', color: '#00d4ff' },
  { id: 'creative', name: 'Créatif', icon: '🎨', description: 'Imagination et pensée divergente', color: '#ff006e' },
  { id: 'empathic', name: 'Empathique', icon: '💜', description: 'Compréhension émotionnelle', color: '#a78bfa' },
  { id: 'stoic', name: 'Stoïque', icon: '🏛️', description: 'Calme et rationalité', color: '#64748b' },
  { id: 'chaotic', name: 'Entropie+', icon: '🔥', description: 'Déstabilisation créative', color: '#f97316' },
];

export default function Sidebar({ collapsed, onToggle, activePreset, onPresetChange, modelsLoaded }: SidebarProps) {
  return (
    <div className={`sidebar-transition flex flex-col bg-bg-secondary border-r border-border-subtle relative ${collapsed ? 'w-14' : 'w-72'}`}>
      <button
        onClick={onToggle}
        className="absolute -right-3 top-6 z-20 w-6 h-6 rounded-full bg-bg-tertiary border border-border-accent flex items-center justify-center text-text-muted hover:text-text-primary hover:border-accent-cyan transition-all duration-200 shadow-lg"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`}>
          <path d="M7 1L3 5L7 9" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      </button>

      {!collapsed && (
        <>
          <div className="p-4 border-b border-border-subtle">
            <div className="flex items-center gap-3 mb-1">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 border border-border-accent flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" stroke="url(#logoGrad)" strokeWidth="1.5" />
                  <path d="M8 12c0-2.2 1.8-4 4-4s4 1.8 4 4-1.8 4-4 4" stroke="#00d4ff" strokeWidth="1.2" />
                  <path d="M12 8c2.2 0 4 1.8 4 4s-1.8 4-4 4" stroke="#ff006e" strokeWidth="1.2" opacity="0.7" />
                  <circle cx="12" cy="12" r="1.5" fill="#8b5cf6" />
                  <defs>
                    <linearGradient id="logoGrad" x1="2" y1="2" x2="22" y2="22">
                      <stop offset="0%" stopColor="#00d4ff" />
                      <stop offset="100%" stopColor="#ff006e" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-wider bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
                  BicameriS
                </h1>
                <p className="text-[9px] text-text-muted tracking-widest uppercase">Interface Bicamérale</p>
              </div>
            </div>
          </div>

          <div className="p-4 border-b border-border-subtle flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-cyan/10 via-accent-purple/10 to-accent-magenta/10 rounded-2xl blur-xl animate-pulse-glow" />
              <div className="relative glass-card rounded-2xl p-3 neon-border-purple">
                <BrainSVG size={100} />
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            <div className="mb-4">
              <span className="text-[10px] font-semibold tracking-wider text-text-secondary uppercase block mb-2">Personnalité</span>
              <div className="grid grid-cols-2 gap-1.5">
                {personalityPresets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => onPresetChange(preset.id)}
                    className={`p-2 rounded-lg text-left transition-all duration-200 border ${
                      activePreset === preset.id
                        ? 'border-accent-cyan/40 bg-accent-cyan/10'
                        : 'border-border-subtle bg-bg-glass hover:border-border-accent hover:bg-bg-hover'
                    }`}
                    style={activePreset === preset.id ? { borderColor: preset.color + '60', backgroundColor: preset.color + '15' } : undefined}
                  >
                    <div className="text-sm mb-0.5">{preset.icon}</div>
                    <div className="text-[10px] font-medium text-text-primary truncate">{preset.name}</div>
                    <div className="text-[8px] text-text-muted truncate">{preset.description}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="p-3 border-t border-border-subtle">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${modelsLoaded ? 'bg-accent-green animate-pulse' : 'bg-accent-red'}`} />
              <span className="text-[9px] text-text-muted">{modelsLoaded ? 'Modèles chargés' : 'En attente'}</span>
              <div className="flex-1" />
              <span className="text-[9px] text-text-muted font-mono">v4.0</span>
            </div>
          </div>
        </>
      )}

      {collapsed && (
        <div className="flex-1 flex flex-col items-center py-4 gap-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 border border-border-accent flex items-center justify-center">
            <span className="text-xs">🧠</span>
          </div>
          <div className={`w-2 h-2 rounded-full ${modelsLoaded ? 'bg-accent-green animate-pulse' : 'bg-accent-red'}`} />
        </div>
      )}
    </div>
  );
}
