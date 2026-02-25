import React from 'react';
import { useChatContext } from '../contexts/ChatContext';

interface QuickRepliesProps {
  options: string[];
}

const QuickReplies: React.FC<QuickRepliesProps> = ({ options }) => {
  const { sendMessage } = useChatContext();

  return (
    <div className="flex flex-wrap gap-2 mt-3" role="group" aria-label="Quick reply options">
      {options.map((option, index) => (
        <button
          key={index}
          onClick={() => sendMessage(option)}
          className="bg-white hover:bg-primary-50 border border-primary-600 text-primary-600 text-sm py-2 px-4 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
          tabIndex={0}
        >
          {option}
        </button>
      ))}
    </div>
  );
};

export default QuickReplies;
