import React, { useRef, useEffect } from 'react';
import { useChatContext } from '../contexts/ChatContext';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

interface ChatWindowProps {
  onClose: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ onClose }) => {
  const { messages, isTyping } = useChatContext();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col overflow-hidden md:w-96 md:h-[600px] max-md:w-screen max-md:h-screen max-md:rounded-none">
      {/* Header */}
      <div className="bg-primary-600 text-white p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-primary-600 font-bold">
            HW
          </div>
          <div>
            <h3 className="font-semibold">Himalayan Willow</h3>
            <p className="text-xs text-primary-100">Cricket Equipment Store</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:text-primary-100 transition-colors"
          aria-label="Close chat"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isTyping && (
          <div className="flex items-center space-x-2 text-gray-500">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm">Typing...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput />
    </div>
  );
};

export default ChatWindow;
