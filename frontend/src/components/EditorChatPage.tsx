import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
}

type SpecialistMode = 'chat' | 'research' | 'code' | 'osint';

export default function EditorChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'system', content: 'Éditeur Spécialiste activé. Sélectionnez un mode de fonctionnement.', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState({ left: false, right: false, corpus: false });
  const [mode, setMode] = useState<SpecialistMode>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    setIsTyping({ left: true, right: false, corpus: false });

    try {
      const res = await fetch('/api/specialist/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input, context: { mode } }),
      });
      const data = await res.json();

      setIsTyping({ left: false, right: false, corpus: false });

      if (data.result) {
        const content = typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2);
        const assistantMsg: Message = {
          id: `resp-${Date.now()}`,
          role: 'corpus',
          content: content,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMsg]);
      }
    } catch (err) {
      setIsTyping({ left: false, right: false, corpus: false });
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `Erreur: ${err}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const changeMode = async (newMode: SpecialistMode) => {
    setMode(newMode);
    setMessages(prev => [...prev, {
      id: `sys-${Date.now()}`,
      role: 'system',
      content: `Mode changé: ${newMode}`,
      timestamp: new Date()
    }]);
    
    try {
      await fetch('/api/specialist/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode }),
      });
    } catch {}
  };

  const getRoleStyle = (role: string) => {
    switch (role) {
      case 'user':
        return { bg: 'bg-blue-500/15', border: 'border-blue-500/20', align: 'justify-end', label: 'Vous', labelColor: 'text-blue-400' };
      case 'assistant-left':
        return { bg: 'bg-cyan-500/10', border: 'border-cyan-500/15', align: 'justify-start', label: 'Hémisphère Gauche', labelColor: 'text-cyan-400' };
      case 'assistant-right':
        return { bg: 'bg-purple-500/10', border: 'border-purple-500/15', align: 'justify-start', label: 'Hémisphère Droit', labelColor: 'text-purple-400' };
      case 'corpus':
        return { bg: 'bg-green-500/10', border: 'border-green-500/15', align: 'justify-center', label: 'Corpus Callosum', labelColor: 'text-green-400' };
      case 'system':
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-center', label: 'Système', labelColor: 'text-gray-400' };
      default:
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-start', label: '', labelColor: 'text-gray-400' };
    }
  };

  const modeColors: Record<SpecialistMode, { bg: string; icon: string }> = {
    chat: { bg: 'bg-blue-600', icon: '💬' },
    research: { bg: 'bg-purple-600', icon: '🔬' },
    code: { bg: 'bg-green-600', icon: '💻' },
    osint: { bg: 'bg-red-600', icon: '🕵️' },
  };

  return (
    <div className="flex h-full">
      {/* Mode Selector Sidebar */}
      <div className="w-16 bg-bg-secondary border-r border-border-subtle flex flex-col py-4 gap-2 px-2">
        {(['chat', 'research', 'code', 'osint'] as SpecialistMode[]).map(m => (
          <button
            key={m}
            onClick={() => changeMode(m)}
            className={`flex-1 flex items-center justify-center text-xl rounded-lg transition-all ${
              mode === m
                ? modeColors[m].bg
                : 'bg-bg-glass text-text-muted hover:bg-bg-hover'
            }`}
            title={m.charAt(0).toUpperCase() + m.slice(1)}
          >
            {modeColors[m].icon}
          </button>
        ))}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle bg-bg-secondary/80">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${modeColors[mode].bg} border border-border-accent flex items-center justify-center`}>
              <span className="text-lg">{modeColors[mode].icon}</span>
            </div>
            <div>
              <div className="text-sm font-semibold">Éditeur Spécialiste</div>
              <div className="flex items-center gap-1 text-[10px]">
                <span className={`${isTyping.left ? 'text-cyan-400 animate-pulse' : 'text-text-muted'}`}>●</span>
                <span className={`${isTyping.corpus ? 'text-green-400 animate-pulse' : 'text-text-muted'}`}>●</span>
                <span className={`${isTyping.right ? 'text-purple-400 animate-pulse' : 'text-text-muted'}`}>●</span>
                <span className="text-accent-green ml-1">En ligne</span>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map(msg => {
            const style = getRoleStyle(msg.role);
            return (
              <div key={msg.id} className={`flex ${style.align}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${style.bg} ${style.border} border shadow-sm`}>
                  <div className={`text-[9px] font-semibold mb-1 ${style.labelColor}`}>{style.label}</div>
                  <div className="text-xs text-text-primary leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            );
          })}

          {(isTyping.left || isTyping.right || isTyping.corpus) && (
            <div className="flex items-center gap-2">
              <div className="px-4 py-2 rounded-2xl bg-bg-tertiary border border-border-subtle">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
              <span className="text-[9px] text-text-muted">
                {isTyping.left ? 'Hémisphère Gauche' : isTyping.right ? 'Hémisphère Droit' : 'Corpus'} écrit...
              </span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border-subtle bg-bg-secondary/80 p-3">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={`Message en mode ${mode}...`}
              rows={1}
              className="flex-1 bg-bg-primary border border-border-subtle rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/40 resize-none"
              style={{ minHeight: '42px', maxHeight: '120px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="p-2.5 rounded-xl bg-gradient-to-r from-accent-cyan/20 to-accent-purple/20 text-text-primary border border-accent-purple/30 hover:from-accent-cyan/30 hover:to-accent-purple/30 transition-all disabled:opacity-50"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M16 2L9 9M16 2L11 16L9 9M16 2L2 7L9 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
