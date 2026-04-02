import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
  sources?: string[];
}

export default function ResearchPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: 'Mode Research activé. L\'IA va effectuer une recherche récursive et générer un rapport académique.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [template, setTemplate] = useState('academic');
  const [thinkingMode, setThinkingMode] = useState('plan_execute');
  const [sources, setSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startResearch = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: `[Recherche] ${input}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // Simulate research phases
    setTimeout(() => {
      const planMsg: Message = {
        id: `plan-${Date.now()}`,
        role: 'corpus',
        content: `📋 Plan de recherche généré:\n1. Analyse de la littérature\n2. Collecte de données\n3. Analyse des résultats\n4. Rédaction du rapport`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, planMsg]);
    }, 500);

    setTimeout(() => {
      const searchMsg: Message = {
        id: `search-${Date.now()}`,
        role: 'assistant-left',
        content: `🔍 Recherche en cours...\n\nSources trouvées:\n- arXiv: 15 papers\n- Semantic Scholar: 23 papers\n- Web: 8 articles`,
        timestamp: new Date(),
        sources: ['arXiv', 'Semantic Scholar', 'Web'],
      };
      setMessages((prev) => [...prev, searchMsg]);
      setSources(['arXiv', 'Semantic Scholar', 'Web']);
    }, 1500);

    setTimeout(() => {
      const analysisMsg: Message = {
        id: `analysis-${Date.now()}`,
        role: 'assistant-right',
        content: `💡 Analyse intuitive:\n\nPatterns détectés:\n1. Convergence vers une théorie unifiée\n2. Lacunes dans la littérature actuelle\n3. Opportunités de recherche originales`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, analysisMsg]);
    }, 2500);

    setTimeout(() => {
      const reportMsg: Message = {
        id: `report-${Date.now()}`,
        role: 'corpus',
        content: `📄 Rapport académique généré (Format: ${template.toUpperCase()})\n\nLe rapport a été sauvegardé dans:\n/storage/research/report_${Date.now()}.md\n\nStatus: ✅ Terminé`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, reportMsg]);
    }, 3500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      startResearch();
    }
  };

  const getRoleStyle = (role: string) => {
    switch (role) {
      case 'user':
        return { bg: 'bg-blue-500/15', border: 'border-blue-500/20', align: 'justify-end', label: 'Vous', labelColor: 'text-blue-400' };
      case 'assistant-left':
        return { bg: 'bg-cyan-500/10', border: 'border-cyan-500/15', align: 'justify-start', label: 'Analyse', labelColor: 'text-cyan-400' };
      case 'assistant-right':
        return { bg: 'bg-purple-500/10', border: 'border-purple-500/15', align: 'justify-start', label: 'Intuition', labelColor: 'text-purple-400' };
      case 'corpus':
        return { bg: 'bg-green-500/10', border: 'border-green-500/15', align: 'justify-center', label: 'Corpus Callosum', labelColor: 'text-green-400' };
      case 'system':
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-center', label: 'Système', labelColor: 'text-gray-400' };
      default:
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-start', label: '', labelColor: 'text-gray-400' };
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Sources */}
      <div className="w-64 bg-gray-800/50 border-r border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">📚 Sources</h3>
        {sources.length === 0 ? (
          <div className="text-[10px] text-gray-500">Aucune source pour le moment</div>
        ) : (
          <div className="space-y-2">
            {sources.map((source, i) => (
              <div key={i} className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
                <div className="text-[10px] text-gray-300">{source}</div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-300 mb-3">📄 Template</h3>
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-[10px] text-white focus:outline-none focus:border-purple-500/40"
          >
            <option value="academic">Academic (IMRAD)</option>
            <option value="research">Research (EU-US)</option>
            <option value="analysis">Analysis</option>
            <option value="report">Executive Report</option>
          </select>
        </div>

        <div className="mt-4">
          <h3 className="text-xs font-semibold text-gray-300 mb-3">🧠 Thinking Mode</h3>
          <select
            value={thinkingMode}
            onChange={(e) => setThinkingMode(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-[10px] text-white focus:outline-none focus:border-purple-500/40"
          >
            <option value="plan_execute">Plan-Execute</option>
            <option value="react">ReAct</option>
            <option value="reflexion">Reflexion</option>
            <option value="tot">Tree of Thoughts</option>
            <option value="critic_refine">Critic-Refine</option>
          </select>
        </div>
      </div>

      {/* Center - Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500/30 to-pink-500/30 border border-gray-600 flex items-center justify-center">
              <span className="text-lg">🔬</span>
            </div>
            <div>
              <div className="text-sm font-semibold">Research Mode</div>
              <div className="text-[10px] text-gray-500">Template: {template}</div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((msg) => {
            const style = getRoleStyle(msg.role);
            return (
              <div key={msg.id} className={`flex ${style.align}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${style.bg} ${style.border} border shadow-sm`}>
                  <div className={`text-[9px] font-semibold mb-1 ${style.labelColor}`}>{style.label}</div>
                  <div className="text-xs text-gray-200 leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                  {msg.sources && (
                    <div className="mt-2 text-[9px] text-gray-500">
                      Sources: {msg.sources.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-700 bg-gray-800/80 p-3">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Décrivez votre sujet de recherche..."
              rows={1}
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/40 resize-none"
              style={{ minHeight: '42px', maxHeight: '120px' }}
            />
            <button
              onClick={startResearch}
              disabled={!input.trim()}
              className="p-2.5 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-purple-500/30 hover:from-purple-500/30 hover:to-pink-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" fill="none" />
                <path d="M9 6V9M9 12H9.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - Logs */}
      <div className="w-64 bg-gray-800/50 border-l border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">📊 Logs de Recherche</h3>
        <div className="space-y-2">
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-gray-400">Status: En cours</div>
            <div className="text-[9px] text-gray-500 mt-1">Dernière mise à jour: maintenant</div>
          </div>
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-gray-400">Sources trouvées: {sources.length}</div>
            <div className="text-[9px] text-gray-500 mt-1">arXiv, Semantic Scholar, Web</div>
          </div>
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-gray-400">Template: {template}</div>
            <div className="text-[9px] text-gray-500 mt-1">Format académique</div>
          </div>
        </div>
      </div>
    </div>
  );
}
