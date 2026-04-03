import { useEffect, useRef, useState, useCallback } from 'react';

interface BrainStreamOptions {
  onThinking?: (hemisphere: 'left' | 'right' | 'corpus', active: boolean) => void;
  onMessage?: (role: string, content: string) => void;
}

export function useBrainStream(options: BrainStreamOptions) {
  const { onThinking, onMessage } = options;
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [thinking, setThinking] = useState({ left: false, right: false, corpus: false });

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/brain`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'thinking':
              setThinking(prev => {
                const updated = { ...prev };
                if (data.hemisphere === 'left') updated.left = data.active;
                else if (data.hemisphere === 'right') updated.right = data.active;
                else if (data.hemisphere === 'corpus') updated.corpus = data.active;
                return updated;
              });
              onThinking?.(data.hemisphere, data.active);
              break;
              
            case 'message':
              onMessage?.(data.role, data.content);
              break;
              
            case 'pong':
              break;
          }
        } catch (err) {
          console.error('Brain stream parse error:', err);
        }
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        reconnectTimerRef.current = window.setTimeout(() => {
          connect();
        }, 2000);
      };
      
      wsRef.current.onerror = () => {
        setIsConnected(false);
      };
      
    } catch (err) {
      console.error('WebSocket connection error:', err);
    }
  }, [onThinking, onMessage]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    thinking,
    send,
    connect,
    disconnect,
  };
}

export function useChatStream() {
  const [messages, setMessages] = useState<{ id: string; role: string; content: string; timestamp: string }[]>([]);
  const [isTyping, setIsTyping] = useState({ left: false, right: false, corpus: false });
  const [currentSpeaker, setCurrentSpeaker] = useState<'left' | 'right' | 'corpus' | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource('/api/specialist/stream');
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'thinking':
            setIsTyping(prev => {
              const updated = { ...prev };
              if (data.role === 'assistant-left') {
                updated.left = true;
                setCurrentSpeaker('left');
              } else if (data.role === 'assistant-right') {
                updated.right = true;
                setCurrentSpeaker('right');
              } else if (data.role === 'corpus') {
                updated.corpus = true;
                setCurrentSpeaker('corpus');
              }
              return updated;
            });
            break;
            
          case 'message':
            setMessages(prev => [...prev, {
              id: data.id || `msg-${Date.now()}`,
              role: data.role || 'corpus',
              content: data.content,
              timestamp: data.timestamp || new Date().toISOString(),
            }]);
            break;
            
          case 'status':
          case 'complete':
            setIsTyping({ left: false, right: false, corpus: false });
            setCurrentSpeaker(null);
            break;
            
          case 'error':
            setMessages(prev => [...prev, {
              id: `error-${Date.now()}`,
              role: 'system',
              content: data.content,
              timestamp: new Date().toISOString(),
            }]);
            setIsTyping({ left: false, right: false, corpus: false });
            setCurrentSpeaker(null);
            break;
        }
      } catch (err) {
        console.error('Chat stream error:', err);
      }
    };

    eventSource.onerror = () => {
      setIsTyping({ left: false, right: false, corpus: false });
      setCurrentSpeaker(null);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  return {
    messages,
    isTyping,
    currentSpeaker,
    clearMessages,
  };
}
