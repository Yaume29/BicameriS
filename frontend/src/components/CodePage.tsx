import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
  code?: string;
}

export default function CodePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: 'Mode Code activé. L\'IA va itérer jusqu\'à la finition complète selon les standards industriels.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [thinkingMode, setThinkingMode] = useState('critic_refine');
  const [files, setFiles] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startCode = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: `[Code] ${input}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // Simulate code generation
    setTimeout(() => {
      const planMsg: Message = {
        id: `plan-${Date.now()}`,
        role: 'corpus',
        content: `📋 Plan d'implémentation:\n1. Créer la structure de base\n2. Implémenter les fonctionnalités\n3. Ajouter les tests\n4. Documenter le code`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, planMsg]);
    }, 500);

    setTimeout(() => {
      const codeMsg: Message = {
        id: `code-${Date.now()}`,
        role: 'assistant-left',
        content: `💻 Code généré:\n\n\`\`\`python\ndef example_function():\n    """Example function"""\n    return "Hello, World!"\n\`\`\``,
        timestamp: new Date(),
        code: 'def example_function():\n    """Example function"""\n    return "Hello, World!"',
      };
      setMessages((prev) => [...prev, codeMsg]);
      setFiles(['example.py']);
    }, 1500);

    setTimeout(() => {
      const reviewMsg: Message = {
        id: `review-${Date.now()}`,
        role: 'assistant-right',
        content: `✅ Révision du code:\n\n- Syntaxe: ✓\n- Standards: ✓\n- Documentation: ✓\n- Tests: En attente`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, reviewMsg]);
    }, 2500);

    setTimeout(() => {
      const finalMsg: Message = {
        id: `final-${Date.now()}`,
        role: 'corpus',
        content: `📄 Fichiers générés:\n- example.py\n- tests/test_example.py\n- docs/README.md\n\nStatus: ✅ Terminé`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, finalMsg]);
    }, 3500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      startCode();
    }
  };

  const getRoleStyle = (role: string) => {
    switch (role) {
      case 'user':
        return { bg: 'bg-blue-500/15', border: 'border-blue-500/20', align: 'justify-end', label: 'Vous', labelColor: 'text-blue-400' };
      case 'assistant-left':
        return { bg: 'bg-green-500/10', border: 'border-green-500/15', align: 'justify-start', label: 'Code', labelColor: 'text-green-400' };
      case 'assistant-right':
        return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/15', align: 'justify-start', label: 'Révision', labelColor: 'text-yellow-400' };
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
      {/* Left Panel - Files */}
      <div className="w-64 bg-gray-800/50 border-r border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">📁 Fichiers</h3>
        {files.length === 0 ? (
          <div className="text-[10px] text-gray-500">Aucun fichier pour le moment</div>
        ) : (
          <div className="space-y-2">
            {files.map((file, i) => (
              <div key={i} className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
                <div className="text-[10px] text-gray-300">{file}</div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-300 mb-3">🧠 Thinking Mode</h3>
          <select
            value={thinkingMode}
            onChange={(e) => setThinkingMode(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-[10px] text-white focus:outline-none focus:border-green-500/40"
          >
            <option value="critic_refine">Critic-Refine</option>
            <option value="plan_execute">Plan-Execute</option>
            <option value="react">ReAct</option>
            <option value="reflexion">Reflexion</option>
            <option value="tot">Tree of Thoughts</option>
          </select>
        </div>
      </div>

      {/* Center - Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500/30 to-yellow-500/30 border border-gray-600 flex items-center justify-center">
              <span className="text-lg">💻</span>
            </div>
            <div>
              <div className="text-sm font-semibold">Code Mode</div>
              <div className="text-[10px] text-gray-500">Thinking: {thinkingMode}</div>
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
              placeholder="Décrivez ce que vous voulez coder..."
              rows={1}
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-green-500/40 resize-none"
              style={{ minHeight: '42px', maxHeight: '120px' }}
            />
            <button
              onClick={startCode}
              disabled={!input.trim()}
              className="p-2.5 rounded-xl bg-gradient-to-r from-green-500/20 to-yellow-500/20 text-white border border-green-500/30 hover:from-green-500/30 hover:to-yellow-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M16 2L9 9M16 2L11 16L9 9M16 2L2 7L9 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - Hooks */}
      <div className="w-64 bg-gray-800/50 border-l border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">🔗 Hooks & Quality</h3>
        <div className="space-y-2">
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-green-400">✓ Security Audit</div>
            <div className="text-[9px] text-gray-500 mt-1">Priorité: Haute</div>
          </div>
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-blue-400">● Memory Reconcile</div>
            <div className="text-[9px] text-gray-500 mt-1">Priorité: Moyenne</div>
          </div>
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-yellow-400">● Style Check</div>
            <div className="text-[9px] text-gray-500 mt-1">Priorité: Basse</div>
          </div>
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-gray-400">○ Telemetry</div>
            <div className="text-[9px] text-gray-500 mt-1">Priorité: Basse</div>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-xs font-semibold text-gray-300 mb-3">📊 Quality Metrics</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-gray-400">Cobertura de tests</span>
              <span className="text-[9px] text-green-400">85%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-gray-400">Documentation</span>
              <span className="text-[9px] text-yellow-400">70%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-gray-400">Standards</span>
              <span className="text-[9px] text-green-400">95%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
