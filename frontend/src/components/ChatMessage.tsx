import React from 'react';
import { Message } from '../types';
import ProductCard from './ProductCard';
import QuickReplies from './QuickReplies';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-800 border border-gray-200'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.message}</p>
          <p className={`text-xs mt-1 ${isUser ? 'text-primary-100' : 'text-gray-500'}`}>
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>

        {/* Product Cards */}
        {message.productCards && message.productCards.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.productCards.map((card) => (
              <ProductCard key={card.id} product={card} />
            ))}
          </div>
        )}

        {/* Quick Replies */}
        {message.quickReplies && message.quickReplies.length > 0 && (
          <QuickReplies options={message.quickReplies} />
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
