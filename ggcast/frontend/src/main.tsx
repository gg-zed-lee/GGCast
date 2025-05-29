import React from 'react'; // Changed from 'react' to 'react' for consistency, StrictMode not used here
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App'; // Assuming App.tsx extension is resolved by build tool
import { WebSocketProvider } from './contexts/WebSocketContext';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Failed to find the root element');

const root = createRoot(rootElement);

root.render(
  <React.StrictMode>
    {' '}
    {/* Keep StrictMode for development benefits */}
    <WebSocketProvider>
      <App />
    </WebSocketProvider>
  </React.StrictMode>
);
