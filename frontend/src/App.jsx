import React from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import WelcomeScreen from './components/WelcomeScreen';
import { useChat } from './hooks/useChat';

function App() {
  const { messages, isStreaming, currentTool, sendMessage, cancelStream, clearMessages } = useChat();
  const hasMessages = messages.length > 0;

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header onNewChat={clearMessages} hasMessages={hasMessages} />

      {/* Main content area */}
      {hasMessages ? (
        <ChatWindow
          messages={messages}
          isStreaming={isStreaming}
          currentTool={currentTool}
        />
      ) : (
        <div className="flex-1 overflow-y-auto">
          <WelcomeScreen onSendMessage={sendMessage} />
        </div>
      )}

      <MessageInput
        onSend={sendMessage}
        isStreaming={isStreaming}
        onCancel={cancelStream}
      />
    </div>
  );
}

export default App;
