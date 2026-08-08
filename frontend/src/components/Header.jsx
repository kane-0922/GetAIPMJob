import React from 'react';
import { MessageSquarePlus, Trash2 } from 'lucide-react';

export default function Header({ onNewChat, hasMessages }) {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white text-sm font-bold">AI</span>
        </div>
        <div>
          <h1 className="text-base font-semibold text-gray-800">AI 求职助手</h1>
          <p className="text-xs text-gray-400">AI 产品方向求职顾问</p>
        </div>
      </div>

      {hasMessages && (
        <button
          onClick={onNewChat}
          className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="新建对话"
        >
          <MessageSquarePlus size={16} />
          <span className="hidden sm:inline">新对话</span>
        </button>
      )}
    </header>
  );
}
