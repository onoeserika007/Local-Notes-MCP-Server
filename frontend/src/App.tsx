import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageSquare, FileText } from 'lucide-react';
import NoteList from './components/NoteList';
import NoteDetail from './components/NoteDetail';
import { ChatInterface } from './components/ChatInterface';
import './App.css';

function AppLayout() {
  const location = useLocation();
  const isChat = location.pathname.startsWith('/chat');

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-2">
          <NavLink to="/" icon={<FileText className="w-5 h-5" />} label="笔记" />
          <NavLink to="/chat" icon={<MessageSquare className="w-5 h-5" />} label="AI 助手" />
        </div>
      </header>

      {/* Main */}
      <main
        className={`flex-1 ${
          isChat
            ? 'flex'
            : 'max-w-6xl mx-auto w-full px-4 py-6'
        }`}
      >
        <Routes>
          <Route path="/" element={<NoteList />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
          <Route
            path="/chat"
            element={
              <div className="flex-1 flex justify-center">
                <div className="w-full max-w-4xl flex">
                  <ChatInterface />
                </div>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

function NavLink({
  to,
  icon,
  label,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
}) {
  const location = useLocation();
  const active = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition
        ${
          active
            ? 'bg-gray-100 text-gray-900'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
    >
      {icon}
      {label}
    </Link>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
