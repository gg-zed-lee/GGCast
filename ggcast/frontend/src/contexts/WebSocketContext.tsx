import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from 'react';
// Adjust the path based on the actual location of your shared schema
// Assuming this file is in /app/ggcast/frontend/src/contexts/
// And events.ts is in /app/ggcast/shared/schema/
import {
  GameState,
  ActionEvent,
  PlayerState,
} from '../../../../shared/schema/events';

interface WebSocketContextType {
  gameState: GameState | null;
  isConnected: boolean;
  sendAction: (actionEvent: ActionEvent) => void;
  sendAdminNewHand: () => void; // Added for convenience
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(
  undefined
);

interface WebSocketProviderProps {
  children: ReactNode;
}

// Determine WebSocket URL based on environment
const WS_URL =
  process.env.NODE_ENV === 'production'
    ? `wss://${window.location.host}/ws/game` // Example for production
    : 'ws://localhost:3000/ws/game'; // For local development (proxied by Caddy)

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
}) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    setSocket(ws);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data as string);
        // Assuming the server sends the full GameState object directly
        // Add type checking or validation if necessary
        setGameState(message as GameState);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setSocket(null); // Clear socket state
      // Optional: Implement reconnection logic here
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      // ws.close(); // Ensure closure on error
    };

    // Cleanup function
    return () => {
      if (
        ws.readyState === WebSocket.OPEN ||
        ws.readyState === WebSocket.CONNECTING
      ) {
        ws.close();
      }
      setSocket(null);
    };
  }, []); // Empty dependency array means this runs once on mount and cleans up on unmount

  const sendAction = useCallback(
    (actionEvent: ActionEvent) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(actionEvent));
      } else {
        console.error('WebSocket is not connected.');
      }
    },
    [socket]
  );

  const sendAdminNewHand = useCallback(() => {
    sendAction({ type: 'ADMIN_NEW_HAND', payload: {} }); // Assuming empty payload for now
  }, [sendAction]);

  return (
    <WebSocketContext.Provider
      value={{ gameState, isConnected, sendAction, sendAdminNewHand }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
