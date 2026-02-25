import React, { useState, KeyboardEvent } from 'react';
import { useChatContext } from '../contexts/ChatContext';

const ChatInput: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const { sendMessage, isTyping } = useChatContext();

  const handleSend = async () => {
    if (inputText.trim() && !isTyping) {
      await sendMessage(inputText);
      setInputText('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      <div className="flex space-x-2">
        <label htmlFor="chat-input" className="sr-only">
          Type your message
        </label>
        <input
          id="chat-input"
          type="text"
          placeholder="Ask me about cricket gear..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isTyping}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          aria-label="Chat message input"
          aria-describedby="chat-help-text"
        />
        <button
          onClick={handleSend}
          disabled={!inputText.trim() || isTyping}
          className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="Send message"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
      <p id="chat-help-text" className="text-xs text-gray-500 mt-2">
        Press Enter to send
      </p>
    </div>
  );
};

export default ChatInput;
