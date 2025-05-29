# shared/schema/events.py
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field

class PlayerState(BaseModel):
    id: str
    name: str
    stack: int
    hole_cards: Optional[List[str]] = Field(default=None, alias='holeCards') # e.g., ["As", "Kd"]
    current_bet: int = Field(default=0, alias='currentBet')
    last_action: Optional[str] = Field(default=None, alias='lastAction')
    is_active: bool = Field(default=False, alias='isActive') # Is it their turn?
    is_dealer: bool = Field(default=False, alias='isDealer')
    is_sb: bool = Field(default=False, alias='isSB')
    is_bb: bool = Field(default=False, alias='isBB')
    is_folded: bool = Field(default=False, alias='isFolded')
    is_all_in: bool = Field(default=False, alias='isAllIn')

    class Config:
        populate_by_name = True # Allows using aliases in constructor and model_dump
        # alias_generator = lambda field_name: field_name.replace("_", "") # Basic snake_case to camelCase, if needed


class GameState(BaseModel):
    pot: int
    community_cards: List[str] = Field(alias='communityCards') # e.g., ["Ah", "Td", "Js"]
    players: List[PlayerState]
    current_street: Literal['setup', 'preflop', 'flop', 'turn', 'river', 'showdown', 'hand_over'] = Field(alias='currentStreet')
    dealer_position: int = Field(alias='dealerPosition') # seat_id of the dealer
    active_player_position: Optional[int] = Field(default=None, alias='activePlayerPosition') # seat_id of the player whose turn it is
    
    class Config:
        populate_by_name = True

# --- ActionEvent related models ---
class PlayerActionPayload(BaseModel):
    player_id: str = Field(alias='playerId')
    action: Literal["fold", "check", "call", "bet", "raise", "all-in"]
    amount: Optional[int] = None

class AdminNewHandPayload(BaseModel):
    # Define fields if ADMIN_NEW_HAND needs a specific payload, e.g., dealer_seat_id: Optional[int] = None
    # For now, keeping it simple. If no specific payload, this can be an empty model or just rely on type.
    pass

class ActionEvent(BaseModel):
    type: Literal["PLAYER_ACTION", "ADMIN_NEW_HAND"]
    # The payload type depends on the 'type' field. Pydantic doesn't directly support discriminated unions
    # in the same way as TypeScript out-of-the-box for parsing without custom logic or Pydantic v2 features.
    # For simplicity in Pydantic v1 style, we might make payload more generic or parse it in two steps.
    # Using Union for type hinting, but validation needs care.
    payload: Union[PlayerActionPayload, AdminNewHandPayload]

    class Config:
        populate_by_name = True


# --- ClockEvent (remains unchanged but included for completeness) ---
class ClockEventPayload(BaseModel):
    level: int
    time_left: int = Field(alias='timeLeft')  # seconds
    small_blind: int = Field(alias='smallBlind')
    big_blind: int = Field(alias='bigBlind')
    ante: Optional[int] = None
    
    class Config:
        populate_by_name = True

class ClockEvent(BaseModel):
    type: Literal["CLOCK_UPDATE"]
    payload: ClockEventPayload

    class Config:
        populate_by_name = True
