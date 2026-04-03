import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const messages: Message[] = [];
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    setInput('');
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 1000);
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

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle bg-bg-secondary/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-cyan/30 to-accent-purple/30 border border-border-accent flex items-center justify-center">
            <span className="text-lg">🧠</span>
          </div>
          <div>
            <div className="text-sm font-semibold">BicameriS Chat</div>
            <div className="flex items-center gap-1 text-[10px]">
              <span className="text-accent-cyan">●</span>
              <span className="text-accent-purple">●</span>
              <span className="text-accent-green ml-1">En ligne</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex justify-center py-8">
            <div className="text-xs text-text-muted text-center">
              <div className="text-lg mb-2">🧠</div>
              <div>Bienvenue sur BicameriS</div>
              <div className="text-[10px] mt-1">Commencez une conversation avec le cortex bicaméral</div>
            </div>
          </div>
        )}

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

        {isTyping && (
          <div className="flex items-center gap-2">
            <div className="px-4 py-2 rounded-2xl bg-bg-tertiary border border-border-subtle">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
            <span className="text-[9px] text-text-muted">Pensée en cours...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border-subtle bg-bg-secondary/80 p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Message à BicameriS..."
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
  );
}
