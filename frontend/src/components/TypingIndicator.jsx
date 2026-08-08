import React from 'react';

export default function TypingIndicator({ toolName }) {
  return (
    <div className="flex items-center gap-2 py-2 animate-fade-in">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0s' }}></span>
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.16s' }}></span>
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.32s' }}></span>
      </div>
      {toolName && (
        <span className="text-xs text-gray-400 ml-1">
          正在调用: {toolName}
        </span>
      )}
    </div>
  );
}
