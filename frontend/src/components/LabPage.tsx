import { useState, useEffect } from 'react';

export default function LabPage() {
  const [conversations, setConversations] = useState<{ id: string; name: string; specialist: string }[]>([]);
  const [selectedConv, setSelectedConv] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/lab/conversations')
      .then(r => r.json())
      .then(data => {
        if (data.conversations) setConversations(data.conversations);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🔬</span>
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Laboratoire</h2>
            <p className="text-xs text-text-muted">Environnement de développement autonome</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button className="p-4 rounded-xl border border-border-subtle bg-bg-glass hover:border-accent-cyan/30 hover:bg-bg-hover transition-all text-left">
            <div className="text-2xl mb-2">🤖</div>
            <div className="text-sm font-medium text-text-primary">Module Autonome</div>
            <div className="text-[10px] text-text-muted">Exécution automatique de tâches complexes</div>
          </button>
          
          <button className="p-4 rounded-xl border border-border-subtle bg-bg-glass hover:border-accent-purple/30 hover:bg-bg-hover transition-all text-left">
            <div className="text-2xl mb-2">💡</div>
            <div className="text-sm font-medium text-text-primary">Module d'Induction</div>
            <div className="text-[10px] text-text-muted">Génération d'idées et exploration</div>
          </button>
          
          <button className="p-4 rounded-xl border border-border-subtle bg-bg-glass hover:border-accent-magenta/30 hover:bg-bg-hover transition-all text-left">
            <div className="text-2xl mb-2">🎯</div>
            <div className="text-sm font-medium text-text-primary">Module d'Inception</div>
            <div className="text-[10px] text-text-muted">Création de concepts et frameworks</div>
          </button>
          
          <button className="p-4 rounded-xl border border-border-subtle bg-bg-glass hover:border-accent-amber/30 hover:bg-bg-hover transition-all text-left">
            <div className="text-2xl mb-2">🧪</div>
            <div className="text-sm font-medium text-text-primary">Expérimentation</div>
            <div className="text-[10px] text-text-muted">Tests et validation d'hypothèses</div>
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-border-subtle">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Conversations actives</h3>
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-text-muted text-xs">
              Aucune conversation活跃. Créez-en une nouvelle depuis le launcher.
            </div>
          ) : (
            <div className="space-y-2">
              {conversations.map(conv => (
                <button key={conv.id} className="w-full p-3 rounded-lg border border-border-subtle bg-bg-glass hover:border-border-accent text-left">
                  <div className="text-xs font-medium text-text-primary">{conv.name}</div>
                  <div className="text-[10px] text-text-muted">{conv.specialist}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
