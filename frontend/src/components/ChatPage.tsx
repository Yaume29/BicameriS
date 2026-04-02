import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: 'BicameriS initialisé. Les deux hémisphères sont en ligne.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState<{ left: boolean; right: boolean; corpus: boolean }>({
    left: false,
    right: false,
    corpus: false,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // Simulate bicameral response
    setIsTyping({ left: true, right: false, corpus: false });

    setTimeout(() => {
      setIsTyping({ left: false, right: false, corpus: false });
      const leftResp: Message = {
        id: `resp-l-${Date.now()}`,
        role: 'assistant-left',
        content: `[Analyse logique] J'ai analysé votre requête.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, leftResp]);

      setIsTyping({ left: false, right: true, corpus: false });
    }, 800);

    setTimeout(() => {
      setIsTyping({ left: false, right: false, corpus: false });
      const rightResp: Message = {
        id: `resp-r-${Date.now()}`,
        role: 'assistant-right',
        content: `[Intuition créative] Je perçois des connexions intéressantes.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, rightResp]);

      setIsTyping({ left: false, right: false, corpus: true });
    }, 1500);

    setTimeout(() => {
      setIsTyping({ left: false, right: false, corpus: false });
      const corpusResp: Message = {
        id: `resp-c-${Date.now()}`,
        role: 'corpus',
        content: `⚡ [Corpus Callosum] Synthèse bicamérale complète.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, corpusResp]);
    }, 2200);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
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
      {/* Chat Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500/30 to-purple-500/30 border border-gray-600 flex items-center justify-center">
            <span className="text-lg">🧠</span>
          </div>
          <div>
            <div className="text-sm font-semibold">BicameriS</div>
            <div className="flex items-center gap-1 text-[10px]">
              <span className={`${isTyping.left ? 'text-cyan-400 animate-pulse' : 'text-gray-500'}`}>●</span>
              <span className={`${isTyping.corpus ? 'text-green-400 animate-pulse' : 'text-gray-500'}`}>●</span>
              <span className={`${isTyping.right ? 'text-purple-400 animate-pulse' : 'text-gray-500'}`}>●</span>
              <span className="text-green-400 ml-1">En ligne</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
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

        {/* Typing Indicators */}
        {(isTyping.left || isTyping.right || isTyping.corpus) && (
          <div className="flex items-center gap-2">
            <div className="px-4 py-2 rounded-2xl bg-gray-800 border border-gray-700">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
            <span className="text-[9px] text-gray-500">
              {isTyping.left ? 'Hémisphère Gauche' : isTyping.right ? 'Hémisphère Droit' : 'Corpus'} écrit...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 bg-gray-800/80 p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message à BicameriS..."
            rows={1}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/40 resize-none"
            style={{ minHeight: '42px', maxHeight: '120px' }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white border border-purple-500/30 hover:from-cyan-500/30 hover:to-purple-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
