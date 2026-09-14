import { Kanban, Moon, Sun } from 'lucide-react';
import { Link, Route, Routes } from 'react-router-dom';
import { useTheme } from './hooks/useTheme';
import { BoardsPage } from './pages/BoardsPage';
import { BoardPage } from './pages/BoardPage';

function App() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-title">
          <span className="logo-mark">
            <Kanban strokeWidth={2.25} />
          </span>
          Flowboard
        </Link>
        <div className="header-actions">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            aria-label="Toggle color theme"
          >
            {theme === 'light' ? <Moon /> : <Sun />}
          </button>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<BoardsPage />} />
          <Route path="/boards/:id" element={<BoardPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
