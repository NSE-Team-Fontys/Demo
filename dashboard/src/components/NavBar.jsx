import { Link } from 'react-router-dom'

export default function NavBar() {
  return (
    <nav className="bg-blue-600 text-white p-4 shadow-lg">
      <div className="max-w-7xl mx-auto flex gap-6">
        <Link to="/" className="hover:underline font-bold">
          📊 Overview
        </Link>
        <Link to="/pipeline-demo" className="hover:underline font-bold">
          🔄 Pipeline
        </Link>
        
        <Link to="/presentatie" className="hover:underline font-bold">
          🎯 Presentation
        </Link>
      </div>
    </nav>
  )
}
