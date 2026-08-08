/**
 * Chat API layer - handles SSE streaming communication with the Agent backend.
 * 
 * The backend /stream_run endpoint expects:
 * {
 *   "content": {
 *     "query": {
 *       "prompt": [
 *         { "type": "text", "content": { "text": "user message" } }
 *       ]
 *     }
 *   }
 * }
 * 
 * SSE response events have types:
 * - message_start: response begins
 * - answer: text token chunk
 * - thinking: model thinking content
 * - tool_request: agent is calling a tool
 * - tool_response: tool returned result
 * - message_end: response complete
 * - error: error occurred
 */

const API_BASE = '';

/**
 * Build the request payload for /stream_run
 */
export function buildPayload(text, fileUrl = null, fileName = null) {
  const prompt = [];

  if (fileUrl) {
    prompt.push({
      type: 'upload_file',
      content: {
        upload_file: {
          url: fileUrl,
          file_name: fileName || 'file',
        },
      },
    });
  }

  if (text) {
    prompt.push({
      type: 'text',
      content: { text },
    });
  }

  return {
    content: {
      query: {
        prompt,
      },
    },
  };
}

/**
 * Stream a chat message via SSE and process events through callbacks.
 * Returns an AbortController so the caller can cancel the stream.
 */
export function streamChat(payload, callbacks) {
  const { onAnswer, onToolRequest, onToolResponse, onMessageStart, onMessageEnd, onError, onDone } = callbacks;

  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/stream_run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        onError?.(`HTTP ${response.status}: ${errorText}`);
        onDone?.();
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            try {
              const data = JSON.parse(dataStr);
              handleSSEEvent(data, callbacks);
            } catch {
              // Skip malformed JSON
            }
          } else if (line === '' && currentEvent) {
            currentEvent = '';
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        onError?.(err.message);
      }
    } finally {
      onDone?.();
    }
  })();

  return controller;
}

/**
 * Route an SSE event to the appropriate callback
 */
function handleSSEEvent(data, callbacks) {
  const { onAnswer, onToolRequest, onToolResponse, onMessageStart, onMessageEnd, onError } = callbacks;

  switch (data.type) {
    case 'message_start':
      onMessageStart?.(data);
      break;
    case 'answer':
      if (data.content?.answer) {
        onAnswer?.(data.content.answer);
      }
      break;
    case 'thinking':
      // Thinking content - could display in a collapsible section
      break;
    case 'tool_request':
      if (data.content?.tool_request) {
        onToolRequest?.(data.content.tool_request);
      }
      break;
    case 'tool_response':
      if (data.content?.tool_response) {
        onToolResponse?.(data.content.tool_response);
      }
      break;
    case 'message_end':
      onMessageEnd?.(data);
      break;
    case 'error':
      if (data.content?.error) {
        onError?.(data.content.error.error_msg || 'Unknown error');
      }
      break;
    default:
      break;
  }
}
