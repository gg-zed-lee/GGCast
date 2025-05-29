import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { PlayerState } from '../../../../shared/schema/events'; // Adjust path as needed

// Helper to get card display value (e.g., "AS" -> "As", "10H" -> "Th")
// This is a simple version; a real one would handle suits and ranks better.
const formatCard = (
  cardStr: string
): { rank: string; suit: string; display: string } => {
  if (!cardStr || cardStr.length < 2)
    return { rank: '?', suit: '', display: '?' };
  let rank = cardStr.slice(0, -1).toUpperCase();
  const suit = cardStr.slice(-1).toLowerCase();

  // Normalize rank for display (e.g., 10 -> T)
  if (rank === '10') rank = 'T';
  if (rank === '1') rank = 'A'; // Or however A is represented

  // Suit symbols (optional, can use letters)
  const suitSymbols: { [key: string]: string } = {
    h: '♥',
    d: '♦',
    c: '♣',
    s: '♠',
  };
  const suitDisplay = suitSymbols[suit] || suit;

  return { rank, suit, display: `${rank}${suitDisplay}` };
};

const Card: React.FC<{ card?: string | null; isHidden?: boolean }> = ({
  card,
  isHidden,
}) => {
  if (isHidden || !card) {
    return (
      <div className="w-16 h-24 bg-gray-600 border-2 border-gray-700 rounded-md shadow-md flex items-center justify-center text-gray-400">
        ?
      </div>
    );
  }
  const { rank, suit } = formatCard(card);
  const color = suit === 'h' || suit === 'd' ? 'text-red-500' : 'text-black';

  return (
    <div
      className={`w-16 h-24 bg-white border-2 border-gray-300 rounded-md shadow-md flex flex-col items-center justify-center p-1 ${color}`}
    >
      <span className="text-2xl font-bold">{rank}</span>
      <span className="text-xl">
        {formatCard(card).suit === 'h'
          ? '♥'
          : formatCard(card).suit === 'd'
            ? '♦'
            : formatCard(card).suit === 'c'
              ? '♣'
              : '♠'}
      </span>
    </div>
  );
};

const PlayerOverlayCard: React.FC<{ card?: string | null }> = ({ card }) => {
  if (!card) {
    return (
      <div className="w-10 h-14 bg-gray-600 border border-gray-700 rounded flex items-center justify-center text-gray-400 text-xs">
        ?
      </div>
    );
  }
  const { rank, suit } = formatCard(card);
  const color = suit === 'h' || suit === 'd' ? 'text-red-500' : 'text-black';
  return (
    <div
      className={`w-10 h-14 bg-white border border-gray-300 rounded flex flex-col items-center justify-center p-0.5 ${color} text-xs`}
    >
      <span className="text-lg font-bold">{rank}</span>
      <span className="text-sm">
        {formatCard(card).suit === 'h'
          ? '♥'
          : formatCard(card).suit === 'd'
            ? '♦'
            : formatCard(card).suit === 'c'
              ? '♣'
              : '♠'}
      </span>
    </div>
  );
};

const OverlayPage: React.FC = () => {
  const { gameState, isConnected } = useWebSocket();
  const [scale, setScale] = useState(1); // For testing scaling

  // Example: Listen to parent window messages for scale changes (if embedded in an iframe)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data && typeof event.data.scale === 'number') {
        setScale(event.data.scale);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  if (!isConnected) {
    return (
      <div className="p-4 text-red-500 bg-black min-h-screen">
        WebSocket not connected. Overlay unavailable.
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="p-4 bg-black min-h-screen text-white">
        Loading game state...
      </div>
    );
  }

  // Define player positions (example for up to 10 players)
  // These would need to be adjusted based on your desired layout and number of players.
  // For simplicity, using absolute positioning within a relative container.
  // This is a very basic layout example.
  const playerPositions = [
    { top: '80%', left: '45%' }, // Seat 0 (bottom center)
    { top: '70%', left: '15%' }, // Seat 1 (bottom left)
    { top: '40%', left: '5%' }, // Seat 2 (middle left)
    { top: '10%', left: '15%' }, // Seat 3 (top left)
    { top: '5%', left: '45%' }, // Seat 4 (top center)
    { top: '10%', left: '75%' }, // Seat 5 (top right)
    { top: '40%', left: '85%' }, // Seat 6 (middle right)
    { top: '70%', left: '75%' }, // Seat 7 (bottom right)
    // Add more for 8, 9, 10 if needed
  ];

  return (
    <div
      className="w-[1920px] h-[1080px] bg-green-700/70 relative overflow-hidden text-white p-8" // Example 16:9 aspect ratio
      style={{
        transform: `scale(var(--scale, ${scale}))`,
        transformOrigin: 'top left',
      }}
    >
      {/* Button to test scaling - REMOVE FOR PRODUCTION OVERLAY */}
      <button
        onClick={() => setScale((s) => (s === 1 ? 0.5 : 1))}
        className="absolute top-2 right-2 bg-blue-500 text-white p-1 text-xs z-50"
      >
        Toggle Scale (Test)
      </button>

      {/* Community Cards */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex space-x-3 z-20">
        {Array(5)
          .fill(null)
          .map((_, index) => (
            <Card key={index} card={gameState.communityCards[index]} />
          ))}
      </div>

      {/* Pot Display */}
      <div className="absolute top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
        <div className="bg-black/50 p-3 rounded-xl shadow-xl">
          <span className="text-3xl font-bold text-yellow-300">
            Pot: {gameState.pot}
          </span>
        </div>
      </div>

      {/* Players */}
      {gameState.players.map((player, index) => {
        // This assumes player.id can be mapped to a seat index for positioning.
        // A more robust solution would be to have seat_id on SharedPlayerState.
        // For this MVP, we'll use the index in the gameState.players array for positioning.
        // This is not ideal if player list can change order or have gaps.
        const positionStyle =
          playerPositions[index % playerPositions.length] || {}; // Fallback if more players than defined positions

        // Skip rendering if player has no ID (should not happen with valid data)
        if (!player.id) return null;

        return (
          <div
            key={player.id}
            className={`absolute p-3 bg-black/60 rounded-lg shadow-lg w-48 min-h-[6rem]
                        ${player.isActive ? 'ring-4 ring-yellow-400 shadow-yellow-500/50' : ''}
                        ${player.isFolded ? 'opacity-50' : ''}`}
            style={{ ...positionStyle }}
          >
            <div className="flex justify-between items-center mb-1">
              <span
                className={`text-lg font-bold truncate ${player.isFolded ? 'line-through' : ''}`}
              >
                {player.name}
              </span>
              {player.isDealer && (
                <span className="text-xs bg-yellow-500 text-black rounded-full px-1.5 py-0.5 font-bold">
                  D
                </span>
              )}
              {player.isSB && (
                <span className="text-xs bg-blue-500 text-white rounded-full px-1.5 py-0.5 font-bold">
                  SB
                </span>
              )}
              {player.isBB && (
                <span className="text-xs bg-red-500 text-white rounded-full px-1.5 py-0.5 font-bold">
                  BB
                </span>
              )}
            </div>
            <div className="text-xl font-semibold text-yellow-200">
              {player.stack}
            </div>
            {player.currentBet > 0 && (
              <div className="text-sm text-orange-300">
                Bet: {player.currentBet}
              </div>
            )}
            {player.lastAction && (
              <div className="text-xs text-gray-300 italic mt-0.5">
                {player.lastAction}
              </div>
            )}

            {/* Hole Cards */}
            {player.holeCards &&
              player.holeCards.length > 0 &&
              !player.isFolded && (
                <div className="flex space-x-1 mt-2 justify-center">
                  <PlayerOverlayCard card={player.holeCards[0]} />
                  <PlayerOverlayCard card={player.holeCards[1]} />
                </div>
              )}
            {player.isAllIn && (
              <div className="text-center text-red-400 font-bold mt-1 text-sm">
                ALL-IN
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default OverlayPage;
