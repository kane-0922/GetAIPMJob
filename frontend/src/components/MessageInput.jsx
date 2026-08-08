import React, { useState, useRef } from 'react';
import { Send, Paperclip, X } from 'lucide-react';

export default function MessageInput({ onSend, isStreaming, onCancel }) {
  const [text, setText] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [attachedContent, setAttachedContent] = useState('');
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed && !attachedContent) return;
    if (isStreaming) return;

    // Combine file content with user text if file is attached
    let finalText = trimmed;
    if (attachedContent && trimmed) {
      finalText = `${trimmed}\n\n[附件文件: ${attachedFile.name}]\n文件内容:\n${attachedContent}`;
    } else if (attachedContent) {
      finalText = `请帮我解析这份简历文件。\n\n[附件文件: ${attachedFile.name}]\n文件内容:\n${attachedContent}`;
    }

    onSend(finalText);
    setText('');
    setAttachedFile(null);
    setAttachedContent('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e) => {
    setText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setAttachedFile(selectedFile);

    // Read text files directly
    if (selectedFile.name.endsWith('.txt')) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachedContent(event.target.result);
      };
      reader.readAsText(selectedFile);
    } else {
      // For PDF/DOCX, inform user to use URL
      setAttachedContent('');
      alert('PDF/Word 文件请上传到对象存储后，将 URL 粘贴到对话框中发送。\n\n当前仅支持直接读取 .txt 文件。');
      setAttachedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const removeFile = () => {
    setAttachedFile(null);
    setAttachedContent('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* File preview */}
      {attachedFile && (
        <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-blue-50 rounded-lg text-sm max-w-4xl mx-auto">
          <Paperclip size={14} className="text-blue-500" />
          <span className="text-blue-700 truncate flex-1">{attachedFile.name}</span>
          <span className="text-xs text-blue-400">已读取内容</span>
          <button onClick={removeFile} className="text-blue-400 hover:text-blue-600">
            <X size={14} />
          </button>
        </div>
      )}

      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        {/* File upload button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 p-2.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
          title="上传简历文件（支持 TXT，PDF/Word 请粘贴 URL）"
        >
          <Paperclip size={20} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf,.doc,.docx"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... 可直接粘贴简历/文件 URL (Shift+Enter 换行)"
            rows={1}
            className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all placeholder:text-gray-400"
            style={{ maxHeight: '150px' }}
          />
        </div>

        {/* Send / Cancel button */}
        {isStreaming ? (
          <button
            onClick={onCancel}
            className="flex-shrink-0 p-2.5 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors"
            title="停止生成"
          >
            <X size={20} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!text.trim() && !attachedContent}
            className="flex-shrink-0 p-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="发送消息"
          >
            <Send size={20} />
          </button>
        )}
      </div>
    </div>
  );
}
