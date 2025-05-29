from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.poker.game_logic import (
    advance_street,
    create_new_hand,
    deal_hole_cards,
    post_blinds,
    record_action,
)

from app.poker.models import Player, TableState

try:
    from ggcast.shared.schema.events import (
        ActionEvent,
        GameState as SharedGameState,
        PlayerState as SharedPlayerState,
    )
except ImportError:
    # # print("Attempting fallback import for shared.schema.events") # Removed
    from shared.schema.events import (
        ActionEvent,
        GameState as SharedGameState,
        PlayerState as SharedPlayerState,
    )


app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)


manager = ConnectionManager()

initial_players_data = [
    {"id": "player1", "name": "Alice", "stack": 1000, "seat_id": 0},
    {"id": "player2", "name": "Bob", "stack": 1000, "seat_id": 1},
    {"id": "player3", "name": "Charlie", "stack": 1000, "seat_id": 2},
]
initial_players_models = [Player(**data) for data in initial_players_data]

table_state = TableState(players=initial_players_models, dealer_button_position=0)


def get_shared_game_state(current_table_state: TableState) -> SharedGameState:
    shared_players = []
    for p_internal in current_table_state.players:
        shared_players.append(
            SharedPlayerState(
                id=p_internal.id,
                name=p_internal.name,
                stack=p_internal.stack,
                hole_cards=p_internal.hole_cards if p_internal.hole_cards else None,
                current_bet=p_internal.current_bet,
                last_action=p_internal.last_action,
                is_active=(
                    current_table_state.action_on_seat == p_internal.seat_id
                    and not p_internal.is_folded
                ),
                is_dealer=(
                    current_table_state.dealer_button_position == p_internal.seat_id
                ),
                is_sb=(current_table_state.small_blind_position == p_internal.seat_id),
                is_bb=(current_table_state.big_blind_position == p_internal.seat_id),
                is_folded=p_internal.is_folded,
                is_all_in=p_internal.is_all_in,
            )
        )

    total_pot_amount = sum(pot.amount for pot in current_table_state.pots)
    if not current_table_state.pots and any(
        p.current_bet > 0 for p in current_table_state.players
    ):
        total_pot_amount = sum(p.current_bet for p in current_table_state.players)

    return SharedGameState(
        pot=total_pot_amount,
        community_cards=current_table_state.community_cards,
        players=shared_players,
        current_street=current_table_state.current_street,
        dealer_position=current_table_state.dealer_button_position,
        active_player_position=current_table_state.action_on_seat,
    )


@app.get("/api/v1")
async def get_api_v1():
    return {"message": "Hello from GGCast API v1"}


@app.websocket("/ws/game")
async def websocket_game_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            get_shared_game_state(table_state).model_dump(by_alias=True)
        )

        while True:
            data = await websocket.receive_json()
            try:
                action_event = ActionEvent.model_validate(data)
            except Exception as e:
                await websocket.send_json(
                    {"error": f"Invalid event structure: {str(e)}"}
                )
                continue

            global table_state

            if action_event.type == "PLAYER_ACTION":
                if (
                    not isinstance(action_event.payload, dict)
                    or "player_id" not in action_event.payload
                ):
                    await websocket.send_json(
                        {"error": "Invalid PLAYER_ACTION payload structure."}
                    )
                    continue

                payload_data = action_event.payload  
                player_id = payload_data.get("player_id")
                action_type = payload_data.get("action")
                amount_data = payload_data.get("amount")

                player_obj = next(
                    (p for p in table_state.players if p.id == player_id), None
                )

                if not player_obj:
                    await websocket.send_json(
                        {"error": f"Player with id {player_id} not found."}
                    )
                    continue
                if player_obj.seat_id != table_state.action_on_seat:
                    await websocket.send_json(
                        {
                            "error": f"Not player {player_obj.name}'s turn (seat {player_obj.seat_id}). Action on seat {table_state.action_on_seat}"
                        }
                    )
                    continue
                
                table_state = record_action(
                    table=table_state,
                    seat_id=player_obj.seat_id,
                    action=action_type,
                    amount=amount_data,
                )

                if (
                    table_state.action_on_seat is None
                    and table_state.current_street not in ["showdown", "hand_over"]
                ):
                    table_state = advance_street(table_state)

                if table_state.current_street == "hand_over" or (
                    table_state.current_street == "showdown"
                    and table_state.action_on_seat is None
                ):
                    pass

                await manager.broadcast_json(
                    get_shared_game_state(table_state).model_dump(by_alias=True)
                )

            elif action_event.type == "ADMIN_NEW_HAND":
                current_players_in_game = [
                    p.model_copy(deep=True) for p in table_state.players
                ]

                num_players = len(current_players_in_game)
                if num_players > 0:
                    current_dealer_idx = -1
                    for idx, p_model in enumerate(current_players_in_game):
                        if p_model.seat_id == table_state.dealer_button_position:
                            current_dealer_idx = idx
                            break

                    new_dealer_seat_id = current_players_in_game[0].seat_id  
                    if current_dealer_idx != -1:
                        next_dealer_player_idx = (current_dealer_idx + 1) % num_players
                        new_dealer_seat_id = current_players_in_game[
                            next_dealer_player_idx
                        ].seat_id

                    table_state = create_new_hand(
                        TableState(),
                        current_players_in_game,
                        new_dealer_seat_id,
                        10,
                        20,
                    )
                    table_state = post_blinds(table_state, 10, 20)
                    table_state = deal_hole_cards(table_state)
                    await manager.broadcast_json(
                        get_shared_game_state(table_state).model_dump(by_alias=True)
                    )
                else:
                    await websocket.send_json(
                        {"error": "Cannot start new hand, no players."}
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


class MockRfidInput(BaseModel):
    seat_id: int
    card1: str
    card2: str


@app.post("/mock/rfid")
async def mock_rfid_input(data: MockRfidInput):
    global table_state
    player_to_update = next(
        (p for p in table_state.players if p.seat_id == data.seat_id), None
    )

    if player_to_update:
        player_to_update.hole_cards = [data.card1, data.card2]
        await manager.broadcast_json(
            get_shared_game_state(table_state).model_dump(by_alias=True)
        )
        return {
            "message": f"Hole cards updated for player at seat {data.seat_id} to {player_to_update.hole_cards}"
        }
    else:
        return {"error": f"Player not found at seat {data.seat_id}"}, 404


if table_state.current_street == "setup":
    table_state = create_new_hand(
        table_state, initial_players_models, dealer_seat=0, sb_amount=10, bb_amount=20
    )
    table_state = post_blinds(table_state, 10, 20)
    table_state = deal_hole_cards(table_state)

# To run (from ggcast/backend directory): poetry run uvicorn app.main:app --reload
# Or using the script in pyproject.toml: poetry run dev
overwrite_file_with_block
ggcast/backend/app/poker/game_logic.py
from typing import List, Optional

from .models import Player, Pot, TableState


def create_new_hand(
    table: TableState,
    players_at_table: List[Player],
    dealer_seat: int,
    sb_amount: int,
    bb_amount: int,
) -> TableState:
    # # print(f"Creating new hand. Dealer: {dealer_seat}, SB: {sb_amount}, BB: {bb_amount}") # Removed
    table.community_cards = []
    table.pots = [
        Pot(
            amount=0,
            eligible_players=[p.seat_id for p in players_at_table if not p.is_folded],
        )
    ] 
    table.current_street = "preflop"
    table.action_on_seat = None
    table.min_bet = bb_amount 
    table.last_raiser_seat = None
    table.current_bet_to_match = 0
    table.street_opener_seat = None 

    active_players_in_new_hand = []
    num_players = len(players_at_table)

    for p_template in players_at_table:
        player = p_template.model_copy(
            deep=True
        ) 
        player.hole_cards = []
        player.current_bet = 0
        player.total_bet_in_hand = 0
        player.is_folded = False
        player.is_all_in = False
        player.last_action = None
        active_players_in_new_hand.append(player)

    table.players = active_players_in_new_hand
    table.dealer_button_position = dealer_seat

    dealer_player_index = -1
    for i, p in enumerate(table.players):
        if p.seat_id == dealer_seat:
            dealer_player_index = i
            break

    if dealer_player_index == -1:
        raise ValueError(f"Dealer seat {dealer_seat} not found among players.")

    if num_players > 1:
        sb_player_index = (dealer_player_index + 1) % num_players
        bb_player_index = (dealer_player_index + 2) % num_players
        if num_players == 2: 
            sb_player_index = dealer_player_index
            bb_player_index = (dealer_player_index + 1) % num_players

        table.small_blind_position = table.players[sb_player_index].seat_id
        table.big_blind_position = table.players[bb_player_index].seat_id
    else: 
        table.small_blind_position = None
        table.big_blind_position = None
    return table


def post_blinds(table: TableState, sb_amount: int, bb_amount: int) -> TableState:
    # # print(f"Posting blinds. SB: {sb_amount}, BB: {bb_amount}") # Removed
    num_players = len(table.players)
    if num_players == 0:
        return table

    if table.small_blind_position is not None:
        sb_player = next(
            (p for p in table.players if p.seat_id == table.small_blind_position), None
        )
        if sb_player:
            sb_bet = min(sb_player.stack, sb_amount)
            sb_player.stack -= sb_bet
            sb_player.current_bet = sb_bet
            sb_player.total_bet_in_hand = sb_bet
            sb_player.last_action = "blind"
            if sb_player.stack == 0:
                sb_player.is_all_in = True
            # # print(f"Player at seat {sb_player.seat_id} posted SB: {sb_bet}") # Removed

    if table.big_blind_position is not None:
        bb_player = next(
            (p for p in table.players if p.seat_id == table.big_blind_position), None
        )
        if bb_player:
            bb_bet = min(bb_player.stack, bb_amount)
            bb_player.stack -= bb_bet
            bb_player.current_bet = bb_bet
            bb_player.total_bet_in_hand = bb_bet
            bb_player.last_action = "blind"
            if bb_player.stack == 0:
                bb_player.is_all_in = True
            # # print(f"Player at seat {bb_player.seat_id} posted BB: {bb_bet}") # Removed
            table.current_bet_to_match = bb_bet 
            table.min_bet = bb_amount 

    if num_players > 1:
        if num_players == 2: 
            action_seat_index = next(
                i
                for i, p in enumerate(table.players)
                if p.seat_id == table.small_blind_position
            )
        else: 
            bb_player_idx = next(
                i
                for i, p in enumerate(table.players)
                if p.seat_id == table.big_blind_position
            )
            action_seat_index = (bb_player_idx + 1) % num_players

        start_idx = action_seat_index
        while True:
            player_to_act = table.players[start_idx % num_players]
            if not player_to_act.is_folded and not player_to_act.is_all_in:
                table.action_on_seat = player_to_act.seat_id
                table.street_opener_seat = (
                    player_to_act.seat_id
                ) 
                break
            start_idx += 1
            if (
                start_idx % num_players == action_seat_index
            ): 
                table.action_on_seat = None 
                table.street_opener_seat = None
                break
    return table


def deal_hole_cards(table: TableState, num_cards: int = 2) -> TableState:
    # # print(f"Dealing {num_cards} hole cards to each active player.") # Removed
    for player in table.players:
        if not player.is_folded:
            player.hole_cards = [
                f"Xx{i + 1}" for i in range(num_cards)
            ] 
            # # print(f"Dealt cards to player at seat {player.seat_id}") # Removed
    return table


def _get_next_active_player_seat(
    table: TableState, start_seat_id: int
) -> Optional[int]:
    player_indices = {p.seat_id: i for i, p in enumerate(table.players)}
    start_player_idx = player_indices.get(start_seat_id)

    if start_player_idx is None:
        return None 

    num_players = len(table.players)
    for i in range(1, num_players + 1):
        next_player_idx = (start_player_idx + i) % num_players
        next_player = table.players[next_player_idx]
        if not next_player.is_folded and not next_player.is_all_in:
            return next_player.seat_id
    return None 


def _check_if_betting_round_is_over(table: TableState) -> bool:
    active_players = [p for p in table.players if not p.is_folded]
    if not active_players:
        return True
    if len(active_players) == 1:
        # # print("Betting round over: Only one player left.") # Removed
        return True

    if table.action_on_seat is None:
        # # print("Betting round over: action_on_seat is None (no one to act).") # Removed
        return True

    all_bets_matched = True
    for p in active_players:
        if p.is_all_in:
            continue
        if p.current_bet < table.current_bet_to_match:
            all_bets_matched = False
            break

    is_bb_option_case = (
        table.current_street == "preflop"
        and table.action_on_seat == table.big_blind_position
        and table.current_bet_to_match
        == next(
            (
                p.current_bet
                for p in table.players
                if p.seat_id == table.big_blind_position
            ),
            0,
        )
        and table.last_raiser_seat is None
    )

    if is_bb_option_case:
        # # print("Betting round continues: BB option.") # Removed
        return False

    if all_bets_matched:
        is_back_to_last_raiser = (
            table.last_raiser_seat is not None
            and table.action_on_seat == table.last_raiser_seat
        )
        if is_back_to_last_raiser:
            # # print( # Removed
            # #     "Betting round over: Action back to the last raiser, and all bets matched."
            # # )
            return True

        all_checked_around_to_opener = (
            table.current_bet_to_match == 0
            and table.last_raiser_seat is None
            and table.action_on_seat == table.street_opener_seat
        )
        if all_checked_around_to_opener:
            # # print( # Removed
            # #     "Betting round over: All players checked around to the street opener."
            # # )
            return True

        if (
            table.current_bet_to_match > 0
            and table.last_raiser_seat is not None
            and not is_back_to_last_raiser
        ):
            # # print( # Removed
            # #     f"Betting round continues: Bets matched, but action not yet full circle to raiser (action on {table.action_on_seat}, raiser {table.last_raiser_seat})."
            # # )
            return False

        if (
            table.current_bet_to_match == 0
            and table.last_raiser_seat is None
            and not all_checked_around_to_opener
        ):
            # # print( # Removed
            # #     f"Betting round continues: All checks, but action not yet full circle to opener (action on {table.action_on_seat}, opener {table.street_opener_seat})."
            # # )
            return False
        
        # # print( # Removed
        # #     "Betting round over: All bets matched and conditions for continuation not met."
        # # )
        return True

    # # print( # Removed
    # #     f"Betting round continues: Bets not all matched (action on {table.action_on_seat}, to match {table.current_bet_to_match})."
    # # )
    return False


def record_action(
    table: TableState, seat_id: int, action: str, amount: Optional[int] = None
) -> TableState:
    if table.action_on_seat != seat_id:
        # # print( # Removed
        # #     f"Warning: Action by seat {seat_id} but it's seat {table.action_on_seat}'s turn."
        # # )
        pass 

    player = next((p for p in table.players if p.seat_id == seat_id), None)
    if not player or player.is_folded or player.is_all_in:
        # # print(f"Warning: Player {seat_id} cannot act (not found, folded, or all-in).") # Removed
        table.action_on_seat = _get_next_active_player_seat(table, seat_id)
        return table

    # # print( # Removed
    # #     f"Seat {seat_id} action: {action}, amount: {amount if amount is not None else ''}"
    # # )
    player.last_action = action

    if action == "fold":
        player.is_folded = True
    elif action == "check":
        if player.current_bet < table.current_bet_to_match:
            # # print( # Removed
            # #     f"Warning: Player {seat_id} cannot check, current bet {player.current_bet} < bet to match {table.current_bet_to_match}"
            # # )
            player.last_action = "invalid_check_attempt" 
    elif action == "call":
        bet_amount = table.current_bet_to_match - player.current_bet
        if bet_amount > player.stack: 
            bet_amount = player.stack

        player.stack -= bet_amount
        player.current_bet += bet_amount
        player.total_bet_in_hand += bet_amount
        if player.stack == 0:
            player.is_all_in = True
    elif action == "bet":
        if amount is None or amount <= 0: 
            # # print(f"Warning: Player {seat_id} invalid bet amount {amount}.") # Removed
            player.last_action = "invalid_bet_attempt"
        elif amount > player.stack:
            # # print( # Removed
            # #     f"Warning: Player {seat_id} bet amount {amount} > stack {player.stack}. Treated as all-in."
            # # )
            amount = player.stack 
            player.is_all_in = True
        else: 
            player.stack -= amount
            player.current_bet += amount 
            player.total_bet_in_hand += amount
            table.current_bet_to_match = player.current_bet
            table.last_raiser_seat = player.seat_id
            if player.stack == 0:
                player.is_all_in = True

    elif action == "raise":
        if (
            amount is None or amount <= table.current_bet_to_match
        ): 
            # # print(f"Warning: Player {seat_id} invalid raise amount {amount}.") # Removed
            player.last_action = "invalid_raise_attempt"
        elif (
            amount > player.stack + player.current_bet
        ): 
            # # print( # Removed
            # #     f"Warning: Player {seat_id} raise amount {amount} > stack available. Treated as all-in."
            # # )
            amount = player.stack + player.current_bet 
            player.is_all_in = True
        else: 
            actual_bet_for_street = amount - player.current_bet
            player.stack -= actual_bet_for_street
            player.total_bet_in_hand += actual_bet_for_street
            player.current_bet = amount 

            table.current_bet_to_match = player.current_bet
            table.last_raiser_seat = player.seat_id
            if player.stack == 0:
                player.is_all_in = True
    elif action == "all-in":
        all_in_amount = player.stack
        player.current_bet += all_in_amount
        player.total_bet_in_hand += all_in_amount
        player.stack = 0
        player.is_all_in = True
        if player.current_bet > table.current_bet_to_match:
            table.current_bet_to_match = player.current_bet
            table.last_raiser_seat = player.seat_id

    potential_next_actor_seat_id = _get_next_active_player_seat(table, seat_id)
    original_action_on_seat_for_check = (
        table.action_on_seat
    ) 
    table.action_on_seat = potential_next_actor_seat_id

    round_is_over = _check_if_betting_round_is_over(table)

    if round_is_over:
        # # print( # Removed
        # #     f"Betting round is over after action from seat {original_action_on_seat_for_check}."
        # # )
        table.action_on_seat = None 
    else:
        if table.action_on_seat is not None:
            # # print(f"Action moves to seat {table.action_on_seat}") # Removed
            pass 
        else:
            # # print( # Removed
            # #     f"No next active player found after seat {original_action_on_seat_for_check}, round should be over."
            # # )
            if (
                not round_is_over
            ): 
                # # print( # Removed
                # #     "Contradiction: round not over but no next player. Forcing round over."
                # # )
                table.action_on_seat = None

    return table


def _collect_bets_and_form_pots(table: TableState) -> TableState:
    # # print("Collecting bets and forming pots...") # Removed

    if not table.pots:
        table.pots.append(
            Pot(amount=0, eligible_players=[])
        ) 

    main_pot = table.pots[0]
    current_pot_amount_from_this_street = 0

    for player in table.players:
        if player.current_bet > 0:
            current_pot_amount_from_this_street += player.current_bet
            if (
                player.seat_id not in main_pot.eligible_players and not player.is_folded
            ): 
                main_pot.eligible_players.append(player.seat_id)

    main_pot.amount += current_pot_amount_from_this_street
    # # print(f"Main pot is now {main_pot.amount} with players {main_pot.eligible_players}") # Removed

    for player in table.players:
        player.current_bet = 0

    # # print("TODO: Implement side pot logic for _collect_bets_and_form_pots") # Removed
    return table


def advance_street(table: TableState) -> TableState:
    # # print(f"Advancing street from {table.current_street}") # Removed
    table = _collect_bets_and_form_pots(table)

    table.current_bet_to_match = 0
    table.last_raiser_seat = None
    table.street_opener_seat = None 

    if table.current_street == "preflop":
        table.current_street = "flop"
        table.community_cards.extend(["Fx1", "Fx2", "Fx3"]) 
        # # print(f"Dealt flop: {table.community_cards}") # Removed
    elif table.current_street == "flop":
        table.current_street = "turn"
        table.community_cards.append("Tx1") 
        # # print(f"Dealt turn: {table.community_cards}") # Removed
    elif table.current_street == "turn":
        table.current_street = "river"
        table.community_cards.append("Rx1") 
        # # print(f"Dealt river: {table.community_cards}") # Removed
    elif table.current_street == "river":
        table.current_street = "showdown"
        # # print("Proceeding to showdown.") # Removed
    elif table.current_street == "showdown" or table.current_street == "hand_over":
        table.current_street = "hand_over"
        # # print("Hand is over.") # Removed
        table.action_on_seat = None
        return table 
    else: 
        # # print( # Removed
        # #     f"Warning: Cannot advance street from {table.current_street} in this manner."
        # # )
        return table

    num_active_players = sum(
        1 for p in table.players if not p.is_folded and not p.is_all_in
    )

    if num_active_players < 2 and table.current_street not in ["showdown", "hand_over"]:
        # # print( # Removed
        # #     "Less than 2 active (non-all-in) players. Advancing to showdown or ending hand."
        # # )
        table.action_on_seat = None
    
    elif table.current_street not in ["showdown", "hand_over"]:
        first_to_act_seat = None
        num_players = len(table.players) 
        if num_players == 0: 
            table.action_on_seat = None
            # # print( # Removed
            # #     f"Warning: advance_street called with no players on table. Street: {table.current_street}"
            # # )
            return table

        if num_players == 2:
            dealer_player = next(
                (p for p in table.players if p.seat_id == table.dealer_button_position),
                None,
            )
            if (
                dealer_player
                and not dealer_player.is_folded
                and not dealer_player.is_all_in
            ):
                first_to_act_seat = table.dealer_button_position
            else:
                other_player_seat = next(
                    (
                        p.seat_id
                        for p in table.players
                        if p.seat_id != table.dealer_button_position
                    ),
                    None,
                )
                if other_player_seat is not None:
                    other_player_model = next(
                        (p for p in table.players if p.seat_id == other_player_seat),
                        None,
                    )
                    if (
                        other_player_model
                        and not other_player_model.is_folded
                        and not other_player_model.is_all_in
                    ):
                        first_to_act_seat = other_player_seat
        else: 
            dealer_idx = -1
            for i, p in enumerate(table.players):
                if p.seat_id == table.dealer_button_position:
                    dealer_idx = i
                    break

            if dealer_idx != -1:
                for i in range(1, len(table.players) + 1):
                    player_to_check_idx = (dealer_idx + i) % len(table.players)
                    player_to_check = table.players[player_to_check_idx]
                    if not player_to_check.is_folded and not player_to_check.is_all_in:
                        first_to_act_seat = player_to_check.seat_id
                        break

        table.action_on_seat = first_to_act_seat
        table.street_opener_seat = (
            first_to_act_seat 
        )
        if first_to_act_seat is not None:
            # # print( # Removed
            # #     f"New street: {table.current_street}. Action on seat {table.action_on_seat}."
            # # )
            pass 
        else:
            # # print(f"New street: {table.current_street}. No active player to act.") # Removed
            pass

    return table
overwrite_file_with_block
ggcast/backend/app/poker/models.py
from typing import List, Literal, Optional 

from pydantic import BaseModel, Field

try:
    from ggcast.shared.schema.events import PlayerState as SharedPlayerState
except ImportError: 
    # # print(f"ImportError for ggcast.shared.schema.events: {e1}") # Removed
    try:
        from shared.schema.events import PlayerState as SharedPlayerState
        # # print("Successfully imported from shared.schema.events") # Removed
    except ImportError: 
        # # print(f"ImportError for shared.schema.events: {e2}") # Removed
        class SharedPlayerState(BaseModel): # type: ignore 
            id: str
            name: str
            pass  


class Player(BaseModel):
    id: str
    name: str
    stack: int
    hole_cards: list[str] = Field(default_factory=list) 
    current_bet: int = 0 
    total_bet_in_hand: int = (
        0 
    )
    last_action: Optional[str] = (
        None 
    )
    is_folded: bool = False
    is_all_in: bool = False
    seat_id: int 


class Pot(BaseModel):
    amount: int = 0
    eligible_players: list[int] = Field( 
        default_factory=list
    ) 
    is_side_pot: bool = False


class TableState(BaseModel):
    players: list[Player] = Field(default_factory=list) 
    community_cards: list[str] = Field( 
        default_factory=list
    ) 
    pots: list[Pot] = Field(default_factory=list) 
    current_street: Literal[
        "setup", "preflop", "flop", "turn", "river", "showdown", "hand_over"
    ] = "setup"
    dealer_button_position: int = 0 
    small_blind_position: Optional[int] = None
    big_blind_position: Optional[int] = None
    action_on_seat: Optional[int] = None 
    min_bet: int = 0 
    last_raiser_seat: Optional[int] = None 
    current_bet_to_match: int = (
        0 
    )
    street_opener_seat: Optional[int] = (
        None 
    )


class BlindClock(BaseModel):
    current_level: int = 1
    small_blind: int = 10
    big_blind: int = 20
    ante: int = 0
    time_remaining_in_level: int = 600 
overwrite_file_with_block
ggcast/.github/workflows/backend-ci.yml
name: Backend CI

on:
  push:
    branches: [ main ] 
    paths:
      - 'backend/**'
      - 'shared/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'backend/**'
      - 'shared/**'
      - '.github/workflows/backend-ci.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10' 
    - name: Install Poetry
      run: pipx install poetry
    - name: Install dependencies
      run: poetry install --no-root --sync --with dev
    - name: Run Ruff Linter Check
      run: poetry run ruff check . --config pyproject.toml
    - name: Run Ruff Formatter Check
      run: poetry run ruff format --check . --config pyproject.toml
    - name: Run Black Formatter Check
      run: poetry run black --check . --config pyproject.toml
    - name: Run Pytest
      run: poetry run pytest
      env:
        PYTHONPATH: /app 
overwrite_file_with_block
ggcast/.github/workflows/frontend-ci.yml
name: Frontend CI

on:
  push:
    branches: [ main ]
    paths:
      - 'frontend/**'
      - 'shared/**'
      - '.github/workflows/frontend-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'frontend/**'
      - 'shared/**'
      - '.github/workflows/frontend-ci.yml'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
    - uses: actions/checkout@v4
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18' 
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json 

    - name: Install dependencies
      run: npm ci 
    - name: Lint and Format Check
      run: npm run lint 
    - name: Build Project
      run: npm run build
overwrite_file_with_block
ggcast/frontend/package.json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx --report-unused-disable-directives --max-warnings 0 && prettier --check ./**/*.{js,jsx,ts,tsx,css,md,json}",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^7.6.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@typescript-eslint/eslint-plugin": "^7.2.0",
    "@typescript-eslint/parser": "^7.2.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.6",
    "postcss": "^8.4.38",
    "prettier": "^3.1.0", 
    "tailwindcss": "^3.4.8",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
