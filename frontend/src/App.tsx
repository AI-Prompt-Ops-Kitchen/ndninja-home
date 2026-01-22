import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        <Routes>
          <Route path="/" element={<div>Sage Mode Dashboard</div>} />
          <Route path="/login" element={<div>Login</div>} />
          <Route path="/teams" element={<div>Teams</div>} />
          <Route path="/sessions" element={<div>Sessions</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
