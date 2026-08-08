import React from 'react';
import {
  FileText,
  Search,
  Building2,
  BookOpen,
  MessageCircle,
} from 'lucide-react';

const actions = [
  {
    icon: FileText,
    label: '解析简历',
    prompt: '我想上传我的简历，请帮我解析并分析',
    color: 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100',
  },
  {
    icon: Search,
    label: 'JD匹配',
    prompt: '我有一个目标岗位的JD，请帮我分析匹配度',
    color: 'bg-green-50 text-green-600 border-green-200 hover:bg-green-100',
  },
  {
    icon: Building2,
    label: '企业背调',
    prompt: '帮我做一下企业背调',
    color: 'bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100',
  },
  {
    icon: BookOpen,
    label: '知识问答',
    prompt: '我想了解AI产品领域的专业知识',
    color: 'bg-orange-50 text-orange-600 border-orange-200 hover:bg-orange-100',
  },
  {
    icon: MessageCircle,
    label: '模拟面试',
    prompt: '我想开始模拟面试',
    color: 'bg-pink-50 text-pink-600 border-pink-200 hover:bg-pink-100',
  },
];

export default function WelcomeScreen({ onSendMessage }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 animate-fade-in">
      {/* Logo & Title */}
      <div className="mb-8 text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <span className="text-white text-2xl font-bold">AI</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">AI 求职助手</h1>
        <p className="text-gray-500 text-sm max-w-md">
          你的 AI 产品方向求职顾问，提供简历优化、JD匹配、企业背调、知识问答和模拟面试等一站式服务
        </p>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 max-w-2xl w-full mb-8">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              onClick={() => onSendMessage(action.prompt)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-200 ${action.color}`}
            >
              <Icon size={24} />
              <span className="text-xs font-medium">{action.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tips */}
      <div className="bg-white rounded-xl p-4 max-w-lg w-full shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">💡 使用提示</h3>
        <ul className="text-xs text-gray-500 space-y-1.5">
          <li>• 发送 <strong>简历文件 URL</strong> 即可自动解析分析</li>
          <li>• 粘贴 <strong>JD 文本</strong> 或发送 JD 截图进行匹配诊断</li>
          <li>• 输入 <strong>公司名称</strong> 进行企业背景调查</li>
          <li>• 随时提问 AI 产品领域的 <strong>专业问题</strong></li>
          <li>• 说 <strong>"模拟面试"</strong> 开始面试练习</li>
        </ul>
      </div>
    </div>
  );
}
