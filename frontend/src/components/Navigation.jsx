import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { BookOpen, Home, BarChart3 } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="bg-white/10 backdrop-blur-sm border-b border-white/20 p-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 text-white hover:text-yellow-400 transition-colors">
            <Home className="w-5 h-5" />
            <span className="font-medium">Home</span>
          </Link>
          <Link 
            to="/interview-questions" 
            className={`flex items-center gap-2 transition-colors ${
              location.pathname === '/interview-questions' 
                ? 'text-yellow-400' 
                : 'text-white hover:text-yellow-400'
            }`}
          >
            <BookOpen className="w-5 h-5" />
            <span className="font-medium">Interview Questions</span>
          </Link>
          <Link 
            to="/scraping-dashboard" 
            className={`flex items-center gap-2 transition-colors ${
              location.pathname === '/scraping-dashboard' 
                ? 'text-yellow-400' 
                : 'text-white hover:text-yellow-400'
            }`}
          >
            <BarChart3 className="w-5 h-5" />
            <span className="font-medium">Scraping Dashboard</span>
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;