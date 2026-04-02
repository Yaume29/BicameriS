import { useRef, useEffect } from 'react';
import { useBicameralStream } from '../hooks/useBicameralStream';
import type { Message, AppMode } from '../types/api';

const MODE: AppMode = 'chat';

export default function ChatPage() {
  const {
    messages,
    isTyping,
    isConnected,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  } = useBicameralStream({ mode: MODE, autoConnect: true });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const input = inputRef.current;
    if (!input || !input.value.trim()) return;

    const value = input.value;
    input.value = '';
    await sendMessage(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
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

  const getConnectionStatus = () => {
    if (error) return { color: 'text-red-400', text: 'Erreur' };
    if (isLoading) return { color: 'text-yellow-400', text: 'Traitement...' };
    if (!isConnected) return { color: 'text-gray-500', text: 'Déconnecté' };
    return { color: 'text-green-400', text: 'En ligne' };
  };

  const status = getConnectionStatus();

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
              <span className={`${status.color} ml-1`}>{status.text}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex justify-center py-8">
            <div className="text-xs text-gray-500">
              BicameriS initialisé. Les deux hemispheres sont en ligne.
            </div>
          </div>
        )}

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
            ref={inputRef}
            onKeyDown={handleKeyDown}
            placeholder="Message à BicameriS..."
            rows={1}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/40 resize-none"
            style={{ minHeight: '42px', maxHeight: '120px' }}
            disabled={!isConnected || isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!isConnected || isLoading}
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
