import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NoteList from './components/NoteList';
import NoteDetail from './components/NoteDetail';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<NoteList />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
