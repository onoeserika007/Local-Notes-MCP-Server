import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { MessageSquare, FileText } from 'lucide-react';
import NoteList from './components/NoteList';
import NoteDetail from './components/NoteDetail';
import { ChatInterface } from './components/ChatInterface';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 transition-colors"
          >
            <FileText className="w-5 h-5" />
            <span>笔记</span>
          </Link>
          <Link
            to="/chat"
            className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 transition-colors"
          >
            <MessageSquare className="w-5 h-5" />
            <span>AI 助手</span>
          </Link>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<NoteList />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
          <Route
            path="/chat"
            element={
              <div className="h-[calc(100vh-57px)] p-4">
                <ChatInterface className="h-full" />
              </div>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
