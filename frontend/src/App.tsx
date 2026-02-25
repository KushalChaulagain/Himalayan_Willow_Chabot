import React from 'react';
import { ChatProvider } from './contexts/ChatContext';
import ChatWidget from './components/ChatWidget';

const App: React.FC = () => {
  const config = {
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    storeId: 1,
  };

  return (
    <ChatProvider config={config}>
      <ChatWidget />
    </ChatProvider>
  );
};

export default App;
