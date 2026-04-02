import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import type { Message, StreamEvent, AppMode, SpecialistStatus } from '../types/api';

const API_BASE = '/api/specialist';
const THROTTLE_MS = 50;
const RECONNECT_DELAY = 2000;
const MAX_RECONNECT_ATTEMPTS = 3;

type CurrentSpeaker = 'left' | 'right' | 'corpus' | 'none';

interface UseBicameralStreamOptions {
  mode: AppMode;
  autoConnect?: boolean;
}

interface UseBicameralStreamReturn {
  messages: Message[];
  isTyping: { left: boolean; right: boolean; corpus: boolean };
  currentSpeaker: CurrentSpeaker;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  sendMessage: (input: string, context?: Record<string, unknown>) => Promise<void>;
  changeMode: (mode: AppMode) => Promise<void>;
  clearMessages: () => void;
  retryConnection: () => void;
}

export function useBicameralStream(options: UseBicameralStreamOptions): UseBicameralStreamReturn {
  const { mode, autoConnect = true } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState<{ left: boolean; right: boolean; corpus: boolean }>({
    left: false,
    right: false,
    corpus: false,
  });
  const [currentSpeaker, setCurrentSpeaker] = useState<CurrentSpeaker>('none');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const bufferRef = useRef<Message[]>([]);
  const throttleTimerRef = useRef<number | null>(null);
  const lastUpdateRef = useRef<number>(0);
  
  const activeMessageIdRef = useRef<string | null>(null);
  const activeMessageRoleRef = useRef<string | null>(null);

  const initializeSession = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, capabilities: {} }),
      });
      const data = await response.json();
      return data;
    } catch (err) {
      const msg = `Init failed: ${err}`;
      setError(msg);
      return null;
    }
  }, [mode]);

  const changeMode = useCallback(async (newMode: AppMode) => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode }),
      });
      const data = await response.json();
      if (data.status !== 'ok') {
        throw new Error(data.message || 'Mode change failed');
      }
      return data;
    } catch (err) {
      const msg = `Mode change failed: ${err}`;
      setError(msg);
      return null;
    }
  }, []);

  const sendMessage = useCallback(async (input: string, context: Record<string, unknown> = {}) => {
    setError(null);
    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    const userMessage: Message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping({ left: true, right: false, corpus: false });
    setCurrentSpeaker('left');

    try {
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input,
          context: { ...context, mode, session_id: `session-${Date.now()}` },
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      setIsTyping({ left: false, right: false, corpus: false });
      setCurrentSpeaker('none');

      if (data.status === 'ok') {
        const result = data.result || {};
        const content = typeof result === 'string' ? result : JSON.stringify(result, null, 2);

        const assistantMessage: Message = {
          id: `resp-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          role: 'corpus',
          content: content,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error(data.message || 'Processing failed');
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setError(null);
      } else {
        const msg = `Error: ${err}`;
        setError(msg);
        setIsTyping({ left: false, right: false, corpus: false });
        setCurrentSpeaker('none');
      }
    } finally {
      setIsLoading(false);
    }
  }, [mode]);

  const flushBuffer = useCallback(() => {
    if (bufferRef.current.length === 0) return;

    const now = Date.now();
    if (now - lastUpdateRef.current < THROTTLE_MS) {
      if (!throttleTimerRef.current) {
        throttleTimerRef.current = window.setTimeout(() => {
          flushBuffer();
          throttleTimerRef.current = null;
        }, THROTTLE_MS);
      }
      return;
    }

    setMessages((prev) => [...prev, ...bufferRef.current]);
    bufferRef.current = [];
    lastUpdateRef.current = now;
  }, []);

  const handleStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case 'thinking':
        if (event.role === 'assistant-left') {
          setIsTyping((prev) => ({ ...prev, left: true }));
          setCurrentSpeaker('left');
        } else if (event.role === 'assistant-right') {
          setIsTyping((prev) => ({ ...prev, right: true }));
          setCurrentSpeaker('right');
        }
        break;

      case 'message':
        if (event.content) {
          const incomingRole = event.role || 'corpus';
          
          if (activeMessageIdRef.current && activeMessageRoleRef.current === incomingRole) {
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg && lastMsg.id === activeMessageIdRef.current) {
                lastMsg.content += event.content;
              }
              return updated;
            });
          } else {
            activeMessageIdRef.current = `stream-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
            activeMessageRoleRef.current = incomingRole;
            
            const msg: Message = {
              id: activeMessageIdRef.current,
              role: incomingRole as Message['role'],
              content: event.content,
              timestamp: new Date().toISOString(),
            };
            bufferRef.current.push(msg);
            flushBuffer();
          }
        }
        break;

      case 'status':
        setIsTyping({ left: false, right: false, corpus: false });
        setCurrentSpeaker('none');
        activeMessageIdRef.current = null;
        activeMessageRoleRef.current = null;
        break;

      case 'error':
        setError(event.content);
        setIsTyping({ left: false, right: false, corpus: false });
        setCurrentSpeaker('none');
        activeMessageIdRef.current = null;
        activeMessageRoleRef.current = null;

        const errorMsg: Message = {
          id: `error-${Date.now()}`,
          role: 'system',
          content: `[Erreur de Flux - Entropie réseau détectée] ${event.content}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
        break;

      case 'complete':
        setIsTyping({ left: false, right: false, corpus: false });
        setCurrentSpeaker('none');
        activeMessageIdRef.current = null;
        activeMessageRoleRef.current = null;
        reconnectAttemptsRef.current = 0;
        break;

      case 'heartbeat':
        break;
    }
  }, [flushBuffer]);

  const subscribeToStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    eventSource.onmessage = (rawEvent) => {
      try {
        const data: StreamEvent = JSON.parse(rawEvent.data);
        handleStreamEvent(data);
      } catch (err) {
        console.error('Stream parse error:', err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);

      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current += 1;
        setTimeout(() => {
          subscribeToStream();
        }, RECONNECT_DELAY * reconnectAttemptsRef.current);
      } else {
        const errorMsg = '[Erreur de Flux - Entropie réseau détectée] Connexion perdue. Tentatives de reconnexion épuisées.';
        setError(errorMsg);

        const systemMsg: Message = {
          id: `conn-error-${Date.now()}`,
          role: 'system',
          content: errorMsg,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, systemMsg]);
      }
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [handleStreamEvent]);

  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (throttleTimerRef.current) {
      clearTimeout(throttleTimerRef.current);
      throttleTimerRef.current = null;
    }
    setIsTyping({ left: false, right: false, corpus: false });
    setCurrentSpeaker('none');
    setIsLoading(false);
  }, []);

  const clearMessages = useCallback(() => {
    bufferRef.current = [];
    setMessages([]);
    activeMessageIdRef.current = null;
    activeMessageRoleRef.current = null;
  }, []);

  const retryConnection = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    subscribeToStream();
  }, [subscribeToStream]);

  useEffect(() => {
    if (!autoConnect) return;

    initializeSession();
    const cleanupStream = subscribeToStream();

    return () => {
      cleanupStream();
      cancelRequest();
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
      }
    };
  }, [mode, autoConnect]);

  return useMemo(() => ({
    messages,
    isTyping,
    currentSpeaker,
    isConnected,
    isLoading,
    error,
    sendMessage,
    changeMode,
    clearMessages,
    retryConnection,
  }), [messages, isTyping, currentSpeaker, isConnected, isLoading, error, sendMessage, changeMode, clearMessages, retryConnection]);
}
