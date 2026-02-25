import React, { useState } from 'react';
import ChatWindow from './ChatWindow';

const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="chat-widget-container">
      {isOpen ? (
        <ChatWindow onClose={() => setIsOpen(false)} />
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="w-16 h-16 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110"
          aria-label="Open chat"
        >
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

export default ChatWidget;
