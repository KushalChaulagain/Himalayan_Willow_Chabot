import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// For development
if (import.meta.env.DEV) {
  const root = document.getElementById('root');
  if (root) {
    ReactDOM.createRoot(root).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  }
}

// For production embedding
export function init(config: { apiUrl: string; storeId: number }) {
  const container = document.createElement('div');
  container.id = 'himalayan-willow-chat';
  document.body.appendChild(container);

  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// Expose to window for script tag usage
if (typeof window !== 'undefined') {
  (window as any).HimalayanWillowChat = { init };
}
