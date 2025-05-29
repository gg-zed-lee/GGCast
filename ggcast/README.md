# GGCast (Good Game Cast)

GGCast is a web-based poker broadcast overlay system. This repository contains the source code for the backend, frontend, and shared components.

## Quick Start

To get the development environment up and running:

1.  **Clone the repository:**
    ```bash
    git clone <https://github.com/gg-zed-lee/> ggcast
    cd ggcast
    ```
    *(Replace `<your-repository-url>` with the actual URL of this repository once it's on GitHub).*

2.  **Build and run with Docker Compose:**
    ```bash
    docker compose up --build
    ```

3.  **Access the application:**
    *   **Operator Interface:** Open your browser to [http://localhost:3000/operator](http://localhost:3000/operator)
    *   **Overlay Display:** Open your browser to [http://localhost:3000/overlay](http://localhost:3000/overlay)
    *   **Backend API (example):** [http://localhost:3000/api/v1](http://localhost:3000/api/v1)
    *   **Backend WebSocket (example):** `ws://localhost:3000/ws/game`

## Project Structure

*   `/backend`: FastAPI application (Python)
    *   Manages game state, WebSocket communication, and core poker logic.
    *   Run tests with `cd backend && poetry run pytest`.
*   `/frontend`: React + TypeScript PWA (Vite)
    *   Provides the operator interface and the broadcast overlay.
    *   Run lint checks with `cd frontend && npm run lint`.
*   `/shared`: Language-agnostic schemas (TypeScript, Python)
    *   Defines data structures for communication between backend and frontend.
*   `/Caddyfile`: Configuration for the Caddy reverse proxy.
*   `/docker-compose.yml`: Defines services for local development.
*   `/.github/workflows`: GitHub Actions for CI.

## Basic Customization

### Card Asset Packs (Frontend)

*   Card images are typically stored in the `frontend/src/assets/cards/` directory (this directory might need to be created and populated).
*   To use a different set of card images:
    1.  Prepare your card images (e.g., `As.png`, `Kd.png`, `2c.svg`, etc.).
    2.  Replace the files in `frontend/src/assets/cards/` with your new images, ensuring the naming convention matches what the frontend components expect (e.g., `[Rank][Suit].png`).
    3.  Alternatively, update the frontend components that render cards (e.g., `Card.tsx`, `PlayerOverlayCard.tsx`) to use your new asset paths or naming scheme.

### Blind Structure (Backend)

*   The initial blind structure and player setup are currently hardcoded in `backend/app/main.py` around the `table_state` initialization and the `create_new_hand` / `post_blinds` calls.
*   To change starting blinds, number of players, or starting stacks for development:
    1.  Modify the `initial_players` list in `backend/app/main.py`.
    2.  Adjust the `sb_amount` and `bb_amount` passed to `create_new_hand` or `post_blinds` in `backend/app/main.py`.
*   For a production setup, this would typically be managed via an admin interface or configuration files, which are planned for future development.

### Tournament Clock Configuration (Future)

*   The `BlindClock` model exists in `backend/app/poker/models.py`, but full tournament clock management (levels, durations, breaks) is not yet implemented in the MVP.
*   Future enhancements will allow defining a full blind schedule.

## Development

### Prerequisites
*   Docker and Docker Compose
*   Node.js (for frontend development if not using Docker primarily)
*   Python & Poetry (for backend development if not using Docker primarily)

### Backend
*   Located in the `/backend` directory.
*   Uses FastAPI and Poetry.
*   To install dependencies: `cd backend && poetry install`
*   To run the dev server (if not using Docker): `cd backend && poetry run dev` (access at `http://localhost:8000`)

### Frontend
*   Located in the `/frontend` directory.
*   Uses React, TypeScript, Vite, and Tailwind CSS.
*   To install dependencies: `cd frontend && npm install`
*   To run the dev server (if not using Docker): `cd frontend && npm run dev` (access at `http://localhost:5173`)


## Contributing

Contributions are welcome! Please refer to the project's issue tracker and consider discussing significant changes before implementation.
