import React from 'react';
import { ChatProvider } from './contexts/ChatContext';
import ChatWidget from './components/ChatWidget';

const App: React.FC = () => {
  // Use localhost/127.0.0.1 in browser; 0.0.0.0 is not routable from client
  const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const u = new URL(rawApiUrl);
  const apiUrl = u.hostname === '0.0.0.0'
    ? `${u.protocol}//localhost${u.port ? ':' + u.port : ''}`
    : rawApiUrl;
  const config = {
    apiUrl,
    storeId: 1,
  };

  return (
    <ChatProvider config={config}>
      <ChatWidget />
    </ChatProvider>
  );
};

export default App;
