import React from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import ChatWidget from './components/ChatWidget';

const App: React.FC = () => {
  // Use localhost/127.0.0.1 in browser; 0.0.0.0 is not routable from client
  const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const u = new URL(rawApiUrl);
  const apiUrl = u.hostname === '0.0.0.0'
    ? `${u.protocol}//localhost${u.port ? ':' + u.port : ''}`
    : rawApiUrl;
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const config = {
    apiUrl,
    storeId: 1,
    googleClientId: googleClientId || undefined,
  };

  const content = (
    <AuthProvider>
      <ChatProvider config={config}>
        <ChatWidget />
      </ChatProvider>
    </AuthProvider>
  );

  return googleClientId ? (
    <GoogleOAuthProvider clientId={googleClientId}>{content}</GoogleOAuthProvider>
  ) : (
    content
  );
};

export default App;
