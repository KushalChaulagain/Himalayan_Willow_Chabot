import React from 'react';
import ChatWindow from './ChatWindow';

const ChatWidget: React.FC = () => {
  return (
    <div className="chat-widget-container chat-widget-fullpage">
      <ChatWindow />
    </div>
  );
};

export default ChatWidget;
