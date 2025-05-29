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
