import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
// Ensure './index.css' is imported in main.tsx (should be handled in previous step)

// Import actual page components
import OperatorPage from './pages/OperatorPage';
import OverlayPage from './pages/OverlayPage';

function HomePage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">GGCast Home</h1>
      <p className="mb-4">
        Welcome to GGCast, the real-time poker game overlay system.
      </p>
      <nav>
        <ul className="space-y-2">
          <li>
            <Link
              to="/operator"
              className="text-blue-500 hover:text-blue-700 underline text-xl"
            >
              Go to Operator Panel
            </Link>
            <p className="text-sm text-gray-600">
              Manage game actions, view player states, and control the game
              flow.
            </p>
          </li>
          <li>
            <Link
              to="/overlay"
              className="text-blue-500 hover:text-blue-700 underline text-xl"
            >
              View Game Overlay
            </Link>
            <p className="text-sm text-gray-600">
              Display real-time game information, player cards, and community
              cards for streaming.
            </p>
          </li>
        </ul>
      </nav>
      <div className="mt-8 p-4 border rounded bg-gray-50">
        <h2 className="text-2xl font-semibold mb-2">Project Setup Notes:</h2>
        <p className="text-sm text-gray-700">
          - Backend runs on port 8000 (internally), providing an API and
          WebSocket server.
        </p>
        <p className="text-sm text-gray-700">
          - Frontend (Vite) runs on port 5173 (internally) for development.
        </p>
        <p className="text-sm text-gray-700">
          - Caddy acts as a reverse proxy, serving the application on port 3000.
        </p>
        <ul className="list-disc list-inside text-sm text-gray-700 mt-2">
          <li>
            Frontend (React app) is available at{' '}
            <a
              href="http://localhost:3000"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              http://localhost:3000
            </a>
          </li>
          <li>
            API requests to <code>/api/*</code> are proxied to the backend.
          </li>
          <li>
            WebSocket connections to <code>/ws/game</code> are proxied to the
            backend.
          </li>
        </ul>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      {/* Minimal global navigation for easy access to pages during development, can be removed or restyled */}
      <div className="bg-gray-100 shadow-md">
        <div className="container mx-auto px-4">
          <nav className="flex items-center justify-between py-3">
            <Link
              to="/"
              className="text-2xl font-bold text-gray-800 hover:text-gray-600"
            >
              GGCast
            </Link>
            <div>
              <Link
                to="/"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Home
              </Link>
              <Link
                to="/operator"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Operator
              </Link>
              <Link
                to="/overlay"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Overlay
              </Link>
            </div>
          </nav>
        </div>
      </div>

      <div className="container mx-auto p-4">
        {' '}
        {/* Added a container for better spacing of page content */}
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/operator" element={<OperatorPage />} />
          <Route path="/overlay" element={<OverlayPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
