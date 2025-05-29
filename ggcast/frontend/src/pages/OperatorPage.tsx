import React, { useState } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { PlayerState, ActionEvent } from '../../../../shared/schema/events'; // Adjust path as needed

type ActionType = 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'all-in';

const OperatorPage: React.FC = () => {
  const { gameState, isConnected, sendAction, sendAdminNewHand } =
    useWebSocket();
  const [selectedAction, setSelectedAction] = useState<ActionType>('fold');
  const [betAmount, setBetAmount] = useState<number>(0);

  const handleActionSubmit = (playerId: string) => {
    if (!playerId) {
      console.error('No player selected or player ID is undefined.');
      return;
    }
    const actionEvent: ActionEvent = {
      type: 'PLAYER_ACTION',
      payload: {
        playerId: playerId, // Use the string ID of the player
        action: selectedAction,
        amount:
          selectedAction === 'bet' || selectedAction === 'raise'
            ? Number(betAmount)
            : undefined,
      },
    };
    sendAction(actionEvent);
    setBetAmount(0); // Reset bet amount after action
  };

  if (!isConnected) {
    return (
      <div className="p-4 text-red-500">
        WebSocket not connected. Operator controls unavailable.
      </div>
    );
  }

  if (!gameState) {
    return <div className="p-4">Loading game state...</div>;
  }

  const getPlayerSeatId = (player: PlayerState): number => {
    // This is a bit of a hack. The GameState.players has PlayerState from shared schema.
    // The activePlayerPosition is a seat_id (number).
    // We need to find the original seat_id. For now, let's assume player.id can be parsed or we find it.
    // This needs a more robust mapping if player.id isn't directly the seat_id or parsable to it.
    // For now, let's find the player in the backend's original player list if that was passed or reconstruct.
    // Or, assume player.id is like "player0", "player1" corresponding to seat_id.
    // This is a placeholder. Ideally, SharedPlayerState should include seat_id.
    // For the current MVP, we'll find the player in gameState.players by id, then use their index as a proxy for seat_id if no explicit seat_id on SharedPlayerState.
    // The backend uses `p_internal.seat_id` for `activePlayerPosition`.
    // The backend's `Player` model has `seat_id`. The `SharedPlayerState` does not explicitly have `seat_id`.
    // Let's assume for now that the order in `gameState.players` can be used, or `id` implies seat.
    // This is a known gap to be addressed by adding `seatId` to `SharedPlayerState`.
    // For now, if activePlayerPosition is set, we find that player.
    const playerIndex = gameState.players.findIndex((p) => p.id === player.id);
    return playerIndex; // Fallback: use index if seat_id not on SharedPlayerState.
    // This will only work if activePlayerPosition is also an index, which it is (seat_id)
    // The backend `Player` model has `seat_id`. `get_shared_game_state` maps to `SharedPlayerState`.
    // `active_player_position` in `SharedGameState` is `table_state.action_on_seat` (a `seat_id`).
    // So, we need `seat_id` on `SharedPlayerState`.
    // TEMPORARY: For the MVP, if SharedPlayerState doesn't have seat_id, this comparison will be tricky.
    // Let's assume the backend's `active_player_position` (a seat_id) correctly identifies whose turn it is.
    // The `player.isActive` flag in `SharedPlayerState` is the truth source from backend.
    return -1; // Should not be reached if player.isActive is used.
  };

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-3xl font-bold text-center">
        GGCast - Operator Panel
      </h1>

      <div className="text-center">
        <button
          onClick={sendAdminNewHand}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Start New Hand
        </button>
      </div>

      {/* Game Info Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-800 text-white rounded-lg shadow">
        <div>
          <span className="font-semibold">Pot:</span> {gameState.pot}
        </div>
        <div>
          <span className="font-semibold">Current Street:</span>{' '}
          <span className="capitalize">{gameState.currentStreet}</span>
        </div>
        <div>
          <span className="font-semibold">Community Cards:</span>
          <div className="flex space-x-1 mt-1">
            {gameState.communityCards.map((card, index) => (
              <div
                key={index}
                className="w-10 h-14 bg-white border border-gray-300 rounded flex items-center justify-center text-black font-bold"
              >
                {card}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Players Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {gameState.players.map((player) => (
          <div
            key={player.id}
            className={`p-4 rounded-lg shadow ${player.isActive ? 'ring-2 ring-green-500 bg-gray-700' : 'bg-gray-700'} text-white`}
          >
            <h3
              className={`font-bold text-xl mb-2 ${player.isDealer ? 'text-yellow-400' : ''}`}
            >
              {player.name} (ID: {player.id}) {player.isDealer ? '(D)' : ''}{' '}
              {player.isSB ? '(SB)' : ''} {player.isBB ? '(BB)' : ''}
            </h3>
            <p>
              <span className="font-semibold">Stack:</span> {player.stack}
            </p>
            <p>
              <span className="font-semibold">Current Bet:</span>{' '}
              {player.currentBet}
            </p>
            <p>
              <span className="font-semibold">Last Action:</span>{' '}
              {player.lastAction || 'N/A'}
            </p>
            {player.isFolded && (
              <p className="text-red-400 font-semibold">FOLDED</p>
            )}
            {player.isAllIn && (
              <p className="text-orange-400 font-semibold">ALL-IN</p>
            )}

            {player.isActive && !player.isFolded && !player.isAllIn && (
              <div className="mt-4 pt-4 border-t border-gray-600">
                <h4 className="font-semibold mb-2 text-lg">Player Action:</h4>
                <div className="space-y-2">
                  <select
                    value={selectedAction}
                    onChange={(e) =>
                      setSelectedAction(e.target.value as ActionType)
                    }
                    className="w-full p-2 rounded bg-gray-600 border border-gray-500 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="fold">Fold</option>
                    <option value="check">Check</option>
                    <option value="call">Call</option>
                    <option value="bet">Bet</option>
                    <option value="raise">Raise</option>
                    <option value="all-in">All-In</option>
                  </select>

                  {(selectedAction === 'bet' || selectedAction === 'raise') && (
                    <input
                      type="number"
                      value={betAmount}
                      onChange={(e) => setBetAmount(Number(e.target.value))}
                      placeholder="Amount"
                      className="w-full p-2 rounded bg-gray-600 border border-gray-500 focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}
                  <button
                    onClick={() => handleActionSubmit(player.id)}
                    className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-opacity-75"
                  >
                    Submit{' '}
                    {selectedAction.charAt(0).toUpperCase() +
                      selectedAction.slice(1)}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OperatorPage;
