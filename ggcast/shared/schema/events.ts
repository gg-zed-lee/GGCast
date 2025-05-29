// shared/schema/events.ts
export interface PlayerState {
  id: string;
  name: string;
  stack: number;
  holeCards?: [string, string]; // Should be string[] to match Python Optional[List[str]] more closely
  currentBet: number;
  lastAction?: string; // e.g., "fold", "check", "call", "bet", "raise"
  isActive: boolean; // Is it their turn?
  isDealer: boolean;
  isSB: boolean;
  isBB: boolean;
  isFolded: boolean;
  isAllIn: boolean;
}

export interface GameState {
  pot: number;
  communityCards: string[];
  players: PlayerState[];
  currentStreet: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown' | 'setup' | 'hand_over'; // Added setup & hand_over
  dealerPosition: number; // seat_id of the dealer
  activePlayerPosition?: number; // seat_id of the player whose turn it is
}

export interface ActionEvent {
  type: "PLAYER_ACTION" | "ADMIN_NEW_HAND"; // Added ADMIN_NEW_HAND
  payload: {
    playerId: string;
    action: "fold" | "check" | "call" | "bet" | "raise" | "all-in";
    amount?: number;
  } | AdminNewHandPayload; // Union type for payload
}

// Payload for ADMIN_NEW_HAND if it has specific data, otherwise can be {} or omitted if no payload data needed
export interface AdminNewHandPayload {
  // Example: could define specific parameters if needed for new hand setup via admin action
  // For now, assuming it might not need a specific payload beyond the type if backend handles defaults
}


export interface ClockEvent {
  type: "CLOCK_UPDATE";
  payload: {
    level: number;
    timeLeft: number; // seconds
    smallBlind: number;
    bigBlind: number;
    ante?: number;
  };
}
