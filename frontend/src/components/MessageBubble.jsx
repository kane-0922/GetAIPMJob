import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json';
import markdown from 'react-syntax-highlighter/dist/esm/languages/prism/markup';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Register languages
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('js', javascript);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('py', python);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('html', markdown);
SyntaxHighlighter.registerLanguage('markdown', markdown);
import { Bot, User, ChevronDown, ChevronUp, Wrench } from 'lucide-react';

function ToolCallBadge({ toolCall }) {
  const [expanded, setExpanded] = useState(false);
  const isRunning = toolCall.status === 'running';

  return (
    <div className="mb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-colors ${
          isRunning
            ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
            : 'bg-gray-50 border-gray-200 text-gray-600'
        }`}
      >
        <Wrench size={12} />
        <span>{toolCall.name}</span>
        {isRunning && (
          <span className="flex gap-0.5 ml-1">
            <span className="w-1 h-1 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
            <span className="w-1 h-1 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
            <span className="w-1 h-1 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
          </span>
        )}
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {expanded && toolCall.result && (
        <div className="mt-1 text-xs bg-gray-50 border border-gray-200 rounded-lg p-2 max-h-40 overflow-y-auto text-gray-600">
          <pre className="whitespace-pre-wrap break-words">{toolCall.result}</pre>
        </div>
      )}
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser
          ? 'bg-gradient-to-br from-green-400 to-green-600'
          : 'bg-gradient-to-br from-blue-500 to-purple-600'
      }`}>
        {isUser ? (
          <User size={16} className="text-white" />
        ) : (
          <Bot size={16} className="text-white" />
        )}
      </div>

      {/* Message content */}
      <div className={`max-w-[75%] ${isUser ? 'text-right' : ''}`}>
        {/* Tool calls */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-2">
            {message.toolCalls.map((tc, idx) => (
              <ToolCallBadge key={idx} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Bubble */}
        <div className={`inline-block text-left rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-500 text-white'
            : message.isError
              ? 'bg-red-50 border border-red-200 text-red-700'
              : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
        }`}>
          {isUser ? (
            <div>
              {message.fileUrl && (
                <div className="mb-1 text-xs opacity-80">
                  📎 {message.fileName || 'file'}
                </div>
              )}
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
            </div>
          ) : (
            <div className="markdown-content text-sm">
              {message.content ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              ) : message.isStreaming ? (
                <div className="flex gap-1 py-1">
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce-dot" style={{ animationDelay: '0s' }}></span>
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce-dot" style={{ animationDelay: '0.16s' }}></span>
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce-dot" style={{ animationDelay: '0.32s' }}></span>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {message.timestamp?.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
