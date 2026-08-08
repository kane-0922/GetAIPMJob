import { useState, useRef, useCallback } from 'react';
import { buildPayload, streamChat } from '../api/chat';

/**
 * Custom hook for managing chat state and streaming communication.
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);
  const abortControllerRef = useRef(null);

  const sendMessage = useCallback((text) => {
    if (!text || !text.trim()) return;

    // Add user message
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    // Add placeholder for assistant response
    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      toolCalls: [],
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setCurrentTool(null);

    const payload = buildPayload(text);

    const controller = streamChat(payload, {
      onAnswer: (token) => {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMsgId
              ? { ...msg, content: msg.content + token }
              : msg
          )
        );
      },
      onToolRequest: (toolReq) => {
        setCurrentTool(toolReq.tool_name);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  toolCalls: [...(msg.toolCalls || []), {
                    name: toolReq.tool_name,
                    status: 'running',
                    parameters: toolReq.parameters,
                  }],
                }
              : msg
          )
        );
      },
      onToolResponse: (toolResp) => {
        setCurrentTool(null);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  toolCalls: (msg.toolCalls || []).map(tc =>
                    tc.status === 'running'
                      ? { ...tc, status: 'done', result: toolResp.result }
                      : tc
                  ),
                }
              : msg
          )
        );
      },
      onMessageStart: () => {},
      onMessageEnd: () => {},
      onError: (error) => {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMsgId
              ? { ...msg, content: msg.content + `\n\n⚠️ 错误: ${error}`, isError: true, isStreaming: false }
              : msg
          )
        );
      },
      onDone: () => {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMsgId
              ? { ...msg, isStreaming: false }
              : msg
          )
        );
        setIsStreaming(false);
        setCurrentTool(null);
      },
    });

    abortControllerRef.current = controller;
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setCurrentTool(null);
    // Mark the last streaming message as done
    setMessages(prev => {
      const updated = [...prev];
      for (let i = updated.length - 1; i >= 0; i--) {
        if (updated[i].isStreaming) {
          updated[i] = { ...updated[i], isStreaming: false };
          break;
        }
      }
      return updated;
    });
  }, []);

  const clearMessages = useCallback(() => {
    cancelStream();
    setMessages([]);
  }, [cancelStream]);

  return {
    messages,
    isStreaming,
    currentTool,
    sendMessage,
    cancelStream,
    clearMessages,
  };
}
