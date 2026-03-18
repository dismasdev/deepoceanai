'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface BridgeTranscriptMessage {
  id: string;
  timestamp: number;
  from: {
    isLocal: boolean;
  };
  message: string;
}

const DEFAULT_BACKEND_BASE = 'http://127.0.0.1:8000';

function buildWsUrl(httpBase: string): string {
  const trimmed = httpBase.replace(/\/$/, '');
  if (trimmed.startsWith('https://')) {
    return `${trimmed.replace('https://', 'wss://')}/ws/stream`;
  }
  if (trimmed.startsWith('http://')) {
    return `${trimmed.replace('http://', 'ws://')}/ws/stream`;
  }
  return `ws://${trimmed}/ws/stream`;
}

function isChunkEvent(event: string): boolean {
  return event === 'idea_chunk' || event === 'plan_chunk';
}

export function useFastApiBridge() {
  const backendBase = process.env.NEXT_PUBLIC_BACKEND_API_BASE?.trim() || DEFAULT_BACKEND_BASE;
  const wsUrl = useMemo(() => buildWsUrl(backendBase), [backendBase]);

  const wsRef = useRef<WebSocket | null>(null);
  const pendingChunksRef = useRef<string>('');
  const pendingMessageIdRef = useRef<string | null>(null);

  const [messages, setMessages] = useState<BridgeTranscriptMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAudioUrl, setLastAudioUrl] = useState<string | null>(null);

  const appendMessage = useCallback((message: BridgeTranscriptMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const updatePendingAssistantMessage = useCallback(
    (text: string) => {
      if (!pendingMessageIdRef.current) {
        pendingMessageIdRef.current = crypto.randomUUID();
        appendMessage({
          id: pendingMessageIdRef.current,
          timestamp: Date.now(),
          from: { isLocal: false },
          message: text,
        });
        return;
      }

      const pendingId = pendingMessageIdRef.current;
      setMessages((prev) =>
        prev.map((msg) => (msg.id === pendingId ? { ...msg, message: text } : msg))
      );
    },
    [appendMessage]
  );

  const resetPendingAssistant = useCallback(() => {
    pendingChunksRef.current = '';
    pendingMessageIdRef.current = null;
  }, []);

  const handleIncomingMessage = useCallback(
    (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as Record<string, unknown>;
        const eventType = String(payload.event ?? '');

        if (eventType === 'error') {
          const err = String(payload.error ?? 'Bridge stream error');
          setError(err);
          setIsStreaming(false);
          appendMessage({
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            from: { isLocal: false },
            message: `Backend error: ${err}`,
          });
          resetPendingAssistant();
          return;
        }

        if (isChunkEvent(eventType)) {
          const chunk = String(payload.chunk ?? '');
          pendingChunksRef.current += chunk;
          updatePendingAssistantMessage(pendingChunksRef.current);
          return;
        }

        if (eventType === 'final') {
          const idea = String(payload.idea ?? '').trim();
          const plan = String(payload.plan ?? '').trim();
          const fullMessage = `Idea:\n${idea}\n\nPlan:\n${plan}`.trim();
          updatePendingAssistantMessage(fullMessage);
          return;
        }

        if (eventType === 'audio_ready') {
          const rawAudioUrl = String(payload.audio_url ?? '').trim();
          if (rawAudioUrl) {
            const resolvedAudioUrl = rawAudioUrl.startsWith('http')
              ? rawAudioUrl
              : `${backendBase}${rawAudioUrl}`;
            setLastAudioUrl(resolvedAudioUrl);
            const audio = new Audio(resolvedAudioUrl);
            void audio.play().catch(() => {
              // Auto-play can be blocked by browser policy; UI remains functional.
            });
          }
          setIsStreaming(false);
          resetPendingAssistant();
        }
      } catch {
        setError('Failed to parse bridge stream payload');
        setIsStreaming(false);
        resetPendingAssistant();
      }
    },
    [appendMessage, backendBase, resetPendingAssistant, updatePendingAssistantMessage]
  );

  const connectSocket = useCallback(async (): Promise<WebSocket> => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    return await new Promise<WebSocket>((resolve, reject) => {
      ws.onopen = () => resolve(ws);
      ws.onmessage = handleIncomingMessage;
      ws.onerror = () => reject(new Error('Failed to connect to backend stream'));
      ws.onclose = () => {
        wsRef.current = null;
      };
    });
  }, [handleIncomingMessage, wsUrl]);

  const sendTextToBackend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) {
        return;
      }

      setError(null);
      setIsStreaming(true);
      resetPendingAssistant();

      appendMessage({
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        from: { isLocal: true },
        message: trimmed,
      });

      const ws = await connectSocket();
      ws.send(JSON.stringify({ text: trimmed, stream: true }));
    },
    [appendMessage, connectSocket, resetPendingAssistant]
  );

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return {
    backendBase,
    messages,
    isStreaming,
    error,
    lastAudioUrl,
    sendTextToBackend,
  };
}
